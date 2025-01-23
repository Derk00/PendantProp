import cv2
from pypylon import pylon
import threading
from threading import Thread, Event
import time
import os
from datetime import datetime

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
        self.settings = load_settings()
        self.experiment_name = self.settings["EXPERIMENT_NAME"]
        self.save_dir = f"experiments/{self.experiment_name}/data"
        self.logger = Logger(
            name="pendant_drop_camera",
            file_path=f"experiments/{self.experiment_name}/meta_data",
        )
        self.analysis_pipeline = PendantDropAnalysis()

        try:
            # Camera settings
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice()
            )
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            self.running = False
            self.logger.info("Camera: initialized")
        except:
            self.logger.error("Camera: Could not find pendant drop camera. Close camera software and check cables.")

        # this is to prevent racing conditions
        self.save_thread = threading.Thread(target=self._save_current_image)
        self.analyze_thread = threading.Thread(target=self._analyze_current_image)
        self.lock = (threading.Lock())

        # initialize some empty attributes
        self.current_image = None
        self.image4feed = None
        self.save_thread = None
        self.analyze_thread = None
        self.thread = None
        self.ST = None
        self.well_id = None

    def initialize_measurement(self, well_id: str):
        self.well_id = well_id
        self.ST = [0]
        self.logger.info(f"camera: updated well id to {self.well_id}")

    def start_capture(self):
        if not self.running:
            self.running = True
            # Create new thread instances every time start_capture is called
            self.thread = threading.Thread(target=self._capture)
            self.save_thread = threading.Thread(target=self._save_current_image)
            self.analyze_thread = threading.Thread(target=self._analyze_current_image)
            # Start the new threads
            self.thread.start()
            self.save_thread.start()
            self.analyze_thread.start()        

    def _capture(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while self.running and self.camera.IsGrabbing():
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
            # ? here we can also store st?

    def _analyze_current_image(self):
        while self.running:
            if self.current_image is not None:
                self.analyze_image(self.current_image)

    def save_image(self, img):
        filepath = f"{self.save_dir}/{self.well_id}"
        filename = os.path.join(
            filepath, f"{self.ST[-1]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        )
        cv2.imwrite(filename, img)

    def analyze_image(self, img):
        try:
            st, analysis_image = self.analysis_pipeline(img)
            self.ST.append(st)
            self.image4feed = analysis_image
        except:
            self.image4feed = img

    def stop_capture(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        if self.save_thread is not None:
            self.save_thread.join()
        if self.analyze_thread is not None:
            self.analyze_thread.join()
        
        # Reset the thread attributes to None to ensure they are recreated in the next start_capture call
        self.thread = None
        self.save_thread = None
        self.analyze_thread = None
    
    def generate_frames(self):
        while True:
            with self.lock:
                image4feed = self.image4feed
            if image4feed is not None:
                ret, buffer = cv2.imencode(".jpg", image4feed)
                frame = buffer.tobytes()
                yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            else:
                pass


if __name__ == "__main__":
    pendant_drop_camera = PendantDropCamera()
