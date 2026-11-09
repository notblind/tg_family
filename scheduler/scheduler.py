from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger
from config import settings
from scheduler.jobs import check_birthdays_monthly, check_task_deadlines, check_pill_reminders
import logging

logger = logging.getLogger(__name__)

# Support both PostgreSQL and SQLite for job store
db_url = settings.database_url
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Configure job store
jobstores = {
    "default": SQLAlchemyJobStore(url=db_url)
}

# Configure executor
executors = {
    "default": AsyncIOExecutor()
}

# Configure job defaults
job_defaults = {
    "coalesce": False,
    "max_instances": 1,
    "misfire_grace_time": 3600
}

# Create scheduler
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=settings.tz_info
)


async def init_scheduler():
    """Initialize and start the scheduler with jobs from database"""
    # Schedule birthday reminder (last day of each month at 18:00)
    scheduler.add_job(
        check_birthdays_monthly,
        CronTrigger(day="last", hour=18, minute=0),
        id="birthday_reminder",
        replace_existing=True
    )

    # Schedule task deadline check (every day at 09:00)
    scheduler.add_job(
        check_task_deadlines,
        CronTrigger(hour=9, minute=0),
        id="task_deadline_check",
        replace_existing=True
    )

    # Schedule pill reminder check (every minute)
    scheduler.add_job(
        check_pill_reminders,
        CronTrigger(minute="*"),
        id="pill_reminder_check",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler shutdown")
