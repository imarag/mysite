from flask import (
    Blueprint,
    current_app,
    render_template,
    abort,
    request,
    jsonify,
    session,
    send_file,
    url_for,
)
import os
import re
from obspy.core import read, UTCDateTime
from obspy.core.trace import Trace
from obspy.core.stream import Stream
import numpy as np
import pandas as pd
import datetime
from .functions import get_record_name, raise_error, validate_seismic_file


bp = Blueprint("BP_edit_seismic_file", __name__, url_prefix="/edit-seismic-file")


def create_path(name):
    path = os.path.join(
        current_app.config["DATA_FILES_FOLDER"],
        str(session.get("user_id", "test")) + "_" + name,
    )
    return path


@bp.route("/upload-seismic-file", methods=["POST"])
def upload():
    # get the files
    files = request.files

    # check if file exists
    if "file" not in files or len(files) < 1:
        error_message = "No file uploaded!"
        return raise_error(error_message)

    # Get the uploaded file from the request
    seismic_file = files["file"]

    # try to read the seimsic file
    try:
        stream = read(seismic_file)
    except Exception as e:
        error_message = str(e)
        return raise_error(error_message)

    # if the seismic file is empty then error
    if len(stream) == 0:
        error_message = (
            "The uploaded seismic file is empty. There are no records in the file!"
        )
        return raise_error(error_message)

    # if the seismic file is empty then error
    if len(stream) > 30:
        error_message = f"The uploaded seismic file contains an excessive number of traces ({len(stream)}). This may impact the performance of the tool. Please upload a file with fewer traces!"
        return raise_error(error_message)

    for tr in stream:
        if len(tr.data) > 300000:
            error_message = f"The uploaded seismic file contains records with excessive number of sample points, npts (>300000). This may impact the performance of the tool. Please upload a file with less number of sample points!"
            return raise_error(error_message)

    # check if the data of the traces are indeed numbers and not any string
    for tr in stream:
        try:
            pd.to_numeric(tr.data, errors="raise")
        except:
            error_message = f"The data in one of your records contain a non-valid input value in their data. Only numbers and NaN values are allowed!"
            return error_message

    # get the file path to save the uploaded file as miniseed in the server
    seismic_file_save_path = create_path("edit-seismic-file-tool-stream.mseed")

    # write the uploaded file as mseed
    stream.write(seismic_file_save_path)

    # convert the uploaded mseed file to json
    json_data = jsonify([f"trace-{i}" for i in range(1, len(stream) + 1)])
    return json_data


@bp.route("/get-trace-info", methods=["GET"])
def get_trace_info():
    selected_trace = request.args.get("selected-trace")

    # read the uploaded seismic file
    seismic_file = create_path("edit-seismic-file-tool-stream.mseed")

    # try to read the seimsic file
    try:
        st = read(seismic_file)
    except Exception as e:
        error_message = str(e)
        return raise_error(error_message)

    number_in_array = int(selected_trace[-1]) - 1

    tr = st[number_in_array]

    trace_dict = {
        "ydata": tr.data.tolist(),
        "xdata": tr.times().tolist(),
        "number_in_array": number_in_array,
        "stats": {
            "channel": tr.stats["channel"],
            "npts": tr.stats["npts"],
            "sampling_rate": tr.stats["sampling_rate"],
            "station": tr.stats["station"],
            "date": tr.stats["starttime"].date.isoformat(),
            "time": tr.stats["starttime"].time.isoformat()[:8],
        },
    }
    print(trace_dict)
    return jsonify(trace_dict)


@bp.route("/update-header", methods=["POST"])
def update_header():
    # get the fetch request query parameters
    selected_trace = request.form["trace-selected"]
    station = request.form.get("station")
    date = request.form.get("date")
    time = request.form.get("time")
    component = request.form.get("component")

    # read the uploaded seismic file
    seismic_file = create_path("edit-seismic-file-tool-stream.mseed")

    # try to read the seimsic file
    try:
        st = read(seismic_file)
    except Exception as e:
        error_message = str(e)
        return raise_error(error_message)

    station = station.strip()
    if station:
        if not re.search("^[a-zA-Z0-9]{2,6}$", station):
            error_message = "The station name must contain 2 up to 6 characters or numbers (a-z, A-Z, 0-9)!"
            return raise_error(error_message)

    if not date:
        date = "1970-01-01"
    if not time:
        time = "00:00:00"

    try:
        starttime = UTCDateTime(date + " " + time)
    except Exception as e:
        error_message = str(e)
        return raise_error(error_message)

    component = component.strip()
    if component:
        if not re.search("^[a-zA-Z0-9]{1,3}$", component):
            error_message = "The component must contain 1 up to 3 characters or numbers (a-z, A-Z, 0-9)!"
            return raise_error(error_message)

        component = component.upper()

    number_in_array = int(selected_trace[-1]) - 1

    st[number_in_array].stats["station"] = station
    st[number_in_array].stats["starttime"] = starttime
    st[number_in_array].stats["channel"] = component

    updated_stream = create_path("edit-seismic-file-tool-stream.mseed")
    st.write(updated_stream)

    return jsonify({"update": "succesful"})


@bp.route("/download-file", methods=["GET"])
def download_file():
    # get the updated stream
    updated_stream = create_path("edit-seismic-file-tool-stream.mseed")

    # return it
    return send_file(
        updated_stream,
        as_attachment=True,
        download_name=get_record_name(updated_stream) + ".mseed",
    )


@bp.route("/download-data", methods=["GET"])
def download_data():
    seismic_file = create_path("edit-seismic-file-tool-stream.mseed")
    # try to read the seimsic file
    try:
        stream = read(seismic_file)
    except Exception as e:
        error_message = str(e)
        return raise_error(error_message)

    # create an empty dataframe to put the data
    df = pd.DataFrame()

    # loop through the stream and put the data in columns with names the trace channels
    for i, tr in enumerate(stream, start=1):
        # get the channel
        channel = tr.stats.channel
        # if there is not channel then name it ch and the index i
        if not channel:
            channel = f"ch{i}"
        # get the data
        data_values = tr.data
        # add the data as a column to the dataframe
        df[channel] = data_values

    # create a csv path to save the pandas dataframe as csv file
    csv_path = create_path("edit-seismic-file-tool-csv.csv")

    # save the csv file
    df.to_csv(csv_path, index=None)

    # return the saved file
    return send_file(
        csv_path,
        as_attachment=True,
        download_name=get_record_name(seismic_file) + ".csv",
    )


@bp.route("/download-header", methods=["GET"])
def download_header():
    seismic_file = create_path("edit-seismic-file-tool-stream.mseed")
    # try to read the seimsic file
    try:
        stream = read(seismic_file)
    except Exception as e:
        error_message = str(e)
        return raise_error(error_message)

    # create a csv path to save the pandas dataframe as csv file
    txt_path = create_path("header-info.txt")

    with open(txt_path, "w") as fw:
        for n, tr in enumerate(stream, start=1):
            fw.write(f"Trace {n}\n")
            fw.write(f"----------------\n")
            for k in tr.stats:
                fw.write(f"{k} : {tr.stats[k]}\n")
            fw.write("\n\n")

    # return the saved file
    return send_file(
        txt_path,
        as_attachment=True,
        download_name=get_record_name(seismic_file) + "-info.txt",
    )
