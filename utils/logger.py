import logging
from utils.load_save_functions import load_settings
import os


class Logger:
    def __init__(self, name: str):
        os.environ["NUMEXPR_MAX_THREADS"] = (
            "8"  # set the number of threads for numexpr (avoid logger warning)
        )
        self.settings = load_settings()
        self.name = name
        self.file_path_log = (
            f'experiments/{self.settings["EXPERIMENT_NAME"]}/meta_data/{self.name}.log'
        )
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(self.file_path_log), logging.StreamHandler()],
        )

    def info(self, message: str):
        logging.info(message)

    def warning(self, message: str):
        logging.warning(message)

    def error(self, message: str):
        logging.error(message)
