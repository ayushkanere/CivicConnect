import os
from flask import Flask, render_template, jsonify, request
from app.config import config_by_name
from app.extensions import db, login_manager, csrf, limiter


def create_app(config_name=None):
    """Application factory for CivicConnect."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Exempt API endpoints from CSRF
    csrf.exempt("app.blueprints.api.api_bp")

    # Register Blueprints
    from app.blueprints.public import public_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Register User Loader
    from app.services import auth  # Registers @login_manager.user_loader

    # Global Template Context Processor
    @app.context_processor
    def inject_global_vars():
        return {
            "app_name": "CivicConnect",
            "app_tagline": "A Digital Platform for Community Issue Reporting & Awareness",
            "enable_map": app.config.get("ENABLE_MAP", False)
        }

    # Error Handlers with custom friendly pages
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"400 Bad Request: {error}")
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Bad Request", "detail": str(error)}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Forbidden"}), 403
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Resource Not Found"}), 404
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error", 
                "message": "Rate limit exceeded. Please wait a moment before trying again."
            }), 429
        return render_template("errors/429.html", error=e), 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": "Internal Server Error"}), 500
        return render_template("errors/500.html", error=error), 500

    return app
