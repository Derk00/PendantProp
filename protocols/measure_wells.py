import pandas as pd
import numpy as np

from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from hardware.cameras import PendantDropCamera
from hardware.sensor.sensor_api import SensorApi
from utils.load_save_functions import load_settings

def prototcol_measure_wells(pendant_drop_camera: PendantDropCamera):
    n_measurement_in_eq = 100 # number of last frames to average over TODO make this a setting?
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
    containers = config.load_containers()
    print(containers)
    pipettes = config.load_pipettes()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]

    # #! exucutable commands
    # api.home()

    # for well_id in well_ids:
    #     sensor_data = sensor_api.capture_sensor_data()
    #     st_t = left_pipette.measure_pendant_drop(
    #         source=containers[well_id], 
    #         drop_volume=float(settings["DROP_VOLUME"]),
    #         delay=float(settings["EQUILIBRATION_TIME"]),
    #         flow_rate=float(settings["FLOW_RATE"]),
    #         pendant_drop_camera=pendant_drop_camera
    #     )

    #     if st_t:
    #         df = pd.DataFrame(st_t, columns=["time (s)", "surface tension (mN/m)"])
    #         df.to_csv(
    #             f"experiments/{settings['EXPERIMENT_NAME']}/data/{well_id}/dynamic_surface_tension.csv"
    #         )
    #         if len(st_t) > n_measurement_in_eq:
    #             st_t = st_t[-n_measurement_in_eq:]
    #             results.loc[results["well id"] == well_id, "surface tension eq. (mN/m)"] = np.mean([x[1] for x in st_t])
    #         else:
    #             results.loc[results["well id"] == well_id, "surface tension eq. (mN/m)"] = np.mean([x[1] for x in st_t])
    #             print(f"less than {n_measurement_in_eq} measurements")

    #         results.loc[results["well id"] == well_id, "Temperature (C)"] = (
    #             float(sensor_data["Temperature (C)"])
    #         )
    #         results.loc[results["well id"] == well_id, "Humidity (%)"] = float(
    #             sensor_data["Humidity (%)"]
    #         )
    #         results.loc[results["well id"] == well_id, "Pressure (Pa)"] = float(
    #             sensor_data["Pressure (Pa)"]
    #         )

    #     else:
    #         print("was not able to measure pendant drop")

    # file_name_results = f"experiments/{settings['EXPERIMENT_NAME']}/results.csv"
    # results.to_csv(file_name_results, index=False)
