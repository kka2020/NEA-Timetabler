import flask
from werkzeug.utils import secure_filename
import os
import authenticate
from authenticate import LoginFailure

app = flask.Flask(__name__)
app.config["UPLOAD_FOLDER"] = "C:/Users/kavin/OneDrive - Reading School/Year 12/COMSCI/NEA/Final/web_app/uploads"

@app.route("/")
def root():
    return flask.redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    
    if flask.request.method == "POST":
        try:
            admin, course_group, creator = authenticate.login(flask.request.form["username"], flask.request.form["password"])
            flask.session["username"] = flask.request.form["username"]
            flask.session["admin"] = admin
            flask.session["course_group"] = course_group
            flask.session["creator"] = creator
            
            if admin:
                return flask.redirect(flask.url_for("admin_hub"))
            else:
                return flask.redirect(flask.url_for("viewer"))
        except LoginFailure:
            error = "Invalid username or password"
    
    return flask.render_template("login.html", error=error)

@app.route("/admin_hub")
def admin_hub():
    return flask.render_template("admin_hub.html")
    
@app.route("/generator")
def generator():
    return flask.render_template("generator.html")

@app.route("/download_template")
def download_template():
    return flask.send_file("./Data input spreadsheet template.xlsx")
        
@app.route("/generate_timetable", methods=["GET", "POST"])
def generate_timetable():
    if flask.request.method == "POST":
        file = flask.request.files['file']
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file.filename)))
    
@app.route("/viewer")
def viewer():
    return flask.render_template("viewer.html", creator=flask.session["creator"], course_group=flask.session["course_group"], admin=flask.session["admin"])

if __name__ == "__main__":
    app.run(debug=True)