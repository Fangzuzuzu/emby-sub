from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from backend.jobs.check_media import check_new_media_job

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(
        check_new_media_job,
        trigger=IntervalTrigger(minutes=2),
        id="check_new_media",
        replace_existing=True,
        next_run_time=datetime.now()
    )
    scheduler.start()


