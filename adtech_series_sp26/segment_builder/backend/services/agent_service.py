"""Agent service for LLM-powered segment building."""

import json
import logging
import os
import re
from typing import Any

from openai import OpenAI

from backend.config.features import FEATURES, get_all_features
from backend.config.settings import get_settings
from backend.models.segment import SegmentCondition, SegmentDefinition, SegmentGroup
from backend.services.segment_service import get_segment_service
from backend.services.sql_generator import get_sql_generator

logger = logging.getLogger(__name__)


def _detect_databricks_apps_env() -> bool:
    """Detect if running in Databricks Apps environment (use SDK default auth)."""
    return bool(
        os.environ.get("DATABRICKS_APP_NAME")
        or os.environ.get("DATABRICKS_HOST")
    )


def get_feature_schema() -> str:
    """Generate a description of available features for the LLM."""
    lines = ["Available features for audience segmentation:"]

    for name, meta in FEATURES.items():
        feature_type = meta["type"]
        operators = ", ".join(meta["operators"])
        desc = meta.get("description", "")

        line = f"- {name} ({meta['display_name']}): {feature_type}, operators: [{operators}]"
        if desc:
            line += f" - {desc}"
        if meta.get("values"):
            line += f" Values: {meta['values']}"
        if meta.get("brackets"):
            bracket_labels = [b["label"] for b in meta["brackets"]]
            line += f" Brackets: {bracket_labels}"
        elif meta.get("range"):
            line += f" Range: {meta['range']['min']}-{meta['range']['max']}"

        lines.append(line)

    return "\n".join(lines)


SYSTEM_PROMPT = f"""You are an audience segmentation assistant for advertising campaigns.
You help users build audience segments by translating natural language requests into structured segment rules.

{get_feature_schema()}

When the user describes an audience, respond with:
1. A brief natural language confirmation of what you understood
2. A JSON segment definition wrapped in ```json blocks

IMPORTANT: For features with brackets (age, income_level), ALWAYS use the IN operator with bracket labels.
- age brackets: "Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"
  - "over 50" → select brackets that include ages over 50: IN ["45-54", "55-64", "65+"]
  - "25-54" → select brackets that overlap: IN ["25-34", "35-44", "45-54"]
  - "young adults" → IN ["18-24", "25-34"]
- income_level brackets: "<10K", "10K-15K", "15K-25K", "25K-35K", "35K-50K", "50K-75K", "75K-100K", "100K-150K", "150K-200K", "200K+"
  - "high income" → IN ["100K-150K", "150K-200K", "200K+"]
  - "under 50K" → IN ["<10K", "10K-15K", "15K-25K", "25K-35K", "35K-50K"]
Do NOT use GT, LT, GTE, LTE, or BETWEEN operators for age or income_level. Always use bracket labels with IN.

JSON format:

```json
{{
  "name": "segment_name",
  "description": "Human readable description",
  "groups": [
    {{
      "id": "group_1",
      "logic": "AND",
      "conditions": [
        {{
          "id": "cond_1",
          "feature": "feature_name",
          "operator": "IS|IN|NOT",
          "values": ["value1", "value2"]
        }}
      ]
    }}
  ],
  "group_logic": "AND"
}}
```

Rules:
- Use exact feature names from the list above
- Use appropriate operators for the feature type
- For boolean features, use true/false as values
- For IN/NOT operators, provide multiple values as an array
- Generate unique IDs for groups and conditions (e.g., "group_1", "cond_1")
- Always wrap the JSON output in ```json code blocks

Example:
User: "Cat owners over 50 in Texas"
Response: I'll create a segment for cat owners aged 45 and above in Texas.

```json
{{
  "name": "cat_owners_over_50_texas",
  "description": "Cat owners over 50 in Texas",
  "groups": [
    {{
      "id": "group_1",
      "logic": "AND",
      "conditions": [
        {{"id": "cond_1", "feature": "is_cat_owner", "operator": "IS", "values": [true]}},
        {{"id": "cond_2", "feature": "age", "operator": "IN", "values": ["45-54", "55-64", "65+"]}},
        {{"id": "cond_3", "feature": "state", "operator": "IS", "values": ["TX"]}}
      ]
    }}
  ],
  "group_logic": "AND"
}}
```

If the user asks to modify an existing segment, update only the relevant parts while preserving the rest.
If the request is unclear, ask clarifying questions.
Always respond with valid JSON that can be parsed."""


class AgentService:
    """Service for LLM-powered segment building."""

    def __init__(self):
        self.settings = get_settings()
        self._use_sdk_auth = _detect_databricks_apps_env()
        self._workspace_client = None
        self._static_client: OpenAI | None = None
        self.segment_service = get_segment_service()
        self.sql_generator = get_sql_generator()

        if self._use_sdk_auth:
            from databricks.sdk import WorkspaceClient
            self._workspace_client = WorkspaceClient()
            logger.info("AgentService: Using Databricks Apps SDK auth")
        elif self.settings.databricks_server_hostname and self.settings.databricks_token:
            base_url = f"https://{self.settings.databricks_server_hostname}/serving-endpoints"
            self._static_client = OpenAI(
                api_key=self.settings.databricks_token,
                base_url=base_url,
            )
            logger.info("AgentService: Using env var auth")
        elif self.settings.databricks_config_profile:
            from databricks.sdk import WorkspaceClient
            self._workspace_client = WorkspaceClient(profile=self.settings.databricks_config_profile)
            logger.info("AgentService: Using profile '%s' for local dev", self.settings.databricks_config_profile)
        else:
            raise RuntimeError(
                "AgentService: No Databricks config. Set DATABRICKS_SERVER_HOSTNAME and DATABRICKS_TOKEN, "
                "set DATABRICKS_CONFIG_PROFILE for local dev (default: e2-demo-field-eng), "
                "or deploy to Databricks Apps."
            )

    def _get_client(self) -> OpenAI:
        """Get an OpenAI client (profile/SDK or static env)."""
        if self._workspace_client:
            host = self._workspace_client.config.host.replace("https://", "").replace("http://", "")
            headers = self._workspace_client.config.authenticate()
            token = headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                raise RuntimeError("Failed to get OAuth token from Databricks SDK")
            return OpenAI(api_key=token, base_url=f"https://{host}/serving-endpoints")
        return self._static_client

    @property
    def agent_mode(self) -> str:
        """Return the current agent mode."""
        return "llm"

    def _extract_json_from_response(self, text: str) -> dict | None:
        """Extract JSON from LLM response text."""
        # Try to find JSON between ```json and ```
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        try:
            # Find first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

        return None

    def _strip_json_from_response(self, text: str) -> str:
        """Remove JSON code blocks from the response text shown to the user."""
        # Remove ```json ... ``` blocks
        cleaned = re.sub(r'```json\s*[\s\S]*?\s*```', '', text)
        # Remove any remaining ``` blocks that look like JSON
        cleaned = re.sub(r'```\s*\{[\s\S]*?\}\s*```', '', cleaned)
        # Collapse multiple blank lines into one
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def _json_to_segment(self, data: dict) -> SegmentDefinition:
        """Convert JSON dict to SegmentDefinition."""
        groups = []
        for g in data.get("groups", []):
            conditions = []
            for c in g.get("conditions", []):
                conditions.append(SegmentCondition(
                    id=c.get("id", f"cond_{len(conditions)}"),
                    feature=c["feature"],
                    operator=c["operator"],
                    values=c["values"],
                ))
            groups.append(SegmentGroup(
                id=g.get("id", f"group_{len(groups)}"),
                logic=g.get("logic", "AND"),
                conditions=conditions,
            ))

        return SegmentDefinition(
            name=data.get("name", ""),
            description=data.get("description", ""),
            groups=groups,
            group_logic=data.get("group_logic", "AND"),
        )

    def parse_input(
        self,
        user_input: str,
        conversation_history: list[dict[str, str]],
        current_segment: SegmentDefinition | None = None,
    ) -> dict[str, Any]:
        """Parse natural language input to segment rules."""
        # Build messages for LLM
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # Add current segment context if exists
        if current_segment and current_segment.groups:
            context = f"\n\nCurrent segment state:\n```json\n{json.dumps(current_segment.model_dump(), indent=2)}\n```"
            messages.append({
                "role": "system",
                "content": f"The user has an existing segment. Modify it based on their request.{context}"
            })

        # Add user input
        messages.append({"role": "user", "content": user_input})

        try:
            client = self._get_client()
            logger.info(f"AgentService: Calling LLM (model={self.settings.databricks_model_endpoint})")
            response = client.chat.completions.create(
                model=self.settings.databricks_model_endpoint,
                messages=messages,
                max_tokens=2000,
                temperature=0.1,
            )

            raw_response = response.choices[0].message.content
            segment_json = self._extract_json_from_response(raw_response)
            response_text = self._strip_json_from_response(raw_response)

            # Convert to segment definition
            segment = None
            preview = None
            sql = None

            if segment_json:
                segment = self._json_to_segment(segment_json)

                # Generate SQL
                sql = self.sql_generator.generate_count_query(segment)

                # Try to get preview (may fail if Databricks not connected)
                try:
                    preview_result = self.segment_service.preview_segment(segment, include_sql=False)
                    preview = {
                        "individual_count": preview_result.individual_count,
                        "household_count": preview_result.household_count,
                    }
                except Exception as e:
                    logger.warning(f"Could not get preview: {e}")
                    preview = {"individual_count": 0, "household_count": 0}

            return {
                "response_text": response_text,
                "segment": segment.model_dump() if segment else None,
                "preview": preview,
                "sql": sql,
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"AgentService: LLM call failed: {error_msg}")

            if "404" in error_msg or "not found" in error_msg.lower():
                raise RuntimeError(
                    f"Model endpoint '{self.settings.databricks_model_endpoint}' not found. "
                    "Check DATABRICKS_MODEL_ENDPOINT configuration."
                ) from e

            raise

    def summarize_segment(
        self,
        segment: SegmentDefinition,
        conversation_history: list[dict[str, str]],
    ) -> tuple[str, str]:
        """Generate a 1-2 sentence summary and a suggested segment name from the conversation context.
        Returns (summary, suggested_name)."""
        messages = [{"role": "system", "content": (
            "You are an advertising audience analyst. Given a segment definition and the "
            "conversation that led to it, respond with valid JSON only (no markdown, no extra text), "
            "with exactly two keys: \"summary\" and \"suggested_name\". "
            "\"summary\": 1-2 short sentences summarizing the target audience for the description field. "
            "Be concise and business-friendly. "
            "\"suggested_name\": a short segment name suitable for a campaign identifier: use underscores, "
            "no spaces, alphanumeric plus underscores only (e.g. CA_Dog_Owners_25_54). Keep it under 50 characters."
        )}]
        for msg in conversation_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        segment_context = (
            f"Segment definition (JSON):\n{json.dumps(segment.model_dump(), indent=2)}\n\n"
            "Output JSON with keys: summary, suggested_name."
        )
        messages.append({"role": "user", "content": segment_context})

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.settings.databricks_model_endpoint,
                messages=messages,
                max_tokens=200,
                temperature=0.2,
            )
            raw = (response.choices[0].message.content or "").strip()
            # Strip markdown code fence if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(raw)
            summary = (data.get("summary") or "").strip() or ""
            name = (data.get("suggested_name") or "").strip()
            # Sanitize name: alphanumeric and underscores only
            name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)[:50]
            return (summary, name or "Suggested_Segment")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("AgentService: summarize_segment JSON parse failed: %s", e)
            # Fallback: treat whole response as summary
            return (raw if isinstance(raw, str) else "Suggested segment.", "Suggested_Segment")
        except Exception as e:
            logger.warning("AgentService: summarize_segment failed: %s", e)
            raise


# Singleton instance
_agent: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get the singleton agent service."""
    global _agent
    if _agent is None:
        _agent = AgentService()
    return _agent
