"""
TODO
----
- maybe i messed up by changing the version of aionotify (opentrons requires 0.2.0, but have pip upgraded to 0.3.1)
- Eppendorf child class
- Well diameter from labware_info, not hard coded.
"""

import numpy as np
import os
from utils.logger import Logger
from utils.load_save_functions import load_settings

# from hardware.opentrons.pipette import Pipette


class Container:
    def __init__(
        self,
        labware_info: dict,
        well: str,
        initial_volume_mL: float = 0,
        solution_name: str = "empty",
        concentration: any = "pure",
        inner_diameter_mm: float = None,
    ):
        # Settings
        settings = load_settings()

        # Constant attributes
        self.WELL = well
        self.LOCATION = labware_info["location"]
        self.WELL_ID = f"{self.LOCATION}{self.WELL}"
        self.INITIAL_VOLUME_ML = initial_volume_mL
        self.MAX_VOLUME = labware_info["max_volume"]
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        self.DEPTH = labware_info["depth"]
        self.INNER_DIAMETER_MM = inner_diameter_mm
        self.INITIAL_HEIGHT_MM = self.update_liquid_height(
            volume_mL=self.INITIAL_VOLUME_ML
        )
        self.WELL_DIAMETER = labware_info["well_diameter"]
        self.CONTAINER_TYPE = None

        # Variable attributes
        self.volume_mL = self.INITIAL_VOLUME_ML
        self.height_mm = self.INITIAL_HEIGHT_MM
        self.solution_name = solution_name
        self.concentration = concentration  # TODO this can be extended to mixtures

        # Create logger (container & protocol)
        os.makedirs(f"experiments/{settings['EXPERIMENT_NAME']}/data", exist_ok=True)
        os.makedirs(
            f"experiments/{settings['EXPERIMENT_NAME']}/data/{self.WELL_ID}",
            exist_ok=True,
        )
        self.container_logger = Logger(
            name=self.WELL_ID,
            file_path=f"experiments/{settings['EXPERIMENT_NAME']}/data/{self.WELL_ID}",
        )
        self.protocol_logger = Logger(
            name="protocol",
            file_path=f'experiments/{settings["EXPERIMENT_NAME"]}/meta_data',
        )

    def aspirate(self, volume: float):
        if self.volume_mL < (volume * 1e-3):
            self.protocol_logger.error(
                "Aspiration volume is larger than container volume!"
            )
            return
        self.volume_mL -= volume * 1e-3
        self.update_liquid_height(volume_mL=self.volume_mL)
        self.container_logger.info(
            f"Container: Aspirated {volume} uL from this container with content {self.solution_name}"
        )

    def dispense(self, volume: float, source: "Container"):
        if (self.volume_mL * 1e3) + volume > self.MAX_VOLUME:
            self.protocol_logger.error("Overflowing of container!")
            return
        self.volume_mL += volume * 1e-3
        self.update_liquid_height(volume_mL=self.volume_mL)

        if source.concentration != "pure":
            # case source contains solution
            self.concentration = (
                float(source.concentration) * volume * 1e-3 / self.volume_mL
            )
            self.solution_name = source.solution_name
        elif self.concentration != "pure":
            # case container contains solution and source is water
            self.concentration = self.concentration * volume * 1e-3 / self.volume_mL
            self.solution_name = self.solution_name
        else:
            # case container is empty and source is pure
            self.concentration = "pure"
            self.solution_name = source.solution_name

        self.container_logger.info(
            f"Container: Dispensed {volume} uL into this container from source {source.WELL} of {source.LABWARE_NAME} ({source.WELL_ID}) containing {source.solution_name}"
        )

    def measure_pendant_drop(self, p20_pipette, drop_volume: float):
        pass

    def update_liquid_height(self, volume_mL):
        raise NotImplementedError("This method should be implemented by subclasses")

    def __str__(self):
        return f"""
        Container object

        Container type = {self.CONTAINER_TYPE}
        Well ID = {self.WELL_ID}
        Solution name: {self.solution_name}
        Concentration: {self.concentration}
        Inner diameter: {self.INNER_DIAMETER_MM} mm
        Well: {self.WELL}
        Location: {self.LOCATION}
        Initial height: {self.INITIAL_HEIGHT_MM:.2f} mm
        Current height: {self.height_mm:.2f} mm
        Current volume: {self.volume_mL * 1e3:.0f} uL
        """


class FalconTube15(Container):
    def __init__(
        self,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
        solution_name: str,
        concentration: any,
    ):
        super().__init__(
            labware_info,
            well,
            initial_volume_mL,
            solution_name,
            concentration,
            inner_diameter_mm=15.25,
        )
        self.CONTAINER_TYPE = "Falcon tube 15 mL"

    def update_liquid_height(self, volume_mL):
        dead_volume_mL = 1.0
        dispense_bottom_out_mm = 15
        self.height_mm = (
            (volume_mL - dead_volume_mL)
            * 1e3
            / (np.pi * (self.INNER_DIAMETER_MM / 2) ** 2)
        ) + dispense_bottom_out_mm
        return self.height_mm


class FalconTube50(Container):
    def __init__(
        self,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
        solution_name: str,
        concentration: any,
    ):
        super().__init__(
            labware_info,
            well,
            initial_volume_mL,
            solution_name,
            concentration,
            inner_diameter_mm=28,
        )
        self.CONTAINER_TYPE = "Falcon tube 50 mL"

    def update_liquid_height(self, volume_mL):
        dead_volume_mL = 5
        dispense_bottom_out_mm = 21
        self.height_mm = (
            (volume_mL - dead_volume_mL)
            * 1e3
            / (np.pi * (self.INNER_DIAMETER_MM / 2) ** 2)
        ) + dispense_bottom_out_mm
        return self.height_mm


class GlassVial(Container):
    def __init__(
        self,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
        solution_name: str,
        concentration: any,
    ):
        super().__init__(
            labware_info,
            well,
            initial_volume_mL,
            solution_name,
            concentration,
            inner_diameter_mm=18,
        )
        self.CONTAINER_TYPE = "Glass Vial"

    def update_liquid_height(self, volume_mL):
        self.height_mm = 1e3 * (volume_mL) / (np.pi * (self.INNER_DIAMETER_MM / 2) ** 2)
        return self.height_mm - 1


class PlateWell(Container):

    def __init__(
        self,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
        solution_name: str,
        concentration: any,
    ):
        super().__init__(
            labware_info,
            well,
            initial_volume_mL,
            solution_name,
            concentration,
            inner_diameter_mm=6.96,
        )
        self.CONTAINER_TYPE = "Plate Well"

    def update_liquid_height(self, volume_mL):
        self.height_mm = 1e3 * (volume_mL) / (np.pi * (self.INNER_DIAMETER_MM / 2) ** 2)
        return self.height_mm


class DropStage:
    def __init__(self, labware_info):
        settings = load_settings()
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        self.LOCATION = labware_info["location"]
        self.CONTAINER_TYPE = "Cuvette"
        self.WELL = "A1"  # always 1 well in drop stage
        self.WELL_ID = f"{self.LOCATION}{self.WELL}"
        self.DEPTH = labware_info["depth"]
        self.height_mm = labware_info["depth"]
        self.MAX_VOLUME = labware_info["max_volume"]
        self.solution_name = "empty"
        os.makedirs(f"experiments/{settings['EXPERIMENT_NAME']}/data", exist_ok=True)
        os.makedirs(
            f"experiments/{settings['EXPERIMENT_NAME']}/data/{self.LABWARE_NAME}",
            exist_ok=True,
        )
        self.container_logger = Logger(
            name=self.LABWARE_NAME,
            file_path=f"experiments/{settings['EXPERIMENT_NAME']}/data/{self.LABWARE_NAME}",
        )

    def aspirate(self, volume):
        pass

    def dispense(self, volume, source: Container):
        self.solution_name = source.solution_name
        self.container_logger.info(
            f"Drop stage: measured pendant drop from {source.WELL_ID}. See container log for more details."
        )
        pass

    def __str__(self):
        return f"""
        Drop stage object

        Container type: {self.CONTAINER_TYPE}
        Well: {self.WELL}
        Location: {self.LOCATION}
        Drop height:  {self.height_mm:.2f} mm
        """


class LightHolder:
    def __init__(self, labware_info):
        settings = load_settings()
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        self.LOCATION = labware_info["location"]
        self.CONTAINER_TYPE = "Light holder"
        self.WELL = "A1"  # place holder
        self.WELL_ID = f"{self.LOCATION}{self.WELL}"
        self.DEPTH = labware_info["depth"]
        self.height_mm = labware_info["depth"]
        self.MAX_VOLUME = labware_info["max_volume"]

    def aspirate(self, volume):
        print(
            "Attempted to aspirate from light holder. This should never be the case!"
        )
        pass

    def dispense(self, volume, source: Container):
        print(
            "Attempted to dispense from light holder. This should never be the case!"
        )
        pass

    def __str__(self):
        return f"""
        Light holder object:

        Container type: {self.CONTAINER_TYPE}
        Location: {self.LOCATION}
        """


class Sponge:
    def __init__(self, labware_info):
        settings = load_settings()
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        self.LOCATION = labware_info["location"]
        self.CONTAINER_TYPE = "Sponge"
        self.ORDERING = labware_info["ordering"]
        self.DEPTH = labware_info["depth"]
        self.height_mm = labware_info["depth"]
        self.MAX_VOLUME = labware_info["max_volume"]

        self.index = 0
        self.well = self.ORDERING[self.index]

    def update_well(self):
        self.index += 1
        self.well = self.ORDERING[self.index]

    def aspirate(self, volume):
        print("Attempted to aspirate from sponge. This should never be the case!")
        pass

    def dispense(self, volume, source: Container):
        print("Attempted to dispense from sponge. This should never be the case!")
        pass

    def __str__(self):
        return f"""
        Sponge object:

        Container type: {self.CONTAINER_TYPE}
        Location: {self.LOCATION}
        Current well: {self.well}
        """
