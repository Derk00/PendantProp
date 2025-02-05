import pandas as pd
import os
from hardware.opentrons.containers import *
from hardware.opentrons.pipette import Pipette
from utils.load_save_functions import load_settings, save_instances_to_csv
from utils.logger import Logger
from hardware.opentrons.http_communications import Opentrons_http_api

# TODO no difference between source and destination?


class Configuration:

    def __init__(self, http_api: Opentrons_http_api):
        settings = load_settings()
        self.settings = settings
        self.api = http_api
        self.LABWARE_DEFINITIONS_FOLDER = self.api.LABWARE_DEFINITIONS_FOLDER
        self.ROBOT_TYPE = settings["ROBOT_TYPE"]
        self.FILE_PATH_CONFIG = f'experiments/{settings["EXPERIMENT_NAME"]}/meta_data/{settings["CONFIG_FILENAME"]}'
        self.LAYOUT = self.load_config_file()
        self.RIGHT_PIPETTE_NAME = "p1000_single_gen2"
        self.LEFT_PIPETTE_NAME = "p20_single_gen2"
        self.RIGHT_PIPETTE_ID = None
        self.LEFT_PIPETTE_ID = None
        self.LABWARE = None
        self.logger = Logger(
            name="protocol",
            file_path=f'experiments/{settings["EXPERIMENT_NAME"]}/meta_data',
        )

    def load_config_file(self):
        try:
            return pd.read_csv(self.FILE_PATH_CONFIG)
        except FileNotFoundError:
            self.logger.error(
                f"Configuration file not found at {self.FILE_PATH_CONFIG}"
            )
            return None

    def check_if_custom_labware(self, labware_file: str) -> bool:
        list_of_custom_labware = os.listdir(self.LABWARE_DEFINITIONS_FOLDER)
        for custom_labware in list_of_custom_labware:
            if labware_file == custom_labware[:-5]:
                return True
        return False

    def load_pipettes(self):
        try:
            self.RIGHT_PIPETTE_ID = self.api.load_pipette(
                name=self.RIGHT_PIPETTE_NAME, mount="right"
            )
            right_pipette = Pipette(
                http_api=self.api,
                mount="right",
                pipette_name=self.RIGHT_PIPETTE_NAME,
                pipette_id=self.RIGHT_PIPETTE_ID,
                tips_info=self.LABWARE["tips P1000, 1"],  # create list?
            )

            self.LEFT_PIPETTE_ID = self.api.load_pipette(
                name=self.LEFT_PIPETTE_NAME, mount="left"
            )
            left_pipette = Pipette(
                http_api=self.api,
                mount="left",
                pipette_name=self.LEFT_PIPETTE_NAME,
                pipette_id=self.LEFT_PIPETTE_ID,
                tips_info=self.LABWARE["tips P20, 1"],
            )
            self.logger.info("Pipettes loaded successfully")
            return {"right": right_pipette, "left": left_pipette}
        except Exception as e:
            self.logger.error(f"Error loading pipettes: {e}")
            return None

    def load_labware(self):
        layout = self.LAYOUT
        labware = {}
        try:
            for position in layout["deck position"].unique():
                # robot type causes different position (int or str)
                if self.ROBOT_TYPE == "OT2":
                    position = int(position)
                elif self.ROBOT_TYPE == "Flex":
                    position = str(position)
                else:
                    self.logger.error("robot type not known")

                labware_df = layout[layout["deck position"] == position]
                labware_file = labware_df["labware file"].values[0]
                labware_name = labware_df["labware name"].values[0]
                # TODO: how to load trash in Flex?

                # check if labware is custom
                custom_labware = self.check_if_custom_labware(labware_file)

                labware_info = self.api.load_labware(
                    labware_name=labware_name,
                    labware_file=labware_file,
                    location=position,
                    custom_labware=custom_labware,
                )
                labware[labware_name] = labware_info

                self.LABWARE = labware
            self.logger.info("Labware loaded successfully")
            return self.LABWARE
        except Exception as e:
            self.logger.error(f"Error loading labware: {e}")

    def load_containers(self):
        try:
            containers = {}
            layout = self.LAYOUT
            # Define a mapping from labware name to container class #TODO generalize to multiple labwares
            labware_mapping = {
                "tube rack 15 mL": FalconTube15,
                "glass vial rack": GlassVial,
                "tube rack 50 mL": FalconTube50,
                "plate 1": PlateWell
            }
            for i, function in enumerate(layout["function"]):
                labware_name = layout.loc[i, "labware name"]
                labware_info = self.LABWARE[labware_name]
                location = labware_info["location"]
                name_solution = layout.loc[i, "solution"]
                concentration = layout.loc[i, "concentration (mM)"]
                well = layout.loc[i, "well"]
                initial_volume = layout.loc[i, "initial volume (mL)"]

                if function == "drop_stage":
                    containers[labware_name] = DropStage(labware_info=labware_info)
                
                elif function == "light_holder":
                    containers[labware_name] = LightHolder(labware_info=labware_info)

                elif function == "container":
                    container_class = labware_mapping.get(labware_name)
                    well_id = f"{location}{well}"
                    containers[well_id] = container_class(
                        labware_info=labware_info,
                        well=well,
                        initial_volume_mL=initial_volume,
                        solution_name=name_solution,
                        concentration=concentration,
                    )

            self.logger.info("Containers loaded successfully")
            return containers

        except Exception as e:
            self.logger.error(f"Error loading containers: {e}")
            return None

    def save_containers(self, containers: list):
        containers_only = []
        for key in containers.keys():
            if key == "drop_stage" or key == "light_holder":
                pass
            else:
                containers_only.append(containers[key])
        filename = f'experiments/{self.settings["EXPERIMENT_NAME"]}/meta_data/initial_well_config.csv'
        save_instances_to_csv(instances=containers_only, filename=filename)
