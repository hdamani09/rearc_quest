import requests
from src.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import argparse
from src.utils.file import load_config_file, write_as_json

logger = get_logger(__name__)


class PopulationDataDownloader:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the downloader with configuration

        :param config_path: Path to the configuration YAML file
        """
        config_dict = load_config_file(config_path)
        self.config = config_dict["population"]

        # Prepare HTTP headers from config
        self.headers = self.config['headers']

        # Base BLS URL configuration
        self.base_url = self.config["base_url"]

        # Determine json payload file path
        self.json_dir = self.config["download"].get("json_directory", "")
        self.json_filename = self.config["download"].get("json_filename")
        self.json_file = (
            os.path.join(self.json_dir, self.json_filename)
            if self.json_dir
            else self.json_filename
        )
        logger.info(f"Obtained json filepath : {self.json_file}")

    def log_retry_attempt(retry_state):
        """
        Logging function to provide detailed information about retry attempts.

        Args:
            retry_state (RetryCallState): The current state of the retry attempt
        """
        logger.info(
            f"Retry attempt {retry_state.attempt_number}. "
            f"Last exception: {retry_state.outcome.exception()}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def retrieve_population_data(self) -> str:
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response_txt = response.text
            if response.status_code == 200:
                logger.info("Obtained Population Data successfully!")
                return response_txt
            else:
                raise Exception(
                    f"Unable to retrieve the Population Data : {response.status_code} {response_txt}"
                )
        except Exception as e:
            raise e

def main(config_path: str):
    downloader = PopulationDataDownloader(config_path)
    payload = downloader.retrieve_population_data()
    write_as_json(payload, downloader.json_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    
    main(args.config)
