"""
Load functions for the complex mixture from csv script

TODO:
- error message in load functions
"""

__author__ = "Pim Dankloff"
__copyright__ = "Copyright 2024, Pim Dankloff"
__credits__ = ["Pim Dankloff"]
__license__ = "MIT"
__version__ = "1.0.3"
__maintainer__ = "Pim Dankloff"
__email__ = "pim.dankloff@ru.nl"
__status__ = "Production"

import numpy as np
import opentrons.system
import opentrons.types
import opentrons.util
import pandas as pd
import opentrons.execute
import opentrons.simulate
from containers import Eppendorf, FalconTube15, GlassVial, FalconTube50
import json
from pathlib import Path


def load_custom_labware(
    labware_type: str,
    location: int,
    protocol: opentrons.execute.protocol_api.ProtocolContext,
):
    """
    To simulate with custom labware, this function is utilized. file_path is the path to the custom labware JSON file.
    input:
        labware_type: str, name of the custom labware
        location: int, location on the deck
        protocol: opentrons.execute.protocol_api.ProtocolContext, protocol object from opentrons
    return:
        labware: labware object
    """
    root_dir = Path(__file__).parent.parent.parent
    file_path = root_dir / f"labware_definitions/{labware_type}.json"
    with open(file_path, "r", encoding="utf-8-sig") as labware_file:
        labware_def = json.load(labware_file)
    return protocol.load_labware_from_definition(labware_def, location)


def load_labware_from_csv(
    layout_file: str,
    simulation: bool,
    robot: str,
    protocol: opentrons.execute.protocol_api.ProtocolContext,
):
    """
    Load labware from a CSV file
    input:
        layout_file: str, path to CSV file
        simulation: bool, True if simulation, False if not
        protocol: opentrons.execute.protocol_api.ProtocolContext, protocol object from opentrons
    return:
        labware: dict, key is the labware name, value is the labware object
    """
    layout = pd.read_csv(layout_file)
    labware = dict()
    for position in layout["deck position"].unique():

        if robot == "OT-2":
            position = int(position)
        elif robot == "Flex":
            position = str(position)
        else:  # raise error if robot is not recognized
            raise ValueError("Robot type not recognized")

        labware_df = layout[layout["deck position"] == position]
        labware_file = labware_df["labware file"].values[0]
        labware_name = labware_df["labware name"].values[0]
        if labware_name == "trash":
            labware[labware_name] = protocol.load_trash_bin(location=position)
        else:
            if simulation:
                labware[labware_name] = load_custom_labware(
                    labware_file, position, protocol
                )
            else:
                labware[labware_name] = protocol.load_labware(labware_file, position)
    return labware


def load_containers(layout_file: str, labware: dict):
    """
    Load containers from a CSV file
    input:
        layout_file: str, path to CSV file
    return:
        containers: dict, key is the container name, value is the container object
    """
    containers = dict()
    layout = pd.read_csv(layout_file)
    for i, function in enumerate(layout["function"]):
        if function == "container":  # check if function is container
            name_solution = layout.loc[i, "solution"]
            well = layout.loc[i, "well"]
            if layout.loc[i, "labware name"] == "tube rack 15 mL":
                containers[name_solution] = FalconTube15(
                    name_solution,
                    labware["tube rack 15 mL"][well],
                    layout.loc[i, "initial volume (mL)"],
                )
            elif layout.loc[i, "labware name"] == "eppendorf rack":
                containers[name_solution] = Eppendorf(
                    name_solution,
                    labware["eppendorf rack"][well],
                    layout.loc[i, "initial volume (mL)"],
                )
            elif layout.loc[i, "labware name"] == "glass vial rack":
                containers[name_solution] = GlassVial(
                    name_solution,
                    labware["glass vial rack"][well],
                    layout.loc[i, "initial volume (mL)"],
                )
            elif layout.loc[i, "labware name"] == "tube rack 50 mL":
                containers[name_solution] = FalconTube50(
                    name_solution,
                    labware["tube rack 50 mL"][well],
                    layout.loc[i, "initial volume (mL)"],
                )

    return containers


def load_pipette(
    type: str,
    location: str,
    layout_file: str,
    labware: dict,
    robot: str,
    protocol: opentrons.execute.protocol_api.ProtocolContext,
):
    """
    Load tips from a CSV file
    input:
        type: str, type of pipette
            OT2: p20 or p1000
            FLEX: p50 or p1000
        location: str, location of the pipette (either left or right)
        layout_file: str
        labware: dict, key is the labware name, value is the labware object
        protocol: opentrons.execute.protocol_api.ProtocolContext, protocol object from opentrons
    return:
        pipette: pipette object from opentrons with tips information
    """
    layout = pd.read_csv(layout_file)
    tips = []
    for i, function in enumerate(layout["function"]):
        if function == "tips":  # check if function is tip
            tips_name = layout.loc[i, "labware name"]
            tips_name_truncated = tips_name[:-3]
            if tips_name_truncated == f"tips {type}":
                tips.append(labware[tips_name])
    if robot == "OT-2":
        pipette_name = f"{type}_single_gen2".lower()
    elif robot == "Flex":
        pipette_name = f"flex_1channel_{type[1:]}".lower()
    pipette = protocol.load_instrument(pipette_name, mount=location, tip_racks=tips)
    return pipette


def add_2_numbers(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    protocol = opentrons.simulate.get_protocol_api("2.19", robot_type="Flex")
    test_pipette = protocol.load_instrument(
        "flex_1channel_50", mount="left", tip_racks=[]
    )
    print(test_pipette.ti)
