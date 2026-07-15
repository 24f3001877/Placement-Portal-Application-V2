

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from flask import Flask, jsonify, render_template
from config import config_map
from extensions import db, jwt, mail, cors


def create_app(config_name: str = "development") -> Flask:
    """
    Flask application factory.
    Creates and configures the app, initializes all extensions,
    and registers all API blueprints.
    """
    app = Flask(
        __name__,
        template_folder="frontend",       # serves frontend/index.html via Jinja2
        static_folder="frontend",
        static_url_path="/static",
    )

    # ── Load config 
    cfg = config_map.get(config_name, config_map["default"])
    app.config.from_object(cfg)

    # Ensure uploads folder exists (inside backend/uploads/)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Initialize Flask extensions 
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── Initialize Redis client
    import redis as redis_lib
    import extensions as ext_module
    try:
        ext_module.redis_client = redis_lib.from_url(
            app.config["REDIS_URL"],
            decode_responses=True,
        )
        ext_module.redis_client.ping()
    except Exception:
        app.logger.warning("RecruitRadar: Redis unavailable — caching disabled.")
        ext_module.redis_client = None

    #  Initialize Celery CLIENT for dispatching tasks from the web process 
    
    # executes tasks. This just lets Flask hand tasks off to the same broker
    from tasks import make_celery
    import tasks as tasks_module
    tasks_module.celery_app = make_celery(app)


    #  Register API Blueprints 
    from routes import auth_bp, admin_bp, company_bp, student_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    # ── Public stats endpoint (no JWT — for landing page) 
    _register_public_routes(app)

    # ── JWT error handlers 
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": f"Authorization required. {reason}"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": f"Invalid token. {reason}"}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_data):
        return jsonify({"error": "Session expired. Please log in again."}), 401

    # ── Global HTTP error handlers 
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return jsonify({"error": "Internal server error."}), 500

    # ── Serve Vue frontend shell 
    # Only the root "/" route serves index.html.
    # Vue Router runs in HASH mode: URLs are like http://localhost:5000/#/login
    # Flask only ever sees "/" — the "#/login" part is handled entirely by the browser.
    # This means NO conflict with /static/ file serving or /api/ routes.
    # Jinja2 is ONLY used to render this one entry point — never for UI.
    @app.route("/")
    def serve_frontend():
        return render_template("index.html")

    return app


def _register_public_routes(app: Flask) -> None:
    """
    Public (no-auth) routes registered directly on the app.
    Kept separate from blueprints because they need no JWT guard.
    """
    from cache import rr_cache_get, rr_cache_set

    @app.route("/api/public/stats")
    def public_stats():
        """
        Aggregated placement statistics for the public landing page.
        Cached under rr_cache:public:stats for 5 minutes.
        No sensitive data is exposed.
        """
        cached = rr_cache_get("public:stats")
        if cached:
            return jsonify(cached)

        from models import StudentProfile, CompanyProfile, PlacementDrive, Application
        result = {
            "total_students":  StudentProfile.query.count(),
            "total_companies": CompanyProfile.query.filter_by(approval_status="approved").count(),
            "total_drives":    PlacementDrive.query.filter_by(status="approved").count(),
            "total_placed":    Application.query.filter_by(status="placed").count(),
        }
        rr_cache_set("public:stats", result, 300)
        return jsonify(result)


# Dev server entry point 
# Run with: python app.py
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
