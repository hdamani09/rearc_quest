import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import concurrent.futures
import pandas as pd
import yaml
from typing import List, Dict, Tuple
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BLSDataDownloader:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the downloader with configuration

        :param config_path: Path to the configuration YAML file
        """
        config_dict = self.load_config_file(config_path)
        http_headers_dict = config_dict["common"]["headers"]
        self.config = config_dict["bls"]

        # Prepare HTTP headers from config
        self.headers = {
            "User-Agent": http_headers_dict["user_agent"],
            "sec-ch-ua": http_headers_dict["sec_ch_ua"],
            "sec-ch-ua-mobile": http_headers_dict["sec_ch_ua_mobile"],
            "sec-ch-ua-platform": http_headers_dict["sec_ch_ua_platform"],
        }

        # Base BLS URL configuration
        self.base_url = self.config["base_url"]

        # Determine tracking file path
        tracking_dir = self.config["file_tracking"].get("csv_directory", "")
        tracking_filename = self.config["file_tracking"].get("csv_filename")
        self.tracking_csv_file = (
            os.path.join(tracking_dir, tracking_filename)
            if tracking_dir
            else tracking_filename
        )

        # Determine download target directory
        self.download_dir = self.config["download"].get("target_directory", "")

        # Max workers for concurrent downloads
        self.max_workers = self.config["download"]["max_workers"]

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
        Read config file

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
    def download_file(self, url, filename):
        """
        Download a file from a given URL

        :param url: URL of the file to download
        :param filename: Name of the file to save
        """
        # Determine full save path
        save_path = (
            os.path.join(self.download_dir, filename) if self.download_dir else filename
        )

        # Ensure directory exists if a specific directory is specified
        if self.download_dir:
            os.makedirs(self.download_dir, exist_ok=True)

        response = requests.get(url, headers=self.headers)
        with open(save_path, "wb") as f:
            f.write(response.content)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def delete_files(self, file_list):
        """
        Delete files from the given directory

        :param file_list: List of file names to delete
        :param directory: Directory path where files are located (default: current directory)
        """
        directory = "." if not self.download_dir else self.download_dir
        for file_name in file_list:
            file_path = os.path.join(directory, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Deleted: {file_path}")
            else:
                logger.debug(f"File not found: {file_path}")

    def read_list_as_dataframe(self, source_data) -> pd.DataFrame:
        try:
            return pd.DataFrame(source_data)
        except Exception as e:
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def read_csv_as_dataframe(self, file_path, delim=",", d_type=None) -> pd.DataFrame:
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
    def write_dataframe_as_csv(self, df, file_path):
        try:
            df.to_csv(file_path, index=False)
        except Exception as e:
            raise e

    def upsert_file_tracker(
        self, source_data, target_file
    ) -> Tuple[pd.DataFrame, List[Dict], List[str]]:
        """
        Implement a SCD Type 2-like tracking mechanism for downloaded files

        :param source_data: List of dictionaries with 'file_name', 'file_timestamp', 'full_url'
        :param target_file: Path to the CSV file where the tracking data is stored

        :return: A tuple containing:
             - pd.DataFrame: Updated tracking data as a Pandas DataFrame.
             - List[Dict]: A list of dictionaries capturing changes (new/updated file entries).
             - List[str]: A list of file names that were marked as inactive (due to absence in source)
        """
        target_dir = os.path.dirname(target_file)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        updates = []
        deletions = []
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_source = self.read_list_as_dataframe(source_data)

        # If target file does not exist, create it with initial data
        if not os.path.exists(target_file):
            logger.info("Tracking file doesn't exist")
            df_source["start_timestamp"] = current_timestamp
            df_source["end_timestamp"] = None
            df_source["is_active"] = "Y"
            df_source.to_csv(target_file, index=False)
            logger.info("Created initial tracking file")
            return df_source, df_source.to_dict(orient="records"), deletions

        try:
            # Load existing tracking data
            df_target = self.read_csv_as_dataframe(target_file)
            df_target.fillna({"end_timestamp": pd.NaT}, inplace=True)

            source_file_names = set(df_source["file_name"])

            for _, row in df_source.iterrows():
                existing_records = df_target[
                    (df_target["file_name"] == row["file_name"])
                    & (df_target["is_active"] == "Y")
                ]

                if not existing_records.empty:
                    latest_record = existing_records.iloc[0]
                    # If an existing file is updated
                    if (
                        latest_record["file_timestamp"] != row["file_timestamp"]
                        or latest_record["full_url"] != row["full_url"]
                    ):
                        # Mark old record as inactive
                        df_target.loc[
                            df_target.index == latest_record.name, "is_active"
                        ] = "N"
                        df_target.loc[
                            df_target.index == latest_record.name, "end_timestamp"
                        ] = current_timestamp

                        # Add new record with updated details
                        updates.append(
                            {
                                "file_name": row["file_name"],
                                "file_timestamp": row["file_timestamp"],
                                "full_url": row["full_url"],
                                "start_timestamp": current_timestamp,
                                "end_timestamp": None,
                                "is_active": "Y",
                            }
                        )
                else:
                    # If new files are present in source not present in target
                    updates.append(
                        {
                            "file_name": row["file_name"],
                            "file_timestamp": row["file_timestamp"],
                            "full_url": row["full_url"],
                            "start_timestamp": current_timestamp,
                            "end_timestamp": None,
                            "is_active": "Y",
                        }
                    )

            # Mark files that are no longer in source as inactive in target
            missing_files = df_target[
                (df_target["file_name"].isin(source_file_names) == False)
                & (df_target["is_active"] == "Y")
            ]
            if not missing_files.empty:
                df_target.loc[
                    df_target.index.isin(missing_files.index), "is_active"
                ] = "N"
                df_target.loc[
                    df_target.index.isin(missing_files.index), "end_timestamp"
                ] = current_timestamp
                deletions = missing_files["file_name"].tolist()

            if updates:
                df_updates = self.read_list_as_dataframe(updates)
                df_target = pd.concat([df_target, df_updates], ignore_index=True)

            return df_target, updates, deletions
        except Exception as e:
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def retrieve_files_metadata(self):
        try:
            file_metadata_list = []
            response = requests.get(
                f"{self.base_url}{self.config['scraping']['directory_path']}",
                headers=self.headers,
            )
            # Check if the request was successful
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Find all file links (they are in <a> tags)
                pattern = re.compile(
                    rf"{self.config['scraping']['file_regex_pattern']}"
                )

                # Iterate and check all the hyperlinks that are entries for files
                for i in str(soup.find("pre")).split("<br/>"):
                    match = pattern.search(i)
                    if match:
                        date_str, time_str, file_size, href, file_name = match.groups()
                        file_timestamp = datetime.strptime(
                            f"{date_str} {time_str}", "%m/%d/%Y %I:%M %p"
                        )
                        full_url = self.base_url + href

                        file_metadata_list.append(
                            {
                                "file_name": file_name,
                                "file_timestamp": file_timestamp.strftime(
                                    "%m/%d/%Y %I:%M %p"
                                ),
                                "full_url": full_url,
                            }
                        )
            else:
                raise Exception(
                    f"Unable to retrieve the BLS Directory contents : {response.status_code} {response.text}"
                )

            return file_metadata_list
        except Exception as e:
            logger.error(e)
            raise e

    def download_relevant_files(self):
        """
        Scrape and download files that have changed or are new
        """
        files_to_download = []
        file_metadata_list = self.retrieve_files_metadata()

        # Perform SCD Type 2 Upsert on tracking data to identify what files to download
        df_updated_target, updates, deletions = self.upsert_file_tracker(
            file_metadata_list, self.tracking_csv_file
        )
        for update in updates:
            files_to_download.append((update["full_url"], update["file_name"]))

        # Optimize download by using threadpools
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_file = {
                executor.submit(self.download_file, full_url, file_name): file_name
                for full_url, file_name in files_to_download
            }

            for future in concurrent.futures.as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    future.result()
                    logger.info(f"Successfully downloaded {file_name}")
                except Exception as e:
                    logger.info(f"Error downloading {file_name}: {e}")

        if updates or deletions:
            self.write_dataframe_as_csv(df_updated_target, self.tracking_csv_file)
            logger.info("Tracking file updated")
            if deletions:
                self.delete_files(deletions)
        else:
            logger.info("No changes found in source hence tracking file is not updated")


def main():
    downloader = BLSDataDownloader("config.yaml")
    downloader.download_relevant_files()


if __name__ == "__main__":
    main()
