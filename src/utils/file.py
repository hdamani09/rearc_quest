import yaml
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger
import os
import requests
import json

logger = get_logger(__name__)

def log_retry_attempt(retry_state):
    """
    Logging function to provide detailed information about retry attempts.

    Args:
        retry_state (RetryCallState): The current state of the retry attempt
    """
    logger.info(
        f"Retry attempt {retry_state.attempt_number}"
        f"Last exception: {retry_state.outcome.exception()}"
    )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def load_config_file(config_path):
    """
    Read config file

    :param config_path: Path of the configuration file
    """
    try:
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
        return config
    except Exception as e:
        raise Exception(f"Failed to read : {config_path} with {str(e)}")
    
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def download_file(url, headers, directory, filename):
    """
    Download a file from a given URL

    :param url: URL of the file to download
    :param filename: Name of the file to save
    """
    # Determine full save path
    save_path = (
        os.path.join(directory, filename) if directory else filename
    )

    # Ensure directory exists if a specific directory is specified
    if directory:
        os.makedirs(directory, exist_ok=True)

    if headers and len(headers) > 0:
        response = requests.get(url, headers=headers)
    else:
        response = requests.get(url)
    with open(save_path, "wb") as f:
        f.write(response.content)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def delete_files(directory, file_list):
    """
    Delete files from the given directory

    :param file_list: List of file names to delete
    :param directory: Directory path where files are located (default: current directory)
    """
    for file_name in file_list:
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted: {file_path}")
        else:
            logger.debug(f"File not found: {file_path}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def read_json_as_obj(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        raise e
        
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def write_as_json(payload_str, filepath):
    try:
        # Ensure directory exists if a specific directory is specified
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(filepath, "w") as file:
            json.dump(json.loads(payload_str), file, indent=4)
        logger.info("Population file created/updated successfully!")

    except Exception as e:
        raise e