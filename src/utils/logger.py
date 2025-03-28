import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s] [%(name)s] - %(message)s",
)

def get_logger(classname):
    """
    Returns a central logger for the given class name

    Args:
        classname: The name of the class

    Returns:
        logging.Logger: The logger instance
    """
    return logging.getLogger(classname)