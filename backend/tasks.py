# RecruitRadar — tasks.py
# Celery tasks using the "rr_task" prefix.
# Three tasks: daily deadline reminder, monthly report, user-triggered CSV export.

import csv
import os
from datetime import datetime, date, timedelta
from celery import Celery
from flask import render_template_string


def make_celery(app):
    """
    Create and configure a Celery instance bound to the Flask app context.
    Called from celery_worker.py.
    """
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Ensure every Celery task runs inside the Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# ── celery instance (configured properly in celery_worker.py) ─────────────────
# Imported and used in route files that trigger tasks
celery_app: Celery | None = None


def get_celery():
    """Return the Celery app (must be initialized via make_celery first)."""
    return celery_app


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — Daily Deadline Reminder (Scheduled)
# rr_task_send_deadline_reminders
# ─────────────────────────────────────────────────────────────────────────────
def rr_task_send_deadline_reminders():
    """
    Scheduled daily task.
    Finds all approved drives whose deadline is within the next 3 days
    and sends a reminder email to all students who haven't applied yet.
    """
    from extensions import mail, db
    from models import PlacementDrive, StudentProfile, Application, User
    from flask_mail import Message

    today = datetime.utcnow()
    cutoff = today + timedelta(days=3)

    # Drives with deadlines approaching in next 3 days
    upcoming_drives = PlacementDrive.query.filter(
        PlacementDrive.status == "approved",
        PlacementDrive.deadline >= today,
        PlacementDrive.deadline <= cutoff,
    ).all()

    if not upcoming_drives:
        return {"status": "no upcoming drives"}

    # Get all active, non-blacklisted students
    students = (
        StudentProfile.query
        .join(User, StudentProfile.user_id == User.id)
        .filter(User.is_active == True, User.is_blacklisted == False)
        .all()
    )

    sent_count = 0
    for student in students:
        # Find drives the student hasn't applied to yet
        applied_ids = {app.drive_id for app in student.applications}
        drives_to_remind = [d for d in upcoming_drives if d.id not in applied_ids]

        if not drives_to_remind:
            continue

        drive_lines = "\n".join(
            [f"- {d.job_title} at {d.company.company_name} (Deadline: {d.deadline.strftime('%d %b %Y')})"
             for d in drives_to_remind]
        )

        body = (
            f"Dear {student.full_name},\n\n"
            f"This is a reminder from RecruitRadar. The following placement drives "
            f"have deadlines approaching in the next 3 days:\n\n"
            f"{drive_lines}\n\n"
            f"Log in to RecruitRadar to apply before the deadline.\n\n"
            f"— RecruitRadar Placement Portal"
        )

        try:
            msg = Message(
                subject="RecruitRadar — Upcoming Placement Drive Deadlines",
                recipients=[student.user.email],
                body=body,
            )
            mail.send(msg)
            sent_count += 1
        except Exception:
            pass  # Log failure but continue sending to others

    return {"status": "done", "emails_sent": sent_count}


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — Monthly Placement Report (Scheduled, 1st of month)
# rr_task_send_monthly_report
# ─────────────────────────────────────────────────────────────────────────────
def rr_task_send_monthly_report():
    """
    Runs daily but only executes the actual report on the 1st of each month.
    Generates an HTML report with placement statistics and emails it to admin.
    """
    from extensions import mail
    from flask_mail import Message
    from flask import current_app

    # Only execute on 1st of month
    if date.today().day != 1:
        return {"status": "skipped — not 1st of month"}

    from models import PlacementDrive, Application, Placement, StudentProfile, CompanyProfile

    last_month = date.today().replace(day=1) - timedelta(days=1)
    month_start = last_month.replace(day=1)
    month_end = last_month

    drives_count = PlacementDrive.query.filter(
        PlacementDrive.created_at >= month_start,
        PlacementDrive.created_at <= month_end,
    ).count()

    apps_count = Application.query.filter(
        Application.applied_at >= month_start,
        Application.applied_at <= month_end,
    ).count()

    placed_count = Application.query.filter(
        Application.status == "placed",
        Application.applied_at >= month_start,
        Application.applied_at <= month_end,
    ).count()

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()

    html_report = f"""
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; color: #333; padding: 24px; }}
        h1 {{ color: #2563eb; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px 14px; text-align: left; }}
        th {{ background-color: #2563eb; color: white; }}
        tr:nth-child(even) {{ background-color: #f3f4f6; }}
        .footer {{ margin-top: 32px; font-size: 12px; color: #888; }}
      </style>
    </head>
    <body>
      <h1>RecruitRadar — Monthly Placement Report</h1>
      <p>Report for: <strong>{last_month.strftime('%B %Y')}</strong></p>
      <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Placement Drives Conducted</td><td>{drives_count}</td></tr>
        <tr><td>Total Applications Received</td><td>{apps_count}</td></tr>
        <tr><td>Students Selected / Placed</td><td>{placed_count}</td></tr>
        <tr><td>Total Registered Students</td><td>{total_students}</td></tr>
        <tr><td>Total Registered Companies</td><td>{total_companies}</td></tr>
      </table>
      <p class="footer">Generated automatically by RecruitRadar on {date.today().strftime('%d %B %Y')}.</p>
    </body>
    </html>
    """

    admin_email = current_app.config.get("ADMIN_EMAIL", "admin@recruitradar.com")
    try:
        msg = Message(
            subject=f"RecruitRadar — Monthly Report ({last_month.strftime('%B %Y')})",
            recipients=[admin_email],
            html=html_report,
        )
        mail.send(msg)
        return {"status": "report sent", "month": last_month.strftime("%B %Y")}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — User-Triggered CSV Export (Async)
# rr_task_export_applications_csv
# CHANGED: the CSV file is now attached directly to the completion email,
# instead of only telling the user to log in and download it from the dashboard.
# ─────────────────────────────────────────────────────────────────────────────
def rr_task_export_applications_csv(export_job_id: int, user_id: int, role: str):
    """
    Async task triggered by student or company from their dashboard.
    Generates a CSV file of their application history.
    File is named with the rr_export_ prefix.
    Updates ExportJob status and emails the CSV as an attachment when done.
    """
    from extensions import db, mail
    from models import ExportJob, Application, Placement, User, StudentProfile, CompanyProfile
    from flask_mail import Message
    from flask import current_app

    export_job = ExportJob.query.get(export_job_id)
    if not export_job:
        return {"status": "export_job not found"}

    export_job.status = "processing"
    db.session.commit()

    try:
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"rr_export_{role}_{user_id}_{timestamp}.csv"
        filepath = os.path.join(upload_folder, filename)

        user = User.query.get(user_id)

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            if role == "student":
                student = StudentProfile.query.filter_by(user_id=user_id).first()
                if not student:
                    raise ValueError("Student profile not found")

                writer.writerow([
                    "Student ID", "Student Name", "Company Name",
                    "Drive Title", "Application Status",
                    "Applied Date", "Interview Date", "Feedback"
                ])
                for app in student.applications:
                    writer.writerow([
                        student.id,
                        student.full_name,
                        app.drive.company.company_name if app.drive and app.drive.company else "",
                        app.drive.job_title if app.drive else "",
                        app.status,
                        app.applied_at.strftime("%Y-%m-%d"),
                        app.interview_date.strftime("%Y-%m-%d") if app.interview_date else "",
                        app.feedback or "",
                    ])

            elif role == "company":
                company = CompanyProfile.query.filter_by(user_id=user_id).first()
                if not company:
                    raise ValueError("Company profile not found")

                writer.writerow([
                    "Application ID", "Student Name", "Student Email",
                    "Drive Title", "Application Status",
                    "Applied Date", "Interview Date", "Feedback"
                ])
                for drive in company.drives:
                    for app in drive.applications:
                        writer.writerow([
                            app.id,
                            app.student.full_name if app.student else "",
                            app.student.user.email if app.student and app.student.user else "",
                            drive.job_title,
                            app.status,
                            app.applied_at.strftime("%Y-%m-%d"),
                            app.interview_date.strftime("%Y-%m-%d") if app.interview_date else "",
                            app.feedback or "",
                        ])

        # Update export job as done
        export_job.status = "done"
        export_job.file_path = filename
        export_job.completed_at = datetime.utcnow()
        db.session.commit()

        # Email the CSV as a direct attachment (visible/openable right inside Mailpit)
        if user:
            try:
                msg = Message(
                    subject="RecruitRadar — Your CSV Export is Ready",
                    recipients=[user.email],
                    body=(
                        f"Hello,\n\nYour application history export from RecruitRadar is attached "
                        f"to this email as a CSV file.\n\n"
                        f"File: {filename}\n\n"
                        f"— RecruitRadar Placement Portal"
                    ),
                )
                with open(filepath, "rb") as f:
                    msg.attach(
                        filename=filename,
                        content_type="text/csv",
                        data=f.read(),
                    )
                mail.send(msg)
            except Exception:
                pass  # Email failure shouldn't fail the export

        return {"status": "done", "file": filename}

    except Exception as e:
        export_job.status = "failed"
        db.session.commit()
        return {"status": "failed", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4 — Company-Triggered Interview Reminder (Async)
# rr_task_send_interview_reminder
# ─────────────────────────────────────────────────────────────────────────────
def rr_task_send_interview_reminder(application_id: int):
    """
    Triggered by a company from the Applications page for a specific candidate
    whose status is 'interview'. Sends a reminder email with the interview date.
    """
    from extensions import mail
    from models import Application
    from flask_mail import Message

    app = Application.query.get(application_id)
    if not app:
        return {"status": "application not found"}

    if app.status != "interview":
        return {"status": "skipped — application is not in interview stage"}

    student = app.student
    drive = app.drive
    if not student or not student.user or not drive:
        return {"status": "skipped — missing student/drive data"}

    interview_str = app.interview_date.strftime("%d %B %Y, %I:%M %p") if app.interview_date else "To be confirmed"

    body = (
        f"Dear {student.full_name},\n\n"
        f"This is a reminder about your upcoming interview for the position of "
        f"{drive.job_title} at {drive.company.company_name if drive.company else ''}.\n\n"
        f"Interview Date & Time: {interview_str}\n\n"
        f"Please be prepared and log in to RecruitRadar for any updates.\n\n"
        f"— RecruitRadar Placement Portal"
    )

    try:
        msg = Message(
            subject=f"RecruitRadar — Interview Reminder: {drive.job_title}",
            recipients=[student.user.email],
            body=body,
        )
        mail.send(msg)
        return {"status": "sent"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}