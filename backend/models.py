# RecruitRadar — models.py
# RR-SEED: All database models defined using SQLAlchemy ORM.
# Tables are created programmatically via db.create_all() — never manually.

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db



# USER MODEL  (unified model for all roles)

class User(db.Model):
    """
    Unified user model for Admin, Company, and Student roles.
    Role is stored as a string — 'admin' | 'company' | 'student'.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin | company | student
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (one-to-one profiles)
    student_profile = db.relationship(
        "StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    company_profile = db.relationship(
        "CompanyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and store password using Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Return safe public fields — password_hash is always excluded."""
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "is_blacklisted": self.is_blacklisted,
            "created_at": self.created_at.isoformat(),
        }



# STUDENT PROFILE

class StudentProfile(db.Model):
    """
    Extended profile for students.
    Linked 1:1 to User (role='student').
    """
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    branch = db.Column(db.String(80), nullable=False)   # e.g. CSE, ECE
    year = db.Column(db.Integer, nullable=False)         # e.g. 3 (3rd year)
    cgpa = db.Column(db.Float, nullable=False)
    skills = db.Column(db.Text, nullable=True)           # comma-separated
    experience = db.Column(db.Text, nullable=True)       # brief experience text
    resume_path = db.Column(db.String(256), nullable=True)  # path under uploads/
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship(
        "Application", back_populates="student", cascade="all, delete-orphan"
    )
    placements = db.relationship(
        "Placement", back_populates="student", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "full_name": self.full_name,
            "phone": self.phone,
            "branch": self.branch,
            "year": self.year,
            "cgpa": self.cgpa,
            "skills": self.skills,
            "experience": self.experience,
            "resume_path": self.resume_path,
            "is_active": self.user.is_active if self.user else None,
            "is_blacklisted": self.user.is_blacklisted if self.user else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }



# COMPANY PROFILE

class CompanyProfile(db.Model):
    """
    Extended profile for companies.
    Linked 1:1 to User (role='company').
    Approval is managed by Admin.
    """
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    hr_contact = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    # Approval states: pending | approved | rejected
    approval_status = db.Column(db.String(20), default="pending", nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="company_profile")
    drives = db.relationship(
        "PlacementDrive", back_populates="company", cascade="all, delete-orphan"
    )
    placements = db.relationship(
        "Placement", back_populates="company", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.user.email if self.user else None,
            "company_name": self.company_name,
            "industry": self.industry,
            "location": self.location,
            "website": self.website,
            "hr_contact": self.hr_contact,
            "description": self.description,
            "approval_status": self.approval_status,
            "is_active": self.user.is_active if self.user else None,
            "is_blacklisted": self.user.is_blacklisted if self.user else None,
            "registered_at": self.registered_at.isoformat(),
        }



# PLACEMENT DRIVE (Job Position)

class PlacementDrive(db.Model):
    """
    A recruitment event / job posting created by a Company.
    Only visible to students after Admin approves it.
    Status lifecycle: pending → approved → closed
    """
    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("company_profiles.id"), nullable=False
    )
    job_title = db.Column(db.String(120), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.Text, nullable=True)   # comma-separated
    experience_required = db.Column(db.String(80), nullable=True)  # e.g. "0-2 years"
    salary = db.Column(db.String(80), nullable=True)       # e.g. "8-12 LPA"
    benefits = db.Column(db.Text, nullable=True)

    # Eligibility criteria
    eligible_branch = db.Column(db.String(200), nullable=True)  # comma-separated branches
    min_cgpa = db.Column(db.Float, default=0.0)
    eligible_year = db.Column(db.Integer, nullable=True)  # e.g. 3 or 4

    deadline = db.Column(db.DateTime, nullable=False)
    # Status: pending | approved | closed
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company = db.relationship("CompanyProfile", back_populates="drives")
    applications = db.relationship(
        "Application", back_populates="drive", cascade="all, delete-orphan"
    )

    def to_dict(self, include_company=True) -> dict:
        data = {
            "id": self.id,
            "company_id": self.company_id,
            "job_title": self.job_title,
            "job_description": self.job_description,
            "skills_required": self.skills_required,
            "experience_required": self.experience_required,
            "salary": self.salary,
            "benefits": self.benefits,
            "eligible_branch": self.eligible_branch,
            "min_cgpa": self.min_cgpa,
            "eligible_year": self.eligible_year,
            "deadline": self.deadline.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "applicant_count": len(self.applications),
        }
        if include_company and self.company:
            data["company_name"] = self.company.company_name
            data["company_industry"] = self.company.industry
        return data



# APPLICATION

class Application(db.Model):
    """
    Records a student applying to a PlacementDrive.
    Status lifecycle: applied → shortlisted → interview → offer → placed | rejected
    Duplicate prevention: unique constraint on (student_id, drive_id).
    """
    __tablename__ = "applications"
    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    drive_id = db.Column(
        db.Integer, db.ForeignKey("placement_drives.id"), nullable=False
    )
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Status: applied | shortlisted | interview | offer | placed | rejected
    status = db.Column(db.String(20), default="applied", nullable=False)

    # Interview scheduling (company fills these)
    interview_date = db.Column(db.DateTime, nullable=True)
    feedback = db.Column(db.Text, nullable=True)

    # Relationships
    student = db.relationship("StudentProfile", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "drive_id": self.drive_id,
            "student_name": self.student.full_name if self.student else None,
            "student_email": self.student.user.email if self.student and self.student.user else None,
            "student_branch": self.student.branch if self.student else None,
            "student_cgpa": self.student.cgpa if self.student else None,
            "company_name": self.drive.company.company_name if self.drive and self.drive.company else None,
            "job_title": self.drive.job_title if self.drive else None,
            "applied_at": self.applied_at.isoformat(),
            "status": self.status,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
            "feedback": self.feedback,
        }



# PLACEMENT (confirmed placement record)

class Placement(db.Model):
    """
    Created when a student is officially placed (status='placed' on Application).
    Stores final placement details — salary, joining date, offer letter.
    """
    __tablename__ = "placements"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("company_profiles.id"), nullable=False
    )
    drive_id = db.Column(
        db.Integer, db.ForeignKey("placement_drives.id"), nullable=False
    )
    position = db.Column(db.String(120), nullable=False)
    salary = db.Column(db.String(80), nullable=True)
    joining_date = db.Column(db.Date, nullable=True)
    # Path to generated offer letter PDF (rr_export_ prefix naming)
    offer_letter_path = db.Column(db.String(256), nullable=True)
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship("StudentProfile", back_populates="placements")
    company = db.relationship("CompanyProfile", back_populates="placements")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "company_id": self.company_id,
            "company_name": self.company.company_name if self.company else None,
            "drive_id": self.drive_id,
            "position": self.position,
            "salary": self.salary,
            "joining_date": self.joining_date.isoformat() if self.joining_date else None,
            "offer_letter_path": self.offer_letter_path,
            "placed_at": self.placed_at.isoformat(),
        }



# EXPORT JOB (tracks async CSV export tasks)

class ExportJob(db.Model):
    """
    Tracks user-triggered CSV export batch jobs.
    Created when student/company requests export; updated by Celery task.
    """
    __tablename__ = "export_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # pending | processing | done | failed
    status = db.Column(db.String(20), default="pending", nullable=False)
    # File stored with rr_export_ prefix
    file_path = db.Column(db.String(256), nullable=True)
    celery_task_id = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "file_path": self.file_path,
            "celery_task_id": self.celery_task_id,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
