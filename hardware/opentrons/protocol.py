import pandas as pd
import numpy as np
import pyttsx3
import warnings
import winsound
import time

# Suppress the specific FutureWarning of Pandas
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated",
)


from analysis.plots import Plotter
from analysis.utils import suggest_volume
from hardware.opentrons.http_communications import OpentronsAPI
from hardware.opentrons.droplet_manager import DropletManager
from hardware.opentrons.configuration import Configuration
from hardware.opentrons.containers import Container
from hardware.cameras import PendantDropCamera
from hardware.sensor.sensor_api import SensorAPI
from utils.load_save_functions import load_settings
from utils.logger import Logger


class Protocol:
    def __init__(
        self,
        opentrons_api: OpentronsAPI,
        sensor_api: SensorAPI,
        pendant_drop_camera: PendantDropCamera,
    ):
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
        self.n_measurement_in_eq = 100  # number of data points which is averaged for equillibrium surface tension
        self.results = self._initialize_results()
        self.plotter = Plotter()
        self.droplet_manager = DropletManager(
            left_pipette=self.left_pipette,
            containers=self.containers,
            pendant_drop_camera=self.pendant_drop_camera,
            opentrons_api=self.opentrons_api,
            plotter=self.plotter,
            logger=self.logger,
        )
        self.opentrons_api.home()
        self.logger.info("Initialization finished.")
        self._play_sound("Initialized.")

    def calibrate(self):
        self.logger.info("Starting calibration...")
        drop_parameters = {"drop_volume": 13, "max_measure_time": 10, "flow_rate": 1}
        scale_t = self.droplet_manager.measure_pendant_drop(
            source=self.containers["8A1"],
            drop_parameters=drop_parameters,
            calibrate=True,
        )
        self._save_calibration_data(scale_t)
        average_scale = self._calculate_average_scale(scale_t)
        self.logger.info(f"Finished calibration, average scale is: {average_scale}")
        self._play_sound("CALI DONE.")

    def measure_wells(self):
        self.logger.info("Starting measure wells protocol...")
        self._update_settings()
        well_info = self._load_info(
            file_name=f"experiments/{self.settings['EXPERIMENT_NAME']}/meta_data/{self.settings['WELL_INFO_FILENAME']}"
        )
        wells_ids = well_info["location"].astype(str) + well_info["well"].astype(str)
        for i, well_id in enumerate(wells_ids):
            drop_parameters = {
                "drop_volume": float(well_info["drop volume (uL)"][i]),
                "max_measure_time": float(self.settings["EQUILIBRATION_TIME"]),
                "flow_rate": float(well_info["flow rate (uL/s)"][i]),
            }
            dynamic_surface_tension, drop_parameters = (
                self.droplet_manager.measure_pendant_drop(
                    source=self.containers[well_id], drop_parameters=drop_parameters
                )
            )
            self._save_results(dynamic_surface_tension, well_id, drop_parameters)
            self.plotter.plot_results_well_id(df=self.results)

        self._save_final_results()
        self.logger.info("Finished measure wells protocol.")
        self._play_sound("DATA DATA.")

    def characterize_surfactant(self):
        self.logger.info("Starting characterization protocol...")
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
                well_volume=float(self.settings["WELL_VOLUME"]),
            )
            for i in range(explore_points):
                well_id = f"{row_id}{i+1}"
                drop_volume_suggestion = suggest_volume(
                    results=self.results,
                    next_concentration=float(self.containers[well_id].concentration),
                )
                drop_parameters = {
                    "drop_volume": drop_volume_suggestion,
                    "max_measure_time": float(self.settings["EQUILIBRATION_TIME"]),
                    "flow_rate": float(self.settings["FLOW_RATE"]),
                }
                dynamic_surface_tension, drop_parameters = (
                    self.droplet_manager.measure_pendant_drop(
                        source=self.containers[well_id], drop_parameters=drop_parameters
                    )
                )
                self._save_results(dynamic_surface_tension, well_id, drop_parameters)
                self.plotter.plot_results_concentration(df=self.results)

        self._save_final_results()
        self.logger.info("Finished characterization protocol.")
        self._play_sound("DATA DATA.")

    def _play_sound(self, text: str):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def _update_settings(self):
        self.settings = load_settings()

    def _calculate_average_scale(self, scale_t):
        scale = [item[1] for item in scale_t]
        return np.mean(scale)

    def _load_info(self, file_name: str):
        return pd.read_csv(file_name)

    def _initialize_results(self):
        # Initialize an empty DataFrame with the required columns
        return pd.DataFrame(
            columns=[
                "well id",
                "solution",
                "concentration",
                "surface tension eq. (mN/m)",
                "drop count",
                "drop volume (uL)",
                "max measure time (s)",
                "flow rate (uL/s)",
                "temperature (C)",
                "humidity (%)",
                "pressure (Pa)",
            ]
        )

    def _save_calibration_data(self, scale_t):
        df = pd.DataFrame(scale_t, columns=["time (s)", "scale"])
        df.to_csv(
            f"experiments/{self.settings['EXPERIMENT_NAME']}/data/calibration.csv"
        )

    def _save_results(
        self, dynamic_surface_tension: list, well_id: str, drop_parameters: dict
    ):
        if dynamic_surface_tension:
            self._save_dynamic_surface_tension(dynamic_surface_tension, well_id)
            st_eq = self._calculate_equilibrium_surface_tension(dynamic_surface_tension)
            self._add_data_to_results(
                well_id=well_id,
                surface_tension_eq=st_eq,
                drop_parameters=drop_parameters,
            )
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
            self.logger.info(f"Less than {n_measurement_in_eq} data points measured!")
        return np.mean([x[1] for x in dynamic_surface_tension])

    def _add_data_to_results(
        self, well_id: str, surface_tension_eq: float, drop_parameters: dict
    ):
        sensor_data = self.sensor_api.capture_sensor_data()
        container = self.containers[well_id]
        new_row = pd.DataFrame(
            {
                "well id": [well_id],
                "solution": [container.solution_name],
                "concentration": [container.concentration],
                "surface tension eq. (mN/m)": [surface_tension_eq],
                "drop count": [drop_parameters["drop_count"]],
                "drop volume (uL)": [drop_parameters["drop_volume"]],
                "max measure time (s)": [drop_parameters["max_measure_time"]],
                "flow rate (uL/s)": [drop_parameters["flow_rate"]],
                "temperature (C)": [float(sensor_data["Temperature (C)"])],
                "humidity (%)": [float(sensor_data["Humidity (%)"])],
                "pressure (Pa)": [float(sensor_data["Pressure (Pa)"])],
            }
        )
        self.results = pd.concat([self.results, new_row], ignore_index=True)

    def _save_final_results(self):
        file_name_results = (
            f"experiments/{self.settings['EXPERIMENT_NAME']}/results.csv"
        )
        self.results.to_csv(file_name_results, index=False)
