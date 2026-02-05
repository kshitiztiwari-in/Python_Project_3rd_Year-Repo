from flask import Flask
from utils.extensions import mysql  

from routes.home import home_bp
from routes.admin import admin_bp

app = Flask(__name__)

app.config['SECRET_KEY'] = "ajsdh2378yr238yr2@#jds"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'blood_donation_web_application'

mysql.init_app(app)

# Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)
