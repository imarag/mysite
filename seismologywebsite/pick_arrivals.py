from flask import Blueprint, current_app, render_template, abort, request, jsonify, session, send_file
import os
from obspy.core import read, UTCDateTime
from obspy.core.trace import Trace
from obspy.core.stream import Stream
from .functions import convert_mseed_to_json, raise_error

bp = Blueprint('BP_pick_arrivals', __name__, url_prefix = '/pick-arrivals')


def create_path(name):
    path = os.path.join(
        current_app.config['DATA_FILES_FOLDER'], 
        str(session.get("user_id", "test")) + "_" + name
        )
    return path

@bp.route('/upload-mseed-file', methods=['POST'])
def upload():
    # get the files (in our case just one)
    files = request.files

    # check if file exists
    if 'file' not in files or len(files) < 1:
        error_message = "No file uploaded!"
        return raise_error(error_message)

    # Get the uploaded file from the request
    mseed_file = files['file']

    # Read the MSeed file using obspy
    try:
        stream = read(mseed_file)
    except Exception as e:
        error_message=str(e)
        return raise_error(error_message)

    # if the stream has 0, 1 or more than 3 traces abort
    if len(stream) not in [2, 3]:
        error_message = f'The stream must contain two or three traces to select its arrivals. Your stream contains {len(stream)} traces!'
        return raise_error(error_message)

    # if at least one of the traces is empty abort
    for tr in stream:
        if len(tr.data) == 0:
            error_message = 'One or more than one of your traces in the stream object, is empty!'
            return raise_error(error_message)

    # if the user hasn't defined nor the fs neither the delta, then error
    if stream[0].stats['sampling_rate'] == 1 and stream[0].stats['delta'] == 1:
        error_message = 'Neither sampling rate (fs[Hz]) nor sample distance (delta[sec]) are specified in the traces. Consider including them in the stream traces, for the correct x-axis time representation!'
        return raise_error(error_message)

    # if the user hasn't defined any channel then abort
    for tr in stream:
        if not tr.stats.channel:
            error_message = 'At least one of your traces does not have a defined channel (ej. E or N or Z). You should define the channel of the traces in order to be able to select the P and S arrivals one the corresponding components!'
            return raise_error(error_message)


    # get the file path to save the mseed file on the server
    mseed_save_file_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_pick-arrivals.mseed")

    # write the uploaded file
    stream.write(mseed_save_file_path)

    # convert the uploaded mseed file to json
    json_data = convert_mseed_to_json(stream)

    return json_data


@bp.route("/apply-filter", methods=["GET"])
def apply_filter():

    # get the filter value
    filter_value = request.args.get('filter')

    # get the uploaded mseed file path to apply the filter to it
    mseed_file_location_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_pick-arrivals.mseed")
    
    # read it
    mseed_data = read(mseed_file_location_path)
    
    # according to the filter value, apply a filter to it
    # if the filter is "initial" then don't do any filter, just return the raw values
    if filter_value != 'initial':

        # get the freqmin and freqmax
        freqmin = filter_value.split('-')[0].strip()
        freqmax = filter_value.split('-')[1].strip()

        # if the user inserted something different than a number abort
        # first check if the value is something other than the empty string
        # because the user CAN leave the entry, empty
        if freqmin:
            try:
                dummy = float(freqmin)
            except:
                error_message="You need to provide a number for the left filter!"
                return raise_error(error_message)

        if freqmax:
            try:
                dummy = float(freqmax)
            except:
                error_message="You need to provide a number for the right filter!"
                return raise_error(error_message)

        # if freqmin exists and not freqmax
        if freqmin and not freqmax:
            if float(freqmin) < 0.01 or float(freqmin) > 100:
                error_message="The acceptable filter range is from 0.01 to 100 Hz!"
                return raise_error(error_message)
            
            try:
                mseed_data.filter("highpass", freq=float(freqmin))
            except Exception as e:
                error_message = str(e)
                return raise_error(error_message)

        # elif freqmin does not exist but freqmax exists
        elif not freqmin and freqmax:
            if float(freqmax) < 0.01 or float(freqmax) > 100:
                error_message = "The acceptable filter range is from 0.01 to 100 Hz!"
                return raise_error(error_message)
            
            try:
                mseed_data.filter("lowpass", freq=float(freqmax))
            except Exception as e:
                error_message = str(e)
                return raise_error(error_message)

        # if neither freqmin nor freqmax exists, do nothing (return the initial unfiltered values)
        elif not freqmin and not freqmax:
            pass

        # if both are defined (freqmin and freqmax)
        else:
            if float(freqmin) >= float(freqmax):
                error_message = 'The left filter cannot be greater or equal to the right filter!'
                return raise_error(error_message)

            elif float(freqmin) < 0.01 or float(freqmin) > 100 or float(freqmax) < 0.01 or float(freqmax) > 100:
                error_message = "The acceptable filter range is from 0.01 to 100 Hz!"
                return raise_error(error_message)
            
            try:
                mseed_data.filter("bandpass", freqmin=float(freqmin), freqmax=float(freqmax))
            except Exception as e:
                error_message = str(e)
                return raise_error(error_message)
    
    json_data = convert_mseed_to_json(mseed_data)

    return json_data
    


@bp.route("/save-arrivals", methods=["GET"])
def save_arrivals():
    
    Parr = str(request.args.get('Parr')).strip()
    Sarr = str(request.args.get('Sarr')).strip()

    # check if the Parr and Sarr exist and create a dict_arrivals dict accordingly
    if Parr == "null" and Sarr == "null":
        error_message = "You need to select at least one arrival to save them!"
        return raise_error(error_message)
    elif Parr != "null" and Sarr == "null":
        dict_arrivals = {"P": float(Parr)}
    elif Parr == "null" and Sarr != "null":
        dict_arrivals = {"S": float(Sarr)}
    else:
        dict_arrivals = {"P": float(Parr), "S": float(Sarr)}

    # get the mseed file path and the parent of the mseed file path
    # i am going to create a txt file and save it in than parent
    mseed_file_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_pick-arrivals.mseed")
    mseed_file_parent = os.path.dirname(mseed_file_path)

    # read the mseed
    df = read(mseed_file_path)

    # get some seismic info
    station = df[0].stats.station
    starttime = df[0].stats.starttime

    # create the txt file path from the date and time and station and save it in the previous parent
    arrivals_file_name = str(starttime.date) + "_" + str(starttime.time) + "_" + station + ".txt"
    arrivals_file_name = arrivals_file_name.replace(":", "").replace("-", "")
    arrivals_file_path = os.path.join(mseed_file_parent, arrivals_file_name)
    
    # write the file to the parent
    with open(arrivals_file_path, "w") as fw:
        for pick_label in dict_arrivals:
            fw.write(pick_label + " ")
        fw.write("\n")

        for pick_label in dict_arrivals:
            fw.write(str(dict_arrivals[pick_label]) + " ")
        fw.write("\n")
    
    # return the file. The download name does not matter. I will use the dummy paragraph that i created
    # later in the javascript
    return send_file(arrivals_file_path, mimetype=None, as_attachment=True, download_name=arrivals_file_name)
            