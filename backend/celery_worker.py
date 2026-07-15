# RecruitRadar — backend/celery_worker.py
# Celery worker entry point.
#
# app.py lives at the project ROOT, not in backend/.
# So we add the root to sys.path before importing it.
#
# Commands (run from RecruitRadar/ root):
#   Worker : celery -A backend.celery_worker.celery worker --loglevel=info
#   Beat   : celery -A backend.celery_worker.celery beat   --loglevel=info

import os
import sys

# Add project root to path so "from app import create_app" resolves correctly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
# Add backend/ itself so tasks.py and other backend modules resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from tasks import (
    make_celery,
    rr_task_send_deadline_reminders,
    rr_task_send_monthly_report,
    rr_task_export_applications_csv,
    rr_task_send_interview_reminder,
)

flask_app = create_app()
celery = make_celery(flask_app)

# Register all three rr_task functions as named Celery tasks
# The name must match exactly what config.py CELERYBEAT_SCHEDULE refers to
celery.task(name="tasks.rr_task_send_deadline_reminders")(rr_task_send_deadline_reminders)
celery.task(name="tasks.rr_task_send_monthly_report")(rr_task_send_monthly_report)
celery.task(name="tasks.rr_task_export_applications_csv")(rr_task_export_applications_csv)
celery.task(name="tasks.rr_task_send_interview_reminder")(rr_task_send_interview_reminder)

# Expose celery instance to route files that call send_task()
import tasks as tasks_module
tasks_module.celery_app = celery
