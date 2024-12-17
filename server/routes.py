import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
    Response,
    jsonify,
)
from utils.load_save_functions import save_csv_file, load_settings, save_settings
from hardware.cameras import OpentronCamera, PendantDropCamera
from hardware.opentrons import Opentrons_API


# initialize the Opentrons API
opentrons_api = Opentrons_API()

# initialize the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["UPLOAD_FOLDER"] = "experiments"


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
    settings["NEEDLE_DIAMETER"] = request.form.get("NEEDLE_DIAMETER")
    settings["SCALE"] = request.form.get("SCALE")
    settings["DROP_HEIGHT"] = request.form.get("DROP_HEIGHT")
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

    csv_file = request.files.get("csv_file")
    settings["CONFIG_FILENAME"] = csv_file.filename
    sub_dir = "meta_data"
    save_csv_file(exp_name, sub_dir, csv_file, app)

    save_settings(settings)
    session["last_action"] = "Initialisation done"
    return redirect(url_for("index"))


@app.route("/input_formulate", methods=["POST"])
def input_formulate():
    return render_template("input_formulate.html")


@app.route("/formulate", methods=["POST"])
def formulate():
    csv_file = request.files.get("csv_file")
    settings = load_settings()
    exp_name = settings.get("EXPERIMENT_NAME")
    if not exp_name:
        abort(400, "Experiment name not found in session")
    sub_dir = "meta_data"
    save_csv_file(exp_name, sub_dir, csv_file, app)

    opentrons_api.formulate()
    session["last_action"] = "Formulation done"
    return redirect(url_for("index"))


@app.route("/input_measure_wells", methods=["POST"])
def input_measure_wells():
    return render_template("input_measure_wells.html")


@app.route("/measure", methods=["POST"])
def measure():
    plate_location = request.form.get("plate_location")
    start_well = request.form.get("start_well")
    end_well = request.form.get("end_well")
    print(
        f"Measuring wells {start_well} to {end_well}, plate at location: {plate_location}..."
    )
    session["last_action"] = "Wells measured"
    return redirect(url_for("index"))


@app.route("/input_surfactant_characterization", methods=["POST"])
def input_surfactant_characterization():
    return render_template("input_surfactant_characterization.html")


@app.route("/characterize", methods=["POST"])
def characterize():
    csv_file = request.files.get("csv_file")
    settings = load_settings()
    exp_name = settings["EXPERIMENT_NAME"]
    if not exp_name:
        abort(400, "Experiment name not found in session")
    sub_dir = "meta_data"
    save_csv_file(exp_name, sub_dir, csv_file, app)
    session["last_action"] = "Surfactant characterized"
    return redirect(url_for("index"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/input_calibration", methods=["POST"])
def input_calibration():
    return render_template("input_calibration.html")


@app.route("/calibrate", methods=["POST"])
def calibrate():
    opentrons_api.calibration()
    session["last_action"] = "Calibration done"
    return redirect(url_for("index"))


opentron_camera = (
    OpentronCamera()
)  # needs to be outside the route function to avoid issues


@app.route("/opentron_video_feed")
def opentron_video_feed():
    return Response(
        opentron_camera.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/pendant_drop_video_feed")
def pendant_drop_video_feed():
    pendant_drop_camera = (
        PendantDropCamera()
    )  # needs to be in the route function to avoid issues
    return Response(
        pendant_drop_camera.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/status", methods=["POST"])
def status():
    data = request.get_json()
    status = data.get("status")
    print(f"Status: {status}")
    return jsonify({"status": status})


# TODO feed plots
