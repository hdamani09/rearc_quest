import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] [%(name)s] - %(message)s",
)

def get_logger(classname):
    return logging.getLogger(classname)