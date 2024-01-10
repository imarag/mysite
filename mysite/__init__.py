from flask import (
    Flask,
    render_template,
    send_file,
    request,
    flash,
    session,
    redirect,
    url_for,
    abort,
)
from flask_mail import Mail, Message
import os
from .functions import generate_random_string, get_topic
from markupsafe import escape

mail = Mail()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config["DATA_FILES_FOLDER"] = os.path.join(app.root_path, "data_files")
    app.config["ALL_TOPICS_FILE"] = os.path.join(app.root_path, "all-topics.json")
    app.config["ALL_TOPICS_FILE_BACKUP"] = os.path.join(
        app.root_path, "all-topics.json"
    )

    app.config["ADMIN_USERNAME"] = "ioannis95"
    app.config["ADMIN_PASSWORD"] = "Seismologia95@"

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 465
    app.config["MAIL_USERNAME"] = "seismoweb95@gmail.com"
    app.config["MAIL_PASSWORD"] = "qppnzstyxltfjcnz"
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USE_SSL"] = True

    app.config["SECRET_KEY"] = "asdf12345po45i34OI"

    mail.init_app(app)

    try:
        os.makedirs(app.instance_path)
    except:
        pass

    try:
        os.mkdir(os.path.join(app.root_path, "data_files"))
    except:
        pass

    @app.before_request
    def before_request():
        if "user_id" not in session:
            user_id = generate_random_string()
            session["user_id"] = user_id

    @app.route("/")
    @app.route("/index")
    def home():
        return render_template("index.html")

    @app.route("/get-page/<page_name>")
    def get_page(page_name):
        if not os.path.exists(
            os.path.join(app.root_path, "templates", f"{page_name}.html")
        ):
            abort(404)
        return render_template(f"{page_name}.html")

    @app.route("/show-topic/<topic_tmp_name>")
    def show_topic(topic_tmp_name):
        if not os.path.exists(
            os.path.join(app.root_path, "templates", "topics", f"{topic_tmp_name}.html")
        ):
            abort(404)
        topic = get_topic("template_name", topic_tmp_name)
        return render_template(f"topics/{topic_tmp_name}.html", topic_object=topic)

    @app.route("/download-static-file/<file>")
    def download_static_file(file):
        static_file_path = os.path.join(app.root_path, "static", "static-files", file)
        return send_file(static_file_path, as_attachment=True, download_name=file)

    @app.route("/receive-feedback", methods=["POST"])
    def receive_feedback():
        feedback_user_email = request.form["feedback-email"]
        feedback_input_text = request.form["feedback-input"]

        if not feedback_user_email:
            flash("Feedback has not been sent. An email address is required!", "danger")
            return redirect(url_for("get_page", page_name="help-and-support"))

        if not feedback_input_text:
            flash(
                "Feedback has not been sent. A feedback message is required!", "danger"
            )
            return redirect(url_for("get_page", page_name="help-and-support"))

        try:
            msg = Message(
                subject=f"Feedback",
                sender="seismoweb95@gmail.com",
                recipients=["seismoweb95@gmail.com"],
                body=escape(feedback_input_text + f"\n from: {feedback_user_email}"),
            )
            mail.send(msg)
            flash("Thank you for your feedback!", "info")
        except Exception as e:
            print(e, "**************")
            flash(str(e))

        return redirect(url_for("get_page", page_name="help-and-support"))

    @app.errorhandler(400)
    def error_400(error):
        error = {
            "title": "Oops! Something Went Wrong!",
            "description": "The server could not understand the request due to invalid syntax or missing parameters. Check your request syntax or format and try sending it again.",
            "code": 400,
        }
        return render_template("base-error.html", error=error), 400

    @app.errorhandler(401)
    def error_401(error):
        error = {
            "title": "Access Denied!",
            "description": "You must authenticate to access this page. Double-check and try again with the proper access codes.",
            "code": 401,
        }
        return render_template("base-error.html", error=error), 401

    @app.errorhandler(403)
    def error_403(error):
        error = {
            "title": "Forbidden Access!",
            "description": "You do not have the permission to access the requested resource.",
            "code": 403,
        }
        return render_template("base-error.html", error=error), 403

    @app.errorhandler(404)
    def error_404(error):
        error = {
            "title": "Oops! Something Went Wrong!",
            "description": "This page doesn't exist! Please try a different location.",
            "code": 404,
        }
        return render_template("base-error.html", error=error), 404

    # @app.errorhandler(503)
    # def error_503(error):
    #     error = {
    #         "title": "Service Unavailable!",
    #         "description": "The server is not ready to handle the request. Commonly used when a server is temporarily down for maintenance.",
    #         "code": 503,
    #     }
    #     return render_template("base-error.html", error=error), 503

    from . import fourier
    from . import pick_arrivals
    from . import file_to_mseed
    from . import signal_processing
    from . import search_topics
    from . import admin
    from . import distance_between_points
    from . import edit_seismic_file
    from . import get_data

    app.register_blueprint(fourier.bp)
    app.register_blueprint(pick_arrivals.bp)
    app.register_blueprint(file_to_mseed.bp)
    app.register_blueprint(signal_processing.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(search_topics.bp)
    app.register_blueprint(distance_between_points.bp)
    app.register_blueprint(edit_seismic_file.bp)
    app.register_blueprint(get_data.bp)

    return app
