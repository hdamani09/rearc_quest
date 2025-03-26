from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logger import get_logger
import pandas as pd

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
    try:
        if not d_type:
            return pd.read_csv(file_path, delimiter=delim)
        else:
            return pd.read_csv(file_path, delimiter=delim, dtype=d_type)
    except Exception as e:
        raise e

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2),
    before_sleep=log_retry_attempt,
)
def write_dataframe_as_csv(df, file_path):
    try:
        df.to_csv(file_path, index=False)
    except Exception as e:
        raise e