# RecruitRadar — extensions.py
# All Flask extensions are initialized here (without the app object).
# app.py calls .init_app(app) on each one.
# Every other file imports from here — never from app.py — to prevent circular imports.

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
import redis as redis_lib

# ── SQLAlchemy ORM ────────────────────────────────────────────────────────────
db = SQLAlchemy()

# ── JWT Authentication ────────────────────────────────────────────────────────
jwt = JWTManager()

# ── Mail ──────────────────────────────────────────────────────────────────────
mail = Mail()

# ── CORS (allows Vue CDN frontend to call Flask API) ─────────────────────────
cors = CORS()

# ── Redis client (rr_cache prefix used for all keys) ─────────────────────────
# Initialized lazily in app.py after config is loaded
redis_client: redis_lib.Redis | None = None
