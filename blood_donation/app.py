from flask import Flask
from routes.home import home_bp

app = Flask(__name__)

# REGISTER BLUEPRINTS
app.register_blueprint(home_bp)

if __name__ == "__main__":
    app.run(debug=True)
