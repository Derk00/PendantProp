import pandas as pd

from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from utils.load_save_functions import load_settings

# TODO add sensor data

def prototcol_measure_wells():
    settings = load_settings()
    file_name = f"experiments/{settings['EXPERIMENT_NAME']}/meta_data/well_info.csv"
    well_info = pd.read_csv(file_name)
    results = well_info.copy()
    results["well id"] = well_info["location"].astype(str) + well_info["well"]
    well_ids = results["well id"]

    # initialize
    # api = Opentrons_http_api()
    # api.initialise()
    # config = Configuration(http_api=api)
    # labware = config.load_labware()
    # pipettes = config.load_pipettes()
    # containers = config.load_containers()
    # right_pipette = pipettes["right"]
    # left_pipette = pipettes["left"]

    for well_id in well_ids:
        # st_eq, st_t = left_pipette.measure_pendant_drop(
        #     source=containers[well_id],
        #     destination=containers["drop_stage"],
        #     drop_volume=settings["DROP_VOLUME"],
        #     delay=settings["EQUILIBRATION_TIME"],
        #     flow_rate=settings["FLOW_RATE"],
        # )
        st_eq = 10
        results.loc[results["well id"] == well_id, "surface tension eq. (mN/m)"] = st_eq
        st_t = [
            [1, 10.5],  # Time 1, Surface Tension 10.5
            [2, 11.0],  # Time 2, Surface Tension 11.0
            [3, 10.8],  # Time 3, Surface Tension 10.8
        ]
        df = pd.DataFrame(st_t, columns=["time (s)", "surface tension (mN/m)"])
        df.to_csv(f"experiments/{settings['EXPERIMENT_NAME']}/{well_id}/dynamic_surface_tension.csv")

    file_name_results = f"experiments/{settings['EXPERIMENT_NAME']}/results.csv"
    results.to_csv(file_name_results) 
