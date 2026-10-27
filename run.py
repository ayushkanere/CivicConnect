import os
from app import create_app
from app.extensions import db
from app.services.auth import init_db_and_admin

app = create_app(os.getenv("FLASK_ENV", "development"))

# Safely initialize database tables and environment-based admin for Gunicorn / Render
init_db_and_admin(app)


@app.cli.command("init-db")
def init_db():
    """CLI helper to initialize database tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
