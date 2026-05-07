from databricks.sdk import WorkspaceClient
import flask
import os

def get_workspace_client():
    """
    Get a workspace client for the current user.
    Needed because when using `databricks apps run-local` you can't use the default credential chain, works fine for the deployed app.
    """
    profile = os.getenv("DATABRICKS_PROFILE", None)
    if profile is None:
        return WorkspaceClient()
    else:
        return WorkspaceClient(profile=profile)
    
def get_current_user_name() -> str:
    """Resolve the current user's name.

    - Prefer the forwarded access token header when within a request context (Databricks Apps proxy).
    - Otherwise, fall back to the default WorkspaceClient (profile/env-based auth).
    - As a last resort in local dev, return OS user to avoid crashing the app shell.
    """
    # Try forwarded token only when there is an active Flask request context
    try:
        if flask.has_request_context():
            token = flask.request.headers.get('X-Forwarded-Access-Token')
            if token:
                try:
                    client_with_token = WorkspaceClient(token=token, auth_type="pat")
                    me = client_with_token.current_user.me()
                    return me.user_name
                except Exception:
                    # Fall back to the default client if token-based auth fails
                    pass
    except Exception:
        # If anything goes wrong probing request headers, ignore and fall back below
        pass

    # Fallback: use workspace client from the configured profile/env
    try:
        me = get_workspace_client().current_user.me()
        return me.user_name
    except Exception:
        # Final non-fatal fallback for local development only
        return os.getenv("USER") or "unknown"
        