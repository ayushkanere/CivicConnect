from typing import Optional
from app.extensions import login_manager, db
from app.models import User


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Flask-Login user loader callback."""
    if not user_id:
        return None
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def authenticate_user(email_or_name: str, password: str) -> Optional[User]:
    """
    Authenticates an administrator with generic timing-safe failure.
    Accepts either admin username or email.
    """
    if not email_or_name or not password:
        return None

    cleaned_identifier = email_or_name.strip()
    user = (
        User.query.filter(
            (User.email == cleaned_identifier) | (User.name == cleaned_identifier)
        ).first()
    )

    if not user or not user.check_password(password):
        return None

    return user
