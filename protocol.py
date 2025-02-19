import pandas as pd
import numpy as np
import warnings

# Suppress the specific FutureWarning of Pandas
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated",
)

from utils.logger import Logger
from hardware.opentrons.http_communications import OpentronsAPI
from hardware.opentrons.configuration import Configuration
from hardware.cameras import PendantDropCamera
from hardware.sensor.sensor_api import SensorAPI
from utils.load_save_functions import load_settings

class Protocol:
    def __init__(self, opentrons_api: OpentronsAPI, sensor_api: SensorAPI, pendant_drop_camera: PendantDropCamera):
        self.settings = load_settings()
        self.logger = Logger(
            name="protocol",
            file_path=f'experiments/{self.settings["EXPERIMENT_NAME"]}/meta_data',
        )
        self.logger.info("Initialization starting...")
        self.opentrons_api = opentrons_api
        self.opentrons_api.initialise()
        self.sensor_api = sensor_api
        self.pendant_drop_camera = pendant_drop_camera
        self.config = Configuration(http_api=opentrons_api)
        self.labware = self.config.load_labware()
        self.containers = self.config.load_containers()
        pipettes = self.config.load_pipettes()
        self.right_pipette = pipettes["right"]
        self.left_pipette = pipettes["left"]
        self.n_measurement_in_eq = 100 # number of data points which is averaged for equillibrium surface tension
        self.results = self._initialize_results()

        self.opentrons_api.home()
        self.logger.info("Initialization finished.")

    def calibrate(self):
        self.logger.info("Starting calibration...")
        scale_t = self.left_pipette.measure_pendant_drop(
            source=self.containers["8A1"],
            drop_volume=13,
            delay=10,
            flow_rate=1,
            pendant_drop_camera=self.pendant_drop_camera,
            calibrate=True
        )
        self._save_calibration_data(scale_t)
        average_scale = self._calculate_average_scale(scale_t)
        self.logger.info(f"finished calibration, average scale is: {average_scale}")

    def measure_wells(self):
        self.logger.info("starting measure wells protocol...")
        self._update_settings()
        well_info = self._load_info(file_name=f"experiments/{self.settings['EXPERIMENT_NAME']}/meta_data/{self.settings['WELL_INFO_FILENAME']}")
        wells_ids = well_info["location"].astype(str) + well_info["well"].astype(str)
        for i, well_id in enumerate(wells_ids):
            dynamic_surface_tension = self.left_pipette.measure_pendant_drop(
                source=self.containers[well_id],
                drop_volume=float(well_info["drop volume (uL)"][i]),
                delay=float(self.settings["EQUILIBRATION_TIME"]),
                flow_rate=float(self.settings["FLOW_RATE"]),
                pendant_drop_camera=self.pendant_drop_camera
            )
            self._save_results(dynamic_surface_tension, well_id)
        self._save_final_results()
        self.logger.info("Finished measure wells protocol. ")

    def characterize_surfactant(self):
        self._update_settings()
        characterization_info = self._load_info(
            file_name=f"experiments/{self.settings['EXPERIMENT_NAME']}/meta_data/{self.settings['CHARACTERIZATION_INFO_FILENAME']}"
        )
        explore_points = int(self.settings["EXPLORE_POINTS"])
        self.results = self._initialize_results()

        for i, surfactant in enumerate(characterization_info["surfactant"]):
            row_id = characterization_info["row id"][i]
            self.right_pipette.serial_dilution(
                row_id=row_id,
                solution_name=surfactant,
                n_dilutions=explore_points,
                well_volume=float(self.settings["WELL_VOLUME"])
            )
            for i in range(explore_points):
                well_id = f"{row_id}{i+1}"
                container = self.containers[well_id]
                dynamic_surface_tension = self.left_pipette.measure_pendant_drop(
                    source=self.containers[well_id],
                    drop_volume=float(self.settings["DROP_VOLUME"]),
                    delay=float(self.settings["EQUILIBRATION_TIME"]),
                    flow_rate=float(self.settings["FLOW_RATE"]),
                    pendant_drop_camera=self.pendant_drop_camera
                )
    def _update_settings(self):
        self.settings = load_settings()

    def _calculate_average_scale(self, scale_t):
        scale = [item[1] for item in scale_t]
        return np.mean(scale)

    def _load_info(self, file_name: str):
        return pd.read_csv(file_name)

    def _initialize_results(self):
        # Initialize an empty DataFrame with the required columns
        return pd.DataFrame(columns=["well id", "surface tension eq. (mN/m)", "Temperature (C)", "Humidity (%)", "Pressure (Pa)"])

    def _save_calibration_data(self, scale_t):
        df = pd.DataFrame(scale_t, columns=["time (s)", "scale"])
        df.to_csv(f"experiments/{self.settings['EXPERIMENT_NAME']}/data/calibration.csv")

    def _save_results(self, dynamic_surface_tension, well_id):
        if dynamic_surface_tension:
            self._save_dynamic_surface_tension(dynamic_surface_tension, well_id)
            st_eq = self._calculate_equilibrium_surface_tension(
                dynamic_surface_tension
            )
            self._add_data_to_results(well_id=well_id, surface_tension_eq=st_eq)
        else:
            self.logger.warning("Was not able to measure pendant drop!")

    def _save_dynamic_surface_tension(self, dynamic_surface_tension, well_id):
        df = pd.DataFrame(
            dynamic_surface_tension, columns=["time (s)", "surface tension (mN/m)"]
        )
        df.to_csv(
            f"experiments/{self.settings['EXPERIMENT_NAME']}/data/{well_id}/dynamic_surface_tension.csv"
        )

    def _calculate_equilibrium_surface_tension(self, dynamic_surface_tension):
        n_measurement_in_eq = 100
        if len(dynamic_surface_tension) > n_measurement_in_eq:
            dynamic_surface_tension = dynamic_surface_tension[-n_measurement_in_eq:]
        else:
            self.logger.info(f"less than {n_measurement_in_eq} data points measured!")
        return np.mean([x[1] for x in dynamic_surface_tension])

    def _add_data_to_results(self, well_id, surface_tension_eq):
        sensor_data = self.sensor_api.capture_sensor_data()
        new_row = pd.DataFrame({
            "well id": [well_id],
            "surface tension eq. (mN/m)": [surface_tension_eq],
            "Temperature (C)": [float(sensor_data["Temperature (C)"])],
            "Humidity (%)": [float(sensor_data["Humidity (%)"])],
            "Pressure (Pa)": [float(sensor_data["Pressure (Pa)"])],
        })
        self.results = pd.concat([self.results, new_row], ignore_index=True)

    def _save_final_results(self):
        file_name_results = f"experiments/{self.settings['EXPERIMENT_NAME']}/results.csv"
        self.results.to_csv(file_name_results, index=False)
