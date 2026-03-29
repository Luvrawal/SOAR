from celery import Celery

from app.core.config import build_celery_broker_url, build_celery_result_backend

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
)

celery_app.autodiscover_tasks(["app.tasks"])
