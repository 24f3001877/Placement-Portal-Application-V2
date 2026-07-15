# RecruitRadar — routes/admin.py
# All admin-only routes. Every endpoint is protected by JWT + role check.

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application, Placement
from cache import rr_cache_get, rr_cache_set, rr_cache_delete, rr_cache_delete_pattern

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _require_admin():
    """Check JWT claims for admin role. Returns error response or None."""
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Admin access required."}), 403
    return None



# DASHBOARD STATS

@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    """
    Admin dashboard statistics.
    Cached under rr_cache:admin:dashboard for RR_CACHE_TTL_DASHBOARD seconds.
    """
    err = _require_admin()
    if err:
        return err

    cache_key = "admin:dashboard"
    cached = rr_cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    pending_companies = CompanyProfile.query.filter_by(approval_status="pending").count()
    pending_drives = PlacementDrive.query.filter_by(status="pending").count()
    total_placed = Application.query.filter_by(status="placed").count()

    result = {
        "total_students": total_students,
        "total_companies": total_companies,
        "total_drives": total_drives,
        "total_applications": total_applications,
        "pending_companies": pending_companies,
        "pending_drives": pending_drives,
        "total_placed": total_placed,
    }

    ttl = current_app.config.get("RR_CACHE_TTL_DASHBOARD", 300)
    rr_cache_set(cache_key, result, ttl)
    return jsonify(result), 200


# COMPANY MANAGEMENT

@admin_bp.route("/companies", methods=["GET"])
@jwt_required()
def list_companies():
    err = _require_admin()
    if err:
        return err

    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    query = CompanyProfile.query
    if search:
        query = query.filter(
            db.or_(
                CompanyProfile.company_name.ilike(f"%{search}%"),
                CompanyProfile.industry.ilike(f"%{search}%"),
            )
        )
    if status_filter:
        query = query.filter_by(approval_status=status_filter)

    # Pending-approval queries are never cached 
    # Only cache general search results.
    if status_filter:
        companies = query.order_by(CompanyProfile.registered_at.desc()).all()
        return jsonify([c.to_dict() for c in companies]), 200

    cache_key = f"admin:companies:{search}"
    ttl = current_app.config.get("RR_CACHE_TTL_SEARCH", 60)
    cached = rr_cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    companies = query.order_by(CompanyProfile.registered_at.desc()).all()
    result = [c.to_dict() for c in companies]
    rr_cache_set(cache_key, result, ttl)
    return jsonify(result), 200


@admin_bp.route("/companies/<int:company_id>/approve", methods=["PUT"])
@jwt_required()
def approve_company(company_id):
    """Approve a pending company registration."""
    err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "approved"
    db.session.commit()
    rr_cache_delete_pattern("admin:companies:*")
    rr_cache_delete("admin:dashboard")
    return jsonify({"message": f"{company.company_name} approved successfully."}), 200


@admin_bp.route("/companies/<int:company_id>/reject", methods=["PUT"])
@jwt_required()
def reject_company(company_id):
    """Reject a company registration."""
    err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    company.approval_status = "rejected"
    db.session.commit()
    rr_cache_delete_pattern("admin:companies:*")
    rr_cache_delete("admin:dashboard")
    return jsonify({"message": f"{company.company_name} rejected."}), 200


@admin_bp.route("/companies/<int:company_id>/blacklist", methods=["PUT"])
@jwt_required()
def blacklist_company(company_id):
    """Toggle blacklist status of a company."""
    err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    user = User.query.get(company.user_id)
    if not user:
        return jsonify({"error": "Associated user not found."}), 404

    user.is_blacklisted = not user.is_blacklisted
    action = "blacklisted" if user.is_blacklisted else "un-blacklisted"
    db.session.commit()
    rr_cache_delete_pattern("admin:companies:*")
    return jsonify({"message": f"{company.company_name} {action}."}), 200


@admin_bp.route("/companies/<int:company_id>", methods=["DELETE"])
@jwt_required()
def delete_company(company_id):
    """Remove a company from the system."""
    err = _require_admin()
    if err:
        return err

    company = CompanyProfile.query.get_or_404(company_id)
    user = User.query.get(company.user_id)
    name = company.company_name
    db.session.delete(company)
    if user:
        db.session.delete(user)
    db.session.commit()
    rr_cache_delete_pattern("admin:companies:*")
    rr_cache_delete("admin:dashboard")
    return jsonify({"message": f"{name} removed from the system."}), 200



# STUDENT MANAGEMENT

@admin_bp.route("/students", methods=["GET"])
@jwt_required()
def list_students():
    """
    List all students with optional search by name, ID, or email.
    Query params: ?search=<text>
    """
    err = _require_admin()
    if err:
        return err

    search = request.args.get("search", "").strip()
    cache_key = f"admin:students:{search}"
    ttl = current_app.config.get("RR_CACHE_TTL_SEARCH", 60)

    cached = rr_cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    query = StudentProfile.query.join(User, StudentProfile.user_id == User.id)
    if search:
        query = query.filter(
            db.or_(
                StudentProfile.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                StudentProfile.id == (int(search) if search.isdigit() else -1),
            )
        )

    students = query.order_by(StudentProfile.id.desc()).all()
    result = [s.to_dict() for s in students]
    rr_cache_set(cache_key, result, ttl)
    return jsonify(result), 200


@admin_bp.route("/students/<int:student_id>/blacklist", methods=["PUT"])
@jwt_required()
def blacklist_student(student_id):
    """Toggle blacklist status of a student."""
    err = _require_admin()
    if err:
        return err

    student = StudentProfile.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    if not user:
        return jsonify({"error": "Associated user not found."}), 404

    user.is_blacklisted = not user.is_blacklisted
    action = "blacklisted" if user.is_blacklisted else "un-blacklisted"
    db.session.commit()
    rr_cache_delete_pattern("admin:students:*")
    return jsonify({"message": f"{student.full_name} {action}."}), 200


@admin_bp.route("/students/<int:student_id>", methods=["DELETE"])
@jwt_required()
def delete_student(student_id):
    """Remove a student from the system."""
    err = _require_admin()
    if err:
        return err

    student = StudentProfile.query.get_or_404(student_id)
    user = User.query.get(student.user_id)
    name = student.full_name
    db.session.delete(student)
    if user:
        db.session.delete(user)
    db.session.commit()
    rr_cache_delete_pattern("admin:students:*")
    rr_cache_delete("admin:dashboard")
    return jsonify({"message": f"{name} removed from the system."}), 200


@admin_bp.route("/students/<int:student_id>", methods=["GET"])
@jwt_required()
def get_student(student_id):
    """View a student's full profile and application history."""
    err = _require_admin()
    if err:
        return err

    student = StudentProfile.query.get_or_404(student_id)
    data = student.to_dict()
    data["applications"] = [app.to_dict() for app in student.applications]
    return jsonify(data), 200



# PLACEMENT DRIVE MANAGEMENT

@admin_bp.route("/drives", methods=["GET"])
@jwt_required()
def list_drives():
    """List all placement drives. Query params: ?status=pending|approved|closed"""
    err = _require_admin()
    if err:
        return err

    status = request.args.get("status", "").strip()
    query = PlacementDrive.query
    if status:
        query = query.filter_by(status=status)

    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    return jsonify([d.to_dict() for d in drives]), 200


@admin_bp.route("/drives/<int:drive_id>/approve", methods=["PUT"])
@jwt_required()
def approve_drive(drive_id):
    """Approve a pending placement drive — makes it visible to students."""
    err = _require_admin()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "approved"
    db.session.commit()
    # Invalidate drives cache so students see the newly approved drive
    rr_cache_delete("drives:approved")
    rr_cache_delete("admin:dashboard")
    return jsonify({"message": f"Drive '{drive.job_title}' approved."}), 200


@admin_bp.route("/drives/<int:drive_id>/reject", methods=["PUT"])
@jwt_required()
def reject_drive(drive_id):
    """Reject a placement drive."""
    err = _require_admin()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "rejected"
    db.session.commit()
    rr_cache_delete("drives:approved")
    return jsonify({"message": f"Drive '{drive.job_title}' rejected."}), 200


@admin_bp.route("/drives/<int:drive_id>", methods=["DELETE"])
@jwt_required()
def delete_drive(drive_id):
    """Remove a placement drive from the system."""
    err = _require_admin()
    if err:
        return err

    drive = PlacementDrive.query.get_or_404(drive_id)
    title = drive.job_title
    db.session.delete(drive)
    db.session.commit()
    rr_cache_delete("drives:approved")
    rr_cache_delete("admin:dashboard")
    return jsonify({"message": f"Drive '{title}' deleted."}), 200



# ALL APPLICATIONS VIEW

@admin_bp.route("/applications", methods=["GET"])
@jwt_required()
def list_all_applications():
    """Admin view of all applications across all drives."""
    err = _require_admin()
    if err:
        return err

    apps = Application.query.order_by(Application.applied_at.desc()).all()
    return jsonify([a.to_dict() for a in apps]), 200
