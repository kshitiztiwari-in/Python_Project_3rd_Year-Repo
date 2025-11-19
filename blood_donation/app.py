from flask import Flask
from routes.home import home_bp
from flask_mysqldb import MySQL


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'blood_donation_web_application'

mysql = MySQL(app)

# REGISTER BLUEPRINTS
app.register_blueprint(home_bp)

if __name__ == "__main__":
    app.run(debug=True)
