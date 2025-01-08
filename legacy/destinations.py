# Could consider to make 1 class for all containers and then later separate them into sources & destinations
import os
from utils.logger import Logger
from utils.load_save_functions import load_settings
from hardware.opentrons.containers import Container


class Well:
    def __init__(self, well: str, labware_info: dict):
        settings = load_settings()
        self.WELL = well
        self.LOCATION = labware_info["location"]
        self.WELL_ID = f"{self.LOCATION}{self.WELL}"
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        self.MAX_VOLUME = labware_info["max_volume"]
        self.WELL_DIAMETER = labware_info["well_diameter"]
        self.volume = 0
        os.makedirs(f"experiments/{settings['EXPERIMENT_NAME']}/data", exist_ok=True)
        os.makedirs(
            f"experiments/{settings['EXPERIMENT_NAME']}/data/{self.WELL_ID}",
            exist_ok=True,
        )
        self.logger = Logger(
            name=self.WELL_ID,
            file_path=f"experiments/{settings['EXPERIMENT_NAME']}/data/{self.WELL_ID}",
        )

    def dispense(self, volume: float, source: Container):
        """
        dispensing into the well
        """
        if self.volume + volume > self.MAX_VOLUME:
            print("Volume exceeds well capacity!")

        self.volume += volume
        self.logger.info(
            f"Well: dispensed {volume} uL from {source.LABWARE_NAME} into {self.WELL_ID}."
        )

    def aspirate(self, volume: float):
        """
        apsirating from the well
        """
        if self.MAX_VOLUME - volume < 0:
            print("More aspirating volume than volume in well!")
        self.volume -= volume

    def measure_well():
        # TODO: implement this method
        pass

    def __str__(self):
        return f"""
        Well object
        Well: {self.WELL}
        Labware ID: {self.LABWARE_ID}
        Volume: {self.volume}
        
        """
