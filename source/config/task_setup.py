from taskiq import AsyncBroker
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker

from source.config.settings import Settings


def create_broker(
    config: Settings,
) -> AsyncBroker:
    redis_async_result = RedisAsyncResultBackend(
        redis_url=config.worker.celery_broker_url,
    )
    broker = ListQueueBroker(
        url=config.worker.celery_broker_url,
    ).with_result_backend(
        redis_async_result,
    )
    return broker
