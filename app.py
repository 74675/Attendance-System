from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from werkzeug.utils import secure_filename

import datetime
import os
import cv2
import face_recognition
import numpy as np
import PIL.Image


# =========================================================
# CUSTOM IMAGE LOADER
# =========================================================

def load_image_file(file, mode="RGB"):
    image = PIL.Image.open(file)

    if mode:
        image = image.convert(mode)

    return np.array(image)


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "SRMU_Attendance_Super_Secret_Key_2026"

bcrypt = Bcrypt(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# MONGODB
# =========================================================

client = MongoClient("mongodb://localhost:27017/")

db = client["attendance_db"]

students_collection = db["students"]
teachers_collection = db["teachers"]
users_collection = db["users"]
attendance_collection = db["attendance"]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_current_user():
    roll = session.get("user")

    if not roll:
        return None

    user = (
        students_collection.find_one({"roll": roll})
        or teachers_collection.find_one({"roll": roll})
        or users_collection.find_one({"roll": roll})
    )

    return user


def user_exists(roll, erp_id):
    return (
        students_collection.find_one({
            "$or": [
                {"roll": roll},
                {"erp_id": erp_id}
            ]
        })
        or teachers_collection.find_one({
            "$or": [
                {"roll": roll},
                {"erp_id": erp_id}
            ]
        })
        or users_collection.find_one({
            "$or": [
                {"roll": roll},
                {"erp_id": erp_id}
            ]
        })
    )


def save_uploaded_image(image):
    if not image or image.filename == "":
        return None

    if not allowed_file(image.filename):
        return None

    filename = secure_filename(image.filename)

    # Prevent duplicate filenames
    name, extension = os.path.splitext(filename)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    filename = f"{name}_{timestamp}{extension}"

    path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    image.save(path)

    return path


def insert_user(data):
    role = data["role"].lower()

    if role == "student":
        students_collection.insert_one(data)

    elif role == "teacher":
        teachers_collection.insert_one(data)

    else:
        users_collection.insert_one(data)


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        roll = request.form.get("roll", "").strip()
        password = request.form.get("password", "")

        user = (
            students_collection.find_one({"roll": roll})
            or teachers_collection.find_one({"roll": roll})
            or users_collection.find_one({"roll": roll})
        )

        if user and bcrypt.check_password_hash(
            user["password"],
            password
        ):

            session["user"] = roll

            flash(
                f"Welcome back, {user.get('name', 'User')}!",
                "success"
            )

            return redirect(url_for("admin"))

        flash(
            "Invalid Roll Number or Password.",
            "danger"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(url_for("login"))


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        erp_id = request.form.get("erp_id", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()
        subject = request.form.get("subject", "").strip()
        role = request.form.get("role", "").strip().lower()
        roll = request.form.get("roll", "").strip()
        password = request.form.get("password", "")

        if not all([
            erp_id,
            name,
            course,
            subject,
            role,
            roll,
            password
        ]):
            flash(
                "Please fill all required fields.",
                "danger"
            )

            return render_template("signup.html")

        if user_exists(roll, erp_id):

            flash(
                "Roll Number or ERP ID already exists.",
                "warning"
            )

            return render_template("signup.html")

        data = {
            "erp_id": erp_id,
            "name": name,
            "course": course,
            "subject": subject,
            "role": role,
            "roll": roll,
            "password": bcrypt.generate_password_hash(
                password
            ).decode("utf-8"),

            "created_at": datetime.datetime.now()
        }

        image = request.files.get("image")

        if image and image.filename:

            image_path = save_uploaded_image(image)

            if image_path:
                data["image_path"] = image_path

            else:
                flash(
                    "Invalid image format. Use JPG, JPEG, PNG or WEBP.",
                    "danger"
                )

                return render_template("signup.html")

        insert_user(data)

        flash(
            "Account created successfully. Please login.",
            "success"
        )

        return redirect(url_for("login"))

    return render_template("signup.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect(url_for("login"))

    current_user = get_current_user()

    total_students = students_collection.count_documents({})
    total_teachers = teachers_collection.count_documents({})

    today = datetime.date.today().strftime("%Y-%m-%d")

    today_present = attendance_collection.count_documents({
        "date": today,
        "status": "Present"
    })

    total_people = total_students + total_teachers

    if total_people > 0:
        attendance_percentage = round(
            (today_present / total_people) * 100,
            1
        )
    else:
        attendance_percentage = 0

    recent_attendance = list(
        attendance_collection.find()
        .sort("_id", -1)
        .limit(8)
    )

    for record in recent_attendance:

        person = (
            students_collection.find_one(
                {"roll": record["roll"]}
            )
            or teachers_collection.find_one(
                {"roll": record["roll"]}
            )
        )

        if person:
            record["name"] = person.get(
                "name",
                "Unknown"
            )

            record["role"] = person.get(
                "role",
                "User"
            )

        else:
            record["name"] = "Unknown"
            record["role"] = "User"

    return render_template(
        "admin.html",
        user=current_user,
        total_students=total_students,
        total_teachers=total_teachers,
        today_present=today_present,
        attendance_percentage=attendance_percentage,
        recent_attendance=recent_attendance
    )


# =========================================================
# ADD USER
# =========================================================

@app.route("/add_user", methods=["GET", "POST"])
def add_user():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        erp_id = request.form.get("erp_id", "").strip()
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()
        subject = request.form.get("subject", "").strip()
        role = request.form.get("role", "").strip().lower()
        roll = request.form.get("roll", "").strip()
        password = request.form.get("password", "")

        if not all([
            erp_id,
            name,
            course,
            subject,
            role,
            roll,
            password
        ]):

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return render_template("add_user.html")

        if user_exists(roll, erp_id):

            flash(
                "Roll Number or ERP ID already exists.",
                "warning"
            )

            return render_template("add_user.html")

        data = {
            "erp_id": erp_id,
            "name": name,
            "course": course,
            "subject": subject,
            "role": role,
            "roll": roll,
            "password": bcrypt.generate_password_hash(
                password
            ).decode("utf-8"),
            "created_at": datetime.datetime.now()
        }

        image = request.files.get("image")

        if image and image.filename:

            image_path = save_uploaded_image(image)

            if image_path:
                data["image_path"] = image_path

            else:

                flash(
                    "Invalid image format.",
                    "danger"
                )

                return render_template("add_user.html")

        insert_user(data)

        flash(
            f"{role.title()} added successfully.",
            "success"
        )

        return redirect(url_for("admin"))

    return render_template("add_user.html")


# =========================================================
# MANUAL ATTENDANCE
# =========================================================

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        roll = request.form.get("roll", "").strip()

        person = (
            students_collection.find_one({"roll": roll})
            or teachers_collection.find_one({"roll": roll})
        )

        if not person:

            flash(
                "No student or teacher found with this Roll Number.",
                "danger"
            )

            return redirect(url_for("attendance"))

        today = datetime.date.today().strftime(
            "%Y-%m-%d"
        )

        already_marked = attendance_collection.find_one({
            "roll": roll,
            "date": today
        })

        if already_marked:

            flash(
                f"Attendance already marked for {person.get('name', roll)}.",
                "warning"
            )

            return redirect(url_for("attendance"))

        attendance_collection.insert_one({
            "roll": roll,
            "name": person.get("name", "Unknown"),
            "date": today,
            "status": "Present",
            "method": "Manual",
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        })

        flash(
            f"Attendance marked successfully for {person.get('name', roll)}.",
            "success"
        )

        return redirect(url_for("attendance"))

    return render_template("attendance.html")


# =========================================================
# FACE ATTENDANCE PAGE
# =========================================================

@app.route("/face_attendance")
def face_attendance():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("face_attendance.html")


# =========================================================
# FACE RECOGNITION
# =========================================================

@app.route("/start_camera")
def start_camera():

    if "user" not in session:
        return redirect(url_for("login"))

    video = cv2.VideoCapture(0)

    known_encodings = []
    known_rolls = []

    users = (
        list(
            students_collection.find({
                "image_path": {
                    "$exists": True
                }
            })
        )
        +
        list(
            teachers_collection.find({
                "image_path": {
                    "$exists": True
                }
            })
        )
    )

    for user in users:

        image_path = user.get("image_path")

        if not image_path:
            continue

        if not os.path.exists(image_path):
            continue

        try:

            img = load_image_file(image_path)

            encodings = face_recognition.face_encodings(img)

            if encodings:

                known_encodings.append(
                    encodings[0]
                )

                known_rolls.append(
                    user["roll"]
                )

        except Exception as error:

            print(
                f"Image error for {user.get('roll')}: {error}"
            )

    if not known_encodings:

        video.release()

        flash(
            "No valid face images found in the database.",
            "danger"
        )

        return redirect(
            url_for("face_attendance")
        )

    while True:

        ret, frame = video.read()

        if not ret:
            break

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        faces = face_recognition.face_locations(
            rgb_frame
        )

        encodings = face_recognition.face_encodings(
            rgb_frame,
            faces
        )

        for enc in encodings:

            matches = face_recognition.compare_faces(
                known_encodings,
                enc,
                tolerance=0.5
            )

            if True in matches:

                idx = matches.index(True)

                roll = known_rolls[idx]

                today = datetime.date.today().strftime(
                    "%Y-%m-%d"
                )

                person = (
                    students_collection.find_one({
                        "roll": roll
                    })
                    or teachers_collection.find_one({
                        "roll": roll
                    })
                )

                already_marked = attendance_collection.find_one({
                    "roll": roll,
                    "date": today
                })

                if not already_marked:

                    attendance_collection.insert_one({
                        "roll": roll,
                        "name": person.get(
                            "name",
                            "Unknown"
                        ) if person else "Unknown",
                        "date": today,
                        "status": "Present",
                        "method": "Face Recognition",
                        "time": datetime.datetime.now().strftime(
                            "%H:%M:%S"
                        )
                    })

                    video.release()
                    cv2.destroyAllWindows()

                    return render_template(
                        "face_attendance.html",
                        success_name=person.get(
                            "name",
                            roll
                        ) if person else roll,
                        success_roll=roll
                    )

                else:

                    video.release()
                    cv2.destroyAllWindows()

                    return render_template(
                        "face_attendance.html",
                        already_name=person.get(
                            "name",
                            roll
                        ) if person else roll,
                        already_roll=roll
                    )

        cv2.imshow(
            "SRMU Face Attendance Scanner",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video.release()

    cv2.destroyAllWindows()

    return render_template(
        "face_attendance.html",
        no_match=True
    )


# =========================================================
# STUDENTS
# =========================================================

@app.route("/students")
def show_students():

    if "user" not in session:
        return redirect(url_for("login"))

    students = list(
        students_collection.find().sort(
            "name",
            1
        )
    )

    return render_template(
        "students.html",
        students=students
    )


# =========================================================
# TEACHERS
# =========================================================

@app.route("/teachers")
def show_teachers():

    if "user" not in session:
        return redirect(url_for("login"))

    teachers = list(
        teachers_collection.find().sort(
            "name",
            1
        )
    )

    return render_template(
        "teachers.html",
        teachers=teachers
    )


# =========================================================
# GRAPH / ANALYTICS
# =========================================================

@app.route("/graph")
def graph():

    if "user" not in session:
        return redirect(url_for("login"))

    current_year = datetime.date.today().year

    monthly_data = []

    for month in range(1, 13):

        start_date = datetime.date(
            current_year,
            month,
            1
        )

        if month == 12:

            end_date = datetime.date(
                current_year + 1,
                1,
                1
            )

        else:

            end_date = datetime.date(
                current_year,
                month + 1,
                1
            )

        present_count = attendance_collection.count_documents({
            "status": "Present",
            "date": {
                "$gte": start_date.strftime("%Y-%m-%d"),
                "$lt": end_date.strftime("%Y-%m-%d")
            }
        })

        monthly_data.append(
            present_count
        )

    return render_template(
        "graph.html",
        monthly_data=monthly_data,
        current_year=current_year
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(413)
def too_large(error):

    flash(
        "Image size must be less than 5 MB.",
        "danger"
    )

    return redirect(
        request.referrer
        or url_for("signup")
    )


@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "base.html"
    ), 404


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )