from apscheduler.schedulers.background import BackgroundScheduler


def init_tasks(app, engine):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        engine.restart,
        "cron",
        day_of_week="mon-fri",
        hour=9,
        minute=30
    )
    scheduler.start()
