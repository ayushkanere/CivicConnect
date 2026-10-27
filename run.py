import os
from app import create_app
from app.extensions import db
from app.models import User, Report, StatusHistory, CommunityEvent

app = create_app(os.getenv("FLASK_ENV", "development"))


@app.cli.command("init-db")
def init_db():
    """CLI helper to initialize database tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=app.config.get("DEBUG", True))
