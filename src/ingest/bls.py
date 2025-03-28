import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import concurrent.futures
import pandas as pd
from typing import List, Dict, Tuple
from src.utils.logger import get_logger
from src.utils.file import (
    load_config_file,
    download_file,
    delete_files,
    ensure_target_dir,
    file_exists,
)
from src.utils.dataframe import (
    read_list_as_dataframe,
    read_csv_as_dataframe,
    write_dataframe_as_csv,
)
from src.models.models import load_config_model, Config, BLSConfig
from tenacity import retry, stop_after_attempt, wait_exponential
import argparse


logger = get_logger(__name__)


class BLSDataDownloader:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the downloader with configuration

        :param config_path: Path to the configuration YAML file
        """
        config_model: Config = load_config_model(load_config_file(config_path))
        self.config: BLSConfig = config_model.bls

        # Determine tracking file path (to maintain changes for subsequent ingestion)
        tracking_dir = self.config.file_tracking.csv_directory
        tracking_filename = self.config.file_tracking.csv_filename
        self.tracking_csv_file = (
            os.path.join(tracking_dir, tracking_filename)
            if tracking_dir
            else tracking_filename
        )
        logger.info(f"Obtained file tracking path : {self.tracking_csv_file}")

        # Determine download target directory
        self.download_dir = self.config.download.target_directory
        logger.info(f"Obtained download dir path : {self.download_dir}")

    def log_retry_attempt(retry_state):
        """
        Logging function to provide detailed information about retry attempts.

        :param retry_state (RetryCallState): The current state of the retry attempt
        """
        logger.info(
            f"Retry attempt {retry_state.attempt_number}. "
            f"Last exception: {retry_state.outcome.exception()}"
        )

    def upsert_file_tracker(
        self, source_data, target_file
    ) -> Tuple[pd.DataFrame, List[Dict], List[str]]:
        """
        Implement a SCD Type 2-like tracking mechanism for downloaded files

        :param source_data: List of dictionaries with 'file_name', 'file_timestamp', 'full_url'
        :param target_file: Path to the CSV file where the tracking data is stored

        :return: A tuple containing:
             - pd.DataFrame: Updated tracking data as a Pandas DataFrame
             - List[Dict]: A list of dictionaries capturing changes (new/updated file entries)
             - List[str]: A list of file names that were marked as inactive (due to absence in source)
        """
        updates = []
        deletions = []
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_source = read_list_as_dataframe(source_data)

        ensure_target_dir(target_file)

        # If target file does not exist, create it with initial data
        if not file_exists(target_file):
            logger.info("Tracking file doesn't exist")
            df_source["start_timestamp"] = current_timestamp
            df_source["end_timestamp"] = None
            df_source["is_active"] = "Y"
            return df_source, df_source.to_dict(orient="records"), deletions

        try:
            # Load existing tracking data
            df_target = read_csv_as_dataframe(target_file)
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
                df_updates = read_list_as_dataframe(updates)
                df_target = pd.concat([df_target, df_updates], ignore_index=True)

            return df_target, updates, deletions
        except Exception as e:
            raise Exception(f"Failure during preparing BLS file tracker : {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2),
        before_sleep=log_retry_attempt,
    )
    def retrieve_files_metadata(self):
        """
        Retrieves metadata of files from a specified directory URL

        Returns:
            list[dict]: A list of file metadata, each containing:
                - file_name (str): The name of the file
                - file_timestamp (str): The timestamp of the file
                - full_url (str): The full URL of the file
        """
        try:
            file_metadata_list = []
            response = requests.get(
                f"{self.config.base_url}{self.config.scraping.directory_path}",
                headers=self.config.headers,
            )
            # Check if the request was successful
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Find all file links (they are in <a> tags)
                pattern = re.compile(
                    rf"{self.config.scraping.file_regex_pattern}"
                )

                # Iterate and check all the hyperlinks that are entries for files
                for i in str(soup.find("pre")).split("<br/>"):
                    match = pattern.search(i)
                    if match:
                        date_str, time_str, file_size, href, file_name = match.groups()
                        file_timestamp = datetime.strptime(
                            f"{date_str} {time_str}", "%m/%d/%Y %I:%M %p"
                        )
                        full_url = self.config.base_url + href

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
            raise Exception(f"Failure during reading BLS Directory : {str(e)}")

    def download_relevant_files(self):
        """
        Scrape and download files that have changed or are new
        """
        try:
            files_to_download = []
            file_metadata_list = self.retrieve_files_metadata()

            # Perform SCD Type 2 Upsert on tracking data to identify what files to download
            df_updated_target, updates, deletions = self.upsert_file_tracker(
                file_metadata_list, self.tracking_csv_file
            )
            for update in updates:
                files_to_download.append((update["full_url"], update["file_name"]))

            # Optimize download by using thread pools
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.download.max_workers
            ) as executor:
                future_to_file = {
                    executor.submit(download_file, full_url, self.config.headers, self.download_dir, file_name): file_name
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
                write_dataframe_as_csv(df_updated_target, self.tracking_csv_file)
                logger.info("Tracking file created/updated")
                if deletions:
                    directory = "." if not self.download_dir else self.download_dir
                    delete_files(directory, deletions)
            else:
                logger.info("No changes found in source hence tracking file is not updated")
        except Exception as e:
            raise Exception(f"Failure during downloading BLS data files : {str(e)}")


def main(config_path: str):
    downloader = BLSDataDownloader(config_path)
    downloader.download_relevant_files()


if __name__ == "__main__":    
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    
    main(args.config)