import yaml
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger
from src.utils.aws import get_bucket_and_key
import os
import requests
import json
import boto3

logger = get_logger(__name__)
s3 = boto3.client("s3")

def log_retry_attempt(retry_state):
    """
    Logging function to provide detailed information about retry attempts.

    :param retry_state (RetryCallState): The current state of the retry attempt
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
    Read config file from local or S3.

    :param config_path: Path of the configuration file
    """
    try:
        if config_path.startswith("s3://"):
            bucket, key = get_bucket_and_key(config_path)
            obj = s3.get_object(Bucket=bucket, Key=key)
            config = yaml.safe_load(obj["Body"].read().decode("utf-8"))
        else:
            with open(config_path, "r") as config_file:
                config = yaml.safe_load(config_file)

        return config
    except Exception as e:
        raise Exception(f"Failed to read {config_path}: {str(e)}")
    
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def download_file(url, headers, directory, filename):
    """
    Download a file from a given URL and save it locally or in S3.

    :param url: URL of the file to download
    :param headers: HTTP headers for the request (optional)
    :param directory: Local directory or S3 bucket prefix
    :param filename: Name of the file to save
    """
    try:
        response = requests.get(url, headers=headers if headers else {})
        response.raise_for_status()

        if directory.startswith("s3://"):
            bucket, prefix = get_bucket_and_key(directory)
            s3_key = f"{prefix}/{filename}" if prefix else filename

            s3.put_object(Bucket=bucket, Key=s3_key, Body=response.content)
            logger.info(f"File downloaded and saved to s3://{bucket}/{s3_key}")
        else:
            save_path = os.path.join(directory, filename) if directory else filename
            os.makedirs(directory, exist_ok=True) if directory else None

            with open(save_path, "wb") as f:
                f.write(response.content)

            logger.info(f"File downloaded and saved to {save_path}")
    except Exception as e:
        raise Exception(f"Failed to download {url} to {directory}{filename}: {str(e)}")

def ensure_target_dir(target_file):
    """
    Ensures the target directory exists for local paths.
    S3 does not require directory creation.

    :param target_file: Local file path or S3 path (s3://bucket/key)
    """
    if not target_file.startswith("s3://"):
        target_dir = os.path.dirname(target_file)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def file_exists(target_file):
    """
    Checks if a file exists locally or in S3.

    :param target_file: File path (local or S3 URL)
    :return: True if file exists, False otherwise
    """
    if target_file.startswith("s3://"):
        bucket, key = get_bucket_and_key(target_file)
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except s3.exceptions.ClientError:
            return False
    else:
        return os.path.exists(target_file)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def delete_files(directory, file_list):
    """
    Delete files from a local directory or S3.

    :param file_list: List of file names or S3 keys to delete
    :param directory: Directory path where files are located or an S3 bucket prefix
    """
    if directory.startswith("s3://"):
        bucket, prefix = get_bucket_and_key(directory)

        for file_name in file_list:
            s3_key = f"{prefix}/{file_name}" if prefix else file_name
            try:
                s3.delete_object(Bucket=bucket, Key=s3_key)
                logger.debug(f"Deleted: s3://{bucket}/{s3_key}")
            except Exception as e:
                logger.debug(f"Failed to delete s3://{bucket}/{s3_key}: {str(e)}")
    else:
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
    """
    Read JSON file from local or S3.

    :param file_path: Path of the JSON file
    """
    try:
        if file_path.startswith("s3://"):
            bucket, key = get_bucket_and_key(file_path)
            obj = s3.get_object(Bucket=bucket, Key=key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        else:
            with open(file_path, "r") as file:
                return json.load(file)
    except Exception as e:
        raise Exception(f"Failed to read JSON from {file_path}: {str(e)}")
        
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
            if not directory.startswith('s3://'):
                os.makedirs(directory, exist_ok=True)
                with open(filepath, "w") as file:
                    json.dump(json.loads(payload_str), file, indent=4)
            else:
                bucket, key = get_bucket_and_key(filepath)
                logger.info(f"Bucket : {bucket} | Key {key}")
                s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=json.dumps(json.loads(payload_str), indent=4),
                    ContentType="application/json"
                )
        logger.info("Population file created/updated successfully!")

    except Exception as e:
        raise Exception(f"Failed to write JSON to {filepath}: {str(e)}")