import logging
from utils.load_save_functions import load_settings

# import settings
settings = load_settings()
file_path_log = f'experiments/{settings["EXPERIMENT_NAME"]}/meta_data/protocol.log'

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(file_path_log), logging.StreamHandler()],
)
