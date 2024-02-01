from flask import Blueprint, session, current_app, request, jsonify, flash, send_file 
from obspy.core import UTCDateTime 
from obspy.clients.fdsn.header import URL_MAPPINGS
import os 

bp = Blueprint("BP_get_data", __name__, url_prefix="/get-data")

def create_path(name):
    path = os.path.join(
        current_app.config["DATA_FILES_FOLDER"],
        str(session.get("user_id", "test")) + "_" + name,
    )
    return path



@bp.route("/get-waveforms", methods=["GET"])
def get_waveforms():
    data_center = request.args.get("data-center")
    network = request.args.get("network")
    station = request.args.get("station")
    start_time = request.args.get("start-time")
    start_date = request.args.get("start-date")
    end_time = request.args.get("end-time")
    end_date = request.args.get("end-date")

    dataselect_url = request.args.get("dataselect-url")
    station_url = request.args.get("station-url")
    event_url = request.args.get("event-url")

    start_date_time = UTCDateTime(start_date + " " + start_time)
    end_date_time = UTCDateTime(end_date + " " + end_time)

    start_date_time_iso = start_date_time.isoformat()
    end_date_time_iso = end_date_time.isoformat()

    query_URL = f"network={network}&station={station}&starttime={start_date_time_iso}&endtime={end_date_time_iso}"

    res = requests.get(f"{dataselect_url}?{query_URL}")
    current_app.logger.warning(f"{dataselect_url}?{query_URL}")
    return jsonify({"message": "nada"})


# @bp.route("/get-waveforms2", methods=["GET"])
# def get_waveforms2():
#     data_center = request.args.get("data-center")
#     network = request.args.get("network")
#     station = request.args.get("station")
#     start_time = request.args.get("start-time")
#     start_date = request.args.get("start-date")
#     end_time = request.args.get("end-time")
#     end_date = request.args.get("end-date")

#     if (
#         not data_center
#         or not network
#         or not start_time
#         or not start_date
#         or not end_time
#         or not end_date
#     ):
#         error = "You must fill in all the available fields!"
#         flash(error, "danger")
#         return render_template("get-waveforms.html", stream=None)

#     start_dt = UTCDateTime(start_date + " " + start_time)
#     end_dt = UTCDateTime(end_date + " " + end_time)
#     total_seconds = end_dt - start_dt

#     try:
#         client = Client(data_center)
#         st = client.get_waveforms(
#             network, station, "*", "*", start_dt, start_dt + total_seconds
#         )
#     except Exception as e:
#         error = str(e)
#         flash(error, "danger")
#         return render_template("get-waveforms.html", stream="no-trace-found")

#     df = pd.DataFrame()
#     for tr in st:
#         tr_stats = tr.stats
#         df_one_row = pd.DataFrame(
#             {
#                 "catalogue": [data_center],
#                 "network": [tr_stats["network"]],
#                 "station": [tr_stats["station"]],
#                 "location": [tr_stats["location"]],
#                 "channel": [tr_stats["channel"]],
#                 "starttime": [tr_stats["starttime"]],
#                 "endtime": [tr_stats["endtime"]],
#             }
#         )

#         if df.empty:
#             df = df_one_row
#         else:
#             df = pd.concat([df, df_one_row])

#     df["compo"] = df["channel"].str[:2]
#     df_total_traces = df.groupby(["location", "compo"])["station"].count().reset_index()
#     df_total_traces = df_total_traces.rename(columns={"station": "total-traces"})
#     df = df.merge(df_total_traces, on=["location", "compo"])
#     group = df.copy().drop_duplicates(subset=["location", "compo"])

#     csv_save_file_path = create_path("stream-csv-file.csv")

#     group["id"] = [f"st{i}" for i in range(1, len(group) + 1)]
#     group.to_csv(csv_save_file_path)

#     front_end_labels = []
#     for i in range(len(group)):
#         row = group.iloc[i]
#         group_id = row["id"]
#         group_label = f'{row["network"]} {row["station"]} {row["location"]} {row["channel"][:2]} {row["starttime"].strftime("%y-%m-%d %H:%M:%S")} {row["endtime"].strftime("%y-%m-%d %H:%M:%S")} | total {row["total-traces"]} trace(s)'
#         front_end_labels.append({"id": group_id, "label": group_label})

#     flash("Traces successfully found! Ready for download.", "success")
#     return render_template("get-waveforms.html", stream=front_end_labels)


@bp.route("/download-selected/<id_value>", methods=["GET"])
def download_selected(id_value):
    csv_save_file_path = create_path("stream-csv-file.csv")

    df = pd.read_csv(csv_save_file_path, dtype={"location": str})
    trace_selected = df.loc[df["id"] == id_value].iloc[0]

    try:
        client = Client(trace_selected["catalogue"])
        st = client.get_waveforms(
            trace_selected["network"],
            trace_selected["station"],
            trace_selected["location"],
            f'{trace_selected["compo"]}*',
            UTCDateTime(trace_selected["starttime"]),
            UTCDateTime(trace_selected["endtime"]),
        )
    except Exception as e:
        error = str(e)
        flash(error, "danger")
        return render_template("get-waveforms.html", stream="no-trace-found")

    mseed_file_path = create_path("mseed-file.mseed")
    st.write(mseed_file_path)

    file_name = f'{trace_selected["station"]}_{trace_selected["location"]}_{trace_selected["compo"]}_{UTCDateTime(trace_selected["starttime"]).strftime("%Y%m%d_%H%M%S")}.mseed'

    return send_file(mseed_file_path, as_attachment=True, download_name=file_name)


@bp.route("/download-all", methods=["GET"])
def download_all():
    csv_save_file_path = create_path("stream-csv-file.csv")

    df = pd.read_csv(csv_save_file_path, dtype={"location": str})

    zip_file_path = create_path("zip-file.mseed")

    # Create a ZipFile object in write mode
    with zipfile.ZipFile(zip_file_path, "w") as zipf:
        for i in range(len(df)):
            row = df.iloc[i]
            catalogue = row["catalogue"]
            network = row["network"]
            station = row["station"]
            location = row["location"]
            compo = row["compo"]
            starttime = row["starttime"]
            endtime = row["endtime"]

            try:
                client = Client(catalogue)
                st = client.get_waveforms(
                    network,
                    station,
                    location,
                    f"{compo}*",
                    UTCDateTime(starttime),
                    UTCDateTime(endtime),
                )
            except Exception as e:
                error = str(e)
                flash(error, "danger")
                return render_template("get-waveforms.html", stream="no-trace-found")

            file_name = f'{station}_{location}_{compo}_{UTCDateTime(starttime).strftime("%Y%m%d_%H%M%S")}.mseed'

            st.write(file_name)
            zipf.write(file_name)
            os.remove(file_name)

        download_zip_name = f'{catalogue}_{network}_{station}_{UTCDateTime(starttime).strftime("%Y%m%d_%H%M%S")}.zip'
        return send_file(
            zip_file_path, as_attachment=True, download_name=download_zip_name
        )


@bp.route("/get-events", methods=["POST"])
def get_events():
    data_center = request.form["data-center"]
    depth_min = request.form["depth-min"]
    depth_max = request.form["depth-max"]
    mag_min = request.form["mag-min"]
    mag_max = request.form["mag-min"]
    lat_min = request.form["lat-min"]
    lat_max = request.form["lat-max"]
    long_min = request.form["long-min"]
    long_max = request.form["long-max"]
    start_time = request.form["start-time"]
    start_date = request.form["start-date"]
    end_time = request.form["end-time"]
    end_date = request.form["end-date"]

    start_dt = UTCDateTime(start_date + " " + start_time)
    end_dt = UTCDateTime(end_date + " " + end_time)
    total_seconds = end_dt - start_dt

    try:
        client = Client(data_center)
        event_catalogue = client.get_events(
            starttime=start_dt,
            endtime=start_dt + total_seconds,
            minlatitude=lat_min,
            maxlatitude=lat_max,
            minlongitude=long_min,
            maxlongitude=long_max,
            mindepth=depth_min,
            maxdepth=depth_max,
            minmagnitude=mag_min,
            maxmagnitude=mag_max,
        )
    except Exception as e:
        error = str(e)
        flash(error, "danger")
        return render_template("get-events.html", stream=None)

    if len(event_catalogue) > 30:
        error = "Your search criteria yield a large number of traces! We recommend refining your search criteria to narrow down the results. Thank you for your understanding."
        flash(error, "danger")
        return render_template("get-events.html", stream=None)

    events_save_path = create_path("events.json")
    event_catalogue.write(events_save_path, format="JSON")

    with open(events_save_path, "r") as fr:
        dict_events_catalogue = json.load(fr)

    return jsonify(dict_events_catalogue)


@bp.route("/download-events-json", methods=["GET"])
def download_events_json():
    events_save_path = create_path("events.json")
    return send_file(events_save_path, as_attachment=True)


@bp.route("/get-datacenters", methods=["GET"])
def get_datacenters():
    res = requests.get("https://www.fdsn.org/ws/datacenters/1/query")
    datacenters = res.json()["datacenters"]
    all_datacenters = []
    for datacenter in datacenters:
        name = datacenter["name"]
        all_datacenters.append(name)
    all_datacenters = list(set(all_datacenters))

    return jsonify({"datacenters": all_datacenters})
