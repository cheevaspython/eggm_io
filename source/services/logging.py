import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logger_warning.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
