# users/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

scheduler = None

def start_scheduler():
    """Inicia el scheduler con jobstore en PostgreSQL"""
    global scheduler
    
    if scheduler is not None:
        logger.info('Scheduler ya está iniciado')
        return
    
    try:
        scheduler = BackgroundScheduler(settings.SCHEDULER_CONFIG)
        
        from .jobs import cleanup_unverified_users
        
        scheduler.add_job(
            cleanup_unverified_users,
            trigger=CronTrigger(hour=14, minute=45),
            id='cleanup_unverified_users',
            name='Limpiar usuarios no verificados',
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=60,
        )
    
        scheduler.start()
        
        logger.info('APScheduler iniciado con jobstore PostgreSQL')
        logger.info(f'Jobs programados: {len(scheduler.get_jobs())}')
        
        for job in scheduler.get_jobs():
            logger.info(
                f'  • {job.name} (ID: {job.id}) - '
                f'Próxima ejecución: {job.next_run_time}'
            )
            
    except Exception as e:
        logger.error(f'Error al iniciar scheduler: {str(e)}')
        raise

def stop_scheduler():
    """Detiene el scheduler gracefully"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info('APScheduler detenido')