import pandas as pd

from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from utils.load_save_functions import load_settings


def prototcol_surfactant_characterization():
    settings = load_settings()
    file_name = f"experiments/{settings['EXPERIMENT_NAME']}/meta_data/{settings['CHARACTERIZATION_INFO_FILENAME']}"
    characterization_info = pd.read_csv(file_name)
    surfactants = characterization_info["surfactant"]
    row_ids = characterization_info["row id"]
    for i, surfactant in enumerate(surfactants):
        print(f"surfactant name: {surfactant}")
        row_id = row_ids[i]
        print(f"row id {row_id}")
    pass