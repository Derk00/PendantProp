# TODO list
# documentation
# move to / blowout / touch_tip?
# lights
# remove redunant methods?

import requests
import json
from utils.load_save_functions import load_settings


class Opentrons_http_api:
    def __init__(self):
        settings = load_settings()
        self.ROBOT_IP_ADDRESS = settings["ROBOT_IP"]
        self.LABWARE_DEFINITIONS_FOLDER = "labware\definitions"
        self.HEADERS = {"opentrons-version": "3"}
        self.PROTOCOL_ID = None
        self.RUN_ID = None
        self.COMMANDS_URL = None

    ####### protocol management #######
    def upload_protocol(self, protocol: str):
        """
        Method to upload protocol + help files (.py, .json, .csv)

        :param protocol: string, path to protocol file
        :param files: list, array of support files path
        """
        print("\n trying to upload protocol file \n")
        url = f"http://{self.ROBOT_IP_ADDRESS}:31950/protocols"
        files = {"files": (protocol, open(f"{protocol}", "rb"))}

        try:
            response = requests.post(url, headers=self.HEADERS, files=files)
            print(f"response code: {response.status_code}")
            if response.status_code == 201:
                print("Protocol uploaded successfully!")
                # print("Response:", response.json())
                self.PROTOCOL_ID = response.json()["data"]["id"]
                print(f"protocol ID: {self.PROTOCOL_ID}")
            elif response.status_code == 200:
                print("Protocol exist already.")
                self.PROTOCOL_ID = response.json()["data"]["id"]
                print(f"protocol ID: {self.PROTOCOL_ID}")
            else:
                print("Failed to upload protocol.")
                print("Response:", response.json())
        finally:
            for key, file_obj in files.items():
                file_obj[1].close()

    def delete_protocol(self):
        """
        Method to delete protocol, given the protocol ID (attribute of API instance).
        """
        print("\n trying to delete protocol \n")
        url = f"http://{self.ROBOT_IP_ADDRESS}:31950/protocols/{self.PROTOCOL_ID}"
        response = requests.delete(url, headers=self.HEADERS)

        print(f"Response code: {response.status_code}")
        if response.status_code == 200:
            print("Protocol deleted successfully!")
        elif response.status_code == 404:
            print("Protocol not found.")
        else:
            print("Failed to delete protocol.")
            print("Response:", response.json())

    def create_run(self):
        """
        Method to create a session. Uses the protocol_ID attribute to find the protocol
        """
        print("\n trying to create a run \n")
        url = f"http://{self.ROBOT_IP_ADDRESS}:31950/runs"
        protocol_id_payload = json.dumps({"data": {"protocolId": self.PROTOCOL_ID}})
        response = requests.post(
            url=url, headers=self.HEADERS, data=protocol_id_payload
        )
        print(f"status code: {response.status_code}")
        try:
            self.RUN_ID = response.json()["data"]["id"]
            self.COMMANDS_URL = (
                f"http://{self.ROBOT_IP_ADDRESS}:31950/runs/{self.RUN_ID}/commands"
            )
            print("Run created succesfully!")
            print(f"run ID: {self.RUN_ID}")
        except:
            print("Failed to create run!")
            print(response.text)

    def delete_run(self):
        "Method to delete the created run in the API instance."

        url = f"http://{self.ROBOT_IP_ADDRESS}:31950/runs/{self.RUN_ID}"
        response = requests.delete(url=url, headers=self.HEADERS)

        print(f"Response code: {response.status_code}")
        if response.status_code == 200:
            print("Run deleted successfully!")
        elif response.status_code == 404:
            print("Run not found.")
        else:
            print("Failed to delete run.")
            print("Response:", response.json())

    def play_run(self):
        print("playing run..")
        runs_url = f"http://{self.ROBOT_IP_ADDRESS}:31950/runs"
        actions_url = f"{runs_url}/{self.RUN_ID}/actions"
        action_payload = json.dumps({"data": {"actionType": "play"}})
        response = requests.post(
            url=actions_url, headers=self.HEADERS, data=action_payload
        )
        print(f"\n Response code play run: {response.status_code}")

    def get_run_status(self):
        "\n get run status \n"
        url = f"http://{self.ROBOT_IP_ADDRESS}:31950/runs/{self.RUN_ID}"
        response = requests.get(url=url, headers=self.HEADERS)
        try:
            # print(response.json()["data"]["status"])
            return response.json()["data"]["status"]
        except:
            print("failed to get run details")
            print(response.text)

    def get_commands(self, cursor=0, pageLength=20):
        print("\n get command types \n")
        response = requests.get(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            params={
                "cursor": cursor,
                "pageLength": pageLength,
            },
        )
        try:
            print(response.json()["data"]["commandType"])
        except:
            print(response.text)

    ####### load functions #######
    def load_pipette(self, name: str, mount: str):
        """
        Loads pipette for a current run.
        """
        command_dict = {
            "data": {
                "commandType": "loadPipette",
                "params": {"pipetteName": name, "mount": mount},
                "intent": "setup",
            }
        }

        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )
        try:
            pipette_id = response.json()["data"]["result"]["pipetteId"]
        except:
            print(f"failed to load pipette {name}: \n{response.text}")
        return pipette_id

    def load_labware(self, labware_name: str, location: int, custom_labware=False):
        """
        loads labware for a current run.
        """
        if custom_labware == True:
            namespace = "custom_beta"  # TODO find this directory
        else:
            namespace = "opentrons"

        command_dict = {
            "data": {
                "commandType": "loadLabware",
                "params": {
                    "location": {"slotName": str(location)},
                    "loadName": labware_name,
                    "namespace": namespace,
                    "version": 1,
                },
                "intent": "setup",
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )
        try:
            labware_id = response.json()["data"]["result"]["labwareId"]
        except:
            print(
                f"failed to load labware {labware_name} on slot {location}. \n {response.text}"
            )
        return labware_id

    def get_loaded_labwares(self):
        """
        get loaded labwares
        """
        response = requests.get(
            url=f"http://{self.ROBOT_IP_ADDRESS}:31950/runs/{self.RUN_ID}/loaded_labware_definitions",
            headers=self.HEADERS,
        )
        return response.json()

    def add_labware_definition(self, labware_definition: str):
        labware_path = self.LABWARE_DEFINITIONS_FOLDER
        with open(f"{labware_path}\{labware_definition}", "rb") as file:
            command_payload = json.dumps({"data": json.load(file)})
        response = requests.post(
            url=f"http://{self.ROBOT_IP_ADDRESS}:31950/runs/{self.RUN_ID}/labware_definitions",
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )

    ####### executable functions #######
    def home(self):
        print("\n homing... \n")
        url = f"http://{self.ROBOT_IP_ADDRESS}:31950/robot/home"
        command_dict = {"target": "robot"}
        command_payload = json.dumps(command_dict)
        response = requests.post(url=url, headers=self.HEADERS, data=command_payload)

    def delay(self, seconds: float, minutes=0, message=None, intent="setup"):
        """
        delay
        """
        command_dict = {
            "data": {
                "commandType": "waitForDuration",
                "params": {"seconds": seconds, "minutes": minutes, "msg": message},
                "intent": intent,
            }
        }

        command_payload = json.dumps(command_dict)

        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )
        print(response.json())

    def pick_up_tip(
        self, tip_labware_id: str, tip_well_name: str, pipette_id: str, intent="setup"
    ):
        "picks up tip on specified pipette"
        command_dict = {
            "data": {
                "commandType": "pickUpTip",
                "params": {
                    "labwareId": tip_labware_id,
                    "wellName": tip_well_name,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {"x": 0, "y": 0, "z": 0},
                        "waitUntilComplete": True,
                    },
                    "pipetteId": pipette_id,
                },
                "intent": intent,
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )

    def drop_tip(
        self, pipette_id: str, labware_id="fixedTrash", well="A1", intent="setup"
    ):
        """
        drop tip of specified pipette
        """
        if labware_id == "fixedTrash":
            depth = 0
        else:
            depth = -50
        command_dict = {
            "data": {
                "commandType": "dropTip",
                "params": {
                    "labwareId": labware_id,
                    "wellName": well,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {"x": 0, "y": 0, "z": depth},
                        "waitUntilComplete": True,
                    },
                    "pipetteId": pipette_id,
                },
                "intent": intent,
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )
        print(response.json())

    def aspirate(
        self,
        pipette_id: str,
        labware_id: str,
        volume: int,
        well: str,
        depth=-5,
        flow_rate=100,
        intent="setup",
    ):
        """
        aspirate
        """
        command_dict = {
            "data": {
                "commandType": "aspirate",
                "params": {
                    "labwareId": labware_id,
                    "wellName": well,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {"x": 0, "y": 0, "z": depth},
                    },
                    "flowRate": flow_rate,
                    "volume": volume,
                    "pipetteId": pipette_id,
                },
                "intent": intent,
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )

    def dispense(
        self,
        pipette_id: str,
        labware_id: str,
        volume: int,
        well: str,
        depth=-5,
        flow_rate=100,
        intent="setup",
    ):
        """
        dispense
        """
        command_dict = {
            "data": {
                "commandType": "dispense",
                "params": {
                    "labwareId": labware_id,
                    "wellName": well,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {"x": 0, "y": 0, "z": depth},
                    },
                    "flowRate": flow_rate,
                    "volume": volume,
                    "pipetteId": pipette_id,
                },
                "intent": intent,
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )

    def blow_out(
        self,
        pipette_id: str,
        labware_id: str,
        well: str,
        depth: float,
        flow_rate=30,
        intent="setup",
    ):
        command_dict = {
            "data": {
                "commandType": "blowout",
                "params": {
                    "labwareId": labware_id,
                    "wellName": well,
                    "wellLocation": {
                        "origin": "top",
                        "offset": {"x": 0, "y": 0, "z": depth},
                    },
                    "flowRate": flow_rate,
                    "pipetteId": pipette_id,
                },
                "intent": intent,
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )

    def move_to_well(
        self, pipette_id: str, labware_id: str, well: str, offset: dict, intent="setup"
    ):
        """
        move to
        """
        command_dict = {
            "data": {
                "commandType": "moveToWell",
                "params": {
                    "labwareId": labware_id,
                    "wellName": well,
                    "wellLocation": {"origin": "top", "offset": offset},
                    "pipetteId": pipette_id,
                },
                "intent": intent,
            }
        }
        command_payload = json.dumps(command_dict)
        response = requests.post(
            url=self.COMMANDS_URL,
            headers=self.HEADERS,
            data=command_payload,
            params={"waitUntilComplete": True},
        )


if __name__ == "__main__":
    pass
