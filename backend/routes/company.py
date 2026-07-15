# RecruitRadar — routes/company.py
# Company-only routes: drives, applications, shortlisting, interviews, offer letters.

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from extensions import db
from models import (
    User, CompanyProfile, PlacementDrive, Application,
    StudentProfile, Placement, ExportJob
)
from cache import rr_cache_get, rr_cache_set, rr_cache_delete, rr_cache_delete_pattern

company_bp = Blueprint("company", __name__, url_prefix="/api/company")


def _require_company():
    """
    Validate JWT for company role and return (company_profile, None) or (None, error_response).
    Also checks that the company is approved — unapproved companies cannot access any route.
    """
    claims = get_jwt()
    if claims.get("role") != "company":
        return None, (jsonify({"error": "Company access required."}), 403)

    user_id = int(get_jwt_identity())
    company = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not company:
        return None, (jsonify({"error": "Company profile not found."}), 404)
    if company.approval_status != "approved":
        return None, (jsonify({
            "error": f"Your company is '{company.approval_status}'. Only approved companies can access this."
        }), 403)

    user = User.query.get(user_id)
    if user and user.is_blacklisted:
        return None, (jsonify({"error": "Your account has been blacklisted."}), 403)

    return company, None



# COMPANY DASHBOARD

@company_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    """
    Company dashboard statistics.
    Cached under rr_cache:company:<id>:dashboard.
    """
    company, err = _require_company()
    if err:
        return err

    cache_key = f"company:{company.id}:dashboard"
    ttl = current_app.config.get("RR_CACHE_TTL_COMPANY_DASH", 180)
    cached = rr_cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    total_drives = len(company.drives)
    total_applicants = sum(len(d.applications) for d in company.drives)
    shortlisted = Application.query.join(PlacementDrive).filter(
        PlacementDrive.company_id == company.id,
        Application.status == "shortlisted",
    ).count()
    placed = Application.query.join(PlacementDrive).filter(
        PlacementDrive.company_id == company.id,
        Application.status == "placed",
    ).count()

    result = {
        "company": company.to_dict(),
        "total_drives": total_drives,
        "total_applicants": total_applicants,
        "shortlisted": shortlisted,
        "placed": placed,
    }
    rr_cache_set(cache_key, result, ttl)
    return jsonify(result), 200



# PLACEMENT DRIVES

@company_bp.route("/drives", methods=["GET"])
@jwt_required()
def list_drives():
    """List all drives created by this company."""
    company, err = _require_company()
    if err:
        return err

    drives = (
        PlacementDrive.query
        .filter_by(company_id=company.id)
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )
    return jsonify([d.to_dict() for d in drives]), 200


@company_bp.route("/drives", methods=["POST"])
@jwt_required()
def create_drive():
    """
    Create a new placement drive.
    Drive starts with status='pending' — admin must approve before students can see it.

    Body (JSON):
        job_title           : string (required)
        job_description     : string (required)
        deadline            : string ISO format (required) e.g. "2025-12-31"
        skills_required     : string (optional)
        experience_required : string (optional) e.g. "0-2 years"
        salary              : string (optional) e.g. "8-12 LPA"
        benefits            : string (optional)
        eligible_branch     : string (optional) comma-separated e.g. "CSE,ECE"
        min_cgpa            : float (optional, default 0.0)
        eligible_year       : int (optional)
    """
    company, err = _require_company()
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body."}), 400

    job_title = data.get("job_title", "").strip()
    job_description = data.get("job_description", "").strip()
    deadline_str = data.get("deadline", "").strip()

    if not job_title:
        return jsonify({"error": "job_title is required."}), 400
    if not job_description:
        return jsonify({"error": "job_description is required."}), 400
    if not deadline_str:
        return jsonify({"error": "deadline is required."}), 400

    try:
        deadline = datetime.fromisoformat(deadline_str)
    except ValueError:
        return jsonify({"error": "deadline must be a valid ISO date string (e.g. '2025-12-31')."}), 400

    if deadline <= datetime.utcnow():
        return jsonify({"error": "Deadline must be a future date."}), 400

    drive = PlacementDrive(
        company_id=company.id,
        job_title=job_title,
        job_description=job_description,
        deadline=deadline,
        skills_required=data.get("skills_required", "").strip() or None,
        experience_required=data.get("experience_required", "").strip() or None,
        salary=data.get("salary", "").strip() or None,
        benefits=data.get("benefits", "").strip() or None,
        eligible_branch=data.get("eligible_branch", "").strip() or None,
        min_cgpa=float(data.get("min_cgpa", 0.0)),
        eligible_year=data.get("eligible_year") or None,
        status="pending",
    )
    db.session.add(drive)
    db.session.commit()

    # Invalidate company dashboard cache
    rr_cache_delete(f"company:{company.id}:dashboard")

    return jsonify({
        "message": "Placement drive created. Awaiting admin approval.",
        "drive": drive.to_dict(),
    }), 201


@company_bp.route("/drives/<int:drive_id>", methods=["PUT"])
@jwt_required()
def update_drive(drive_id):
    """Update drive details or close a drive. Companies can close their own drives."""
    company, err = _require_company()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"error": "Drive not found or does not belong to your company."}), 404

    data = request.get_json(silent=True) or {}

    if "job_title" in data:
        drive.job_title = data["job_title"].strip()
    if "job_description" in data:
        drive.job_description = data["job_description"].strip()
    if "skills_required" in data:
        drive.skills_required = data["skills_required"].strip() or None
    if "salary" in data:
        drive.salary = data["salary"].strip() or None
    if "benefits" in data:
        drive.benefits = data["benefits"].strip() or None
    if "status" in data and data["status"] in ("pending", "closed"):
        drive.status = data["status"]
    if "deadline" in data:
        try:
            drive.deadline = datetime.fromisoformat(data["deadline"])
        except ValueError:
            return jsonify({"error": "Invalid deadline format."}), 400

    db.session.commit()
    rr_cache_delete("drives:approved")
    rr_cache_delete(f"company:{company.id}:dashboard")
    return jsonify({"message": "Drive updated.", "drive": drive.to_dict()}), 200



# APPLICATION MANAGEMENT

@company_bp.route("/drives/<int:drive_id>/applications", methods=["GET"])
@jwt_required()
def list_applications(drive_id):
    """List all student applications for a specific drive."""
    company, err = _require_company()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"error": "Drive not found or does not belong to your company."}), 404

    apps = Application.query.filter_by(drive_id=drive_id).all()
    return jsonify([a.to_dict() for a in apps]), 200


@company_bp.route("/applications/<int:app_id>", methods=["PUT"])
@jwt_required()
def update_application(app_id):
    """
    Update application status and optionally set interview date or feedback.
    Valid status values: applied | shortlisted | interview | placed | rejected

    Body (JSON):
        status          : string (required)
        interview_date  : string ISO format (optional, required when status='interview')
        feedback        : string (optional)
    """
    company, err = _require_company()
    if err:
        return err

    app = Application.query.get_or_404(app_id)

    # Ownership check — this application must belong to one of the company's drives
    drive = PlacementDrive.query.filter_by(id=app.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"error": "Application does not belong to your company's drive."}), 403
    
    previous_status = app.status

    data = request.get_json(silent=True) or {}
    valid_statuses = ("applied", "shortlisted", "interview", "placed", "rejected")
    new_status = data.get("status", "").strip()

    if new_status and new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    if new_status:
        app.status = new_status

    if new_status and previous_status == "interview" and new_status != "interview":
        app.interview_date = None 


    if "interview_date" in data and data["interview_date"]:
        try:
            app.interview_date = datetime.fromisoformat(data["interview_date"])
        except ValueError:
            return jsonify({"error": "Invalid interview_date format."}), 400

    if "feedback" in data:
        app.feedback = data["feedback"].strip() or None

    # If status is 'placed', create a Placement record if it doesn't exist
    if new_status == "placed":
        existing_placement = Placement.query.filter_by(
            student_id=app.student_id,
            drive_id=app.drive_id,
        ).first()

        if not existing_placement:
            placement = Placement(
                student_id=app.student_id,
                company_id=company.id,
                drive_id=app.drive_id,
                position=drive.job_title,
                salary=drive.salary,
            )
            db.session.add(placement)

    elif new_status and previous_status == "placed" and new_status != "placed":
        stale_placement = Placement.query.filter_by(
            student_id=app.student_id, drive_id=app.drive_id,
        ).first()
        if stale_placement:
            db.session.delete(stale_placement)

    db.session.commit()
    rr_cache_delete(f"company:{company.id}:dashboard")
    return jsonify({"message": "Application updated.", "application": app.to_dict()}), 200

# Send Interview Reminder

@company_bp.route("/applications/<int:app_id>/send-interview-reminder", methods=["POST"])
@jwt_required()
def send_interview_reminder(app_id):
    """Trigger an async reminder email to a candidate currently in 'interview' status."""
    company, err = _require_company()
    if err:
        return err

    app = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.filter_by(id=app.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"error": "Application does not belong to your company's drive."}), 403

    if app.status != "interview":
        return jsonify({"error": "Reminder can only be sent for candidates in 'interview' status."}), 400

    from tasks import get_celery
    celery = get_celery()
    if celery:
        celery.send_task("tasks.rr_task_send_interview_reminder", args=[app.id])

    return jsonify({"message": f"Interview reminder queued for {app.student.full_name if app.student else 'candidate'}."}), 202



# OFFER LETTER GENERATION

@company_bp.route("/applications/<int:app_id>/offer-letter", methods=["POST"])
@jwt_required()
def generate_offer_letter(app_id):
    """
    Generate a dummy PDF offer letter for a placed student.
    Stored with rr_export_ prefix. Requires fpdf2 package.
    """
    company, err = _require_company()
    if err:
        return err

    app = Application.query.get_or_404(app_id)
    drive = PlacementDrive.query.filter_by(id=app.drive_id, company_id=company.id).first()
    if not drive:
        return jsonify({"error": "Not authorized."}), 403

    if app.status != "placed":
        return jsonify({"error": "Offer letters can only be generated for placed students."}), 400

    student = StudentProfile.query.get(app.student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 14, "OFFER LETTER", ln=True, align="C")
        pdf.set_font("Helvetica", "", 12)
        pdf.ln(6)
        pdf.cell(0, 8, f"Company: {company.company_name}", ln=True)
        pdf.cell(0, 8, f"Date: {datetime.utcnow().strftime('%d %B %Y')}", ln=True)
        pdf.ln(8)
        pdf.multi_cell(0, 8,
            f"Dear {student.full_name},\n\n"
            f"We are pleased to offer you the position of {drive.job_title} at {company.company_name}.\n\n"
            f"Salary Package: {drive.salary or 'As discussed'}\n"
            f"Benefits: {drive.benefits or 'As per company policy'}\n\n"
            f"Please confirm your acceptance within 7 days.\n\n"
            f"Congratulations and welcome to the team!\n\n"
            f"HR Team\n{company.company_name}"
        )

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        filename = f"rr_export_offer_{app_id}_{student.id}.pdf"
        filepath = os.path.join(upload_folder, filename)
        pdf.output(filepath)

        # Update placement record with offer letter path
        placement = Placement.query.filter_by(
            student_id=app.student_id, drive_id=app.drive_id
        ).first()
        if placement:
            placement.offer_letter_path = filename
            db.session.commit()

        return jsonify({
            "message": "Offer letter generated.",
            "file": filename,
        }), 200

    except ImportError:
        return jsonify({"error": "PDF generation library not installed. Run: pip install fpdf2"}), 500



# CSV EXPORT (async via Celery)

@company_bp.route("/export", methods=["POST"])
@jwt_required()
def export_csv():
    """
    Trigger async CSV export of all applications for this company.
    Creates an ExportJob record and dispatches a Celery task.
    """
    company, err = _require_company()
    if err:
        return err

    user_id = int(get_jwt_identity())

    export_job = ExportJob(user_id=user_id, status="pending")
    db.session.add(export_job)
    db.session.commit()

    from tasks import get_celery
    celery = get_celery()
    if celery:
        task = celery.send_task(
            "tasks.rr_task_export_applications_csv",
            args=[export_job.id, user_id, "company"],
        )
        export_job.celery_task_id = task.id
        db.session.commit()

    return jsonify({
        "message": "Export started. You will receive an email when the file is ready.",
        "export_job_id": export_job.id,
    }), 202


@company_bp.route("/export/<int:job_id>/status", methods=["GET"])
@jwt_required()
def export_status(job_id):
    """Check the status of a CSV export job."""
    company, err = _require_company()
    if err:
        return err

    user_id = int(get_jwt_identity())
    job = ExportJob.query.filter_by(id=job_id, user_id=user_id).first()
    if not job:
        return jsonify({"error": "Export job not found."}), 404

    return jsonify(job.to_dict()), 200

@company_bp.route("/export/<path:filename>/download", methods=["GET"])
@jwt_required()
def download_csv(filename):
    """Download a completed CSV export file."""
    company, err = _require_company()
    if err:
        return err
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)
