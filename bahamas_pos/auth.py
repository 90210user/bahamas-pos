"""
Authentication and access control for the POS system.
"""
from typing import Optional
import database


def login(username: str, password: str) -> Optional[dict]:
    """Authenticate user using database."""
    return database.db.authenticate_user(username, password)


def is_admin(user: Optional[dict]) -> bool:
    """Check if user has admin privileges."""
    return bool(user and user.get("role") == "admin")


def set_logo_path(user: Optional[dict], path: str) -> bool:
    """Set the logo/photo path for branding (admin only)."""
    if not is_admin(user):
        return False
    database.db.set_setting("logo_path", path)
    return True


def get_logo_path() -> str:
    """Get the current logo path."""
    return database.db.get_setting("logo_path", "")
