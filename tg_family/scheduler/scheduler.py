from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from config import settings
import logging

logger = logging.getLogger(__name__)

# Configure job store
jobstores = {
    "default": SQLAlchemyJobStore(url=f"sqlite:///{settings.database_path}")
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
    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler shutdown")
