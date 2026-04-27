#!/usr/bin/env python3
"""
Evaluate the Campaign Reach Q&A Genie space against a set of questions.

For each question, checks that the generated SQL uses the expected data source
(campaign_reach_metrics vs reach_cube) and optionally validates SQL patterns.

Usage:
    python eval_genie_space.py --space-id <id> [--profile <profile>]

Examples:
    python eval_genie_space.py --space-id <space_id>
    python eval_genie_space.py --space-id <space_id> --profile <profile>
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from databricks.sdk import WorkspaceClient


# ---------------------------------------------------------------------------
# Evaluation cases
# ---------------------------------------------------------------------------

@dataclass
class EvalCase:
    question: str
    expected_source: str          # "metric_view" | "reach_cube" | "any"
    must_contain: list[str] = field(default_factory=list)   # SQL substrings that must appear
    must_not_contain: list[str] = field(default_factory=list)  # SQL substrings that must NOT appear
    # result_contains: strings that must appear in the stringified query result rows
    result_contains: list[str] = field(default_factory=list)
    description: str = ""


EVAL_CASES = [
    # --- Cross-dimensional: must use Metric View ---
    EvalCase(
        question="Show me device type breakdown by publisher",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        must_not_contain=["reach_cube"],
        description="publisher × device_type — cross-dim, must use Metric View",
    ),
    EvalCase(
        question="Which publishers drove the most CTV reach for Moving Movie?",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        must_not_contain=["reach_cube"],
        # Rainbow Hemisphere leads for Moving Movie CTV
        result_contains=["Rainbow Hemisphere"],
        description="campaign × publisher × device_type — cross-dim, must use Metric View",
    ),
    EvalCase(
        question="Compare individual reach by publisher across campaigns",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        must_not_contain=["reach_cube"],
        description="campaign × publisher — cross-dim, must use Metric View",
    ),
    EvalCase(
        question="Show me individual reach by content title for each publisher",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        must_not_contain=["reach_cube"],
        description="publisher × content reach — cross-dim, must use Metric View",
    ),
    # --- Single-dimension reach: Metric View preferred ---
    EvalCase(
        question="What is the total individual reach per campaign?",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        # Happy Dogs leads all campaigns
        result_contains=["Happy Dogs"],
        description="campaign-level reach — single dim, Metric View",
    ),
    EvalCase(
        question="What was the total individual reach for Terrific Tacos?",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        # Known correct value from data
        result_contains=["696592", "696,592"],
        description="Terrific Tacos total reach — known value 696,592",
    ),
    EvalCase(
        question="Which publisher had the highest individual reach for Terrific Tacos?",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        result_contains=["Rainbow Hemisphere"],
        description="top publisher for Terrific Tacos — Rainbow Hemisphere",
    ),
    EvalCase(
        question="Which marketing region had the highest reach for Terrific Tacos?",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        result_contains=["Dallas"],
        description="top region for Terrific Tacos — Dallas / Houston Metro",
    ),
    EvalCase(
        question="Show me individual reach by device type",
        expected_source="metric_view",
        must_contain=["campaign_reach_metrics"],
        # CTV should be largest device type
        result_contains=["CTV"],
        description="device_type reach — single dim, CTV should appear",
    ),
    # --- Raw impressions: reach_cube ---
    EvalCase(
        question="Compare raw impressions vs matched impressions by publisher",
        expected_source="reach_cube",
        must_contain=["reach_cube"],
        must_not_contain=["campaign_reach_metrics"],
        description="raw_imps — must use reach_cube (only source for raw_imps)",
    ),
    EvalCase(
        question="What are the raw impressions vs matched impressions for Terrific Tacos by publisher?",
        expected_source="reach_cube",
        must_contain=["reach_cube"],
        must_not_contain=["campaign_reach_metrics"],
        # Rainbow Hemisphere has highest raw imps: 4,518,018
        result_contains=["Rainbow Hemisphere"],
        description="Terrific Tacos raw/matched by publisher — reach_cube",
    ),
]


# ---------------------------------------------------------------------------
# Genie API helpers
# ---------------------------------------------------------------------------

POLL_INTERVAL = 3   # seconds
MAX_WAIT = 120      # seconds


def ask_genie(w: WorkspaceClient, space_id: str, question: str) -> dict:
    """Start a conversation and return the completed message dict."""
    resp = w.api_client.do(
        "POST",
        f"/api/2.0/genie/spaces/{space_id}/start-conversation",
        body={"content": question},
    )
    conv_id = resp["conversation_id"]
    msg_id = resp["message_id"]

    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        msg = w.api_client.do(
            "GET",
            f"/api/2.0/genie/spaces/{space_id}/conversations/{conv_id}/messages/{msg_id}",
        )
        status = msg.get("status", "")
        if status in ("COMPLETED", "FAILED", "QUERY_RESULT_EXPIRED", "CANCELLED"):
            return msg
        time.sleep(POLL_INTERVAL)

    return {"status": "TIMEOUT", "content": question}


def extract_sql(message: dict) -> Optional[str]:
    """Pull the generated SQL from a completed Genie message."""
    for attachment in message.get("attachments", []):
        query = attachment.get("query", {})
        if query.get("query"):
            return query["query"]
    return None


def extract_result_rows(message: dict, w: WorkspaceClient, warehouse_id: str) -> Optional[str]:
    """Return a string representation of the query result rows for value checks.

    First tries to find rows in the Genie message attachments; falls back to
    executing the SQL directly against the warehouse if results aren't embedded.
    """
    # Try embedded rows first
    for attachment in message.get("attachments", []):
        result = attachment.get("query", {}).get("query_result", {})
        rows = result.get("row_results", {}).get("rows", [])
        if rows:
            return json.dumps(rows)

    # Fallback: execute the SQL directly
    sql = extract_sql(message)
    if not sql:
        return None
    try:
        resp = w.api_client.do(
            "POST",
            "/api/2.0/sql/statements/",
            body={
                "statement": sql,
                "warehouse_id": warehouse_id,
                "format": "JSON_ARRAY",
                "wait_timeout": "30s",
            },
        )
        result = resp.get("result", {})
        data = result.get("data_array", [])
        if data:
            return json.dumps(data)
        # Also check manifest for column names
        manifest = resp.get("manifest", {})
        columns = [c.get("name", "") for c in manifest.get("schema", {}).get("columns", [])]
        return json.dumps({"columns": columns, "rows": data})
    except Exception as e:
        return f"execution_error: {e}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_eval(w: WorkspaceClient, space_id: str, warehouse_id: str) -> bool:
    results = []
    all_passed = True

    for i, case in enumerate(EVAL_CASES, 1):
        print(f"\n[{i}/{len(EVAL_CASES)}] {case.description or case.question}")
        print(f"  Q: {case.question}")

        msg = ask_genie(w, space_id, case.question)
        status = msg.get("status", "UNKNOWN")

        if status != "COMPLETED":
            print(f"  ✗ FAIL — Genie returned status: {status}")
            results.append((case, False, f"status={status}", None))
            all_passed = False
            continue

        sql = extract_sql(msg)
        if not sql:
            print(f"  ✗ FAIL — No SQL in response")
            results.append((case, False, "no SQL generated", None))
            all_passed = False
            continue

        sql_lower = sql.lower()
        failures = []

        for must in case.must_contain:
            if must.lower() not in sql_lower:
                failures.append(f"missing '{must}'")

        for must_not in case.must_not_contain:
            if must_not.lower() in sql_lower:
                failures.append(f"unexpected '{must_not}'")

        # Result value checks — verify expected values appear in the returned rows
        if case.result_contains and not failures:
            result_str = extract_result_rows(msg, w, warehouse_id) or ""
            for expected in case.result_contains:
                # Accept any of the comma-separated alternatives (e.g. "696592,696,592")
                alternatives = [a.strip() for a in expected.split(",")]
                if not any(alt.lower() in result_str.lower() for alt in alternatives):
                    failures.append(f"result missing '{expected}'")

        if failures:
            print(f"  ✗ FAIL — {', '.join(failures)}")
            print(f"  SQL: {sql[:300].strip()}...")
            results.append((case, False, "; ".join(failures), sql))
            all_passed = False
        else:
            print(f"  ✓ PASS")
            results.append((case, True, "", sql))

    # Summary
    passed = sum(1 for _, ok, _, _ in results if ok)
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(results)} passed")
    if not all_passed:
        print("\nFailed cases:")
        for case, ok, reason, sql in results:
            if not ok:
                print(f"  - {case.description or case.question}: {reason}")
    print(f"{'='*60}")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Evaluate Genie space question routing")
    parser.add_argument("--space-id", required=False, help="Genie space ID to evaluate")
    parser.add_argument("--warehouse-id", default=None, help="SQL warehouse ID (overrides JSON default)")
    parser.add_argument("--profile", default=None, help="~/.databrickscfg profile")
    parser.add_argument("--host", default=None, help="Workspace host URL")
    args = parser.parse_args()

    config_path = Path(__file__).parent / "campaign_reach_qa.json"
    with open(config_path) as f:
        config = json.load(f)

    space_id = args.space_id or config.get("space_id")
    if not space_id:
        parser.error("--space-id required (no space_id in campaign_reach_qa.json)")

    warehouse_id = args.warehouse_id or config.get("warehouse_id")
    if not warehouse_id:
        parser.error("--warehouse-id required (no warehouse_id in campaign_reach_qa.json)")

    client_kwargs = {}
    if args.host:
        client_kwargs["host"] = args.host
    if args.profile:
        client_kwargs["profile"] = args.profile
    w = WorkspaceClient(**client_kwargs)

    host = w.config.host.rstrip("/")
    print(f"Evaluating Genie space: {space_id}")
    print(f"Workspace: {host}")
    print(f"Cases: {len(EVAL_CASES)}")

    ok = run_eval(w, space_id, warehouse_id)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
