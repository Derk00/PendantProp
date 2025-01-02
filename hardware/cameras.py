import cv2
from threading import Thread, Event
from pypylon import pylon


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
        try:
            self.camera = pylon.InstantCamera(
                pylon.TlFactory.GetInstance().CreateFirstDevice()
            )
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            self.running = False
        except:
            print("Error: Could not open camera.")

    def capture_frames(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        while self.running:
            grabResult = self.camera.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )
            if grabResult.GrabSucceeded():
                image = self.converter.Convert(grabResult)
                frame = image.GetArray()
                grabResult.Release()
                yield frame
        self.camera.StopGrabbing()

    def generate_frames(self):
        self.running = True
        for frame in self.capture_frames():
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    def stop(self):
        self.running = False
        self.camera.Close()


if __name__ == "__main__":
    pendant_drop_camera = PendantDropCamera()
