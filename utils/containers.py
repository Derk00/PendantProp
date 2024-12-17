# -*- coding: utf-8 -*-
"""
File containing all the container classes used in AULab

Classes
-------
Eppendorf
    eppendorf 1.5 mL
FalconTube15
    falcon tube 15 mL
GlassVial
    Glass vial 5 mL
FalconTube50
    falcon tube 50 mL

Functions
---------
None

TODO
----
- add method to dispense at top of container

"""
import numpy as np
from opentrons import protocol_api
from opentrons.types import Location
import atexit

__author__ = "Pim Dankloff"
__copyright__ = "Copyright 2024, Pim Dankloff"
__credits__ = ["Pim Dankloff"]
__license__ = "MIT"
__version__ = "1.0.3"
__maintainer__ = "Pim Dankloff"
__email__ = "pim.dankloff@ru.nl"
__status__ = "Production"


class Eppendorf:
    """
    Container eppendorf 1.5 mL

    Accurate to 200 uL
    """

    name: str
    well: protocol_api.labware.Well
    initial_height_mm: float
    height_mm: float
    inner_diameter_mm: float
    height_mm: float
    volume_mL: float

    def __init__(
        self,
        name: str,
        well: protocol_api.labware.Well,
        initial_volume_mL: float,
        inner_diameter_mm: float = 10,  # this matches for eppendorf tube of 1.5 mL
    ):
        self.name = name
        self.well = well

        self.heightcone_mm = (
            18.6  # this matches for cone part of eppendorf tube of 1.5 mL
        )
        self.inner_diameter_mm = inner_diameter_mm
        self.inner_diameter2_mm = 2  # this matches for the inner diameter of the truncated cone part of eppendorf tube of 1.5 mL
        self.volumecone_mL = (
            1e-3
            * (1 / 12)
            * np.pi
            * self.heightcone_mm
            * (
                self.inner_diameter_mm**2
                + self.inner_diameter_mm * self.inner_diameter2_mm
                + self.inner_diameter2_mm**2
            )
        )
        self.volume_mL = initial_volume_mL
        self.initial_height_mm = self.update_liquid_height()
        self.height_mm = self.initial_height_mm

        atexit.register(self.print_heights)

    def aspirate(self, volume: float) -> Location:
        """
        Withdraw liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL -= volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def dispense(self, volume: float) -> Location:
        """
        Add liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL += volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def update_liquid_height(self):
        """
        Calculate the height of the liquid in the vessel.

        Args:
            None
        Returns:
            None
        """
        if self.volume_mL < self.volumecone_mL:
            self.height_mm = (
                1e3
                * 12
                * self.volume_mL
                / (
                    np.pi
                    * (
                        self.inner_diameter_mm**2
                        + self.inner_diameter_mm * self.inner_diameter2_mm
                        + self.inner_diameter2_mm**2
                    )
                )
                - 3
            )
        else:
            self.height_mm = (
                1e3
                * (self.volume_mL - self.volumecone_mL)
                / (np.pi * (self.inner_diameter_mm / 2) ** 2)
                + self.heightcone_mm
                - 3
            )
        return self.height_mm

    def print_heights(self):
        print(f"{self.name} has a initial height of {self.initial_height_mm:.2f} mm")
        print(f"{self.name} has a final height of {self.height_mm:.2f} mm")
        print(f"{self.name} has a volume of {self.volume_mL} mL")

    def __str__(self):
        output_str = f"""
        Tube object
        Name: {self.name}
        Inner diameter: {self.inner_diameter_mm} mm
        Well: {self.well}
        Initial height: {self.initial_height_mm} mm
        Current height: {self.height_mm} mm
        Current volume: {self.volume_mL} mL
        """
        return output_str


class FalconTube15:
    """
    Container for sample tube data.

    Falcon tube FT15

    Accurate to 1.5 mL
    """

    name: str
    well: protocol_api.labware.Well
    initial_height_mm: float
    height_mm: float
    inner_diameter_mm: float
    height_mm: float
    volume_mL: float

    def __init__(
        self,
        name: str,
        well: protocol_api.labware.Well,
        initial_volume_mL: float,
        inner_diameter_mm: float = 15.25,  # this matches for falcon tube of 15 mL
    ):
        self.name = name
        self.well = well

        # due to the v-bottom of FT15 --> 1 mL is ca. 20 mm
        self.dead_volume_mL = 1.0

        self.dispense_bottom_out_mm = 15
        self.inner_diameter_mm = inner_diameter_mm

        self.volume_mL = initial_volume_mL
        self.initial_height_mm = self.update_liquid_height()
        self.height_mm = self.initial_height_mm

        atexit.register(self.print_heights)

    def aspirate(self, volume: float) -> Location:
        """
        Withdraw liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL -= volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def dispense(self, volume: float) -> Location:
        """
        Add liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL += volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def update_liquid_height(self):
        """
        Calculate the height of the liquid in the vessel.

        Args:
            None
        Returns:
            None
        """
        self.height_mm = (
            (self.volume_mL - self.dead_volume_mL)
            * 1e3
            / (np.pi * (self.inner_diameter_mm / 2) ** 2)
        ) + self.dispense_bottom_out_mm
        return self.height_mm

    def print_heights(self):
        print(f"{self.name} has a initial height of {self.initial_height_mm}")
        print(f"{self.name} has a final height of {self.height_mm}")
        print(f"{self.name} has a volume of {self.volume_mL+self.dead_volume_mL} mL")

    def __str__(self):
        output_str = f"""
        Tube object
        Name: {self.name}
        Inner diameter: {self.inner_diameter_mm} mm
        Well: {self.well}
        Initial height: {self.initial_height_mm} mm
        Current height: {self.height_mm} mm
        Current volume: {self.volume_mL} mL
        """
        return output_str


class GlassVial:
    """
    Glass vial 5 mL
    Accurate till 0.5 mL
    """

    name: str
    well: protocol_api.labware.Well
    initial_height_mm: float
    height_mm: float
    inner_diameter_mm: float
    height_mm: float
    volume_mL: float

    def __init__(
        self,
        name: str,
        well: protocol_api.labware.Well,
        initial_volume_mL: float,
        inner_diameter_mm: float = 18,  # this matches for glass vial of 5 mL
    ):
        self.name = name
        self.well = well

        self.inner_diameter_mm = inner_diameter_mm
        self.volume_mL = initial_volume_mL
        self.initial_height_mm = self.update_liquid_height()
        self.height_mm = self.initial_height_mm

        atexit.register(self.print_heights)

    def aspirate(self, volume: float) -> Location:
        """
        Withdraw liquid from the vial.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL -= volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def dispense(self, volume: float) -> Location:
        """
        Add liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL += volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def update_liquid_height(self):
        """
        Calculate the height of the liquid in the vessel.

        Args:
            None
        Returns:
            heigth_mm: float
        """
        self.height_mm = (
            1e3 * (self.volume_mL) / (np.pi * (self.inner_diameter_mm / 2) ** 2)
        )
        return self.height_mm - 1

    def print_heights(self):
        print(f"{self.name} has a initial height of {self.initial_height_mm:.2f} mm")
        print(f"{self.name} has a final height of {self.height_mm:.2f} mm")
        print(f"{self.name} has a volume of {self.volume_mL} mL")

    def __str__(self):
        output_str = f"""
        Tube object
        Name: {self.name}
        Inner diameter: {self.inner_diameter_mm} mm
        Well: {self.well}
        Initial height: {self.initial_height_mm} mm
        Current height: {self.height_mm} mm
        Current volume: {self.volume_mL} mL
        """
        return output_str


class FalconTube50:
    """
    Container for sample tube data.

    Falcon tube FT50

    Accurate till 5 mL
    """

    name: str
    well: protocol_api.labware.Well
    initial_height_mm: float
    height_mm: float
    inner_diameter_mm: float
    height_mm: float
    volume_mL: float

    def __init__(
        self,
        name: str,
        well: protocol_api.labware.Well,
        initial_volume_mL: float,
        inner_diameter_mm: float = 28,  # this matches for falcon tube of 50 mL
    ):
        self.name = name
        self.well = well

        # due to the v-bottom of FT50 --> 5 mL is ca. 21 mm
        self.dead_volume_mL = 5
        self.dispense_bottom_out_mm = 21
        self.inner_diameter_mm = inner_diameter_mm

        self.volume_mL = initial_volume_mL
        self.initial_height_mm = self.update_liquid_height()
        self.height_mm = self.initial_height_mm

        atexit.register(self.print_heights)

    def aspirate(self, volume: float) -> Location:
        """
        Withdraw liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL -= volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def dispense(self, volume: float) -> Location:
        """
        Add liquid from the container.

        Args:
            volume: float
                Volume is presumed to be in μl.
        Returns:
            opentrons.types.Location
        """

        self.volume_mL += volume * 1e-3
        self.update_liquid_height()
        return self.well.bottom(self.height_mm)

    def update_liquid_height(self):
        """
        Calculate the height of the liquid in the vessel.

        Args:
            None
        Returns:
            None
        """
        self.height_mm = (
            (self.volume_mL - self.dead_volume_mL)
            * 1e3
            / (np.pi * (self.inner_diameter_mm / 2) ** 2)
        ) + self.dispense_bottom_out_mm
        return self.height_mm

    def print_heights(self):
        print(f"{self.name} has a initial height of {self.initial_height_mm}")
        print(f"{self.name} has a final height of {self.height_mm}")
        print(f"{self.name} has a volume of {self.volume_mL+self.dead_volume_mL} mL")

    def __str__(self):
        output_str = f"""
        Tube object
        Name: {self.name}
        Inner diameter: {self.inner_diameter_mm} mm
        Well: {self.well}
        Initial height: {self.initial_height_mm} mm
        Current height: {self.height_mm} mm
        Current volume: {self.volume_mL} mL
        """
        return output_str
