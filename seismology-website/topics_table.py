from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)
from .db import get_db


bp = Blueprint('BP_topics_database', __name__, url_prefix = '/topics-database')


@bp.route('reset-topics', methods=['GET'])
def reset_topics():

    # Connect to the SQLite database
    db = get_db()

    # Define multiple SQL commands
    sql_commands = [
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('Python Obspy', 'ObsPy is an open-source Python library used for seismic data processing and analysis. It stands for Observatory Python and provides a wide range of functionalities for working with seismological data.', 'obspy-icon.png', 'static', 'obspy.html')",
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('Fourier spectra calculation', 'An interactive tool to calculate the Fourier spectra on a window of a seismogram. The Fourier transform is commonly used in seismology to analyze the frequency content of seismic signals.', 'fourier-icon.png', 'interactive', 'fourier.html')",
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('Arrival time picking', 'Arrival time picking refers to the process of extracting the arrival times of specific seismic phases from a seismogram. These arrival times provide valuable information about the timing and characteristics of seismic events.', 'arrival-pick-icon.png', 'interactive', 'pick-arrivals.html')",
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('ASCII to MSEED', 'An interactive tool to convert ASCII files to ObsPy MiniSEED (mseed) format. Use this option if you want to transform your data into a binary format to use the available tools.', 'ascii-to-mseed-icon.png', 'interactive', 'ascii-to-mseed.html')",
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('Signal processing', 'An interactive tool to apply various techniques and algorithms to analyze, filter, enhance, and extract meaningful information from seismic records.', 'signal-processing-icon.png', 'interactive', 'signal-processing.html')",
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('Site effect', 'Refers to the phenomenon where the characteristics of the local site or subsurface geology affect the propagation and amplification of seismic waves.', 'site-effect-icon.png', 'static', 'site-effect.html')",
        "INSERT INTO topics (title, description, image_name, type, template_name) VALUES ('Introduction to Seismology', 'A small introduction to various seismological concepts and the propagation of seismic waves through the Earth', 'introduction-to-seismology.png', 'static', 'seismology-intro.html')"
    ]


    db.execute('DELETE FROM topics')

    # Execute each SQL command
    for command in sql_commands:
        db.execute(command)

    # Commit the changes and close the connection
    db.commit()
    return redirect(url_for('BP_topics_database.show_all_topics'))


@bp.route('/show-all-topics', methods=['GET'])
def show_all_topics():
    database = get_db()
    topics = database.execute("SELECT * FROM topics").fetchall()
    return render_template('database-tables/show-topics.html', topics=topics)


@bp.route('/show_add_template_page', methods=['GET'])
def show_add_template_page():
    return render_template('database-tables/add-topic.html')


@bp.route('/show-edit-template-page/<topic_id>', methods=['GET'])
def show_edit_template_page(topic_id):
    database = get_db()
    topic = database.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)
    ).fetchone()
    return render_template('database-tables/edit-topic.html', topic = topic)






@bp.route('/add-topic', methods=['GET', 'POST'])
def add_topic():
    topic_title = request.form.get('topic-title-input')
    topic_description = request.form.get('topic-description-input')
    topic_image_name = request.form.get('topic-image-name-input')
    topic_type = request.form.get('topic-type-input')
    topic_template_name = request.form.get('topic-template-name-input')

    database = get_db()
    database.execute("INSERT INTO topics (title, description, image_name, type, template_name) VALUES (?, ?, ?, ?, ?)",
        (topic_title, topic_description, topic_image_name, topic_type, topic_template_name)
    )
    database.commit()
    return redirect(url_for('BP_topics_database.show_all_topics'))


@bp.route('/edit-topic/<topic_id>', methods=['GET', 'POST'])
def edit_topic(topic_id):
    topic_title = request.form.get('topic-title-input')
    topic_description = request.form.get('topic-description-input')
    topic_image_name = request.form.get('topic-image-name-input')
    topic_type = request.form.get('topic-type-input')
    topic_template_name = request.form.get('topic-template-name-input')

    database = get_db()
    database.execute("UPDATE topics SET title=?, description=?, image_name=?, type=?, template_name=? WHERE id=?",
        (topic_title, topic_description, topic_image_name, topic_type, topic_template_name, topic_id)
    )
    database.commit()
    return redirect(url_for('BP_topics_database.show_all_topics'))


@bp.route('/delete-topic/<topic_id>', methods=['GET', 'POST'])
def delete_topic(topic_id):
    database = get_db()
    database.execute("DELETE FROM topics WHERE id = ?",
        (topic_id,)
    )
    database.commit()
    return redirect(url_for('BP_topics_database.show_all_topics'))

