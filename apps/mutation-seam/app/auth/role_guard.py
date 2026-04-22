"""
Role-based access control utilities.
"""
from typing import List

from app.auth.jwt import Actor


def check_role(actor: Actor, allowed_roles: List[str]) -> bool:
    """
    Check if the actor's role is in the allowed list.
    
    Args:
        actor: The authenticated actor
        allowed_roles: List of roles that are allowed
    
    Returns:
        True if actor's role is allowed, False otherwise
    """
    return actor.actor_role in allowed_roles


def check_scope(actor: Actor, project_id: str) -> bool:
    """
    Check if the actor has access to the project.
    
    Args:
        actor: The authenticated actor
        project_id: The project being accessed
    
    Returns:
        True if actor has scope access, False otherwise
    """
    return project_id in actor.project_scope
