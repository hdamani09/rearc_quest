from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger
from src.utils.aws import get_bucket_and_key
import pandas as pd
import boto3
import io

logger = get_logger(__name__)
s3_client = boto3.client("s3")

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

def read_list_as_dataframe(source_data) -> pd.DataFrame:
    try:
        return pd.DataFrame(source_data)
    except Exception as e:
        raise e

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def read_csv_as_dataframe(file_path, delim=",", d_type=None) -> pd.DataFrame:
    """
    Read a CSV file from a local path or S3 into a pandas DataFrame.

    :param file_path: Local file path or S3 path (s3://bucket/key)
    :param delim: Delimiter used in the CSV file (default: ",")
    :param d_type: Dictionary of column data types (optional)
    :return: Pandas DataFrame
    """
    try:
        if file_path.startswith("s3://"):
            bucket, key = get_bucket_and_key(file_path)
            response = s3_client.get_object(Bucket=bucket, Key=key)
            csv_content = response["Body"].read().decode("utf-8")
            csv_buffer = io.StringIO(csv_content)

            return pd.read_csv(csv_buffer, delimiter=delim, dtype=d_type)
        else:
            return pd.read_csv(file_path, delimiter=delim, dtype=d_type)
    except Exception as e:
        raise Exception(f"Failed to read CSV from {file_path}: {str(e)}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def write_dataframe_as_csv(df, file_path):
    """
    Write a pandas DataFrame to a CSV file, locally or in S3.

    :param df: Pandas DataFrame
    :param file_path: Local file path or S3 path (s3://bucket/key)
    """
    try:
        if file_path.startswith("s3://"):
            bucket, key = get_bucket_and_key(file_path)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            s3_client.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())

            logger.info(f"CSV file saved to s3://{bucket}/{key}")
        else:
            df.to_csv(file_path, index=False)
            logger.info(f"CSV file saved to {file_path}")
    except Exception as e:
        raise Exception(f"Failed to write CSV to {file_path}: {str(e)}")