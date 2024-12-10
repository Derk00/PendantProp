import os
import cv2
import threading
from threading import Thread, Event
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
)
from custom_functions import measure_well, save_csv_file, generate_opentron_frames


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["UPLOAD_FOLDER"] = "meta-data"


@app.route("/")
def index():
    last_action = session.get("last_action", "None")
    return render_template("index.html", last_action=last_action)


@app.route("/input_settings", methods=["POST"])
def input_settings():
    return render_template("input_settings.html")


@app.route("/settings", methods=["POST"])
def settings():
    exp_name = request.form.get("exp_name")
    csv_file = request.files.get("csv_file")
    save_csv_file(exp_name, csv_file, app)
    session["exp_name"] = exp_name
    session["last_action"] = "Settings saved"
    return redirect(url_for("index"))


@app.route("/input_formulate", methods=["POST"])
def input_formulate():
    return render_template("input_formulate.html")


@app.route("/formulate", methods=["POST"])
def formulate():
    csv_file = request.files.get("csv_file")
    exp_name = session.get("exp_name")
    if not exp_name:
        abort(400, "Experiment name not found in session")
    save_csv_file(exp_name, csv_file, app)
    session["last_action"] = "Formulation done"
    return redirect(url_for("index"))


@app.route("/input_measure_wells", methods=["POST"])
def input_measure_wells():
    return render_template("input_measure_wells.html")


@app.route("/measure", methods=["POST"])
def measure():
    start_well = request.form.get("start_well")
    end_well = request.form.get("end_well")
    measure_well(start_well, end_well)
    session["last_action"] = "Wells measured"
    return redirect(url_for("index"))


@app.route("/input_surfactant_characterization", methods=["POST"])
def input_surfactant_characterization():
    return render_template("input_surfactant_characterization.html")


@app.route("/characterize", methods=["POST"])
def characterize():
    csv_file = request.files.get("csv_file")
    exp_name = session.get("exp_name")
    if not exp_name:
        abort(400, "Experiment name not found in session")
    save_csv_file(exp_name, csv_file, app)
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
    print("Calibrating...")
    session["last_action"] = "Calibration done"
    return redirect(url_for("index"))


@app.route("/opentron_video_feed")
def opentron_video_feed():
    return Response(
        generate_opentron_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
