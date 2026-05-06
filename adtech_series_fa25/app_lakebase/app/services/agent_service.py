import os
import json
import logging
from typing import Any, Dict, List, Optional, Generator

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

from utils.databricks_utils import get_workspace_client
from utils.table_formatter import detect_and_format_tables
from utils.token_counter import (
    count_total_tokens_from_dicts,
    trim_message_dicts_to_fit,
)

logger = logging.getLogger(__name__)

class AgentService:
    """
    Handles interaction with the Databricks chat agent serving endpoint.
    """

    def __init__(self, client: WorkspaceClient | None = None):
        self.client = client or get_workspace_client()

    def _normalize_response_to_text(self, response: Any) -> str:
        """
        Normalize various Databricks Serving response shapes (Claude/chat, LangGraph, raw strings)
        into a single plain text string suitable for display and persistence.
        
        For LangGraph multi-agent responses, preserves agent identity by showing agent names.

        Known shapes handled:
        - str -> returned as-is
        - { choices: [{ message: { content } } ] } -> extract content
        - { output_text | text } -> extract as content
        - { messages: [ { role, content, name, ... } ] } -> format with agent names when available
        - [ { messages: [...] }, ... ] -> format multi-agent responses with names
        - [ str | {text}|{output_text}|{choices}] -> join extracted with double newlines
        Fallback: JSON stringify.
        """
        try:
            # 1) Simple string
            if isinstance(response, str):
                return response

            # 2) choices shape
            if isinstance(response, dict):
                if "choices" in response and isinstance(response["choices"], list) and response["choices"]:
                    choice0 = response["choices"][0]
                    try:
                        return str(choice0["message"]["content"])  # type: ignore[index]
                    except Exception:
                        pass
                # explicit text fields
                if isinstance(response.get("output_text"), str):
                    return str(response["output_text"])  # type: ignore[index]
                if isinstance(response.get("text"), str):
                    return str(response["text"])  # type: ignore[index]
                # messages array with potential multi-agent structure
                msgs = response.get("messages")
                if isinstance(msgs, list) and msgs:
                    return self._format_multi_agent_messages(msgs)

            # 3) top-level list (e.g., LangGraph batches)
            if isinstance(response, list) and response:
                collected: List[str] = []
                for item in response:
                    if isinstance(item, str):
                        if item.strip():
                            collected.append(item)
                        continue
                    if isinstance(item, dict):
                        # nested messages
                        msgs = item.get("messages")
                        if isinstance(msgs, list):
                            formatted = self._format_multi_agent_messages(msgs)
                            if formatted.strip():
                                collected.append(formatted)
                                continue
                        # explicit fields
                        if isinstance(item.get("output_text"), str) and item["output_text"].strip():
                            collected.append(item["output_text"])  # type: ignore[index]
                            continue
                        if isinstance(item.get("text"), str) and item["text"].strip():
                            collected.append(item["text"])  # type: ignore[index]
                            continue
                        if "choices" in item and isinstance(item["choices"], list) and item["choices"]:
                            try:
                                collected.append(str(item["choices"][0]["message"]["content"]))  # type: ignore[index]
                                continue
                            except Exception:
                                pass
                if collected:
                    return "\n\n".join(collected)

            # 4) last resort: stringify
            return json.dumps(response)
        except Exception:
            try:
                return json.dumps(response)
            except Exception:
                return ""
        
        
    def _post_process_text(self, text: str) -> str:
        """
        Final text normalization step applied before returning to callers.
        Currently formats any TSV blocks into Markdown tables.
        """
        try:
            return detect_and_format_tables(text)
        except Exception:
            return text
                
    def _format_multi_agent_messages(self, msgs: List[Dict[str, Any]]) -> str:
        """
        Format a list of messages from potentially multiple agents, preserving agent identity.
        Returns a formatted string that shows which agent contributed what content.
        """
        try:
            # Group messages by agent and preserve order
            agent_responses: List[Dict[str, str]] = []
            
            for m in msgs:
                if not isinstance(m, dict):
                    continue
                role = m.get("role")
                content = m.get("content")
                name = m.get("name")
                
                if role == "assistant" and isinstance(content, str) and content.strip():
                    agent_responses.append({
                        "name": name or "Assistant",
                        "content": content.strip()
                    })
            
            if not agent_responses:
                return ""
            
            # If there's only one response or no names, just return the content
            if len(agent_responses) == 1 or all(resp["name"] == "Assistant" for resp in agent_responses):
                return agent_responses[0]["content"]
            
            # Multiple agents - format with names
            formatted_parts: List[str] = []
            for resp in agent_responses:
                if resp["name"] and resp["name"] != "Assistant":
                    formatted_parts.append(f"**{resp['name']}:** {resp['content']}")
                else:
                    formatted_parts.append(resp["content"])
            
            return "\n\n".join(formatted_parts)
            
        except Exception:
            # Fallback to simple concatenation
            simple_texts: List[str] = []
            for m in msgs:
                if isinstance(m, dict) and m.get("role") == "assistant":
                    content = m.get("content")
                    if isinstance(content, str) and content.strip():
                        simple_texts.append(content)
            return "\n\n".join(simple_texts)

    def _apply_context_limiting(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Apply context limiting based on configuration.
        
        When CHAT_CONTEXT_LIMIT = 0: use token-based limiting
        When CHAT_CONTEXT_LIMIT > 0: use message count limiting
        
        Args:
            messages: List of chat messages
            
        Returns:
            Limited list of messages
        """
        if not messages:
            return messages
            
        # Get configuration values
        chat_context_limit_str = os.getenv("CHAT_CONTEXT_LIMIT", "5")
        try:
            chat_context_limit = int(chat_context_limit_str)
        except ValueError:
            chat_context_limit = 5
            
        context_window_size_str = os.getenv("CONTEXT_WINDOW_SIZE", "200000")
        try:
            context_window_size = int(context_window_size_str)
        except ValueError:
            context_window_size = 200000
            
        if chat_context_limit == 0:
            # Token-based limiting
            logger.debug(f"Using token-based limiting with window size: {context_window_size}")
            
            # Convert messages to message dicts for token counting
            temp_message_dicts = []
            for msg in messages:
                if msg.content and str(msg.content).strip():
                    role_value = "user" if msg.role == ChatMessageRole.USER else "assistant"
                    temp_message_dicts.append({
                        "role": role_value,
                        "content": msg.content,
                    })
            
            # Apply token-based trimming
            trimmed_dicts = trim_message_dicts_to_fit(temp_message_dicts, context_window_size)
            
            # Convert back to ChatMessage objects
            # Find the starting index in the original messages
            if len(trimmed_dicts) == 0:
                return []
            elif len(trimmed_dicts) == len(temp_message_dicts):
                # No trimming needed, return original filtered messages
                return [msg for msg in messages if msg.content and str(msg.content).strip()]
            else:
                # Find where the trimmed messages start in the original list
                trimmed_start_idx = len(temp_message_dicts) - len(trimmed_dicts)
                # Map back to original message indices, accounting for filtered empty messages
                filtered_messages = [msg for msg in messages if msg.content and str(msg.content).strip()]
                return filtered_messages[trimmed_start_idx:]
        else:
            # Traditional message count limiting
            logger.debug(f"Using message count limiting with limit: {chat_context_limit}")
            if chat_context_limit <= 0:
                chat_context_limit = 5
            return messages[-chat_context_limit:]

    def generate_bot_response_stream(self, current_user: str, messages: List[ChatMessage]) -> Generator[str, None, None]:
        """
        Generate bot response using our agent's predict_stream method via direct API call.
        Yields chunks of text as they arrive from the model.
        """
        try:
            agent_endpoint = os.getenv("AGENT_ENDPOINT")
            if not agent_endpoint:
                yield "Error: AGENT_ENDPOINT environment variable not configured."
                return

            # Apply context limiting based on configuration
            limited_messages = self._apply_context_limiting(messages)

            # Build messages list compatible with OpenAI chat API (include system prompt)
            chat_messages: List[Dict[str, str]] = []
            chat_messages.append({"role": "system", "content": "."}) # Minimal system prompt since the agent deals with this internally.
            for msg in limited_messages:
                if not msg.content or not str(msg.content).strip():
                    continue
                chat_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

            # Get configurable k value for chat history retrieval
            agent_chat_k_str = os.getenv("AGENT_CHAT_K", "5")
            try:
                agent_chat_k = int(agent_chat_k_str)
            except ValueError:
                agent_chat_k = 5
            if agent_chat_k <= 0:
                agent_chat_k = 5

            # Use Databricks-configured OpenAI client for true streaming
            oai_client = self.client.serving_endpoints.get_open_ai_client()

            stream = oai_client.chat.completions.create(
                model=agent_endpoint,
                messages=chat_messages,
                stream=True,
                extra_body={
                    "custom_inputs": {
                        "filters": {"user_name": current_user},
                        "k": agent_chat_k,
                    }
                },
            )

            for event in stream:
                chunk = None
                # Standard OpenAI shape
                try:
                    if getattr(event, "choices", None):
                        choice0 = event.choices[0]
                        # dataclasses from openai lib expose .delta.content
                        delta_obj = getattr(choice0, "delta", None)
                        if delta_obj is not None:
                            chunk = getattr(delta_obj, "content", None)
                except Exception:
                    pass

                # Databricks variant: top-level delta dict with content
                if chunk is None:
                    try:
                        delta_top = getattr(event, "delta", None)
                        if isinstance(delta_top, dict):
                            maybe = delta_top.get("content")
                            if isinstance(maybe, str) and maybe:
                                chunk = maybe
                    except Exception:
                        pass

                if chunk:
                    yield chunk
                    
        except Exception as e:
            logger.exception("Error in streaming bot response")
            yield f"Error calling model serving endpoint: {str(e)}"


