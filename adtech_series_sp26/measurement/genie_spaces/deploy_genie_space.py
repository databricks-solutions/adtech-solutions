#!/usr/bin/env python3
"""
Deploy the Campaign Reach Q&A Genie space via the Databricks REST API.

Usage:
    python deploy_genie_space.py [options]

Examples:
    # Fresh create — pass --parent-path and --warehouse-id for your workspace
    python deploy_genie_space.py --parent-path /Shared/Adtech-measurement --warehouse-id <warehouse_id>

    # Deploy to a different catalog/schema
    python deploy_genie_space.py --catalog dev_catalog --schema gold \
      --parent-path /Shared/Adtech-measurement --warehouse-id <warehouse_id>

    # Deploy to a specific workspace with a named profile
    python deploy_genie_space.py --profile <profile> --catalog dev_catalog \
      --parent-path /Shared/Adtech-measurement --warehouse-id <warehouse_id>

    # Update an existing space instead of creating a new one
    python deploy_genie_space.py --space-id <space_id> --warehouse-id <warehouse_id>

Requirements:
    pip install databricks-sdk
"""

import argparse
import json
import re
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient


SPACE_CONFIG = Path(__file__).parent / "campaign_reach_qa.json"


def substitute_catalog_schema(obj, catalog: str, schema: str):
    """Recursively replace media_advertising.gold with catalog.schema in all strings."""
    if isinstance(obj, str):
        return re.sub(
            r"\bmedia_advertising\.gold\b",
            f"{catalog}.{schema}",
            obj,
        )
    if isinstance(obj, list):
        return [substitute_catalog_schema(item, catalog, schema) for item in obj]
    if isinstance(obj, dict):
        return {k: substitute_catalog_schema(v, catalog, schema) for k, v in obj.items()}
    return obj


def build_payload(config: dict, catalog: str, schema: str, warehouse_id: str) -> dict:
    serialized = config["serialized_space"]
    serialized = substitute_catalog_schema(serialized, catalog, schema)

    title = substitute_catalog_schema(config["title"], catalog, schema)
    description = substitute_catalog_schema(config["description"], catalog, schema)

    return {
        "title": title,
        "description": description,
        "warehouse_id": warehouse_id,
        "serialized_space": json.dumps(serialized),
    }


def main():
    parser = argparse.ArgumentParser(description="Deploy Campaign Reach Genie space")
    parser.add_argument("--profile", default=None, help="~/.databrickscfg profile (default: DEFAULT)")
    parser.add_argument("--host", default=None, help="Workspace host URL (overrides profile)")
    parser.add_argument("--catalog", default="media_advertising", help="UC catalog (default: media_advertising)")
    parser.add_argument("--schema", default="gold", help="UC schema (default: gold)")
    parser.add_argument("--warehouse-id", default=None, help="SQL warehouse ID (overrides JSON default)")
    parser.add_argument("--space-id", default=None, help="Update an existing space instead of creating")
    parser.add_argument("--parent-path", default=None, help="Workspace folder for new space (e.g. /Shared/Adtech-measurement)")
    args = parser.parse_args()

    # Load config
    with open(SPACE_CONFIG) as f:
        config = json.load(f)

    warehouse_id = args.warehouse_id or config.get("warehouse_id")
    if not warehouse_id:
        parser.error("--warehouse-id required (no warehouse_id in campaign_reach_qa.json)")

    # Connect
    client_kwargs = {}
    if args.host:
        client_kwargs["host"] = args.host
    if args.profile:
        client_kwargs["profile"] = args.profile
    w = WorkspaceClient(**client_kwargs)

    payload = build_payload(config, args.catalog, args.schema, warehouse_id)

    if args.space_id:
        print(f"Updating Genie space {args.space_id} ...")
        result = w.api_client.do(
            "PATCH",
            f"/api/2.0/genie/spaces/{args.space_id}",
            body=payload,
        )
        space_id = args.space_id
        action = "Updated"
    else:
        print("Creating Genie space ...")
        if args.parent_path:
            payload["parent_path"] = args.parent_path
        result = w.api_client.do(
            "POST",
            "/api/2.0/genie/spaces",
            body=payload,
        )
        space_id = result["space_id"]
        action = "Created"

    host = w.config.host.rstrip("/")
    print(f"{action} successfully.")
    print(f"  Space ID : {space_id}")
    print(f"  URL      : {host}/genie/rooms/{space_id}")


if __name__ == "__main__":
    main()
