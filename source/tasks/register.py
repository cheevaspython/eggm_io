from taskiq import AsyncBroker

from source.tasks.history import default


def register_tasks(broker: AsyncBroker):
    broker.register_task(
        default,
        task_name=default.__name__,
    )
