from flask import Blueprint, render_template


home_bp = Blueprint("home_bp", __name__)

@home_bp.route("/")
def home():
    return render_template("home.html")

@home_bp.route("/find_donor")
def find_donor():
    return "<h2>Find Centers page coming soon</h2>"

@home_bp.route("/register")
def register():
    return render_template("register.html")

@home_bp.route("/contact_us")
def contact_us():
    return "<h2>Contact_us page coming soon</h2>"

@home_bp.route("/donate")
def donate():
    return "<h2>Donate_now page coming soon</h2>"
