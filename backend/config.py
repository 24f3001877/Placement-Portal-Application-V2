# RecruitRadar — backend/config.py
# RR-SEED: All configuration for the RecruitRadar placement portal.
# Environment variables are loaded from .env (copy from .env.example).

import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""

    # ── Core Flask
    SECRET_KEY = os.environ.get("RR_SECRET_KEY", "rr-dev-secret-fallback")
    DEBUG = False

    # ── Database 
    # BASE_DIR points to backend/ — database file lives there
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{os.path.join(BASE_DIR, 'recruitradar.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT 
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "rr-jwt-secret-fallback")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    # Client stores token under the key "rr_token"
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # ── Redis 
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # ── Mail — Mailpit (local email testing) 
    # Mailpit catches all outgoing emails and shows them at http://localhost:8025
    # No real email is sent — perfect for local demo and viva.
    # Install: https://github.com/axllent/mailpit/releases
    # Run    : mailpit          (in a separate terminal)
    # View   : http://localhost:8025
    MAIL_SERVER          = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT            = int(os.environ.get("MAIL_PORT", 1025))
    MAIL_USE_TLS         = False   # Mailpit does not need TLS
    MAIL_USE_SSL         = False
    MAIL_USERNAME        = None    # Mailpit needs no authentication
    MAIL_PASSWORD        = None
    MAIL_DEFAULT_SENDER  = ("RecruitRadar", "noreply@recruitradar.local")
    ADMIN_EMAIL          = os.environ.get("ADMIN_EMAIL", "admin@recruitradar.local")

    # ── File Uploads 
    # uploads/ folder lives inside backend/ — path stays consistent regardless
    # of where app.py is located, because BASE_DIR always points to backend/
    UPLOAD_FOLDER       = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH  = 5 * 1024 * 1024   # 5 MB max for resume PDFs
    ALLOWED_EXTENSIONS  = {"pdf"}

    # ── Celery 
    CELERY_BROKER_URL       = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND   = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    # rr_task prefix on all task names — visible in Celery worker logs
    CELERY_TASK_SERIALIZER  = "json"
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT   = ["json"]
    CELERY_TIMEZONE         = "Asia/Kolkata"
    CELERY_ENABLE_UTC       = False

    # Celery Beat — scheduled job definitions (rr_task prefix on every key)
    CELERYBEAT_SCHEDULE = {
        "rr_task-daily-deadline-reminder": {
            "task":     "tasks.rr_task_send_deadline_reminders",
            "schedule": timedelta(hours=24),   # fires every 24 hours
        },
        "rr_task-monthly-placement-report": {
            "task":     "tasks.rr_task_send_monthly_report",
            # Fires daily; the task itself checks if today is the 1st of the month
            "schedule": timedelta(hours=24),
        },
    }

    # ── Admin seed credentials (used by init_db.py) 
    ADMIN_EMAIL_SEED    = os.environ.get("ADMIN_EMAIL_SEED", "admin@recruitradar.com")
    ADMIN_PASSWORD_SEED = os.environ.get("ADMIN_PASSWORD_SEED", "Admin@1234")

    # ── Redis cache TTLs (seconds) — all keys use rr_cache: prefix 
    RR_CACHE_TTL_DASHBOARD   = 300   # 5 min  — admin stats
    RR_CACHE_TTL_DRIVES      = 120   # 2 min  — approved drives list
    RR_CACHE_TTL_COMPANY_DASH = 180  # 3 min  — company dashboard
    RR_CACHE_TTL_SEARCH      = 60    # 1 min  — search results


class DevelopmentConfig(Config):
    """Development overrides — debug mode on."""
    DEBUG = True


class ProductionConfig(Config):
    """Production overrides — debug off."""
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
