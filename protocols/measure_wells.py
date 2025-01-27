import pandas as pd

from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from hardware.cameras import PendantDropCamera
from hardware.sensor.sensor_api import SensorApi
from utils.load_save_functions import load_settings

# TODO add sensor data

def prototcol_measure_wells(pendant_drop_camera: PendantDropCamera):
    settings = load_settings()
    file_name = f"experiments/{settings['EXPERIMENT_NAME']}/meta_data/well_info.csv"
    well_info = pd.read_csv(file_name)
    results = well_info.copy()
    results["well id"] = well_info["location"].astype(str) + well_info["well"]
    well_ids = results["well id"]

    # initialize
    api = Opentrons_http_api()
    sensor_api = SensorApi()
    api.initialise()
    config = Configuration(http_api=api)
    labware = config.load_labware()
    pipettes = config.load_pipettes()
    containers = config.load_containers()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]

    api.home()

    for well_id in well_ids:
        left_pipette.pick_up_tip()
        sensor_data = sensor_api.capture_sensor_data()
        st_t = left_pipette.measure_pendant_drop(
            source=containers[well_id], 
            destination=containers["drop_stage"],
            drop_volume=float(settings["DROP_VOLUME"]),
            delay=float(settings["EQUILIBRATION_TIME"]),
            flow_rate=float(settings["FLOW_RATE"]),
            pendant_drop_camera=pendant_drop_camera
        )
        left_pipette.drop_tip()
        if st_t:
            df = pd.DataFrame(st_t, columns=["time (s)", "surface tension (mN/m)"])
            df.to_csv(
                f"experiments/{settings['EXPERIMENT_NAME']}/data/{well_id}/dynamic_surface_tension.csv"
            )
            results.loc[results["well id"] == well_id, "surface tension eq. (mN/m)"] = st_t[-1][1] #TODO take average
            results.loc[results["well id"] == well_id, "temperature (C)"] = (
                float(sensor_data["Temperature (C)"])
            )
        else:
            print("was not able to measure pendant drop")

    file_name_results = f"experiments/{settings['EXPERIMENT_NAME']}/results.csv"
    results.to_csv(file_name_results)
