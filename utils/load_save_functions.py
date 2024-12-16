import os
import json


def save_csv_file(exp_name: str, subdir_name: str, csv_file, app):
    """
    Save csv file in experiment directory

    :param exp_name: Experiment name
    :param subdir_name: Subdirectory name (meta_data, experiment_data, etc)
    :param csv_file: File to save
    :param app: Flask app

    :return: None
    """

    exp_dir = os.path.join(app.config["UPLOAD_FOLDER"], f"{exp_name}\{subdir_name}")
    os.makedirs(exp_dir, exist_ok=True)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)



def load_settings(file_name="settings.json"):
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            return json.load(file)
    return {}


def save_settings(settings, file_name="settings.json"):
    with open(file_name, "w") as file:
        json.dump(settings, file, indent=4)


if __name__ == "__main__":
    settings = load_settings()
    print(settings)
