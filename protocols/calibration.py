import pandas as pd
import numpy as np

from hardware.opentrons.http_communications import Opentrons_http_api
from hardware.opentrons.configuration import Configuration
from hardware.cameras import PendantDropCamera
from utils.load_save_functions import load_settings

def prototcol_calibrate(pendant_drop_camera: PendantDropCamera):
    # initialize
    settings = load_settings()
    api = Opentrons_http_api()
    api.initialise()
    config = Configuration(http_api=api)
    labware = config.load_labware()
    containers = config.load_containers()
    pipettes = config.load_pipettes()
    right_pipette = pipettes["right"]
    left_pipette = pipettes["left"]

    #! exucutable commands
    api.home()
    scale_t = left_pipette.measure_pendant_drop(source=containers["6A1"], drop_volume=13, delay=100, flow_rate=2, pendant_drop_camera=pendant_drop_camera, calibrate=True)
    df = pd.DataFrame(scale_t, columns=["time (s)", "scale"])
    df.to_csv(f"experiments/{settings['EXPERIMENT_NAME']}/data/calibration.csv")
    scale = [item[1] for item in scale_t]
    average_scale = np.mean(scale)
    print(f"average scale: {average_scale}")
