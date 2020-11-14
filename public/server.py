from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime, timedelta
from dotenv import load_dotenv
from random import choice
from string import ascii_letters

import os

app = Flask(__name__)

load_dotenv('.env')

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DIRECTOR_DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = ("Find A Tutor", app.config["MAIL_USERNAME"])
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

METHODS = ["GET", "POST"]
ID = 0
FNAME = 1
LNAME = 2
EMAIL = 3
PWD = 4
CONFIRMATION = 5

class User(db.Model):
    id_ = db.Column("id", db.Integer, primary_key=True)
    fname = db.Column(db.String(120), nullable=False)
    lname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    pwd = db.Column(db.Text, nullable=False)
    confirmation = db.Column(db.Text)

    def __repr__(self):
        return f"{self.fname} {self.lname}"

class Request(db.Model):
    id_ = db.Column("id", db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False)
    asker_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    asker = db.relationship(
        "User", 
        foreign_keys=[asker_id],
        backref=db.backref('requests', lazy=True))
    tutor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tutor = db.relationship(
        "User", 
        foreign_keys=[tutor_id],
        backref=db.backref('requested', lazy=True))

    def __repr__(self):
        return f"{self.asker} requests {self.tutor}"
    

def set_session_timeout(remember):
    session.permanent = True
    if remember:
        app.permanent_session_lifetime = timedelta(days=20)
    else:
        app.permanent_session_lifetime = timedelta(minutes=20)
    session.modified = True

def regenerate_tables(user, request):
    users_query = user.query.all()
    users = []
    for user in users_query:
        users.append([user.id_, user.fname, user.lname, user.email, user.pwd, user.confirmation])
    requests_query = request.query.all()
    requests = []
    for request in requests_query:
        requests.append([request.id_, request.asker_id, request.tutor_id])
    return users, requests

@app.before_first_request
def create_db():
    db.create_all()

create_db()
users, requests = regenerate_tables(User, Request)

@app.route("/")
def index():
    return render_template("index.html", user=session.get("user"))

@app.route("/login", methods=METHODS)
def login():
    if session.get("user"):
        flash("You are already logged in!")
        return redirect(url_for("myaccount"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        rememberme = request.form.get("rememberme")
        matching_user = User.query.filter_by(email=email).first()
        if matching_user and password == matching_user.pwd:
            session["user"] = [
                matching_user.id_, 
                matching_user.fname, 
                matching_user.lname, 
                matching_user.email, 
                matching_user.pwd, 
                matching_user.confirmation
            ]
            set_session_timeout(rememberme)
            flash(f"Successfully Logged In as {matching_user.fname} {matching_user.lname}!")
            return redirect(url_for("index"))
        elif matching_user:
            flash(f"Incorrect Password! Please try again.")
            return redirect(url_for("login"))
        else:
            flash(f"Incorrect Username! Please try again.")
            return redirect(url_for("login"))
    return render_template("login.html", user=session.get("user"))

@app.route("/register", methods=METHODS)
def register():
    if session.get("user"):
        flash("You are already logged in!")
        return redirect(url_for("myaccount"))
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        password = request.form.get("password")
        matching_user = User.query.filter_by(email=email).first()
        if matching_user:
            flash(f"There is already an account with this email! " + 
                "Please Log In or use a different email.")
            return redirect(url_for("register"))
        else:
            code = "".join([choice(ascii_letters) for _ in range(6)])
            newuser = User(fname=fname, lname=lname, email=email, pwd=password, confirmation=code)
            db.session.add(newuser)
            db.session.commit()
            users, requests = regenerate_tables(User, Request)
            msg = Message(
                subject="Welcome to Find A Tutor!",
                recipients=[email],
                html="Thanks for registering as a user on Find A Tutor! Log In to get started! " + 
                    "<br><br>Once you log in, you will need to verify your email. " + 
                    f"Please do so by using the code '{code}'."
            )
            mail.send(msg)
            flash("You have successfully been registered! Log In and check your email to verify.")
            return redirect(url_for("login"))
    return render_template("register.html", user=session.get("user"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully Logged Out!")
    return redirect(url_for("login"))

@app.route("/myaccount", methods=METHODS)
def myaccount():
    if not session.get("user"):
        flash("Please Log In or Sign Up to access this page!")
        return redirect(url_for("index"))
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = session["user"][EMAIL]
        oldpassword = request.form.get("oldpassword")
        password = request.form.get("password")
        matching_user = User.query.filter_by(email=email).first()
        if matching_user.pwd == oldpassword:
            changes = []
            change_made = False
            if not fname == matching_user.fname:
                changes.append(f"<li>First Name: {matching_user.fname} -> {fname}</li>")
                change_made = True
            if not lname == matching_user.lname:
                changes.append(f"<li>Last Name: {matching_user.lname} -> {lname}</li>")
                change_made = True
            if not password == "":
                changes.append(f"<li>Password: {matching_user.pwd} -> {password}</li>")
                change_made = True
            if change_made:
                changes = "<br>".join(changes)
                msg = Message(
                    subject="Find A Tutor: Changes to your Account",
                    recipients=[session["email"]],
                    html="Changes were made to your account:<br><ul>" + changes + "</ul>"
                )
                mail.send(msg)
                matching_user.fname = fname
                matching_user.lname = lname
                matching_user.pwd = password if password else matching_user.pwd
                db.session.commit()
                session["user"] = [
                    matching_user.id_, 
                    matching_user.fname, 
                    matching_user.lname, 
                    matching_user.email, 
                    matching_user.pwd, 
                    matching_user.confirmation
                ]
                users, requests = regenerate_tables(User, Request)
                flash("Your account info has been changed! A confirmation email has been sent.")
            else:
                flash("No Profile Changes Detected!")
            return redirect(url_for("myaccount"))
        else:
            flash("Incorrect Old Password! Please Reset Password or Try Again.")
            return redirect(url_for("myaccount"))
    return render_template("myaccount.html", user=session.get("user"))

@app.route("/request")
def request_page():
    if not session.get("user"):
        flash("Please Log In or Sign Up to access this page!")
        return redirect(url_for("index"))
    users, requests = regenerate_tables(User, Request)
    return render_template("request.html", user=session.get("user"), users=users)

@app.route("/ask/<int:id_>")
def ask(id_):
    if not session.get("user"):
        flash("Please Log In or Sign Up to access this page!")
        return redirect(url_for("index"))
    matching_user = User.query.filter_by(id_=id_).first()
    newrequest = Request(
        datetime=datetime.now(), 
        asker=User.query.filter_by(id_=session["user"][ID]).first(), 
        tutor=matching_user
    )
    db.session.add(newrequest)
    db.session.commit()
    msg = Message(
        subject=f"Request for Tutoring from {session['user'][FNAME]} {session['user'][LNAME]}", 
        recipients=[matching_user.email], 
        html=f"{session['user'][FNAME]} {session['user'][LNAME]} requested tutoring! " +
        "Go to your tutoring page on Find My Tutor to view all your requests for tutoring. "
    )
    mail.send(msg)
    flash("Your request for tutoring has been successfully submitted! " + 
    "If the tutor accepts your request, you will get an email with their contact info.")
    return redirect(url_for("request_page"))

@app.route("/myrequests")
def my_requests():
    if not session.get("user"):
        flash("Please Log In or Sign Up to access this page!")
        return redirect(url_for("index"))
    users, requests = regenerate_tables(User, Request)
    me = User.query.filter_by(id_=session["user"][ID]).first()
    requests = me.requests
    requested = me.requested
    return render_template(
        "myrequests.html", 
        user=session.get("user"), 
        requests=requests, 
        requested=requested)

# TODO
# Allow user to verify email by entering confirmation code
    # Verification: Query database for value of confirm_status and check if it matches code entered
    # https://stackoverflow.com/questions/4582264/python-sqlalchemy-order-by-datetime
# Let user select subjects they can Tutor
    # Add new column in DB for CSV of tutorable subjects
    # Let user check all subjects they can tutor when signing up
    # Display tutorable subjects on list of users page
    # IF TIME PERMITS: Add sorting feature to sort tutors by certain tutorable subjects
# Allow tutoring to occur
    # Allow the tutor to accept or decline tutoring offer
        # Link in email takes the tutor to a "Tutoring Requests" page
            # Tutor can accept or reject tutoring requests here
        # IF TIME PERMITS: Add two links in email: one to accept and one to decline
    # Email the tutor requester that their tutoring request has been (confirmed/rejected)
        # If the tutoring request was confirmed, give the tutor requester the email of the tutor
        # Also allow tutor to access email of tutor requester
            # On Requests page - Add a "Current" Tab with emails of current tutor requesters?
            # Email the tutor with the email of the tutor requester? (Inefficient - Too many emails)
        # Now Tutors can communicate? Purpose of website SOLVED!
