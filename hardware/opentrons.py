import requests
import json
from server.utils import load_settings


class Opentrons_API:

    def __init__(self):
        settings = load_settings()
        self.robot_ip = settings["ROBOT_IP"]
        self.headers = {"opentrons-version": "3"}
        self.protocol_file = f'protocols/{settings["PROTOCOL_FILE"]}'
        self.data_file = None
        self.protocol_id = None
        self.run_id = None

    def upload_protocol(self):
        protocols_url = f"http://{self.robot_ip}:31950/protocols"
        with open(self.protocol_file, "rb") as protocol_file_payload:
            r = requests.post(
                url=protocols_url,
                headers=self.headers,
                files={"files": protocol_file_payload},
            )
        try:
            r_dict = json.loads(r.text)
            self.protocol_id = r_dict["data"]["id"]
            print(f"Protocol ID:\n{self.protocol_id}")
            return self.protocol_id
        except:
            #TODO log it in the output
            pass

    def upload_data(self):
        protocols_url = f"http://{self.robot_ip}:31950/protocols"
        with open(self.data_file) as data_file_payload:
            r = requests.post(
                url=protocols_url,
                headers=self.headers,
                files={"supportfiles": data_file_payload},
            )
            print(f"Request status:\n{r}\n{r.text}")

    def create_run_from_protocol(self):
        runs_url = f"http://{self.robot_ip}:31950/runs"
        protocol_id_payload = json.dumps({"data": {"protocolId": self.protocol_id}})
        r = requests.post(url=runs_url, headers=self.headers, data=protocol_id_payload)
        r_dict = json.loads(r.text)
        self.run_id = r_dict["data"]["id"]
        print(f"Run ID:\n{self.run_id}")
        return self.run_id

    def run_protocol(self):
        runs_url = f"http://{self.robot_ip}:31950/runs"
        actions_url = f"{runs_url}/{self.run_id}/actions"
        action_payload = json.dumps({"data": {"actionType": "play"}})
        r = requests.post(url=actions_url, headers=self.headers, data=action_payload)
        print(f"Request status:\n{r}\n{r.text}")

#TODO this as a method in the class
def run_opentron_protocol():
    api = Opentrons_API()
    api.upload_protocol()
    api.create_run_from_protocol()
    api.run_protocol()

