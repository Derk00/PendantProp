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
    def notify_server(status):
        SERVER_IP = "192.168.0.73:5000"
        url = f"http://{SERVER_IP}/status"
        r = requests.post(url, json={"status": status})

    # import custom opentrons functions

    # from load_functions import add_2_numbers

    try:
        from load_functions import (
            load_labware_from_csv,
            load_containers,
            load_pipette,
            add_2_numbers,
        )  # no clue why this is not working. Maybe it needs to be deleleted and re-upload?

        notify_server(status="Loaded load functions")
    except ImportError:
        notify_server(status="Error importing load functions")

    # load settings
    with open("/var/lib/jupyter/notebooks/settings.json", "r") as file:
        settings = json.load(file)

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
    # notify_server(status=f"addition: {c}")
