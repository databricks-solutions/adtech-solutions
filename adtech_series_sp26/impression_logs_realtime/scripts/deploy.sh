#!/usr/bin/env bash
# Deploy script for adtech-impression-logs-realtime Databricks Asset Bundle.
#
# Usage: bash scripts/deploy.sh [COMMAND] [--target TARGET]
#
# Commands:
#   validate        Validate the bundle configuration
#   deploy          Deploy bundle (Lakebase instance + jobs + app resource)
#   wait-db         Poll until Lakebase instance is AVAILABLE
#   start           Start the app compute (skips if already ACTIVE)
#   stop            Stop the app compute
#   app-deploy      Push app source code to Databricks
#   full            deploy → wait-db → start → app-deploy (default)
#   help            Print this help message

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BUNDLE_ROOT"

TARGET="${TARGET:-dev}"
LAKEBASE_INSTANCE="campaign-pacing"

# ── Parse arguments ──────────────────────────────────────────────────────

COMMAND="${1:-full}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Prerequisites ────────────────────────────────────────────────────────

check_prereqs() {
  for cmd in databricks jq; do
    if ! command -v "$cmd" &>/dev/null; then
      echo "Error: '$cmd' not found."
      [[ "$cmd" == "databricks" ]] && echo "       Install: https://docs.databricks.com/dev-tools/cli/install.html"
      [[ "$cmd" == "jq" ]]         && echo "       Install: https://jqlang.github.io/jq/download/"
      exit 1
    fi
  done
}

# ── Bundle helpers ───────────────────────────────────────────────────────

get_app_name() {
  databricks bundle summary -o json -t "$TARGET" \
    | jq -r '.resources.apps | to_entries | first | .value.name'
}

get_workspace_path() {
  databricks bundle summary -o json -t "$TARGET" | jq -r '.workspace.file_path'
}

# ── Subcommands ──────────────────────────────────────────────────────────

cmd_validate() {
  echo "==> Validating bundle (target: $TARGET)..."
  databricks bundle validate -t "$TARGET"
  echo "    Bundle is valid."
}

cmd_deploy() {
  echo "==> Deploying bundle (target: $TARGET)..."
  databricks bundle deploy -t "$TARGET"
  echo "    Bundle deployed."
}

cmd_wait_db() {
  echo "==> Waiting for Lakebase instance '$LAKEBASE_INSTANCE' to be AVAILABLE..."
  while true; do
    STATE="$(databricks database get-database-instance "$LAKEBASE_INSTANCE" -o json | jq -r '.state')"
    echo "    State: $STATE"
    if [[ "$STATE" == "AVAILABLE" ]]; then
      echo "    Lakebase is ready."
      break
    elif [[ "$STATE" == "STARTING" || "$STATE" == "PROVISIONING" ]]; then
      echo "    Waiting 30s..."
      sleep 30
    else
      echo "Error: Unexpected Lakebase state '$STATE'. Manual intervention may be required."
      exit 1
    fi
  done
}

cmd_start() {
  local app_name state
  app_name="$(get_app_name)"
  echo "==> Starting app '$app_name'..."

  state="$(databricks apps get "$app_name" -o json 2>/dev/null | jq -r '.compute_status.state // empty')" || true

  if [[ "$state" == "ACTIVE" ]]; then
    echo "    App is already ACTIVE — skipping start."
    return
  fi

  databricks apps start "$app_name"
  echo "    Start initiated."
}

cmd_stop() {
  local app_name
  app_name="$(get_app_name)"
  echo "==> Stopping app '$app_name'..."
  databricks apps stop "$app_name"
  echo "    Stop initiated."
}

cmd_app_build() {
  echo "==> Building frontend..."
  local frontend_dir="$BUNDLE_ROOT/campaign_pacing_app/frontend"
  if [[ ! -d "$frontend_dir" ]]; then
    echo "Error: frontend directory not found at $frontend_dir"; exit 1
  fi
  (cd "$frontend_dir" && npm install --silent && npm run build)
  echo "    Frontend built → frontend/dist/"
}

cmd_app_deploy() {
  local app_name workspace_path
  app_name="$(get_app_name)"
  workspace_path="$(get_workspace_path)/campaign_pacing_app"
  echo "==> Deploying app source for '$app_name'..."
  echo "    Source path: $workspace_path"
  databricks apps deploy "$app_name" --source-code-path "$workspace_path"
  echo "    App deploy initiated."
}

cmd_full() {
  cmd_app_build
  cmd_deploy
  cmd_wait_db
  cmd_start
  cmd_app_deploy
}

cmd_help() {
  echo "Usage: bash scripts/deploy.sh [COMMAND] [--target TARGET]"
  echo ""
  echo "Commands:"
  echo "  validate        Validate the bundle configuration"
  echo "  deploy          Deploy bundle (Lakebase + jobs + app resource)"
  echo "  wait-db         Poll until Lakebase instance is AVAILABLE"
  echo "  start           Start the app compute (skips if already ACTIVE)"
  echo "  stop            Stop the app compute"
  echo "  app-deploy      Push app source code to Databricks"
  echo "  full            deploy → wait-db → start → app-deploy (default)"
  echo "  help            Print this help message"
  echo ""
  echo "Options:"
  echo "  --target TARGET   Deployment target (default: dev)"
  echo ""
  echo "Demo flow (after full deploy):"
  echo "  1. Start producer:         databricks bundle run kafka_producer_job -t $TARGET"
  echo "  2. Start enrichment:       databricks bundle run kafka_consumer_job -t $TARGET"
  echo "  3. Start pacing consumer:  databricks bundle run campaign_pacing_job -t $TARGET"
  echo "  4. Open app URL from:      databricks apps get \$(bash scripts/deploy.sh help | ...)"
}

# ── Dispatch ─────────────────────────────────────────────────────────────

check_prereqs

case "$COMMAND" in
  validate)       cmd_validate ;;
  deploy)         cmd_deploy ;;
  wait-db)        cmd_wait_db ;;
  start)          cmd_start ;;
  stop)           cmd_stop ;;
  app-deploy)     cmd_app_deploy ;;
  full)           cmd_full ;;
  help)           cmd_help ;;
  *)              echo "Unknown command: $COMMAND"; cmd_help; exit 1 ;;
esac
