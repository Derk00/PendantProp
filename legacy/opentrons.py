import requests
import json
from utils.load_save_functions import load_settings
import subprocess


class Opentrons_API:

    def __init__(self):
        settings = load_settings()
        self.robot_ip = settings["ROBOT_IP"]
        self.experiment_name = settings["EXPERIMENT_NAME"]
        self.config_filename = settings["CONFIG_FILENAME"]
        self.upload_folder = settings["UPLOAD_FOLDER"]
        self.headers = {"opentrons-version": "3"}
        self.protocol_url = f"http://{self.robot_ip}:31950/protocols"
        self.ssh_key = "ot2_ssh_key"
        self.protocol_file = None
        self.data_file = None
        self.protocol_id = None
        self.run_id = None

    def upload_protocol(self, protocol_file):
        self.protocol_file = f"protocols/{protocol_file}"
        with open(self.protocol_file, "rb") as protocol_file_payload:
            r = requests.post(
                url=self.protocol_url,
                headers=self.headers,
                files={"files": protocol_file_payload},
            )
            r_dict = r.json()
            self.protocol_id = r_dict["data"]["id"]
            print(r)
            print(f"Protocol ID:\n{self.protocol_id}")

    def upload_file(self, source_path):
        command = f"scp -O -i {self.ssh_key} {source_path} root@{self.robot_ip}:{self.upload_folder}"
        subprocess.run(command, shell=True)

    def create_run_from_protocol(self):
        runs_url = f"http://{self.robot_ip}:31950/runs"
        protocol_id_payload = json.dumps({"data": {"protocolId": self.protocol_id}})
        try:
            r = requests.post(
                url=runs_url, headers=self.headers, data=protocol_id_payload
            )
            print(r)
            r_dict = json.loads(r.text)
            self.run_id = r_dict["data"]["id"]
            print(f"Run ID:\n{self.run_id}")
        except:
            print(f"Error creating run from protocol: {r.text}")
        return self.run_id

    def run_protocol(self):
        runs_url = f"http://{self.robot_ip}:31950/runs"
        actions_url = f"{runs_url}/{self.run_id}/actions"
        action_payload = json.dumps({"data": {"actionType": "play"}})
        r = requests.post(url=actions_url, headers=self.headers, data=action_payload)
        # print(f"Request status:\n{r}\n{r.text}")
        # print(f"Protocol {self.protocol_file} is running")

    def upload_functions(self):
        function_file = "utils/opentrons_functions.py"
        self.upload_file(source_path=function_file)

    def upload_settings(self):
        settings_file = "settings/settings.json"
        self.upload_file(source_path=settings_file)

    def upload_config(self):
        config_file = (
            f"experiments/{self.experiment_name}/meta_data/{self.config_filename}"
        )
        self.upload_file(source_path=config_file)

    def upload_containers(self):
        containers_file = "utils/containers.py"
        self.upload_file(source_path=containers_file)

    def delete_protocol(self):
        protocol_url = f"http://{self.robot_ip}:31950/protocols/{self.protocol_id}"
        r = requests.delete(url=protocol_url, headers=self.headers)
        print(f"Protocol {self.protocol_id} deleted")

    def calibration(self):
        protocol_file = "calibration.py"
        self.upload_protocol(protocol_file=protocol_file)
        self.create_run_from_protocol()
        self.run_protocol()
        self.delete_protocol()

    def formulate(self):
        print(
            f"uploading files for experiment {self.experiment_name} to folder {self.upload_folder}"
        )
        self.upload_settings()
        self.upload_config()
        self.upload_functions()
        self.upload_containers()
        load_functions_file = "utils/load_functions2.py"
        self.upload_file(source_path=load_functions_file)

        protocol_file = "formulate.py"
        self.upload_protocol(protocol_file=protocol_file)
        self.create_run_from_protocol()
        self.run_protocol()
        # self.delete_protocol()
        pass

    def measure_well(self):
        # TODO: implement this function
        pass

    def characterize(self):
        # TODO: implement this function
        pass


# TODO old code, maybe delete it later?

# def run_experiment(self, protocol_file, data_file=None):
#     self.upload_protocol(protocol_file=protocol_file)
#     if data_file:
#         self.upload_file(source_path=data_file)
#     self.create_run_from_protocol()
#     self.run_protocol()

# def get_protocol_list(self):
#     r = requests.get(url=self.protocol_url, headers=self.headers)
#     protocols = json.loads(r.text)
#     print("protocols:")
#     for protocol in protocols["data"]:
#         print(protocol)

# def get_data_list(self):
#     r = requests.get(url=self.data_url, headers=self.headers)
#     data_files = json.loads(r.text)
#     print("data files:")
#     for data_file in data_files["data"]:
#         print(data_file)

# def get_file_id(self, file_name):
#     r = requests.get(url=self.data_url, headers=self.headers)
#     data_files = json.loads(r.text)
#     for data_file in data_files["data"]:
#         if data_file["name"] == file_name:
#             return data_file["id"]

# def get_file(self, file_name):
#     file_id = self.get_file_id(file_name)
#     r = requests.get(url=f"{self.data_url}/{file_id}", headers=self.headers)
#     return r.text()

# def upload_data(self, data_file):
#     self.data_file = data_file
#     with open(self.data_file, "rb") as data_file_payload:
#         r = requests.post(
#             url=self.data_url,
#             headers=self.headers,
#             files={"file": data_file_payload},
#         )
#         # print(f"Request status:\n{r}\n{r.text}")
#         print(f"Data file {self.data_file} uploaded")
