import os

def measure_well(start_well:str, end_well:str):
    print(f"Measuring well from {start_well} to {end_well}")

def save_csv_file(exp_name:str, csv_file, app):
    exp_dir = os.path.join(app.config["UPLOAD_FOLDER"], exp_name)
    os.makedirs(exp_dir, exist_ok=True)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)
