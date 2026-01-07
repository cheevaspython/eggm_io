from dataclasses import dataclass

from source.common.error import ApplicationError
from source.services.logging import logger


@dataclass(eq=False)
class CustomDoesNotExist(ApplicationError):

    class_name: str
    model_id: int | None = None

    @property
    def message(self):
        text = f"{self.class_name} does not exist with id: {self.model_id}"
        logger.warning(text)
        return text
