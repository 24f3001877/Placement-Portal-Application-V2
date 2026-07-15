# RecruitRadar — routes/student.py
# Student-only routes: profile, drives, apply, history, CSV export.

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import (
    User, StudentProfile, PlacementDrive, Application,
    Placement, ExportJob
)
from cache import rr_cache_get, rr_cache_set, rr_cache_delete

student_bp = Blueprint("student", __name__, url_prefix="/api/student")


def _require_student():
    """
    Validate JWT for student role.
    Returns (student_profile, None) or (None, error_response).
    """
    claims = get_jwt()
    if claims.get("role") != "student":
        return None, (jsonify({"error": "Student access required."}), 403)

    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    if not student:
        return None, (jsonify({"error": "Student profile not found."}), 404)

    user = User.query.get(user_id)
    if user and user.is_blacklisted:
        return None, (jsonify({"error": "Your account has been blacklisted."}), 403)

    return student, None


def _allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension (PDF only)."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"pdf"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed



# PROFILE

@student_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Return the student's own profile."""
    student, err = _require_student()
    if err:
        return err
    return jsonify(student.to_dict()), 200


@student_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    Update student profile fields.
    Accepts multipart/form-data (for resume upload) or JSON.

    Fields:
        full_name, phone, branch, year, cgpa, skills, experience
    Resume:
        resume file (PDF, max 5MB) — field name: 'resume'
    """
    student, err = _require_student()
    if err:
        return err

    # Handle multipart form data (resume upload) or JSON
    if request.content_type and "multipart" in request.content_type:
        data = request.form
    else:
        data = request.get_json(silent=True) or {}

    # Update text fields
    if "full_name" in data and data["full_name"].strip():
        student.full_name = data["full_name"].strip()
    if "phone" in data:
        student.phone = data["phone"].strip() or None
    if "branch" in data and data["branch"].strip():
        student.branch = data["branch"].strip()
    if "year" in data:
        try:
            student.year = int(data["year"])
        except (ValueError, TypeError):
            return jsonify({"error": "year must be an integer."}), 400
    if "cgpa" in data:
        try:
            cgpa = float(data["cgpa"])
            if not (0.0 <= cgpa <= 10.0):
                return jsonify({"error": "CGPA must be between 0.0 and 10.0."}), 400
            student.cgpa = cgpa
        except (ValueError, TypeError):
            return jsonify({"error": "cgpa must be a number."}), 400
    if "skills" in data:
        student.skills = data["skills"].strip() or None
    if "experience" in data:
        student.experience = data["experience"].strip() or None

    # Handle resume upload
    if "resume" in request.files:
        file = request.files["resume"]
        if file.filename:
            if not _allowed_file(file.filename):
                return jsonify({"error": "Only PDF resumes are accepted."}), 400

            upload_folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_folder, exist_ok=True)
            safe_name = secure_filename(file.filename)
            filename = f"resume_{student.id}_{safe_name}"
            file.save(os.path.join(upload_folder, filename))
            student.resume_path = filename

    student.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Profile updated.", "profile": student.to_dict()}), 200


@student_bp.route("/resume/<path:filename>", methods=["GET"])
@jwt_required()
def download_resume(filename):
    """Download a student's own resume (or admin/company can download too — handled by ownership check)."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)



# PLACEMENT DRIVES

@student_bp.route("/drives", methods=["GET"])
@jwt_required()
def list_drives():
    """
    List approved placement drives with optional search/filter.
    Cached under rr_cache:drives:approved for RR_CACHE_TTL_DRIVES seconds.

    Query params:
        search  : text search in job_title, company_name, skills_required
        branch  : filter by eligible branch
        min_cgpa: filter drives where min_cgpa <= student's cgpa
    """
    student, err = _require_student()
    if err:
        return err

    search = request.args.get("search", "").strip()
    branch_filter = request.args.get("branch", "").strip()

    # Build a cache key that includes query params
    cache_key = f"drives:approved:{search}:{branch_filter}"
    ttl = current_app.config.get("RR_CACHE_TTL_DRIVES", 120)
    cached = rr_cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    query = (
        PlacementDrive.query
        .filter_by(status="approved")
        .filter(PlacementDrive.deadline >= datetime.utcnow())
    )

    if search:
        query = query.join(
            PlacementDrive.company
        ).filter(
            db.or_(
                PlacementDrive.job_title.ilike(f"%{search}%"),
                PlacementDrive.skills_required.ilike(f"%{search}%"),
                PlacementDrive.company.has(
                    db.or_(
                        # Search by company name
                    )
                )
            )
        )
        # Simpler join approach
        from models import CompanyProfile
        query = (
            PlacementDrive.query
            .join(CompanyProfile, PlacementDrive.company_id == CompanyProfile.id)
            .filter(PlacementDrive.status == "approved")
            .filter(PlacementDrive.deadline >= datetime.utcnow())
            .filter(
                db.or_(
                    PlacementDrive.job_title.ilike(f"%{search}%"),
                    PlacementDrive.skills_required.ilike(f"%{search}%"),
                    CompanyProfile.company_name.ilike(f"%{search}%"),
                )
            )
        )

    drives = query.order_by(PlacementDrive.deadline.asc()).all()

    # Eligibility filter — show if student meets criteria
    result = []
    for drive in drives:
        if branch_filter and drive.eligible_branch:
            eligible_branches = [b.strip().lower() for b in drive.eligible_branch.split(",")]
            if branch_filter.lower() not in eligible_branches:
                continue
        result.append(drive.to_dict())

    rr_cache_set(cache_key, result, ttl)
    return jsonify(result), 200


@student_bp.route("/drives/<int:drive_id>", methods=["GET"])
@jwt_required()
def get_drive(drive_id):
    """Get details of a single approved drive."""
    student, err = _require_student()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, status="approved").first()
    if not drive:
        return jsonify({"error": "Drive not found or not yet approved."}), 404

    data = drive.to_dict()
    # Check if student already applied
    existing = Application.query.filter_by(
        student_id=student.id, drive_id=drive_id
    ).first()
    data["already_applied"] = existing is not None
    data["application_status"] = existing.status if existing else None
    return jsonify(data), 200


# APPLICATIONS

@student_bp.route("/drives/<int:drive_id>/apply", methods=["POST"])
@jwt_required()
def apply(drive_id):
    """
    Apply for an approved placement drive.
    Enforces:
     - Duplicate prevention (unique constraint on student+drive)
     - Eligibility validation (CGPA, branch, year)
     - Deadline check
    """
    student, err = _require_student()
    if err:
        return err

    drive = PlacementDrive.query.filter_by(id=drive_id, status="approved").first()
    if not drive:
        return jsonify({"error": "Drive not found or not yet approved."}), 404

    # Deadline check
    if drive.deadline < datetime.utcnow():
        return jsonify({"error": "Application deadline has passed."}), 400

    # Duplicate check
    existing = Application.query.filter_by(
        student_id=student.id, drive_id=drive_id
    ).first()
    if existing:
        return jsonify({"error": "You have already applied to this drive."}), 409

    # ── Eligibility validation 
    if drive.min_cgpa and student.cgpa < drive.min_cgpa:
        return jsonify({
            "error": f"Your CGPA ({student.cgpa}) does not meet the minimum requirement ({drive.min_cgpa})."
        }), 400

    if drive.eligible_branch:
        allowed_branches = [b.strip().lower() for b in drive.eligible_branch.split(",")]
        if student.branch.lower() not in allowed_branches:
            return jsonify({
                "error": f"Your branch ({student.branch}) is not eligible for this drive. "
                         f"Eligible branches: {drive.eligible_branch}"
            }), 400

    if drive.eligible_year and student.year < drive.eligible_year:
        return jsonify({
            "error": f"Only Year {drive.eligible_year} students are eligible for this drive."
        }), 400

    # Create application
    application = Application(
        student_id=student.id,
        drive_id=drive_id,
        status="applied",
    )
    db.session.add(application)
    db.session.commit()

    return jsonify({
        "message": "Application submitted successfully.",
        "application": application.to_dict(),
    }), 201


@student_bp.route("/applications", methods=["GET"])
@jwt_required()
def my_applications():
    """View all of the student's own applications (placement history)."""
    student, err = _require_student()
    if err:
        return err

    apps = (
        Application.query
        .filter_by(student_id=student.id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in apps]), 200


@student_bp.route("/placements", methods=["GET"])
@jwt_required()
def my_placements():
    """View confirmed placement records (status='placed') for the student."""
    student, err = _require_student()
    if err:
        return err

    placements = (
        Placement.query
        .filter_by(student_id=student.id)
        .order_by(Placement.placed_at.desc())
        .all()
    )
    return jsonify([p.to_dict() for p in placements]), 200


@student_bp.route("/interviews", methods=["GET"])
@jwt_required()
def my_interviews():
    """View applications with scheduled interview dates."""
    student, err = _require_student()
    if err:
        return err

    interviews = (
        Application.query
        .filter(
            Application.student_id == student.id,
            Application.interview_date.isnot(None),
        )
        .order_by(Application.interview_date.asc())
        .all()
    )
    return jsonify([a.to_dict() for a in interviews]), 200


@student_bp.route("/offer-letter/<int:placement_id>", methods=["GET"])
@jwt_required()
def download_offer_letter(placement_id):
    """Download the offer letter PDF for a confirmed placement."""
    student, err = _require_student()
    if err:
        return err

    placement = Placement.query.filter_by(
        id=placement_id, student_id=student.id
    ).first()
    if not placement:
        return jsonify({"error": "Placement record not found."}), 404
    if not placement.offer_letter_path:
        return jsonify({"error": "Offer letter has not been generated yet."}), 404

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, placement.offer_letter_path, as_attachment=True)



# CSV EXPORT (async via Celery)

@student_bp.route("/export", methods=["POST"])
@jwt_required()
def export_csv():
    """
    Trigger async CSV export of the student's full application history.
    Creates ExportJob and dispatches rr_task_export_applications_csv Celery task.
    """
    student, err = _require_student()
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
            args=[export_job.id, user_id, "student"],
        )
        export_job.celery_task_id = task.id
        db.session.commit()

    return jsonify({
        "message": "Export started. You will receive an email when the file is ready.",
        "export_job_id": export_job.id,
    }), 202


@student_bp.route("/export/<int:job_id>/status", methods=["GET"])
@jwt_required()
def export_status(job_id):
    """Poll the status of a CSV export job."""
    student, err = _require_student()
    if err:
        return err

    user_id = int(get_jwt_identity())
    job = ExportJob.query.filter_by(id=job_id, user_id=user_id).first()
    if not job:
        return jsonify({"error": "Export job not found."}), 404

    return jsonify(job.to_dict()), 200


@student_bp.route("/export/<path:filename>/download", methods=["GET"])
@jwt_required()
def download_csv(filename):
    """Download a completed CSV export file."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)



# ATS RESUME CHECKER

@student_bp.route("/ats-check", methods=["POST"])
@jwt_required()
def ats_check():
    """
    ATS-style resume checker.

    Problem it solves:
        Students often apply to drives without knowing if their resume
        matches the requirements. This tool parses their uploaded resume PDF,
        extracts the text, and compares it against a specific drive's
        skills_required field to give an instant match score.

    Approach (keyword matching):
        1. Extract raw text from the student's resume PDF using pdfplumber.
        2. Split the drive's skills_required into individual keywords.
        3. Check which keywords appear in the resume text (case-insensitive).
        4. Calculate: match_score = matched_count / total_skills * 100
        5. Return matched skills, missing skills, and score.

    Why keyword matching and not ML:
        Transparent, explainable, fast, and zero external API dependency.
        Every result can be justified line by line — ideal for a college project viva.

    Body (JSON):
        drive_id : int — the placement drive to check against
    """
    student, err = _require_student()
    if err:
        return err

    # Student must have uploaded a resume
    if not student.resume_path:
        return jsonify({
            "error": "No resume found. Please upload your resume PDF from My Profile first."
        }), 400

    data = request.get_json(silent=True) or {}
    drive_id = data.get("drive_id")

    if not drive_id:
        return jsonify({"error": "drive_id is required."}), 400

    # Fetch the drive
    from models import PlacementDrive
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found."}), 404

    # Drive must be approved for students to check against it
    if drive.status != "approved":
        return jsonify({"error": "You can only check against approved drives."}), 400

    # ── Step 1: Extract text from resume PDF
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    resume_path = os.path.join(upload_folder, student.resume_path)

    if not os.path.exists(resume_path):
        return jsonify({"error": "Resume file not found on server. Please re-upload."}), 404

    try:
        import pdfplumber
        resume_text = ""
        with pdfplumber.open(resume_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    resume_text += page_text + " "
        resume_text = resume_text.lower().strip()
    except Exception as e:
        return jsonify({"error": f"Could not read resume PDF: {str(e)}"}), 500

    if not resume_text:
        return jsonify({"error": "Resume appears to be empty or is a scanned image PDF. Please upload a text-based PDF."}), 400

    # ── Step 2: Build skills list from drive 
    # skills_required is stored as comma-separated e.g. "Python, SQL, Django, REST APIs"
    if not drive.skills_required:
        return jsonify({
            "message": "This drive has no specific skills listed. Your resume passes by default.",
            "match_score": 100,
            "matched_skills": [],
            "missing_skills": [],
            "total_skills": 0,
            "drive_title": drive.job_title,
            "company_name": drive.company.company_name if drive.company else "",
        }), 200

    raw_skills = [s.strip() for s in drive.skills_required.split(",") if s.strip()]

    # ── Step 3: Match each skill against resume text 
    # Simple case-insensitive substring check.
    # e.g. "REST APIs" → check if "rest apis" appears anywhere in resume text.
    matched = []
    missing = []

    for skill in raw_skills:
        skill_lower = skill.lower()
        if skill_lower in resume_text:
            matched.append(skill)
        else:
            missing.append(skill)

    # ── Step 4: Calculate match score 
    total = len(raw_skills)
    match_score = round((len(matched) / total) * 100, 1) if total > 0 else 100.0

    # ── Step 5: Generate feedback message 
    if match_score == 100:
        feedback = "Excellent! Your resume matches all required skills for this drive."
    elif match_score >= 75:
        feedback = "Good match. Consider adding the missing skills to strengthen your application."
    elif match_score >= 50:
        feedback = "Moderate match. Work on the missing skills before applying."
    else:
        feedback = "Low match. Your resume may not meet the requirements for this drive."

    return jsonify({
        "drive_title":    drive.job_title,
        "company_name":   drive.company.company_name if drive.company else "",
        "total_skills":   total,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score":    match_score,
        "feedback":       feedback,
    }), 200
