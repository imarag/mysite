from flask import Blueprint, render_template, request, current_app, redirect, url_for
import re
import math
import json
import os
import glob

bp = Blueprint("BP_search_topics", __name__, url_prefix="/search-topics")


@bp.route("/filter-topics", methods=["GET", "POST"])
def filter_topics():
    if request.method == "POST":
        filter_selected = request.form.get("topictype")
    else:
        filter_selected = request.args.get("topictype")

    with open(current_app.config["ALL_TOPICS_FILE"], "r") as fjson:
        topics = json.load(fjson)["topics"]

    filtered_topics = []
    if filter_selected == "articles":
        for tp in topics:
            if tp["type"] == "article":
                filtered_topics.append(tp)

    elif filter_selected == "interactive-tools":
        for tp in topics:
            if tp["type"] == "interactive-tool":
                filtered_topics.append(tp)

    elif filter_selected == "python-tutorials":
        for tp in topics:
            if tp["type"] == "python-tutorial":
                filtered_topics.append(tp)
                
    else:
        filtered_topics = topics

    return render_template(
        "search-topics.html",
        topics=filtered_topics,
        selectedtopic=filter_selected.title(),
    )


@bp.route("/search-topic", methods=["GET"])
def search_topic():
    # get the search parameter that the user inserted
    search_param = request.args.get("search-param").lower()

    found_templates = {}

    for arx in glob.glob(current_app.root_path +  '/**/*.html', recursive=True):
        with open(arx, 'r') as fr:
            file_string = fr.read()

            if (search_param in file_string or search_param in arx):
                tmp_name = os.path.basename(arx)[:-5]
                if 'articles' in tmp:
                    found_templates[arx] = f"url_for('get_article', filename='{tmp_name}')"
                elif 'interactive-tools' in tmp:
                    found_templates[arx] = f"url_for('get_interactive_tool', filename='{tmp_name}')"
                elif 'python-tutorials' in tmp:
                    found_templates[arx] = f"url_for('get_python_tutorial', filename='{tmp_name}')"

    return render_template(
        "search-topics.html", topics=found_templates
    )
