from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from utils.extensions import mysql
admin_bp = Blueprint('admin_bp', __name__ ,url_prefix='/admin')

def admin_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_bp.admin_login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    # If admin already logged in, skip login page
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.admin_dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT admin_id, username, password FROM admin WHERE username = %s",
            (username,)
        )
        admin = cur.fetchone()
        cur.close()

        if admin and check_password_hash(admin[2], password):
            session["admin_logged_in"] = True
            session["admin_id"] = admin[0]
            session["admin_username"] = admin[1]

            flash("Admin login successful", "success")
            return redirect(url_for("admin_bp.admin_dashboard"))

        # Same message for security
        flash("Invalid username or password", "danger")

    return render_template("admin/admin_login.html")

@admin_bp.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        cur = mysql.connection.cursor()

        # 🔍 Check duplicate username or email
        cur.execute(
            "SELECT admin_id FROM admin WHERE username = %s OR email = %s",
            (username, email)
        )
        existing_admin = cur.fetchone()

        if existing_admin:
            flash("Username or email already exists", "warning")
            cur.close()
            return render_template("admin/admin_register_admin.html")

        # 🔐 Hash password
        hashed_password = generate_password_hash(password)

        # ✅ Insert new admin
        cur.execute(
            "INSERT INTO admin (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        mysql.connection.commit()
        cur.close()

        flash("Admin registered successfully. You can now login.", "success")
        return redirect(url_for("admin_bp.admin_login"))

    return render_template("admin/admin_register_admin.html")

@admin_bp.route("/admin_dashboard")
@admin_login_required
def admin_dashboard():
    cur = mysql.connection.cursor()

    # Blood stock
    cur.execute("""
        SELECT blood_group, quantity, status
        FROM blood_stock
        ORDER BY FIELD(blood_group,'A+','A-','B+','B-','AB+','AB-','O+','O-')
    """)
    stocks = cur.fetchall()

    # Summary numbers
    cur.execute("SELECT COUNT(*) FROM blood_stock WHERE status='Critical'")
    critical_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM blood_stock WHERE status='Low'")
    low_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM blood_stock WHERE status='Stable'")
    stable_count = cur.fetchone()[0]

    cur.execute("SELECT SUM(quantity) FROM blood_stock")
    total_units = cur.fetchone()[0] or 0

    cur.close()

    return render_template(
        "admin/admin_dashboard.html",
        stocks=stocks,
        critical_count=critical_count,
        low_count=low_count,
        stable_count=stable_count,
        total_units=total_units
    )
    # return render_template('admin/admin_dashboard.html') 

@admin_bp.route("/add_camp", methods=["GET", "POST"])
@admin_login_required
def admin_add_campaign():
    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        date = request.form["date"]
        organizer = request.form.get("organizer")
        description = request.form.get("description")

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO campaigns
            (name, location, date, organizer, description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, location, date, organizer, description)
        )
        mysql.connection.commit()
        cur.close()

        flash("Campaign added successfully", "success")
        return redirect(url_for("admin_bp.admin_add_campaign"))

    return render_template("admin/admin_add_camp.html")

@admin_bp.route("/add_donor", methods=["GET", "POST"])
@admin_login_required
def admin_add_donor():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        gender = request.form["gender"]
        age = request.form["age"]
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]
        email = request.form.get("email") or None
        address = request.form.get("address") or None
        password = request.form["password"]

        cur = mysql.connection.cursor()

        # 🔍 Prevent duplicate email (if email provided)
        if email:
            cur.execute(
                "SELECT donor_id FROM donors WHERE email = %s",
                (email,)
            )
            if cur.fetchone():
                flash("Donor with this email already exists", "warning")
                cur.close()
                return render_template("admin/admin_add_donor.html")

        hashed_password = generate_password_hash(password)

        cur.execute(
            """
            INSERT INTO donors
            (full_name, gender, age, blood_group, phone, email, address, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (full_name, gender, age, blood_group, phone, email, address, hashed_password)
        )

        mysql.connection.commit()
        cur.close()

        flash("Donor added successfully", "success")
        return redirect(url_for("admin_bp.admin_add_donor"))

    return render_template("admin/admin_add_donor.html")

@admin_bp.route("/manage_camp")
@admin_login_required
def admin_manage_camp():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT campaign_id, name, location, date, organizer, status
        FROM campaigns
        ORDER BY date DESC
    """)
    campaigns = cur.fetchall()
    cur.close()

    return render_template(
        "admin/admin_manage_camp.html",
        campaigns=campaigns
    )

@admin_bp.route("/manage_camp/edit/<int:campaign_id>", methods=["GET", "POST"])
@admin_login_required
def admin_edit_campaign(campaign_id):

    cur = mysql.connection.cursor()

    if request.method == "POST":
        location = request.form["location"]
        date = request.form["date"]
        organizer = request.form.get("organizer")
        description = request.form.get("description")
        status = request.form["status"]

        cur.execute("""
            UPDATE campaigns
            SET location=%s,
                date=%s,
                organizer=%s,
                description=%s,
                status=%s
            WHERE campaign_id=%s
        """, (location, date, organizer, description, status, campaign_id))

        mysql.connection.commit()
        cur.close()

        flash("Campaign updated successfully", "success")
        return redirect(url_for("admin_bp.admin_manage_camp"))

    # GET request → fetch campaign
    cur.execute("""
        SELECT campaign_id, name, location, date, organizer, description, status
        FROM campaigns
        WHERE campaign_id=%s
    """, (campaign_id,))
    campaign = cur.fetchone()
    cur.close()

    return render_template(
        "admin/edit_campaign.html",
        campaign=campaign
    )


@admin_bp.route("/manage_donor")
@admin_login_required
def admin_manage_donors():

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            donor_id,
            full_name,
            gender,
            age,
            blood_group,
            phone,
            email,
            address,
            last_donation_date,
            created_at
        FROM donors
        ORDER BY created_at DESC
    """)
    donors = cur.fetchall()
    cur.close()

    return render_template(
        "admin/admin_manage_donors.html",
        donors=donors
    )

@admin_bp.route("/edit-donor/<int:donor_id>", methods=["GET", "POST"])
@admin_login_required
def edit_donor(donor_id):

    cur = mysql.connection.cursor()

    if request.method == "POST":
        full_name = request.form["full_name"]
        gender = request.form["gender"]
        age = request.form["age"]
        phone = request.form["phone"]
        email = request.form["email"]
        address = request.form["address"]
        last_donation_date = request.form["last_donation_date"] or None

        try:
            cur.execute("""
                UPDATE donors
                SET full_name=%s,
                    gender=%s,
                    age=%s,
                    phone=%s,
                    email=%s,
                    address=%s,
                    last_donation_date=%s
                WHERE donor_id=%s
            """, (
                full_name, gender, age,
                phone, email, address,
                last_donation_date, donor_id
            ))

            mysql.connection.commit()
            flash("Donor updated successfully", "success")
            cur.close()
            return redirect(url_for("admin_bp.admin_manage_donors"))

        except Exception:
            mysql.connection.rollback()
            flash("Failed to update donor", "danger")

    # GET request
    cur.execute("""
        SELECT donor_id, full_name, gender, age, blood_group,
               phone, email, address, last_donation_date
        FROM donors
        WHERE donor_id = %s
    """, (donor_id,))
    donor = cur.fetchone()
    cur.close()

    if not donor:
        flash("Donor not found", "danger")
        return redirect(url_for("admin_bp.admin_manage_donors"))

    return render_template("admin/edit_donor.html", donor=donor)

@admin_bp.route("/delete-donor/<int:donor_id>")
@admin_login_required
def delete_donor(donor_id):

    cur = mysql.connection.cursor()

    try:
        # Optional: delete donation history first (recommended)
        cur.execute("DELETE FROM donations WHERE donor_id = %s", (donor_id,))

        # Delete donor
        cur.execute("DELETE FROM donors WHERE donor_id = %s", (donor_id,))
        mysql.connection.commit()

        flash("Donor deleted successfully", "success")

    except Exception:
        mysql.connection.rollback()
        flash("Failed to delete donor", "danger")

    finally:
        cur.close()

    return redirect(url_for("admin_bp.admin_manage_donors"))

@admin_bp.route("/manage_request")
@admin_login_required
def admin_manage_request():
    return render_template('admin/admin_manage_requests.html')

@admin_bp.route("/blood-stock")
@admin_login_required
def admin_blood_stock():

    cur = mysql.connection.cursor()

    # Fetch all blood stock
    cur.execute("""
        SELECT blood_group, quantity, status
        FROM blood_stock
        ORDER BY FIELD(blood_group,'A+','A-','B+','B-','AB+','AB-','O+','O-')
    """)
    stocks = cur.fetchall()

    # Summary counts
    cur.execute("SELECT COUNT(*) FROM blood_stock WHERE status='Critical'")
    critical_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM blood_stock WHERE status='Low'")
    low_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM blood_stock WHERE status='Stable'")
    stable_count = cur.fetchone()[0]

    cur.execute("SELECT SUM(quantity) FROM blood_stock")
    total_units = cur.fetchone()[0] or 0

    cur.close()

    return render_template(
        "admin/admin_blood_stock.html",
        stocks=stocks,
        critical_count=critical_count,
        low_count=low_count,
        stable_count=stable_count,
        total_units=total_units
    )


@admin_bp.route("/logout")
@admin_login_required
def logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_id", None)
    session.pop("admin_username", None)

    flash("Admin logged out", "success")
    return redirect(url_for("admin_bp.admin_login"))