# RecruitRadar — init_db.py
# RR-SEED: Database initialisation script.
# Run ONCE before starting the app for the first time:
#
#     python init_db.py
#
# What it does:
#   1. Creates all SQLite tables programmatically using SQLAlchemy (db.create_all())
#   2. Inserts the admin user if one does not already exist
#
# Admin credentials (change in .env before running):
#   Email    : admin@recruitradar.com
#   Password : Admin@1234
#
# The database file is created at: backend/recruitradar.db
# Tables are NEVER created manually — always through this script.

import os
import sys

# Add backend/ to path so imports resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import create_app
from extensions import db
from models import User

def init_db():
    """Create all tables and seed the admin user."""
    app = create_app()

    with app.app_context():
        print("RecruitRadar — Initialising database...")

        # Create all tables from SQLAlchemy models 
        db.create_all()
        print("  ✓ All tables created successfully.")

        # Read admin credentials from config (set via .env or defaults)
        admin_email    = app.config.get("ADMIN_EMAIL_SEED", "admin@recruitradar.com")
        admin_password = app.config.get("ADMIN_PASSWORD_SEED", "Admin@1234")

        # Only seed admin if no admin exists — safe to run multiple times
        existing = User.query.filter_by(role="admin").first()
        if existing:
            print(f"  ℹ  Admin already exists ({existing.email}) — skipping seed.")
        else:
            admin = User(email=admin_email, role="admin", is_active=True)
            admin.set_password(admin_password)  # password is hashed — never stored as plaintext
            db.session.add(admin)
            db.session.commit()
            print(f"  ✓ Admin user created: {admin_email}")
            print(f"  ✓ Password          : {admin_password}")
            

        print("\nRecruitRadar — Database ready. You can now run: python app.py")


if __name__ == "__main__":
    init_db()
