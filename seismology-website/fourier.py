from flask import Blueprint, current_app, render_template, abort, request, jsonify, session, send_file
import os
from flask_session import Session
from obspy.core import read
from obspy.core.trace import Trace
from obspy.core.stream import Stream
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


bp = Blueprint('BP_fourier_spectra', __name__, url_prefix = '/fourier-spectra')


def get_record_name():
    mseed_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool.mseed")
    # read it
    mseed = read(mseed_path)
    # create the record name
    first_trace = mseed[0]
    starttime = first_trace.stats["starttime"]
    station = first_trace.stats["station"]
    rec_name = str(starttime.date) + "_" + str(starttime.time) + "_" + station
    rec_name = rec_name.replace(":", "").replace("-", "")
    return rec_name

def convert_mseed_to_json(stream):
    traces_data_dict = {}
    first_trace = stream[0]
    starttime = first_trace.stats["starttime"]
    fs = float(first_trace.stats["sampling_rate"])
    station = first_trace.stats["station"]
    rec_name = str(starttime.date) + "_" + str(starttime.time) + "_" + station
    rec_name = rec_name.replace(":", "").replace("-", "")
    starttime = starttime.isoformat()
    
    for n, trace in enumerate(stream):
        ydata = trace.data.tolist()
        xdata = trace.times().tolist()

        trace_data = {
            'record-name': rec_name,
            'ydata': ydata,
            'xdata': xdata,
            'stats': {
                'channel': trace.stats["channel"]
            },
            }
        traces_data_dict[f'trace-{n}'] = trace_data
    return jsonify(traces_data_dict)



@bp.route('/show-template', methods=['GET'])
def show_template():
   return render_template('topics/fourier-spectra.html')


@bp.route('/upload-mseed-file', methods=['POST'])
def upload():
    # get the files
    files = request.files

    # check if file exists
    if 'file' not in files or len(files) < 1:
        error_message = 'No file uploaded!'
        abort(400, description=error_message)

    # Get the uploaded file from the request
    mseed_file = files['file']

    # Read the MSeed file using obspy
    try:
        stream = read(mseed_file)
    except Exception as e:
        error_message = str(e)
        abort(400, description=error_message)
    
    # if the stream has 0, 1 or more that 3 traces abort
    if len(stream) <= 1 or len(stream) > 3:
        error_message = f'The stream must contain two or three traces. Your stream contains {len(stream)} traces!'
        abort(400, description=error_message)

    # if at least one of the traces is empty abort
    for tr in stream:
        if len(tr.data) == 0:
            error_message = 'One or more of your traces in the stream object, is empty.'
            abort(400, description=error_message)

    # if the user hasn't defined nor the fs neither the delta, then error
    if stream[0].stats['sampling_rate'] == 1 and stream[0].stats['delta'] == 1:
        error_message = 'Neither sampling rate (fs[Hz]) nor sample distance (delta[sec]) are specified in the trace objects. Consider including them in the stream traces, for the correct x-axis time representation!'
        abort(400, description=error_message)

    # get the file path to save the mseed file on the server
    mseed_save_file_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool.mseed")

    # write the uploaded file
    stream.write(mseed_save_file_path)

    # convert the uploaded mseed file to json
    json_data = convert_mseed_to_json(stream)
    
    return json_data






@bp.route('/compute-fourier', methods=['GET'])
def compute_fourier():

    # get the uploaded mseed file to apply the filter to it
    file_location_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool.mseed")
    
    # read it
    mseed_data = read(file_location_path)

    # get the first trace
    first_trace = mseed_data[0]

    # get some information of the stream object
    starttime = first_trace.stats.starttime
    total_duration = first_trace.stats.endtime - first_trace.stats.starttime
    station = first_trace.stats.station
    fs = first_trace.stats["sampling_rate"]
    dt = first_trace.stats["delta"]

    # calculate the nyquist frequency
    fnyq = fs / 2
    
    # get the user selected window parameters
    signal_window_left_side = request.args.get('signal-window-left-side')
    noise_window_right_side = request.args.get('noise-window-right-side')
    window_length = request.args.get('window-length')
    noise_selected = request.args.get('noise-selected')

    # initialize an empty error message
    error_message = None
    if float(signal_window_left_side) + float(window_length) >= total_duration:
        error_message = 'The signal window must ends before the time series graph ends! Consider reducing the window side or moving the signal left side to the left!'
    elif float(signal_window_left_side) < 0:
        error_message = 'The signal window must start after the time series graph begins! Consider moving the signal left side to the right, so that it is inside the graph area!'
    elif noise_selected == 'true' and float(noise_window_right_side) > total_duration:
        error_message = 'The noise window must end before the time series graph ends! Consider moving the noise right side to the left!'
    elif noise_selected == 'true' and float(noise_window_right_side) - float(window_length) < 0:
        error_message = 'The noise window must start after the time series graph begins! Consider reducing the window side or moving the noise right side to the right!'

    if error_message:
        abort(400, description=error_message)

    # i will save here the traces
    traces_data_dict = {}

    # loop through the uploaded traces
    for i in range(len(mseed_data)):

        # get the trace name and add it to the traces_data_dict
        trace_label = f'trace-{i}'
        traces_data_dict[trace_label] = {}

        # get a copy of the trace for the singal
        df_s = mseed_data[i].copy()

        # get the current trace channel
        channel = df_s.stats.channel

        # trim the waveform between the user selectd window
        df_s.trim(starttime = starttime + float(signal_window_left_side), endtime=starttime + float(signal_window_left_side) + float(window_length))
        
        # get the npts after the trim
        npts = df_s.stats["npts"]

        # calculate the number of frequncies on the frequency spectra
        sl = int(npts / 2)

        # calculate the frequnecy array to plot the fourier
        freq_x = np.linspace(0 , fnyq , sl)

        # compute the fft of the signal
        yf_s = np.fft.fft(df_s.data[:npts]) 
        y_write_s = dt * np.abs(yf_s)[0:sl]

        # create a dictionary for the signal
        traces_data_dict[trace_label]['signal'] = {
            'ydata': y_write_s.tolist(),
            'xdata': freq_x.tolist(),
            'stats': {
                'channel': channel
            }
        }

        # if the user also added the noise
        if noise_selected != 'false':
            # get a copy of the trace for the noise
            df_p = mseed_data[i].copy()

            # trim it
            df_p.trim(starttime = starttime + float(noise_window_right_side) - float(window_length), endtime=starttime + float(noise_window_right_side))
            
            # calculate the fourier and create the object for the noise
            yf_p = np.fft.fft(df_p.data[:npts]) 
            y_write_p = dt * np.abs(yf_p)[0:sl]

            traces_data_dict[trace_label]['noise'] = {
                'ydata': y_write_p.tolist(),
                'xdata': freq_x.tolist(),
                'stats': {
                    'channel': channel
                }
            }
    
    # get the file path to save the fourier data on the server
    # just save it with the same name but append the _fourier_data 
    # and change the .mseed to .txt
    text_file_path = file_location_path.replace(".mseed", "-fourier-data.txt")
    
    # crete a txt file to save
    with open(text_file_path, "w") as fw:

        # create the header
        fw.write("freq ")
        for tr in traces_data_dict:
            channel = traces_data_dict[tr]['signal']["stats"]["channel"]
            for s_n in traces_data_dict[tr]:
                fw.write(f"{channel}-{s_n} ")
        fw.write("\n")

        xdata = traces_data_dict["trace-0"]['signal']["xdata"]
        for i in range(len(xdata)):
            fw.write(f"{xdata[i]} ")
            for tr in traces_data_dict:
                for s_n in traces_data_dict[tr]:
                    channel = traces_data_dict[tr][s_n]["stats"]["channel"]
                    xdata = traces_data_dict[tr][s_n]["xdata"]
                    ydata = traces_data_dict[tr][s_n]["ydata"]
                    fw.write(f"{ydata[i]} ")
            fw.write("\n")

    fig, ax = plt.subplots(len(traces_data_dict), 1, figsize=(12,6))
    colors = ['#5E62FF', '#B9BBFF', '#FFF532', '#FDF89E', '#FE4252', '#FBA3AA']
    xdata = traces_data_dict["trace-0"]["signal"]["xdata"]

    color_i = 0
    for n, tr in enumerate(traces_data_dict):
        
        for s_n in traces_data_dict[tr]:
            channel = traces_data_dict[tr][s_n]["stats"]["channel"]
            ydata = traces_data_dict[tr][s_n]["ydata"]
            label_name = f"{channel}-{s_n}"
            ax[n].plot(xdata, ydata, color=colors[color_i], lw=1, label=label_name)
            color_i += 1

        ax[n].legend(title=get_record_name())
        ax[n].set_xscale('log')
        ax[n].set_yscale('log')
        ax[n].set_xlabel("frequency [Hz]")
        
    fig.savefig(file_location_path.replace(".mseed", "-fourier-data.png"))

    # return a json response with the fourier data (dictionary)
    json_data = jsonify(traces_data_dict)
    
    return json_data
    



@bp.route('/compute-hvsr', methods=['GET'])
def compute_hvsr():

    # get the written fourier ascii file
    fourier_ascii_file_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-fourier-data.txt")
    
    # get the vertical component 
    vert_compo = request.args.get('vertical-component').lower()

    # read the fourier file using pandas
    fourier_data = pd.read_csv(fourier_ascii_file_path, sep="\s+")

    # get only the hvsr columns calculated from the signal and not the noise
    signal_cols = [c for c in fourier_data.columns if 'signal' in c]

    # save the xdata somewhere
    xdata = fourier_data['freq'].to_numpy()

    # get only those columns
    fourier_data = fourier_data[signal_cols]

    # just initialize the horizontal and vertical parameters
    horizontal_traces = []
    vertical_traces = None

    # initialize the dictionary to return
    traces_data_dict = {}

    # loop through the mseed data
    for i, c in enumerate(fourier_data.columns):

        # get the channel
        channel = c.split("-")[0].lower()

        # creat the label for the dictionary key
        trace_label = f'trace-{i}'

        # add this label
        traces_data_dict[trace_label] = {}
   
        # if you find the vertical component (the one that the user specified) then set the data to the vertical_traces parameter
        if channel == vert_compo:
            vertical_traces = fourier_data[c].to_numpy()
        else:
            horizontal_traces.append(fourier_data[c].to_numpy())

    # calculate the average horizontal fourier and the hvsr depending on if we have one or two horizontals
    if len(horizontal_traces) == 1:
        horizontal_fourier = horizontal_traces[0]
        hvsr = horizontal_fourier / vertical_traces
    else:
        horizontal_fourier = horizontal_traces[0] + horizontal_traces[1]
        hvsr = np.sqrt(horizontal_fourier / vertical_traces)

    # define the dictionary to return
    dict_data = {
        'ydata': hvsr.tolist(),
        'xdata': xdata.tolist(),
    }

    # crete a txt file to save
    hvsr_data_text_file = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-hvsr-data.txt")

    with open(hvsr_data_text_file, "w") as fw:

        # create the header
        fw.write("freq hvsr\n")

        for i in range(len(xdata)):
            fw.write(f"{xdata[i]} ")
            fw.write(f"{hvsr[i]} ")
            fw.write("\n")

    fig, ax = plt.subplots(1, 1, figsize=(12,6))

    ax.plot(xdata, hvsr, color='blue', lw=1, label=f"HVSR")
    ax.legend(title=get_record_name())
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel("frequency [Hz]")
    ax.set_xlabel("HVSR")

    fig.savefig(os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-hvsr-data.png"))

    # return a json response with the fourier data (dictionary)
    json_data = jsonify(dict_data)
    
    return json_data
        


@bp.route('/download', methods=['GET'])
def download():
    # get the label that tells you if the user wants to downloa the data or the values
    what_output = request.args.get('what_output')

    # the "what_to_download" is either graph or data
    # the "method_selected" is fourier or hvsr
    what_to_download, method_selected = what_output.split("-")

    # get the mseed file path
    mseed_file_path = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool.mseed")
    # get the text file (the fourier data)
    text_file_path = mseed_file_path.replace(".mseed", ".txt")
    # get the image
    graph_file_path = mseed_file_path.replace(".mseed", ".png")

    if method_selected == "fourier" and what_to_download == "graph":
        file_to_download = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-fourier-data.png")
        name = get_record_name() + '_fourier_data' + '.png'
    elif method_selected == "fourier" and what_to_download == "data":
        file_to_download = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-fourier-data.txt")
        name = get_record_name() + '_fourier_data' + '.txt'
    elif method_selected == "hvsr" and what_to_download == "graph":
        file_to_download = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-hvsr-data.png")
        name = get_record_name() + '_hvsr_data' + '.png'
    elif method_selected == "hvsr" and what_to_download == "data":
        file_to_download = os.path.join(current_app.config['DATA_FILES_FOLDER'], str(session.get("user_id", "test")) + "_fourier-spectra-tool-hvsr-data.txt")
        name = get_record_name() + '_hvsr_data' + '.txt'

    
    return send_file(
            file_to_download,
            as_attachment=True,
            download_name=name
        )



@bp.route('/get-the-code', methods=['GET'])
def get_the_code():
    return send_file(
            os.path.join(current_app.root_path, 'static', "fourier_spectra_calculation_script.txt"),
            as_attachment=True,
            download_name=f'fourier_spectra_calculation_script.txt'
        )
    

