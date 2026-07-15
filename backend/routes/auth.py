# RecruitRadar — routes/auth.py
# Authentication routes: register (student/company), login (all roles), logout.
# JWT token returned as "rr_token" — client stores it under this key.

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from extensions import db
from models import User, StudentProfile, CompanyProfile

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _validate_password(password: str) -> str | None:
    """Return error message if password doesn't meet requirements, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new student or company account.
    Admin registration is not allowed — admin is pre-seeded.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body."}), 400

    role = data.get("role", "").strip().lower()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # ── Input validation 
    if role not in ("student", "company"):
        return jsonify({"error": "Role must be 'student' or 'company'."}), 400
    if not email:
        return jsonify({"error": "Email is required."}), 400
    if "@" not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    pwd_error = _validate_password(password)
    if pwd_error:
        return jsonify({"error": pwd_error}), 400

    # Check duplicate email
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    # ── Create User 
    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # Get user.id before committing

    # ── Create role-specific profile 
    if role == "student":
        full_name = data.get("full_name", "").strip()
        branch = data.get("branch", "").strip()
        year = data.get("year")
        cgpa = data.get("cgpa")

        if not full_name or not branch or year is None or cgpa is None:
            db.session.rollback()
            return jsonify({"error": "full_name, branch, year, and cgpa are required for students."}), 400

        try:
            year = int(year)
            cgpa = float(cgpa)
        except (ValueError, TypeError):
            db.session.rollback()
            return jsonify({"error": "year must be an integer and cgpa must be a number."}), 400

        if not (0.0 <= cgpa <= 10.0):
            db.session.rollback()
            return jsonify({"error": "CGPA must be between 0.0 and 10.0."}), 400

        profile = StudentProfile(
            user_id=user.id,
            full_name=full_name,
            branch=branch,
            year=year,
            cgpa=cgpa,
            phone=data.get("phone", "").strip() or None,
            skills=data.get("skills", "").strip() or None,
        )
        db.session.add(profile)

    elif role == "company":
        company_name = data.get("company_name", "").strip()
        if not company_name:
            db.session.rollback()
            return jsonify({"error": "company_name is required for companies."}), 400

        profile = CompanyProfile(
            user_id=user.id,
            company_name=company_name,
            industry=data.get("industry", "").strip() or None,
            location=data.get("location", "").strip() or None,
            website=data.get("website", "").strip() or None,
            hr_contact=data.get("hr_contact", "").strip() or None,
            description=data.get("description", "").strip() or None,
            approval_status="pending",
        )
        db.session.add(profile)

    db.session.commit()

# Invalidate admin dashboard cache — total_companies count just changed
    from cache import rr_cache_delete_pattern
    rr_cache_delete_pattern("admin:*") 

    return jsonify({
        "message": f"{role.capitalize()} registered successfully.",
        "role": role,
        "email": email,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login for all roles (admin, student, company).
    Returns a JWT access token stored under key 'rr_token' on the client.

    Body (JSON):
        email    : string
        password : string
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body."}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    # Security: same error for wrong email or wrong password (no enumeration)
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401

    if not user.is_active:
        return jsonify({"error": "Your account has been deactivated. Contact the admin."}), 403

    if user.is_blacklisted:
        return jsonify({"error": "Your account has been blacklisted. Contact the admin."}), 403

    # Company must be approved before they can log in
    if user.role == "company":
        if user.company_profile and user.company_profile.approval_status != "approved":
            status = user.company_profile.approval_status
            return jsonify({
                "error": f"Your company registration is '{status}'. Please wait for admin approval."
            }), 403

    # JWT identity = user id; additional claims carry role
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )

    # Build profile summary for frontend store
    profile = {}
    if user.role == "student" and user.student_profile:
        profile = {"full_name": user.student_profile.full_name}
    elif user.role == "company" and user.company_profile:
        profile = {"company_name": user.company_profile.company_name}
    elif user.role == "admin":
        profile = {"full_name": "Admin"}

    return jsonify({
        "rr_token": access_token,   # client stores under key "rr_token"
        "role": user.role,
        "user_id": user.id,
        "email": user.email,
        **profile,
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout endpoint. JWT is stateless so server-side invalidation is not possible
    without a blocklist; client simply deletes the rr_token from local storage.
    """
    return jsonify({"message": "Logged out successfully. Please delete your rr_token."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return current user info — used by Vue store to rehydrate on page refresh."""
    user_id = get_jwt_identity()
    claims = get_jwt()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = user.to_dict()
    if user.role == "student" and user.student_profile:
        data["profile"] = user.student_profile.to_dict()
    elif user.role == "company" and user.company_profile:
        data["profile"] = user.company_profile.to_dict()

    return jsonify(data), 200
