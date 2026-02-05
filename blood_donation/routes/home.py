from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

# from flask_mysqldb import MySQL
from utils.extensions import mysql

home_bp = Blueprint('home_bp', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_logged_in"):
            return redirect(url_for("home_bp.login"))
        return f(*args, **kwargs)
    return decorated


@home_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT donor_id, full_name, password FROM donors WHERE email = %s",
            (email,)
        )
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            session["user_logged_in"] = True
            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect(url_for("home_bp.home"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")

@home_bp.route("/home")
@login_required
def home():
    return render_template('home.html')

@home_bp.route("/why-donate")
def why_donate():
    return render_template("why_donate.html")


@home_bp.route("/who-can-donate")
def who_can_donate():
    return render_template("who_can_donate.html")


@home_bp.route("/donation-process")
def donation_process():
    return render_template("donation_process.html")


@home_bp.route("/find_donor", methods=["GET", "POST"])
@login_required
def find_donor():
    donors = []
    selected_group = None

    if request.method == "POST":
        selected_group = request.form.get("blood_group")

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT full_name, gender, age, phone, address
            FROM donors
            WHERE blood_group = %s
        """, (selected_group,))
        donors = cur.fetchall()
        cur.close()

        return render_template(
            "donor_list.html",
            donors=donors,
            blood_group=selected_group
        )

    return render_template("find_donor.html")

@home_bp.route("/campings")
@login_required
def campaigns():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT campaign_id, name, location, date, organizer
        FROM campaigns
        WHERE status = 'Active'
        ORDER BY date ASC
    """)
    campaigns = cur.fetchall()
    cur.close()

    return render_template(
        "campaings.html",
        campaigns=campaigns
    )
    # return render_template('campaings.html')

@home_bp.route("/campaigns/<int:campaign_id>/donate", methods=["GET", "POST"])
@login_required
def donate_campaign(campaign_id):

    donor_id = session["user_id"]
    cur = mysql.connection.cursor()

    # Fetch campaign (only Active)
    cur.execute("""
        SELECT campaign_id, name
        FROM campaigns
        WHERE campaign_id = %s AND status = 'Active'
    """, (campaign_id,))
    campaign = cur.fetchone()

    if not campaign:
        flash("Campaign not available", "danger")
        cur.close()
        return redirect(url_for("home_bp.campaigns"))

    # Fetch donor details
    cur.execute("""
        SELECT full_name, blood_group
        FROM donors
        WHERE donor_id = %s
    """, (donor_id,))
    donor = cur.fetchone()

    if request.method == "POST":
        units = int(request.form["units"])
        blood_group = donor[1]

        try:
            # 1️⃣ Insert donation
            cur.execute("""
                INSERT INTO donations
                (donor_id, campaign_id, blood_group, units_donated)
                VALUES (%s, %s, %s, %s)
            """, (donor_id, campaign_id, blood_group, units))

            # 2️⃣ Update blood stock
            cur.execute("""
                UPDATE blood_stock
                SET quantity = quantity + %s,
                    status = CASE
                        WHEN quantity + %s >= 10 THEN 'Stable'
                        WHEN quantity + %s >= 5 THEN 'Low'
                        ELSE 'Critical'
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE blood_group = %s
            """, (units, units, units, blood_group))

            mysql.connection.commit()
            cur.close()

            flash("Thank you for donating blood ❤️", "success")
            return redirect(url_for("home_bp.campaigns"))

        except Exception as e:
            mysql.connection.rollback()
            cur.close()

            flash("Donation failed. Please try again.", "danger")
            return redirect(url_for("home_bp.campaigns"))  # ✅ IMPORTANT

    cur.close()

    return render_template(
        "donate.html",
        campaign=campaign,
        donor=donor
    )

@home_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        
        full_name = request.form['full_name']
        email = request.form['email']
        address = request.form['address']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        password = request.form['password']

        # ---- Prevent Duplicate Email ----
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM donors WHERE email=%s", (email,))
        existing = cur.fetchone()

        if existing:
            flash("Email already exists!", "danger")
            return redirect("/register")

        # ---- Hash Password ----
        hashed_password = generate_password_hash(password)

        # ---- Insert Query ----
        cur.execute("""
            INSERT INTO donors (full_name, gender, age, blood_group, phone, email, address, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (full_name, gender, age, blood_group, phone, email, address, hashed_password))

        mysql.connection.commit()
        cur.close()

        flash("Registration successful!", "success")
        return redirect("/register")

    return render_template("register.html")

@home_bp.route("/contact_us")
@login_required
def contact_us():
    return render_template("contact_us.html")

@home_bp.route("/donate")
@login_required
def donate():
    return "<h2>Donate_now page coming soon</h2>"

@home_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home_bp.login"))