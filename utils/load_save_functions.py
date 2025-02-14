import os
import json
import csv
import subprocess

def save_csv_file(exp_name: str, subdir_name: str, csv_file, app):
    """
    Save csv file in experiment directory

    :param exp_name: Experiment name
    :param subdir_name: Subdirectory name (meta_data, experiment_data, etc)
    :param csv_file: File to save
    :param app: Flask app

    :return: None
    """

    exp_dir = os.path.join(app.config["UPLOAD_FOLDER"], f"{exp_name}/{subdir_name}") #TODO check
    os.makedirs(exp_dir, exist_ok=True)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)


def load_settings(file_name="settings.json"):
    """
    Load settings from json file

    :param file_name: File name to load settings from
    """
    file_path = f"settings/{file_name}"
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)


def save_settings(settings, file_name="settings.json"):
    """
    Save settings to json file

    :param settings: Settings to save
    :param file_name: File name to save settings to
    """
    file_path = f"settings/{file_name}"
    with open(file_path, "w") as file:
        json.dump(settings, file, indent=4)

def save_settings_meta_data(settings: dict):
    file_path = f"experiments/{settings['EXPERIMENT_NAME']}/meta_data/settings.json"
    with open(file_path, "w") as file:
        json.dump(settings, file, indent=4)


def save_instances_to_csv(instances, filename):
    # Get the attribute names from the first instance
    fieldnames = [attr for attr in vars(instances[0])]

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data rows
        for instance in instances:
            writer.writerow(vars(instance))


def load_commit_hash():
    try:
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .strip()
            .decode("utf-8")
        )
        return commit_hash
    except subprocess.CalledProcessError:
        return None


if __name__ == "__main__":
    settings = load_settings()
    print(settings)
