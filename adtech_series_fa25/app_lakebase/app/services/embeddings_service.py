import os
import json
from typing import List
from utils.databricks_utils import get_workspace_client


def get_embedding_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL_NAME", "databricks-gte-large-en")


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for the given text using a Databricks serving endpoint.
    Returns a list of 1024 floats.
    """
    if not text:
        return []

    client = get_workspace_client()
    model_name = get_embedding_model_name()

    payload = {
        "input": [text]
    }

    payload_json = json.dumps(payload)

    response = client.api_client.do(
        method="POST",
        path=f"/serving-endpoints/{model_name}/invocations",
        headers={"Content-Type": "application/json"},
        data=payload_json,
    )

    # Attempt to normalize various possible response shapes into List[float]
    vector: List[float] | None = None

    if isinstance(response, list):
        # Could be [[...]] or ["text"] etc.
        if response and isinstance(response[0], list):
            vector = response[0]
    elif isinstance(response, dict):
        # Common patterns: {'data': [{'embedding': [...]}]} or {'embeddings': [[...]]}
        if 'data' in response and isinstance(response['data'], list):
            item = response['data'][0]
            if isinstance(item, dict) and 'embedding' in item:
                vector = item['embedding']
        elif 'embeddings' in response and isinstance(response['embeddings'], list):
            first = response['embeddings'][0]
            if isinstance(first, list):
                vector = first
            elif isinstance(first, dict) and 'values' in first:
                vector = first['values']
        elif 'output' in response and isinstance(response['output'], list):
            first = response['output'][0]
            if isinstance(first, list):
                vector = first

    if vector is None:
        raise RuntimeError(f"Unexpected embedding response format from {model_name}: {str(response)[:200]}")

    if len(vector) != 1024:
        raise ValueError(f"Embedding length {len(vector)} != 1024 for model {model_name}")

    # Ensure elements are floats
    return [float(x) for x in vector]


