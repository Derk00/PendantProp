import pandas as pd

from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from hardware.sensor.sensor_api import SensorApi
from hardware.cameras import PendantDropCamera
from utils.load_save_functions import load_settings


def prototcol_surfactant_characterization(pendant_drop_camera: PendantDropCamera):
    settings = load_settings()
    file_name = f"experiments/{settings['EXPERIMENT_NAME']}/meta_data/{settings['CHARACTERIZATION_INFO_FILENAME']}"
    characterization_info = pd.read_csv(file_name)
    surfactants = characterization_info["surfactant"]
    row_ids = characterization_info["row id"]
    explore_points = int(settings['EXPLORE_POINTS'])

    # initialize
    api = Opentrons_http_api()
    sensor_api = SensorApi()
    api.initialise()
    config = Configuration(http_api=api)
    labware = config.load_labware()
    containers = config.load_containers()
    pipettes = config.load_pipettes()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]
    pd_cam = pendant_drop_camera

    #! executable section
    api.home()

    for i, surfactant in enumerate(surfactants):
        row_id = row_ids[i]
        right_pipette.serial_dilution(row_id=row_id, surfactant_name=surfactant)
        for i in range(explore_points): 
            st_t = left_pipette.measure_pendant_drop(
                source=containers[f"{row_id}{i+1}"],
                drop_volume=float(settings["DROP_VOLUME"]),
                delay=float(settings["EQUILIBRATION_TIME"]),
                flow_rate=float(settings["FLOW_RATE"]),
                pendant_drop_camera=pd_cam
            )
