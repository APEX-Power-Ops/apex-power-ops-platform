"""
Idempotency key tracking using the memory store.
"""
from typing import Optional

from app.db.memory_store import store
from app.envelope.response import MutationResponse


def check_idempotency(key: str) -> Optional[MutationResponse]:
    """
    Check if an idempotency key has been processed.
    
    Args:
        key: The idempotency key to check
    
    Returns:
        The cached MutationResponse if already processed, None otherwise
    """
    if key in store.idempotency_keys:
        cached = store.idempotency_keys[key]
        # Reconstruct the response
        return MutationResponse(**cached)
    return None


def save_idempotency(key: str, response: MutationResponse) -> None:
    """
    Save a response for idempotency tracking.
    
    Args:
        key: The idempotency key
        response: The mutation response to cache
    """
    store.idempotency_keys[key] = response.model_dump()
