from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os

app = Flask(__name__)
app.secret_key = "secret123"
SUBJECTS = [
    "AI", "ASM", "ADA", "OOPS", "FP", "HONOURS",
    "DSA", "DBMS", "OS", "P&S", "CN", "ML",
    "DH&V", "DMS", "DLCO"
]

# ---------------- DATABASE ---------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- MODELS ---------------- #

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(50), unique=True)
    dob = db.Column(db.String(50))


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(50))
    subject = db.Column(db.String(50))
    status = db.Column(db.String(10))
    day = db.Column(db.String(20))
    date = db.Column(db.String(20))


# ---------------- CREATE DB ---------------- #

with app.app_context():
    db.create_all()


# ---------------- LOGIN ---------------- #

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        reg = request.form["reg"]
        dob = request.form["dob"]

        user = User.query.filter_by(reg_no=reg, dob=dob).first()

        if user:
            session["user"] = reg
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        reg = request.form["reg"]
        dob = request.form["dob"]

        if User.query.filter_by(reg_no=reg).first():
            return "User already exists"

        new_user = User(reg_no=reg, dob=dob)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    reg = session["user"]

    if request.method == "POST":
        subject = request.form["subject"]
        status = request.form["status"]

        today = date.today()
        day_name = today.strftime("%A")

        new_entry = Attendance(
            reg_no=reg,
            subject=subject,
            status=status,
            day=day_name,
            date=str(today)
        )

        db.session.add(new_entry)
        db.session.commit()

    records = Attendance.query.filter_by(reg_no=reg).all()

    summary = {}

    for r in records:
        if r.subject not in summary:
            summary[r.subject] = {"present": 0, "total": 0}

        summary[r.subject]["total"] += 1

        if r.status == "Present":
            summary[r.subject]["present"] += 1

    return render_template(
    "dashboard.html",
    summary=summary,
    records=records,
    subjects=SUBJECTS
)


# ---------------- GRAPH (COLORFUL) ---------------- #

@app.route("/graph")
def graph():
    if "user" not in session:
        return redirect("/")

    reg = session["user"]
    records = Attendance.query.filter_by(reg_no=reg).all()

    subject_data = {}

    for r in records:
        if r.subject not in subject_data:
            subject_data[r.subject] = {"present": 0, "total": 0}

        subject_data[r.subject]["total"] += 1

        if r.status == "Present":
            subject_data[r.subject]["present"] += 1

    subjects = list(subject_data.keys())
    percentages = [
        (v["present"] / v["total"]) * 100 for v in subject_data.values()
    ]

    plt.figure()

    # 🎨 Colorful bars
    colors = cm.viridis(range(len(subjects)))
    plt.bar(subjects, percentages, color=colors)

    plt.xlabel("Subjects")
    plt.ylabel("Attendance %")
    plt.title("Attendance Overview")
    plt.ylim(0, 100)

    # Show % on bars
    for i, v in enumerate(percentages):
        plt.text(i, v + 2, f"{round(v,1)}%", ha='center')

    if not os.path.exists("static"):
        os.makedirs("static")

    graph_path = "static/graph.png"
    plt.savefig(graph_path)
    plt.close()

    return render_template("graph.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)