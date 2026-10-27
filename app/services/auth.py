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


def init_db_and_admin(app):
    """
    Safely creates database tables and initializes the first administrator account
    from environment variables (ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD) if provided.
    Designed for headless deployment environments (e.g. Render Web Services without Shell).
    - Idempotent: Does not reset password if admin already exists.
    - Safe: Catches database errors and rolls back without crashing startup.
    - Secure: Never hardcodes passwords; uses User.set_password() to hash.
    """
    import os
    with app.app_context():
        try:
            # 1. Safely create all tables (idempotent CREATE TABLE IF NOT EXISTS)
            db.create_all()

            # 2. Check for admin initialization credentials in environment
            admin_password = os.getenv("ADMIN_PASSWORD")
            if admin_password and admin_password.strip():
                admin_name = os.getenv("ADMIN_NAME", "admin").strip() or "admin"
                raw_email = os.getenv("ADMIN_EMAIL")
                admin_email = raw_email.strip() if raw_email and raw_email.strip() else None

                # 3. Check if user with this name or email already exists
                existing = User.query.filter(
                    (User.name == admin_name) | 
                    ((User.email == admin_email) if admin_email else False)
                ).first()

                if not existing:
                    new_admin = User(
                        name=admin_name,
                        email=admin_email,
                        role="admin"
                    )
                    new_admin.set_password(admin_password.strip())
                    db.session.add(new_admin)
                    db.session.commit()
                    app.logger.info(f"Initialized admin account '{admin_name}' from environment variables.")
                else:
                    app.logger.info(f"Admin account '{existing.name}' already exists. Skipping environment password reset.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during database/admin initialization: {e}")

