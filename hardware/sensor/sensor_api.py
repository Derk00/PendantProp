import os
import pandas as pd


class SensorApi:
    def __init__(self):
        self.sensor_name = "test"  # TODO look up sensor name

    def capture_sensor_data(self):
        file_path = "hardware/sensor/sensor_data.txt"
        with open(file_path, "r") as file:
            data = file.read()

        # Replace double newlines with a unique separator
        data = data.replace("\n\n", "<NEW_ROW>")

        # Split the data into rows
        rows = data.split("<NEW_ROW>")

        # Create a DataFrame from the rows
        df = pd.DataFrame([row.split("\t") for row in rows])

        # Set the column names
        df.columns = ["date & time", "Temperature (C)", "Humidity (%)", "Pressure (Pa)"]

        # Retrieve the latest sensor data (second last row)
        last_sensor_data = df.iloc[-2].to_json()

        return last_sensor_data


if __name__ == "__main__":
    api = SensorApi()
    sensor_data = api.capture_sensor_data()
    print(sensor_data)
