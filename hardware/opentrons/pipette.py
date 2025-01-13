from utils.logger import Logger
from utils.load_save_functions import load_settings
from hardware.opentrons.containers import *
from hardware.opentrons.http_communications import Opentrons_http_api


class Pipette:
    def __init__(
        self,
        http_api: Opentrons_http_api,
        mount: str,
        pipette_name: str,
        pipette_id: str,
        tips_info: dict,
    ):
        settings = load_settings()
        self.api = http_api
        self.MOUNT = mount
        self.PIPETTE_NAME = pipette_name
        self.PIPETTE_ID = pipette_id
        self.TIPS_INFO = tips_info
        self.TIPS_ID = tips_info["labware_id"]
        self.has_tip = False
        self.volume = 0
        self.current_solution = None
        self.clean = True  # boolean to check if tip is clean
        self.protocol_logger = Logger(
            name="protocol",
            file_path=f'experiments/{settings["EXPERIMENT_NAME"]}/meta_data',
        )

        # warning if no tips id is provided
        if self.TIPS_INFO == None:
            self.protocol_logger.warning("No tips information provided for pipette!")

        # set max volume
        if self.PIPETTE_NAME == "p20_single_gen2":
            self.MAX_VOLUME = 20
            self.OFFSET = dict(x=-1.2, y=0.6, z=0)  # TODO settings?

        elif self.PIPETTE_NAME == "p1000_single_gen2":
            self.MAX_VOLUME = 1000
            self.OFFSET = dict(x=-0.4, y=1, z=0)  # TODO settings?

        else:
            self.protocol_logger.error("Pipette name not recognised!")

        self.ORDERING = tips_info["ordering"]
        self.well_index = 0

    def pick_up_tip(self, well=None):
        if self.has_tip:
            self.protocol_logger.error(
                f"Could not pick up tip as {self.MOUNT} pipette ({self.PIPETTE_NAME}) already has one!"
            )
            return

        if well == None:
            well = self.ORDERING[self.well_index]

        if well not in self.ORDERING:
            self.protocol_logger.error(f"well {well} out of index for tip rack")

        self.api.pick_up_tip(
            pipette_id=self.PIPETTE_ID,
            labware_id=self.TIPS_ID,
            well=well,
            offset=self.OFFSET,
        )
        self.has_tip = True
        self.well_index += 1
        self.protocol_logger.info(
            f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) picked up tip from well {self.ORDERING[self.well_index - 1]} on {self.TIPS_INFO['labware_name']}."
        )

    def drop_tip(self, return_tip=False):
        if not self.has_tip:
            self.protocol_logger.error("Pipette does not have a tip to drop!")
            return

        if return_tip:
            self.api.drop_tip(
                pipette_id=self.PIPETTE_ID,
                labware_id=self.TIPS_ID,
                well=self.ORDERING[self.well_index - 1],
                offset=self.OFFSET,
            )
            self.protocol_logger.info(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) returned tip to well {self.ORDERING[self.well_index - 1]} on {self.TIPS_INFO['labware_name']}."
            )
        else:
            self.api.drop_tip(pipette_id=self.PIPETTE_ID)
            self.protocol_logger.info(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) dropped tip into trash."
            )
        self.has_tip = False

    def aspirate(self, volume: float, source: Container, touch_tip=False):

        # check if pipette has tip
        if not self.has_tip:
            self.protocol_logger.error(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) does not have a tip! Cancelled aspirating step."
            )
            return

        # check if volume exceeds pipette capacity
        if self.volume + volume > self.MAX_VOLUME:
            self.protocol_logger.error(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) does not have enough free volume to aspirate {volume} uL! Cancelled aspirating step."
            )
            return

        if self.clean == False:
            self.protocol_logger.warning(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) is not clean! Aspirating anyway..."
            )

        self.api.aspirate(
            pipette_id=self.PIPETTE_ID,
            labware_id=source.LABWARE_ID,
            well=source.WELL,
            volume=volume,
            depth=source.height_mm - source.DEPTH,
            offset=self.OFFSET,
        )
        if touch_tip:
            self.touch_tip(container=source)

        # update information:
        source.aspirate(volume)
        self.current_solution = source.solution_name
        self.clean = False
        self.volume += volume
        self.protocol_logger.info(
            f"Aspirated {volume} uL from {source.solution_name} (well {source.WELL } on {source.LABWARE_NAME}) with {self.MOUNT} pipette ({self.PIPETTE_NAME})"
        )

    def dispense(
        self, volume: float, source: Container, destination: Container, touch_tip=False
    ):
        if not self.has_tip:
            self.protocol_logger.error(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) does not have a tip! Cancelled dispensing step."
            )
            return

        if self.volume - volume < 0:
            self.protocol_logger.error(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) does not have enough volume to dispense {volume} uL! Cancelled dispensing step."
            )
            return
        self.api.dispense(
            pipette_id=self.PIPETTE_ID,
            labware_id=destination.LABWARE_ID,
            well=destination.WELL,
            volume=volume,
            depth=destination.height_mm - destination.DEPTH,
            offset=self.OFFSET,
        )
        if touch_tip:
            self.touch_tip(container=destination)

        # update information
        self.volume -= volume
        destination.dispense(volume=volume, source=source)
        self.protocol_logger.info(
            f"Dispensed {volume} uL into well {destination.WELL_ID} with {self.MOUNT} pipette ({self.PIPETTE_NAME})"
        )

    def transfer(
        self, volume: float, source: Container, destination: Container, touch_tip=False
    ):
        self.protocol_logger.info(
            f"Transferring {volume} uL from {source.solution_name} (well {source.WELL} on {source.LABWARE_NAME}) to well {destination.WELL} on {destination.LABWARE_NAME} with {self.MOUNT} pipette ({self.PIPETTE_NAME})"
        )
        self.aspirate(volume=volume, source=source, touch_tip=touch_tip)
        self.dispense(
            volume=volume, source=source, destination=destination, touch_tip=touch_tip
        )

    def move_to_well(self, container: Container):
        self.api.move_to_well(
            pipette_id=self.PIPETTE_ID,
            labware_id=container.LABWARE_ID,
            well=container.WELL,
            offset=self.OFFSET,
        )

    def move_to_tip(self, well: str, offset: dict = dict(x=0, y=0, z=0)):
        # This is used to check offset of pipettes!!
        self.api.move_to_well(
            pipette_id=self.PIPETTE_ID,
            labware_id=self.TIPS_ID,
            well=well,
            offset=offset,
        )

    def touch_tip(self, container: Container, repeat=1):
        if not self.has_tip:
            self.protocol_logger.error("no tip attached to perform touch_tip!")
            return
        depth = (
            0.05 * container.DEPTH
        )  # little depth to ensure the tip touches the wall of the container
        initial_offset = self.OFFSET.copy()
        initial_offset["z"] -= 0.05 * container.DEPTH
        self.api.move_to_well(
            pipette_id=self.PIPETTE_ID,
            labware_id=container.LABWARE_ID,
            well=container.WELL,
            offset=initial_offset,
        )
        radius = container.WELL_DIAMETER / 2
        radius = radius * 0.9  # safety TODO fix
        for n in range(repeat):
            for i in range(4):
                offset = (
                    self.OFFSET.copy()
                )  # Create a copy of the offset to avoid modifying the original
                offset["z"] -= depth
                if i == 0:
                    offset["x"] -= radius
                elif i == 1:
                    offset["x"] += radius
                elif i == 2:
                    offset["y"] -= radius
                elif i == 3:
                    offset["y"] += radius
                self.api.move_to_well(
                    pipette_id=self.PIPETTE_ID,
                    labware_id=container.LABWARE_ID,
                    well=container.WELL,
                    offset=offset,
                    speed=50,
                )
                self.api.move_to_well(
                    pipette_id=self.PIPETTE_ID,
                    labware_id=container.LABWARE_ID,
                    well=container.WELL,
                    offset=initial_offset,
                    speed=50,
                )

        self.protocol_logger.info(f"touched tip, repeated {repeat} times")

    # def touch_tip(self, container: Container):
    #     self.api.move_xyz

    def __str__(self):
        return f"""
        Pipette object

        Mount: {self.MOUNT}
        Pipette name: {self.PIPETTE_NAME}
        Pipette ID: {self.PIPETTE_ID}
        Tips ID: {self.TIPS_ID}
        Has tip: {self.has_tip}
        Current volume: {self.volume} uL
        Current solution: {self.current_solution}
        Clean: {self.clean}
        Tip well index: {self.ORDERING[self.well_index]}
        """
