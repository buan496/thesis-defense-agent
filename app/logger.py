import logging


def setup_logger(level: str = "INFO") -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(   
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True,
    )