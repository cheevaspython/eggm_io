from dishka.integrations import taskiq as taskiq_integrations
from taskiq import AsyncBroker, TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker
from taskiq.schedule_sources import LabelScheduleSource

from source.config.settings import settings
from source.ioc import setup_di
from source.tasks.register import register_tasks


def create_taskiq_app() -> AsyncBroker:
    redis_async_result = RedisAsyncResultBackend(
        redis_url=settings.worker.celery_broker_url,
        result_ex_time=settings.worker.result_ex_time,
    )
    broker = ListQueueBroker(
        url=settings.worker.celery_broker_url,
    ).with_result_backend(
        redis_async_result,
    )
    container = setup_di()
    taskiq_integrations.setup_dishka(
        container=container,
        broker=broker,
    )
    register_tasks(broker)
    return broker


def create_taskiq_scheduler() -> TaskiqScheduler:
    broker = create_taskiq_app()
    return TaskiqScheduler(
        broker=broker,
        sources=[LabelScheduleSource(broker=broker)],
    )
