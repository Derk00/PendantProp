from opentrons.execute import protocol_api
import pandas as pd
import requests
import sys
import json

import os

metadata = {
    "protocolName": "Formulate",
    "author": "Pim Dankloff",
    "description": "Formulate with csv",
    "apiLevel": "2.14",
}


def run(protocol: protocol_api.ProtocolContext):
    # load settings
    with open(
        "/var/lib/jupyter/notebooks/settings.json", "r"
    ) as file:  # NOTE if the upload folder of the settings changes, this path should be changed as well
        settings = json.load(file)

    upload_folder = settings.get("UPLOAD_FOLDER")
    sys.path.append(upload_folder)  # add upload folder to path

    def notify_server(status):
        SERVER_IP = "192.168.0.73:5000"
        url = f"http://{SERVER_IP}/status"
        r = requests.post(url, json={"status": status})

    # import custom opentrons functions
    try:
        from opentrons_functions import pick_up_tip

        notify_server(status="Loaded opentrons functions")
    except ImportError as e:
        notify_server(status=f"Error importing opentrons functions: {e}")

    # import load functions
    try:
        from load_functions2 import (
            load_labware_from_csv,
            load_containers,
            load_pipette,
        )

        notify_server(status="Loaded load functions")
    except ImportError as e:
        notify_server(status=f"Error importing load functions: {e}")

    # load labware
    try:
        # config_file_path = f"{upload_folder}/{settings.get('CONFIG_FILENAME')}"
        # df = pd.read_csv(config_file_path)
        labware = load_labware_from_csv(
            f"{settings.get('CONFIG_FILENAME')}",
            robot="OT-2",
            protocol=protocol,
        )
        notify_server(status=f"Loaded labware: \n {labware}")
    except Exception as e:
        notify_server(status=f"Error loading labware: {e}")

    # df = pd.read_csv("/var/lib/jupyter/notebooks/test.csv")  # parametrize?
    # notify_server(status=f"Loaded CSV: {df.head()}")
    layout_file = settings.get("CONFIG_FILENAME")
    # formulation_file = settings.get("FORMULATION_FILE")
    formulation_file = "formulation_file_Flex.csv"
    robot = "Flex"  # OT-2 or Flex
    api_level = "2.19"
    right_pipette = "P1000"
    left_pipette = "P50"  # P50 only for Flex

    # c = add(1, 2)
    notify_server(status="done")
