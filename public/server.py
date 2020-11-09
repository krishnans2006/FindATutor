from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy

from datetime import timedelta
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

class User(db.Model):
    id_ = db.Column("id", db.Integer, primary_key=True)
    fname = db.Column(db.String(120), unique=True, nullable=False)
    lname = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    pwd = db.Column(db.Text, unique=True, nullable=False)
    confirmation = db.Column(db.Text)

    def __repr__(self):
        return f"{self.fname} {self.lname}"

def set_session_timeout(remember):
    session.permanent = True
    if remember:
        app.permanent_session_lifetime = timedelta(days=20)
    else:
        app.permanent_session_lifetime = timedelta(minutes=20)
    session.modified = True

@app.before_first_request
def create_db():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html", 
        fname=session.get("fname"), 
        lname=session.get("lname"), 
        email=session.get("email"), 
        password=session.get("password"))

@app.route("/login", methods=METHODS)
def login():
    if session.get("email"):
        flash("You are already logged in!")
        return redirect(url_for("myaccount"))
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        rememberme = request.form.get("rememberme")
        matching_user = User.query.filter_by(email=email).first()
        if matching_user and password == matching_user.pwd:
            session["fname"] = matching_user.fname
            session["lname"] = matching_user.lname
            session["email"] = matching_user.email
            session["password"] = matching_user.pwd
            session["confirmation"] = matching_user.confirmation
            set_session_timeout(rememberme)
            flash(f"Successfully Logged In as {matching_user.fname} {matching_user.lname}!")
            return redirect(url_for("index"))
        elif matching_user:
            flash(f"Incorrect Password! Please try again!")
            return redirect(url_for("login"))
        else:
            flash(f"Incorrect Username! Please try again!")
            return redirect(url_for("login"))
    return render_template("login.html", 
        fname=session.get("fname"), 
        lname=session.get("lname"), 
        email=session.get("email"), 
        password=session.get("password"))

@app.route("/register", methods=METHODS)
def register():
    if session.get("email"):
        flash("You are already logged in!")
        return redirect(url_for("myaccount"))
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = request.form.get("email")
        password = request.form.get("password")
        matching_user = User.query.filter_by(email=email).first()
        if matching_user:
            flash(f"There is already an account with this email, " + 
                "please Log In or use a different email!")
            return redirect(url_for("register"))
        else:
            code = "".join([choice(ascii_letters) for _ in range(6)])
            newuser = User(fname=fname, lname=lname, email=email, pwd=password, confirmation=code)
            db.session.add(newuser)
            db.session.commit()
            msg = Message(
                subject="Welcome to Find A Tutor!",
                recipients=[email],
                html=f"Thanks for registering as a user on Find A Tutor! Log In to get started! " + 
                    "<br><br>Once you log in, you will need to verify your email. " + 
                    "Please do so by using the code '{code}'."
            )
            mail.send(msg)
            flash("You have successfully been registered, Log In and check your email to verify!")
            return redirect(url_for("login"))
    return render_template("register.html", 
        fname=session.get("fname"), 
        lname=session.get("lname"), 
        email=session.get("email"), 
        password=session.get("password"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully Logged Out!")
    return redirect(url_for("login"))

@app.route("/myaccount", methods=METHODS)
def myaccount():
    if not session.get("email"):
        flash("Please Log In or Sign Up to access this page!")
        return redirect(url_for("index"))
    if request.method == "POST":
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        email = session["email"]
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
                session["fname"] = fname
                session["lname"] = lname
                session["password"] = password if password else session["password"]
                flash("Your account info has been changed, a confirmation email has been sent!")
            else:
                flash("No Profile Changes Detected!")
            return redirect(url_for("myaccount"))
        else:
            flash("Incorrect Old Password, please Reset Password or Try Again!")
            return redirect(url_for("myaccount"))
    return render_template("myaccount.html", 
        fname=session.get("fname"), 
        lname=session.get("lname"), 
        email=session.get("email"), 
        password=session.get("password"))

# TODO
# Allow user to verify email by entering confirmation code
    # Verification: Query database for value of confirm_status and check if it matches code entered
# Add list of users - in new page
# Let user select subjects they can Tutor
    # Add new column in DB for CSV of tutorable subjects
    # Let user check all subjects they can tutor when signing up
    # Display tutorable subjects on list of users page
    # IF TIME PERMITS: Add sorting feature to sort tutors by certain tutorable subjects
# Allow tutoring to occur
    # Allow a user to request tutoring from another user
        # User can click "Request" button on list of users page
    # Send the tutor an email that their service has been requested
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
