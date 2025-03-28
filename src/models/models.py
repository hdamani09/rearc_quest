from typing import Dict


class ScrapingConfig:
    def __init__(self, directory_path: str, file_regex_pattern: str):
        self.directory_path = directory_path
        self.file_regex_pattern = file_regex_pattern


class DownloadConfig:
    def __init__(self, target_directory: str, max_workers: int):
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self.target_directory = target_directory
        self.max_workers = max_workers


class FileTrackingConfig:
    def __init__(self, csv_directory: str, csv_filename: str):
        self.csv_directory = csv_directory
        self.csv_filename = csv_filename


class BLSConfig:
    def __init__(
        self,
        base_url: str,
        headers: Dict[str, str],
        scraping: Dict,
        download: Dict,
        file_tracking: Dict,
    ):
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be a valid HTTP URL")
        
        self.base_url = base_url
        self.headers = headers
        self.scraping = ScrapingConfig(**scraping)
        self.download = DownloadConfig(**download)
        self.file_tracking = FileTrackingConfig(**file_tracking)


class PopulationDownloadConfig:
    def __init__(self, json_directory: str, json_filename: str):
        self.json_directory = json_directory
        self.json_filename = json_filename


class PopulationConfig:
    def __init__(self, base_url: str, headers: Dict[str, str], download: Dict):
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be a valid HTTP URL")
        
        self.base_url = base_url
        self.headers = headers
        self.download = PopulationDownloadConfig(**download)


class AnalysisConfig:
    def __init__(self, download_dir: str, file_name: str):
        self.download_dir = download_dir
        self.file_name = file_name


class Config:
    def __init__(self, bls: Dict, population: Dict, analysis: Dict[str, Dict]):
        self.bls = BLSConfig(**bls)
        self.population = PopulationConfig(**population)
        self.analysis = {k: AnalysisConfig(**v) for k, v in analysis.items()}


def load_config_model(config_dict: Dict) -> Config:
    return Config(**config_dict)
