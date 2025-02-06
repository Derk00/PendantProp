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
    def __init__(self, width=640, height=480, fps=60):
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.camera.set(cv2.CAP_PROP_FPS, fps)

        if not self.camera.isOpened():
            raise Exception("Error: Could not open camera.")

        self.current_frame = None
        self.stop_background_threads = Event()

        # Start the frame capture thread
        self.thread = Thread(target=self.capture_frames, daemon=True)
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

    def __init__(self):

        try:
            # Camera settings
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice()
            )
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            self.stop_background_threads = Event()
            self.running = False
            self.streaming = False
            print("Camera: initialized")
        except:
            print(
                "Camera: Could not find pendant drop camera. Close camera software and check cables."
            )

        # this is to prevent racing conditions
        self.lock = threading.Lock()

        # Initialize attributes
        self.st_t = None  # Will hold time series data for surface tension
        self.current_image = None  # Latest image grabbed from the camera
        self.analysis_image = None  # Latest processed (analyzed) image
        self.plot_image = None  # Latest plot image (as JPEG bytes)
        self.thread = None  # For streaming
        self.process_thread = None  # Combined thread for save, analyze, and plot
        self.well_id = None

    def initialize_measurement(self, well_id: str):
        self.settings = load_settings()
        self.experiment_name = self.settings["EXPERIMENT_NAME"]
        self.save_dir = f"experiments/{self.experiment_name}/data"
        self.analyzer = PendantDropAnalysis()
        self.logger = Logger(
            name="pendant_drop_camera",
            file_path=f"experiments/{self.experiment_name}/meta_data",
        )
        self.well_id = well_id
        self.st_t = []  # List to store [time, surface tension] measurements
        self.logger.info(f"camera: updated well id to {self.well_id}")

    def start_stream(self):
        if not self.streaming:
            self.streaming = True
            self.thread = threading.Thread(target=self._stream, daemon=True)
            self.thread.start()

    def start_capture(self):
        if not self.running:
            self.start_time = datetime.now()
            self.running = True
            # Create and start one thread for saving, analyzing, and plotting
            self.process_thread = threading.Thread(
                target=self._process_thread, daemon=True
            )
            self.process_thread.start()

    def _stream(self):
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

    def _process_thread(self):
        """
        Combined thread function that:
          - Saves the current image (if available) every second,
          - Analyzes the image (if available) every loop iteration,
          - And updates the plot image (if enough data is collected).
        """
        # Use a timer to ensure saving happens roughly once per second
        last_save_time = time.time()
        window_size = 20  # Window size for smoothing in the plot

        while self.running:
            if self.current_image is not None:
                # Save image every ~1 second
                if time.time() - last_save_time >= 1.0:
                    self.save_image(self.current_image)
                    last_save_time = time.time()

                # Analyze the current image
                with self.lock:
                    self.analyze_image(self.current_image)

            # Generate/update the plot image if there are data points to plot
            if self.st_t is not None and len(self.st_t) > window_size:
                # Create the plot
                fig, ax = plt.subplots()
                t = [item[0] for item in self.st_t]
                st = [item[1] for item in self.st_t]

                t_smooth = np.convolve(t, np.ones(window_size), "valid") / window_size
                st_smooth = np.convolve(st, np.ones(window_size), "valid") / window_size

                ax.plot(t_smooth, st_smooth, lw=2, color="black")
                ax.set_xlim(0, t_smooth[-1] + 5)
                ax.set_ylim(20, 80)
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Surface Tension (mN/m)")
                ax.set_title(f"Well ID: {self.well_id}")
                ax.grid(axis="y")

                # Save the plot to a BytesIO buffer and update self.plot_image
                buf = BytesIO()
                plt.savefig(buf, format="png")
                plt.close(fig)
                buf.seek(0)
                # Convert the buffer to a NumPy array and then to a JPEG-encoded image
                image = np.asarray(bytearray(buf.read()), dtype=np.uint8)
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                ret, buffer = cv2.imencode(".jpg", image)
                if ret:
                    self.plot_image = buffer.tobytes()
            # Small sleep to yield control and reduce CPU usage
            time.sleep(0.1)

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
        if self.process_thread is not None:
            self.stop_background_threads.set()
            self.process_thread.join()

        # Reset the thread attribute so that capture can be restarted
        self.process_thread = None
        self.analysis_image = None
        self.current_image = None

    def stop_stream(self):
        self.streaming = False
        if self.thread is not None:
            self.stop_background_threads.set()
            self.thread.join()
        self.thread = None
        self.current_image = None

    def generate_frames(self):
        """
        Generator for streaming either the analyzed image (if available)
        or the raw current image.
        """
        while True:
            with self.lock:
                # Prioritize the analyzed image if available
                if self.analysis_image is not None:
                    image4feed = self.analysis_image
                else:
                    image4feed = self.current_image

            if image4feed is not None:
                ret, buffer = cv2.imencode(".jpg", image4feed)
                if ret:
                    frame = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    )
            else:
                time.sleep(0.05)

    def generate_plot_frame(self):
        """
        Generator for streaming the latest plot image.
        It yields the most recent JPEG-encoded plot (if available).
        """
        while not self.stop_background_threads.is_set():
            if self.plot_image is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + self.plot_image + b"\r\n"
                )
            else:
                time.sleep(0.1)

    def start_plot_frame_thread(self):
        self.plot_frame_thread = threading.Thread(target=self.generate_plot_frame)
        self.plot_frame_thread.daemon = True
        self.plot_frame_thread.start()

    def stop_plot_frame_thread(self):
        self.stop_background_threads.set()
        self.plot_frame_thread.join()

    def stop_measurement(self):
        if self.process_thread is not None:
            self.process_thread.join()

if __name__ == "__main__":
    pass
