import cv2
from pypylon import pylon
import threading
from threading import Thread, Event
import time
import os
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # Use the Agg backend for non-GUI rendering
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

from utils.load_save_functions import load_settings
from utils.logger import Logger
from analysis.image import PendantDropAnalysis

class OpentronCamera:
    def __init__(self, width=640, height=480, fps=30):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.camera.set(cv2.CAP_PROP_FPS, fps)

        if not self.camera.isOpened():
            raise Exception("Error: Could not open camera.")

        self.current_frame = None
        self.stop_background_threads = Event()

        # Start the frame capture thread
        self.thread = Thread(target=self.capture_frames)
        self.thread.daemon = True
        self.thread.start()

    def capture_frames(self):
        while not self.stop_background_threads.is_set():
            success, frame = self.camera.read()
            if success:
                self.current_frame = frame
            else:
                print("Error: Could not read frame.")

    def generate_frames(self):
        while True:
            if self.current_frame is not None:
                # Encode the frame in JPEG format
                ret, buffer = cv2.imencode(".jpg", self.current_frame)
                frame = buffer.tobytes()

                # Yield the frame in byte format
                yield (
                    b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )

    def stop(self):
        self.stop_background_threads.set()
        self.thread.join()
        self.camera.release()


class PendantDropCamera:
    # TODO: thread? save images

    def __init__(self):
        # Settings + Logger

        try:
            # Camera settings
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice()
            )
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            self.running = False
            self.streaming = False
            print("Camera: initialized")
        except:
            print("Camera: Could not find pendant drop camera. Close camera software and check cables.")

        # this is to prevent racing conditions
        self.save_thread = threading.Thread(target=self._save_current_image)
        self.analyze_thread = threading.Thread(target=self._analyze_current_image)
        self.lock = (threading.Lock())

        # initialize some empty attributes
        self.st_t = None
        self.current_image = None
        self.analysis_image = None
        self.save_thread = None
        self.analyze_thread = None
        self.thread = None
        self.well_id = None

    def init_logger(self):
        self.logger = Logger(
            name="pendant_drop_camera",
            file_path=f"experiments/{self.experiment_name}/meta_data",
        )

    def initialize_measurement(self, well_id: str):
        self.settings = load_settings()
        self.experiment_name = self.settings["EXPERIMENT_NAME"]
        self.save_dir = f"experiments/{self.experiment_name}/data"
        analyzer = PendantDropAnalysis()
        self.analyzer = analyzer
        self.init_logger()
        self.well_id = well_id
        self.st_t = []  # surface tension over time (s-1)
        self.logger.info(f"camera: updated well id to {self.well_id}")

    def start_stream(self):
        if not self.streaming:
            self.streaming = True
            self.thread = threading.Thread(target=self._capture)
            self.thread.start()

    def start_capture(self):
        if not self.running:
            self.start_time = datetime.now()
            self.running = True
            # Create new thread instances every time start_capture is called
            self.save_thread = threading.Thread(target=self._save_current_image)
            self.analyze_thread = threading.Thread(target=self._analyze_current_image)
            # Start the new threads
            self.save_thread.start()
            self.analyze_thread.start()        

    def _capture(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while self.streaming and self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )
            if grabResult.GrabSucceeded():
                image = self.converter.Convert(grabResult)
                self.current_image = image.GetArray()
                grabResult.Release()
        self.camera.StopGrabbing()

    def _save_current_image(self):
        while self.running:
            time.sleep(1)  # Ensure it runs every second
            if self.current_image is not None:
                self.save_image(self.current_image)

    def _analyze_current_image(self):
        while self.running:
            if self.current_image is not None:
                self.analyze_image(self.current_image)

    def save_image(self, img):
        directory = f"{self.save_dir}/{self.well_id}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/{timestamp}.png"
        cv2.imwrite(filename, img)

    def analyze_image(self, img):

        try:
            time_stamp = datetime.now()
            relative_time = (time_stamp - self.start_time).total_seconds()
            st, analysis_image = self.analyzer.image2st(img)
            self.st_t.append([relative_time, st])
            self.analysis_image = analysis_image
        except Exception as e:
            # self.logger.error(f"Camera: error {e}")
            self.analysis_image = None

    def stop_capture(self):
        self.running = False
        if self.save_thread is not None:
            self.save_thread.join()
        if self.analyze_thread is not None:
            self.analyze_thread.join()

        # Reset the thread attributes to None to ensure they are recreated in the next start_capture call
        self.save_thread = None
        self.analyze_thread = None
        self.analysis_image = None
        self.current_image = None

    def stop_stream(self):
        self.streaming = False
        if self.thread is not None:
            self.thread.join()
        self.thread = None
        self.current_image = None

    def generate_frames(self):
        while True:
            with self.lock:
                if self.thread == None:
                    image4feed = None
                elif self.save_thread != None:
                    image4feed = self.analysis_image
                else:
                    image4feed = self.current_image

            if image4feed is not None:
                ret, buffer = cv2.imencode(".jpg", image4feed)
                frame = buffer.tobytes()
                yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            else:
                pass

    def generate_plot_frame(self):
        # self.st_t = [[0, 72], [1, 51]]
        while True:
            if self.st_t is not None and len(self.st_t) > 0:
                # Create a plot
                plt.figure()
                t = [item[0] for item in self.st_t]
                st = [item[1] for item in self.st_t]
                plt.scatter(x=t, y=st, s=10)
                plt.title("Surface Tension over Time")
                plt.xlabel("Time")
                plt.ylabel("Surface Tension")

                # Save the plot to a BytesIO object
                buf = BytesIO()
                plt.savefig(buf, format="jpg")
                plt.close()
                buf.seek(0)

                # Convert the BytesIO object to a NumPy array
                image = np.asarray(bytearray(buf.read()), dtype=np.uint8)
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)

                # Encode the image as a JPEG
                ret, buffer = cv2.imencode(".jpg", image)
                frame = buffer.tobytes()
                yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            else:
                pass

    def start_plot_frame_thread(self):
        self.plot_thread = threading.Thread(target=self.generate_plot_frame)
        self.plot_thread.start()

    def print_active_threads(self):
        print(f"stream thread: {self.thread}")
        print(f"analyze thread: {self.analyze_thread}")

        # Get a list of all active threads
        active_threads = threading.enumerate()

        # Print the name of each active thread
        print("Active threads:")
        for thread in active_threads:
            print(f"- {thread.name}")


if __name__ == "__main__":
    pass
