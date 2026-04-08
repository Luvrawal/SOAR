from celery import Celery
from kombu import Queue

from app.core.config import build_celery_broker_url, build_celery_result_backend, settings

celery_app = Celery(
    "soar_worker",
    broker=build_celery_broker_url(),
    backend=build_celery_result_backend(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    task_default_queue=settings.CELERY_QUEUE_DEFAULT,
    task_queues=(
        Queue(settings.CELERY_QUEUE_DEFAULT),
        Queue(settings.CELERY_QUEUE_EMAIL),
        Queue(settings.CELERY_QUEUE_ENDPOINT),
        Queue(settings.CELERY_QUEUE_FILE),
    ),
)

celery_app.autodiscover_tasks(["app.tasks"])
