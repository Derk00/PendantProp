import pandas as pd
import os
from hardware.opentrons.containers import *
from utils.load_save_functions import load_settings


class Pipette:
    def __init__(
        self, http_api, mount: str, pipette_name: str, pipette_id: str, tips_id: str
    ):
        self.api = http_api
        self.MOUNT = mount
        self.PIPETTE_NAME = pipette_name
        self.PIPETTE_ID = pipette_id
        self.TIPS_ID = tips_id
        self.has_tip = False

        # set max volume
        if self.PIPETTE_NAME == "p20_single_gen2":
            self.max_volume = 20
        elif self.PIPETTE_NAME == "p1000_single_gen2":
            self.max_volume = 1000
        else:
            print("Pipette not recognised")

    def pick_up_tip(self):
        try:
            self.api.pick_up_tip(
                tip_labware_id=self.TIPS_ID,
                tip_well_name="A1",
                pipette_id=self.PIPETTE_ID,
            )
            self.has_tip = True
        except:
            print("Error picking up tip")


class Configuration:

    def __init__(self, http_api=None):
        settings = load_settings()
        self.api = http_api
        self.LABWARE_DEFINITIONS_FOLDER = self.api.LABWARE_DEFINITIONS_FOLDER
        self.ROBOT_TYPE = settings["ROBOT_TYPE"]
        self.FILE_PATH_CONFIG = f'experiments/{settings["EXPERIMENT_NAME"]}/meta_data/{settings["CONFIG_FILENAME"]}'
        self.LAYOUT = self.load_config_file()
        self.RIGHT_PIPETTE_NAME = "p1000_single_gen2"
        self.LEFT_PIPETTE_NAME = "p20_single_gen2"
        self.RIGHT_PIPETTE_ID = None
        self.LEFT_PIPETTE_ID = None

    def load_config_file(self):
        return pd.read_csv(self.FILE_PATH_CONFIG)

    def check_if_custom_labware(self, labware_file: str) -> bool:
        list_of_custom_labware = os.listdir(self.LABWARE_DEFINITIONS_FOLDER)
        for custom_labware in list_of_custom_labware:
            if labware_file == custom_labware[:-5]:
                return True
        return False

    def load_pipettes(self):
        self.RIGHT_PIPETTE_ID = self.api.load_pipette(
            name=self.RIGHT_PIPETTE_NAME, mount="right"
        )
        right_pipette = Pipette(
            http_api=self.api,
            mount="right",
            pipette_name=self.RIGHT_PIPETTE_NAME,
            pipette_id=self.RIGHT_PIPETTE_ID,
            tips_id="test",
        )

        self.LEFT_PIPETTE_ID = self.api.load_pipette(
            name=self.LEFT_PIPETTE_NAME, mount="left"
        )
        left_pipette = Pipette(
            http_api=self.api,
            mount="left",
            pipette_name=self.LEFT_PIPETTE_NAME,
            pipette_id=self.LEFT_PIPETTE_ID,
            tips_id="test",
        )
        return {"right": right_pipette, "left": left_pipette}

    def load_labware(self):
        layout = self.LAYOUT
        labware = {}
        for position in layout["deck position"].unique():
            # robot type causes different position (int or str)
            if self.ROBOT_TYPE == "OT2":
                position = int(position)
            elif self.ROBOT_TYPE == "Flex":
                position = str(position)
            else:
                print("Robot type not recognised")

            labware_df = layout[layout["deck position"] == position]
            labware_file = labware_df["labware file"].values[0]
            labware_name = labware_df["labware name"].values[0]
            # TODO: how to load trash in Flex?

            # check if labware is custom
            custom_labware = self.check_if_custom_labware(labware_file)
            print(f"labware file {labware_file} is custom: {custom_labware}")

            labware_id = self.api.load_labware(
                labware_name=labware_file,
                location=position,
                custom_labware=custom_labware,
            )
            labware[labware_name] = labware_id
        return labware

    def load_containers(self, labware):

        containers = {}
        layout = self.LAYOUT

        # Define a mapping from labware name to container class
        labware_mapping = {
            "tube rack": FalconTube15,  # TODO fix this to tube rack 15 mL
            "eppendorf rack": Eppendorf,
            "glass vial rack": GlassVial,
            "tube rack 50 mL": FalconTube50,
        }

        for i, function in enumerate(layout["function"]):
            if function == "container":  # check if function is container
                name_solution = layout.loc[i, "solution"]
                labware_name = layout.loc[i, "labware name"]
                well = layout.loc[i, "well"]
                initial_volume = layout.loc[i, "initial volume (mL)"]
                container_class = labware_mapping.get(labware_name)

                containers[name_solution] = container_class(
                    solution_name=name_solution,
                    well=well,
                    initial_volume_mL=initial_volume,
                )
        return containers

    def load_configuration(self):
        labware = self.load_labware()
        return {
            "labware": labware,
            "pipettes": self.load_pipettes(),
            "containers": self.load_containers(labware=labware),
        }
