import pandas as pd
from src.utils.logger import get_logger
import os
from src.utils.file import load_config_file, read_json_as_obj
from src.utils.dataframe import read_csv_as_dataframe
from src.models.models import load_config_model, Config, AnalysisConfig
import argparse
from typing import Dict

logger = get_logger(__name__)


class Analysis:
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the Analysis class

        :param config_path: Path to the configuration YAML file
        """
        config_model: Config = load_config_model(load_config_file(config_path))
        self.config: Dict[str, AnalysisConfig] = config_model.analysis
        self.population_config: AnalysisConfig = self.config['population']

        # Fetch the relevant filepath from BLS download target directory
        self.bls_config: AnalysisConfig = self.config['bls']
        self.bls_download_dir = self.bls_config.download_dir
        self.bls_filename = self.bls_config.file_name
        self.bls_data_current_filepath = (
            os.path.join(self.bls_download_dir, self.bls_filename)
            if self.bls_download_dir
            else self.bls_filename
        )
        logger.info(f"Obtained bls current filepath : {self.bls_data_current_filepath}")

        # Fetch the population json payload file path
        self.population_json_dir = self.population_config.download_dir
        self.population_json_filename = self.population_config.file_name
        self.population_json_filepath = (
            os.path.join(self.population_json_dir, self.population_json_filename)
            if self.population_json_dir
            else self.population_json_filename
        )
        logger.info(f"Obtained population json path : {self.population_json_filepath}")
        
    def prepare_bls_df(self):
        """
        Prepares and cleans the BLS dataset

        Returns:
            pd.DataFrame: The cleaned BLS data
        """
        bls_current_df = read_csv_as_dataframe(
            self.bls_data_current_filepath, delim="\t", d_type=str
        )
        bls_current_df.columns = bls_current_df.columns.str.strip()
        bls_current_df = bls_current_df.apply(
            lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x)
        )
        bls_current_df["year"] = bls_current_df["year"].astype("int32")
        bls_current_df["value"] = bls_current_df["value"].astype(float).round(3)

        logger.info(bls_current_df)

        return bls_current_df
    
    def prepare_population_df(self):
        """
        Loads and normalizes the US population dataset

        Returns:
            pd.DataFrame: The population data
        """
        population_dict = read_json_as_obj(self.population_json_filepath)
        population_data_df = pd.json_normalize(population_dict["data"])
        population_source_df = pd.json_normalize(population_dict["source"])

        logger.info(population_data_df)

        return population_data_df

    def calculate_population_metrics(self, population_data_df):
        """
        Computes mean and standard deviation of the US population (2013-2018)

        Args:
            population_data_df (pd.DataFrame): The population dataset
        """
        filtered_population_data_df = population_data_df[
            (population_data_df["ID Year"] >= 2013)
            & (population_data_df["ID Year"] <= 2018)
        ]
        mean_population = filtered_population_data_df["Population"].mean()
        std_population = filtered_population_data_df["Population"].std()

        logger.info(f"Mean Population (2013-2018): {mean_population}")
        logger.info(f"Standard Deviation of Population (2013-2018): {std_population}")

        return filtered_population_data_df, mean_population, std_population

    def calculate_bls_metrics(self, bls_current_df):
        """
        Identifies the best year per series_id based on the maximum value

        Args:
            bls_current_df (pd.DataFrame): The BLS dataset
        """
        yearly_series_value_sum_df = (
            bls_current_df.groupby(["series_id", "year"])["value"].sum().reset_index()
        )
        series_best_year_by_value_df = yearly_series_value_sum_df.loc[
            yearly_series_value_sum_df.groupby("series_id")["value"].idxmax()
        ]
        series_best_year_by_value_df = series_best_year_by_value_df.rename(
            columns={"value": "summed_value"}
        )
        logger.info(series_best_year_by_value_df)

        return series_best_year_by_value_df

    def calculate_combined_metrics(self, bls_current_df, population_data_df):
        """
        Merges BLS and population data for analysis

        Args:
            bls_current_df (pd.DataFrame): The BLS dataset
            population_data_df (pd.DataFrame): The population dataset
        """
        filtered_bls_current_df = bls_current_df[
            (bls_current_df["series_id"] == "PRS30006032")
            & (bls_current_df["period"] == "Q01")
        ]
        merged_bls_population_df = filtered_bls_current_df.merge(
            population_data_df, left_on="year", right_on="ID Year", how="left"
        )
        merged_bls_population_df = merged_bls_population_df[
            merged_bls_population_df["Population"].notna()
        ]
        merged_bls_population_df = merged_bls_population_df[
            ["series_id", "year", "period", "value", "Population"]
        ].sort_values(by="year")
        logger.info(merged_bls_population_df)

        return merged_bls_population_df

    def analyze(self):
        """
        Runs the full analysis pipeline by preparing datasets and computing metrics
        """
        bls_current_df = self.prepare_bls_df()
        population_data_df = self.prepare_population_df()

        self.calculate_population_metrics(population_data_df)
        self.calculate_bls_metrics(bls_current_df)
        self.calculate_combined_metrics(bls_current_df, population_data_df)

def main(config_path: str):
    analysis = Analysis(config_path)
    analysis.analyze()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    
    main(args.config)
