"""
TODO
----
- maybe i messed up by changing the version of aionotify (opentrons requires 0.2.0, but have pip upgraded to 0.3.1)
- all caps for constants
"""

import numpy as np
from utils.logger import Logger
from utils.load_save_functions import load_settings


class Container:
    def __init__(
        self,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
        inner_diameter_mm: float,
        solution_name: str = None,
    ):
        settings = load_settings()
        self.well = well
        self.volume_mL = initial_volume_mL
        self.inner_diameter_mm = inner_diameter_mm
        self.initial_height_mm = self.update_liquid_height()
        self.height_mm = self.initial_height_mm
        self.solution_name = solution_name
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        # atexit.register(self.print_heights)

    def aspirate(self, volume: float):
        self.volume_mL -= volume * 1e-3
        self.update_liquid_height()

    def dispense(self, volume: float):
        self.volume_mL += volume * 1e-3
        self.update_liquid_height()

    def update_liquid_height(self):
        raise NotImplementedError("This method should be implemented by subclasses")

    def print_heights(self):
        print(f"{self.name} has an initial height of {self.initial_height_mm:.2f} mm")
        print(f"{self.name} has a final height of {self.height_mm:.2f} mm")
        print(f"{self.name} has a volume of {self.volume_mL} mL")

    def __str__(self):
        return f"""
        Container object
        Solution name: {self.solution_name}
        Inner diameter: {self.inner_diameter_mm} mm
        Well: {self.well}
        Initial height: {self.initial_height_mm} mm
        Current height: {self.height_mm} mm
        Current volume: {self.volume_mL} mL
        """


class Eppendorf(Container):
    def __init__(
        self,
        solution_name: str,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
    ):
        super().__init__(
            solution_name, labware_info, well, initial_volume_mL, inner_diameter_mm=10
        )

    def update_liquid_height(self):
        # TODO fix
        heightcone_mm = 18.6
        inner_diameter2_mm = 2
        volumecone_mL = (
            1e-3
            * (1 / 12)
            * np.pi
            * heightcone_mm
            * (
                self.inner_diameter_mm**2
                + self.inner_diameter_mm * inner_diameter2_mm
                + inner_diameter2_mm**2
            )
        )

        if self.volume_mL < volumecone_mL:
            self.height_mm = (
                1e3
                * 12
                * self.volume_mL
                / (
                    np.pi
                    * (
                        self.inner_diameter_mm**2
                        + self.inner_diameter_mm * inner_diameter2_mm
                        + inner_diameter2_mm**2
                    )
                )
                - 3
            )
        else:
            self.height_mm = (
                1e3
                * (self.volume_mL - volumecone_mL)
                / (np.pi * (self.inner_diameter_mm / 2) ** 2)
                + heightcone_mm
                - 3
            )
        return self.height_mm


class FalconTube15(Container):
    def __init__(
        self,
        solution_name: str,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
    ):
        super().__init__(
            solution_name,
            labware_info,
            well,
            initial_volume_mL,
            inner_diameter_mm=15.25,
        )

    def update_liquid_height(self):
        dead_volume_mL = 1.0
        dispense_bottom_out_mm = 15
        self.height_mm = (
            (self.volume_mL - dead_volume_mL)
            * 1e3
            / (np.pi * (self.inner_diameter_mm / 2) ** 2)
        ) + dispense_bottom_out_mm
        return self.height_mm


class FalconTube50(Container):
    def __init__(
        self,
        solution_name: str,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
    ):
        super().__init__(
            solution_name, labware_info, well, initial_volume_mL, inner_diameter_mm=28
        )

    def update_liquid_height(self):
        dead_volume_mL = 5
        dispense_bottom_out_mm = 21
        self.height_mm = (
            (self.volume_mL - dead_volume_mL)
            * 1e3
            / (np.pi * (self.inner_diameter_mm / 2) ** 2)
        ) + dispense_bottom_out_mm
        return self.height_mm


class GlassVial(Container):
    def __init__(
        self,
        solution_name: str,
        labware_info: dict,
        well: str,
        initial_volume_mL: float,
    ):
        super().__init__(
            solution_name, labware_info, well, initial_volume_mL, inner_diameter_mm=18
        )

    def update_liquid_height(self):
        self.height_mm = (
            1e3 * (self.volume_mL) / (np.pi * (self.inner_diameter_mm / 2) ** 2)
        )
        return self.height_mm - 1


if __name__ == "__main__":
    # Test the container classes
    ft50 = FalconTube50("test", "A1", 40)
    print(ft50)
