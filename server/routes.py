import os
import threading
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Response,
    jsonify,
)

from utils.load_save_functions import (
    save_csv_file,
    load_settings,
    save_settings,
    save_settings_meta_data,
    load_commit_hash
)
from hardware.cameras import OpentronCamera, PendantDropCamera
from protocols.calibration import prototcol_calibrate
from protocols.surfactant_characterization import prototcol_surfactant_characterization
from protocols.formulation import prototcol_formulate
from protocols.protocol import Protocol

# initialize the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["UPLOAD_FOLDER"] = "experiments"

# initialize pendant drop camera
pendant_drop_camera = PendantDropCamera()


@app.route("/")
def index():
    last_action = session.get("last_action", "None")
    return render_template("index.html", last_action=last_action)


@app.route("/input_settings", methods=["POST"])
def input_settings():
    return render_template("input_settings.html", settings=load_settings())


@app.route("/settings", methods=["POST"])
def settings():
    settings = load_settings()

    # update settings with form data
    ## general settings
    settings["ROBOT_IP"] = request.form.get("ROBOT_IP")
    settings["ROBOT_TYPE"] = request.form.get("ROBOT_TYPE")
    ## pendant drop settings
    settings["DROP_VOLUME"] = request.form.get("DROP_VOLUME")
    settings["EQUILIBRATION_TIME"] = request.form.get("EQUILIBRATION_TIME")
    settings["FLOW_RATE"] = request.form.get("FLOW_RATE")
    settings["DENSITY"] = request.form.get("DENSITY")
    settings["SCALE"] = request.form.get("SCALE")
    ## characterization settings
    settings["DILUTION_FACTOR"] = request.form.get("DILUTION_FACTOR")
    settings["EXPLORE_POINTS"] = request.form.get("EXPLORE_POINTS")
    settings["EXPLOIT_POINTS"] = request.form.get("EXPLOIT_POINTS")
    settings["WELL_VOLUME"] = request.form.get("WELL_VOLUME")
    settings["DYNAMIC_EQUILIBRATION_TIME"] = request.form.get(
        "DYNAMIC_EQUILIBRATION_TIME"
    )

    save_settings(settings)
    session["last_action"] = "Settings updated"
    return redirect(url_for("index"))


@app.route("/reset_settings", methods=["POST"])
def reset_settings():
    settings = load_settings(file_name="default_settings.json")
    save_settings(settings)
    session["last_action"] = "Settings reset"
    return redirect(url_for("index"))


@app.route("/input_initialisation", methods=["POST"])
def input_initialisation():
    return render_template("input_initialisation.html")


@app.route("/initialisation", methods=["POST"])
def initialisation():
    exp_name = request.form.get("exp_name")
    settings = load_settings()
    settings["EXPERIMENT_NAME"] = exp_name
    settings["GIT_COMMIT_HASH"] = load_commit_hash()
    csv_file = request.files.get("csv_file")
    settings["CONFIG_FILENAME"] = csv_file.filename
    sub_dir = "meta_data"
    # save data
    save_csv_file(exp_name, sub_dir, csv_file, app)
    save_settings_meta_data(settings=settings)
    save_settings(settings)
    session["last_action"] = "Initialisation done"
    return redirect(url_for("index"))


@app.route("/input_calibration", methods=["POST"])
def input_calibration():
    return render_template("input_calibration.html")


@app.route("/calibrate", methods=["POST"])
def calibrate():
    thread = threading.Thread(
        target=prototcol_calibrate, args=(pendant_drop_camera,)
    )
    thread.daemon = True
    thread.start()
    session["last_action"] = "Calibration done"
    return redirect(url_for("index"))


@app.route("/input_formulate", methods=["POST"])
def input_formulate():
    return render_template("input_formulate.html")


@app.route("/formulate", methods=["POST"])
def formulate():
    settings = load_settings()
    save_csv_file(
        exp_name=settings["EXPERIMENT_NAME"],
        subdir_name="meta_data",
        csv_file=request.files.get("csv_file"),
        app=app,
    )
    prototcol_formulate()
    session["last_action"] = "Formulation done"
    return redirect(url_for("index"))


@app.route("/input_measure_wells", methods=["POST"])
def input_measure_wells():
    return render_template("input_measure_wells.html")


@app.route("/measure_wells", methods=["POST"])
def measure_wells():
    settings = load_settings()
    csv_file = request.files.get("csv_file")
    settings["WELL_INFO_FILENAME"] = csv_file.filename
    save_settings_meta_data(settings=settings)
    save_settings(settings)
    save_csv_file(
        exp_name=settings["EXPERIMENT_NAME"],
        subdir_name="meta_data",
        csv_file=csv_file,
        app=app,
    )
    thread = threading.Thread(
        target=prototcol_measure_wells, args=(pendant_drop_camera,)
    )
    thread.daemon = True
    thread.start()
    session["last_action"] = "Measuring wells"
    return redirect(url_for("index"))


@app.route("/input_surfactant_characterization", methods=["POST"])
def input_surfactant_characterization():
    return render_template("input_surfactant_characterization.html")


@app.route("/characterize", methods=["POST"])
def characterize():
    settings = load_settings()
    csv_file = request.files.get("csv_file")
    settings["CHARACTERIZATION_INFO_FILENAME"] = csv_file.filename
    save_settings_meta_data(settings=settings)
    save_settings(settings)
    save_csv_file(
        exp_name=settings["EXPERIMENT_NAME"],
        subdir_name="meta_data",
        csv_file=csv_file,
        app=app,
    )
    prototcol_surfactant_characterization(pendant_drop_camera=pendant_drop_camera)
    session["last_action"] = "Surfactant characterized"
    return redirect(url_for("index"))


@app.route("/about")
def about():
    return render_template("about.html")


opentron_camera = OpentronCamera()


@app.route("/opentron_video_feed")
def opentron_video_feed():
    return Response(
        opentron_camera.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/pendant_drop_video_feed")
def pendant_drop_video_feed():
    return Response(
        pendant_drop_camera.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/toggle_pendant_drop_camera", methods = ["POST"])
def toggle_pendant_drop_camera():
    if pendant_drop_camera.streaming:
        pendant_drop_camera.stop_stream()
        session["last_action"] = "toggle off pendant drop camera"
    else:
        pendant_drop_camera.start_stream()
        session["last_action"] = "toggle on pendant drop camera"

    return redirect(url_for('index'))


@app.route("/status", methods=["POST"])
def status():
    data = request.get_json()
    status = data.get("status")
    print(f"Status: {status}")  
    return jsonify({"status": status})

@app.route("/pendant_drop_plot_feed")
def pendant_drop_plot_feed():
    pendant_drop_camera.start_plot_frame_thread()
    return Response(
        pendant_drop_camera.generate_plot_frame(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )
