import requests
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PopulationDataDownloader:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the downloader with configuration

        :param config_path: Path to the configuration YAML file
        """
        config_dict = self.load_config_file(config_path)
        http_headers_dict = config_dict["common"]["headers"]
        self.config = config_dict["population"]

        # Prepare HTTP headers from config
        self.headers = {
            "User-Agent": http_headers_dict["user_agent"],
            "sec-ch-ua": http_headers_dict["sec_ch_ua"],
            "sec-ch-ua-mobile": http_headers_dict["sec_ch_ua_mobile"],
            "sec-ch-ua-platform": http_headers_dict["sec_ch_ua_platform"],
        }

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
    def load_config_file(self, config_path):
        """
        Read config file from config.yaml

        :param config_path: Path of the configuration file
        """
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
        return config

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def retrieve_population_data(self) -> str:
        try:
            response = requests.get(self.base_url)
            if response.status_code == 200:
                response_txt = response.text
                logger.info("Obtained Population Data successfully!")
                return response_txt
            else:
                raise Exception(
                    f"Unable to retrieve the Population Data : {response.status_code} {response.text}"
                )
        except Exception as e:
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def write_as_json(self, payload_str):
        try:
            # Ensure directory exists if a specific directory is specified
            if self.json_dir:
                os.makedirs(self.json_dir, exist_ok=True)

            with open(self.json_file, "w") as file:
                json.dump(json.loads(payload_str), file, indent=4)
            logger.info("Population file created/updated successfully!")

        except Exception as e:
            raise e


def main():
    downloader = PopulationDataDownloader("config.yaml")
    payload = downloader.retrieve_population_data()
    downloader.write_as_json(payload)


if __name__ == "__main__":
    main()
