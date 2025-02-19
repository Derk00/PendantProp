from utils.logger import Logger
from utils.load_save_functions import load_settings
from utils.search_containers import get_well_id
from hardware.opentrons.containers import *
from hardware.opentrons.http_communications import OpentronsAPI
from hardware.cameras import PendantDropCamera


class Pipette:
    def __init__(
        self,
        http_api: OpentronsAPI,
        mount: str,
        pipette_name: str,
        pipette_id: str,
        tips_info: dict,
        containers: dict,
    ):
        settings = load_settings()
        self.api = http_api
        self.MOUNT = mount
        self.PIPETTE_NAME = pipette_name
        self.PIPETTE_ID = pipette_id
        self.TIPS_INFO = tips_info
        self.TIPS_ID = tips_info["labware_id"]
        self.CONTAINERS = containers
        self.has_tip = False
        self.volume = 0
        self.current_solution = "empty"
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
        self.last_source = None
        self.last_destination = None
        self.air_gap_volume = 0


    def pick_up_tip(self, well=None):
        if self.has_tip:
            self.protocol_logger.error(
                f"Could not pick up tip as {self.MOUNT} pipette already has one!"
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
            f"{self.MOUNT} pipette picked up tip from well {self.ORDERING[self.well_index - 1]} on {self.TIPS_INFO['labware_name']}."
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
                f"{self.MOUNT} pipette returned tip to well {self.ORDERING[self.well_index - 1]} on {self.TIPS_INFO['labware_name']}."
            )
        else:
            self.api.drop_tip(pipette_id=self.PIPETTE_ID)
            self.protocol_logger.info(
                f"{self.MOUNT} pipette dropped tip into trash."
            )
        self.has_tip = False
        self.volume = 0
        self.current_solution = "empty"

    def aspirate(
        self,
        volume: float,
        source: Container,
        touch_tip=False,
        mix=None,
        depth_offset=0,
        flow_rate=100,
        log=True,
        update_info=True,
    ):

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

        if mix:
            mix_order = mix[0]
            if mix_order not in ["before", "after", "both"]:
                self.protocol_logger.warning(f"mix_order {mix_order} not recognized.")

        if mix and (mix_order == "before" or mix_order == "both"):
            self.mixing(container=source, mix=mix)

        self.api.aspirate(
            pipette_id=self.PIPETTE_ID,
            labware_id=source.LABWARE_ID,
            well=source.WELL,
            volume=volume,
            depth=source.height_mm - source.DEPTH + depth_offset,
            offset=self.OFFSET,
            flow_rate=flow_rate
        )
        if mix and (mix_order == "after" or mix_order == "both"):
            self.mixing(container=source, mix=mix)

        if touch_tip:
            self.touch_tip(container=source)
        
        self.last_source = source
        # update information:
        if update_info:
            source.aspirate(volume, log=log)
            if (
                self.current_solution != "empty"
                and self.current_solution != source.solution_name
            ):
                self.clean = False
            self.current_solution = source.solution_name
            self.volume += volume
            

        if log:
            self.protocol_logger.info(
                f"Aspirated {volume} uL from {source.WELL_ID} with {self.MOUNT} pipette."
            )

    def dispense(
        self,
        volume: float,
        destination: Container,
        touch_tip=False,
        mix=None,
        blow_out=False,
        depth_offset=0,
        flow_rate=100,
        log=True,
        update_info=True,
    ):
        if not self.has_tip:
            self.protocol_logger.error(
                f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) does not have a tip! Cancelled dispensing step."
            )
            return
        
        #TODO this gives a weird error with mixing
        # if self.volume - volume < 0:
        #     self.protocol_logger.error(
        #         f"{self.MOUNT} pipette ({self.PIPETTE_NAME}) does not have enough volume to dispense {volume} uL! Cancelled dispensing step."
        #     )
        #     return

        if mix:
            mix_order = mix[0]
            if mix_order not in ["before", "after", "both"]:
                self.protocol_logger.warning(f"mix_order {mix_order} not recognized.")

        if mix and (mix_order == "before" or mix_order == "both"):
            self.mixing(container=destination, mix=mix)

        self.api.dispense(
            pipette_id=self.PIPETTE_ID,
            labware_id=destination.LABWARE_ID,
            well=destination.WELL,
            volume=volume,
            depth=destination.height_mm - destination.DEPTH + depth_offset,
            offset=self.OFFSET,
            flow_rate=flow_rate,
        )
        if mix and (mix_order == "after" or mix_order == "both"):
            self.mixing(container=destination, mix=mix)
        if blow_out:
            self.blow_out(container=destination)
        if touch_tip:
            self.touch_tip(container=destination)

        self.last_destination = destination
        if update_info:
            self.volume -= volume
            destination.dispense(volume=volume, source=self.last_source, log=log)

        if log:
            self.protocol_logger.info(
                f"Dispensed {volume} uL into well {destination.WELL_ID} with {self.MOUNT} pipette."
            )

    def transfer(
        self,
        volume: float,
        source: Container,
        destination: Container,
        touch_tip=False,
        mix=None,
        blow_out=False,
    ):
        self.protocol_logger.info(
            f"Transferring {volume} uL from {source.WELL_ID} to well {destination.WELL_ID} with {self.MOUNT} pipette.)"
        )
        self.aspirate(volume=volume, source=source, touch_tip=touch_tip, mix=mix)
        self.dispense(
            volume=volume,
            destination=destination,
            touch_tip=touch_tip,
            mix=mix,
            blow_out=blow_out,
        )

    def move_to_well(self, container: Container, offset=None):
        if offset == None:
            offset_move = self.OFFSET.copy()
        else:
            offset_move = self.OFFSET.copy()
            for key in offset:
                offset_move[key] += offset[key]

        self.api.move_to_well(
            pipette_id=self.PIPETTE_ID,
            labware_id=container.LABWARE_ID,
            well=container.WELL,
            offset=offset_move,
        )

    def move_to_well_calibrate(self, well: str, offset: dict = dict(x=0, y=0, z=0)):
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
                    speed=30,
                )
                self.api.move_to_well(
                    pipette_id=self.PIPETTE_ID,
                    labware_id=container.LABWARE_ID,
                    well=container.WELL,
                    offset=initial_offset,
                    speed=30,
                )

        self.protocol_logger.info(f"touched tip, repeated {repeat} times")

    def mixing(self, container: Container, mix: any):
        mix_order, volume_mix, repeat_mix = mix
        for n in range(repeat_mix):
            self.aspirate(volume=volume_mix, source=container, log=False, update_info=False)
            self.dispense(volume=volume_mix, destination=container, log=False, update_info=False)
        self.protocol_logger.info(
            f"done with mixing in {container.WELL_ID} with order {mix_order}, with volume {volume_mix} uL, repeated {repeat_mix} times"
        )

    def blow_out(self, container: Container):
        self.api.blow_out(
            pipette_id=self.PIPETTE_ID,
            labware_id=container.LABWARE_ID,
            well=container.WELL,
            offset=self.OFFSET,
        )
        self.protocol_logger.info(f"blow out done in container {container.WELL_ID}")

    def air_gap(self, air_volume: float):
        if not self.has_tip:
            self.protocol_logger.error("no tip attached to perform air_gap!")
            return

        if air_volume + self.volume > self.MAX_VOLUME:
            self.protocol_logger.error("air gap exceeds pipette capacity!")
            return

        if self.last_source == None:
            self.protocol_logger.error(
                "no source location found, needed to perform air gap!"
            )
            return
        height_percentage = 0.05
        if self.last_source.CONTAINER_TYPE == "Plate Well":
            height_percentage = 1 # needed as plate height is standard 2 mm at the moment #TODO change?
        depth_offset = height_percentage * self.last_source.DEPTH + self.last_source.height_mm
        flow_rate = air_volume / 3
        self.aspirate(
            volume=air_volume,
            source=self.last_source,
            depth_offset=depth_offset,
            flow_rate=flow_rate,
            log=False,
            update_info=False,
        )
        self.air_gap_volume = air_volume
        self.protocol_logger.info(
            f"air gap of {air_volume} uL performed in {self.MOUNT} pipette."
        )

    def remove_air_gap(self, at_drop_stage: bool = False):
        if not self.has_tip:
            self.protocol_logger.error("no tip attached to remove air_gap!")
            return

        if at_drop_stage:
            container = self.CONTAINERS["drop_stage"]
        else:
            if self.last_destination is not None:
                container = self.last_destination
            elif self.last_source is not None:
                container = self.last_source
            else:
                self.protocol_logger.error(
                    "no source or destination location found, needed to remove air gap!"
                )
                return
        height_percentage = 0.05
        if container.CONTAINER_TYPE == "Plate Well":
            height_percentage = 1
        depth_offset = height_percentage * container.DEPTH + container.height_mm
        flow_rate = self.air_gap_volume / 3
        self.dispense(
            volume=self.air_gap_volume,
            destination=container,
            depth_offset=depth_offset,
            flow_rate=flow_rate,
            log=False,
            update_info=False,
        )
        self.protocol_logger.info(f"air gap of {self.air_gap_volume} uL removed in {self.MOUNT} pipette.")
        self.air_gap_volume = 0

    def clean_tip(self):
        if not self.has_tip:
            self.protocol_logger.error("no tip attached to clean tip!")
            return
        try:
            sponge = self.CONTAINERS["sponge"]
        except KeyError:
            self.protocol_logger.error("No sponge container found!")
            return

        self.api.move_to_well(
            pipette_id=self.PIPETTE_ID,
            labware_id=sponge.LABWARE_ID,
            well=sponge.well,
            offset=self.OFFSET,
        )
        for i in range(3):
            offset = self.OFFSET.copy()
            offset["z"] = -7
            self.api.move_to_well(
                pipette_id=self.PIPETTE_ID,
                labware_id=sponge.LABWARE_ID,
                well=sponge.well,
                offset=offset,
                speed=30,
            )
            self.api.move_to_well(
                pipette_id=self.PIPETTE_ID,
                labware_id=sponge.LABWARE_ID,
                well=sponge.well,
                offset=self.OFFSET,
                speed=30,
            )
        self.protocol_logger.info("pipette tip cleaned on sponge.")
        sponge.update_well()

    def measure_pendant_drop(
        self,
        source: Container,
        drop_volume: float,
        delay: float,
        flow_rate: float,
        pendant_drop_camera: PendantDropCamera,
        depth_offset: float = -23.4,
        calibrate = False
    ):
        if self.PIPETTE_NAME != "p20_single_gen2":
            self.protocol_logger.error(
                f"Wrong pipette is given. Expected p20_single_gen2 but got {self.PIPETTE_NAME}"
            )
            return
        self.protocol_logger.info(f"Start pendant drop measurement of {source.WELL_ID}, containing {source.concentration} mM {source.solution_name}")
        if self.has_tip == False:
            self.pick_up_tip()
        self.protocol_logger.info(f"Aspirating 15 uL from {source.WELL_ID}")
        self.aspirate(volume=15, source=source, flow_rate=flow_rate, mix=("before", 15, 5), update_info=False, log=False)
        self.air_gap(air_volume=5)
        self.clean_tip()
        self.remove_air_gap(at_drop_stage=True)
        pendant_drop_camera.initialize_measurement(well_id=source.WELL_ID)
        pendant_drop_camera.start_stream()
        self.dispense(
            volume=drop_volume,
            destination=self.CONTAINERS["drop_stage"],
            depth_offset=depth_offset,
            flow_rate=flow_rate,
            log=False,
            update_info=False
        )
        pendant_drop_camera.start_capture()
        self.api.delay(seconds=delay)
        pendant_drop_camera.stop_capture()
        pendant_drop_camera.stop_stream()
        self.aspirate(
            volume=drop_volume,
            source=self.CONTAINERS["drop_stage"],
            depth_offset=depth_offset,
            log=False,
            update_info=False
        )  # aspirate drop in tip
        self.protocol_logger.info("Re-aspirated the pendant drop into the tip.")
        self.dispense(volume=15, destination=source, update_info=False, log=False)  # return liquid to source
        self.protocol_logger.info("Returned volume in tip to source.")
        self.drop_tip()
        self.protocol_logger.info("Done with pendant drop measurement.")
        if calibrate:
            return pendant_drop_camera.scale_t
        else:
            return pendant_drop_camera.st_t

    def serial_dilution(self, row_id: str, solution_name: str, n_dilutions: int, well_volume: float):
        # find relevant well id's
        well_id_trash = get_well_id(containers=self.CONTAINERS, solution="trash") # well ID liquid waste
        well_id_water = get_well_id(containers=self.CONTAINERS, solution="water") # well ID water stock
        well_id_solution = get_well_id(containers=self.CONTAINERS, solution=solution_name)

        # log start of serial dilution
        self.protocol_logger.info(
            f"Start of serial dilution of {solution_name} in row {row_id}, with {n_dilutions} dilutions."
        )

        # pick up tip if pipette has no tip
        if self.has_tip == False:
            self.pick_up_tip()

        # adding water to all wells
        for i in range(n_dilutions):
            self.transfer(
                volume=well_volume,
                source=self.CONTAINERS[well_id_water],
                destination=self.CONTAINERS[f"{row_id}{i+1}"],
                touch_tip=True,
            )
        self.drop_tip()

        # adding surfactant to the first well
        self.pick_up_tip()
        self.aspirate(
            volume=well_volume, source=self.CONTAINERS[well_id_solution], touch_tip=True
        )
        self.dispense(
            volume=well_volume,
            destination=self.CONTAINERS[f"{row_id}1"],
            touch_tip=True,
            mix=("after", well_volume / 2, 5),
        )

        # serial dilution of surfactant
        for i in range(1, n_dilutions):
            self.aspirate(
                volume=well_volume, source=self.CONTAINERS[f"{row_id}{i}"], touch_tip=True
            )
            self.dispense(
                volume=well_volume,
                destination=self.CONTAINERS[f"{row_id}{i+1}"],
                touch_tip=True,
                mix=("after", well_volume / 2, 5),
            )

        # transfering half of the volume of the last well to trash to ensure equal volume in all wells
        self.aspirate(
            volume=well_volume,
            source=self.CONTAINERS[f"{row_id}{n_dilutions}"],
            touch_tip=True,
        )
        self.dispense(
            volume=well_volume, destination=self.CONTAINERS[well_id_trash], touch_tip=True, update_info=False
        )
        self.drop_tip()

        # log end of serial dilution
        self.protocol_logger.info("End of serial dilution.")

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
