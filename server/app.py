import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from custom_functions import measure_well, save_settings

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')  # Use environment variable or default
app.config['UPLOAD_FOLDER'] = 'meta-data'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/input_settings", methods=["POST"])
def input_settings():
    # Render settings page
    return render_template("input_settings.html")

@app.route("/settings", methods=["POST"])
def settings():
    # Retrieve parameters from the form
    exp_name = request.form.get("exp_name")
    csv_file = request.files.get("csv_file")
    
    # Create a directory for the experiment if it doesn't exist
    exp_dir = os.path.join(app.config['UPLOAD_FOLDER'], exp_name)
    os.makedirs(exp_dir, exist_ok=True)
    
    # Save the uploaded CSV file
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)

    # Store the experiment name in the session
    session['exp_name'] = exp_name
    
    # Perform the custom function with the parameters
    save_settings(exp_name=exp_name)
    
    # Redirect to the home page after completion
    return redirect(url_for("index"))

@app.route("/input_formulate", methods=["POST"])
def input_formulate():
    # Render input page
    return render_template("input_formulate.html")

@app.route("/formulate", methods=["POST"])
def formulate():
    # retrieve parameters from the form
    csv_file = request.files.get("csv_file")
    exp_name = session.get("exp_name")
    if not exp_name:
        abort(400, "Experiment name not found in session")
    exp_dir = os.path.join(app.config['UPLOAD_FOLDER'], exp_name)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)
    return redirect(url_for("index"))

@app.route("/input_measure_wells", methods=["POST"])
def input_measure_wells():
    # Render input page
    return render_template("input_measure_wells.html")

@app.route("/measure", methods=["POST"])
def measure():
    # Retrieve parameters from the form
    start_well = request.form.get("start_well")
    end_well = request.form.get("end_well")
    
    # Perform the custom function with the parameters
    measure_well(start_well, end_well)
    
    # Redirect to the home page after completion
    return redirect(url_for("index"))

@app.route("/input_surfactant_characterization", methods=["POST"])
def input_surfactant_characterization():
    # Render input page
    return render_template("input_surfactant_characterization.html")

@app.route("/characterize", methods=["POST"])
def characterize():
    # retrieve parameters from the form
    csv_file = request.files.get("csv_file")
    exp_name = session.get("exp_name")
    if not exp_name:
        abort(400, "Experiment name not found in session")
    exp_dir = os.path.join(app.config['UPLOAD_FOLDER'], exp_name)
    file_path = os.path.join(exp_dir, csv_file.filename)
    csv_file.save(file_path)
    return redirect(url_for("index"))

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)