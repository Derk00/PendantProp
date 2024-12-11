import os
import json


def save_csv_file(exp_name: str, csv_file, app):
    exp_dir = os.path.join(app.config["UPLOAD_FOLDER"], exp_name)
    os.makedirs(exp_dir, exist_ok=True)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)


SETTINGS_FILE = "settings.json"


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    return {}


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)


if __name__ == "__main__":
    settings = load_settings()
    print(settings)
