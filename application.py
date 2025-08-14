# app.py
from flask import Flask
from config import Config
from extensions import db, login_manager
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialise Flask application
app = Flask(__name__)
# Load configuration from Config class
app.config.from_object(Config)

# Initialise SQLAlchemy with the Flask app
db.init_app(app)
login_manager.init_app(app)

# Set the login view for redirection if an unauthenticated user tries to access a protected page
login_manager.login_view = 'login'
# Set the message category for flash messages when redirection occurs
login_manager.login_message_category = 'info'

# Import models and routes after initialising db and app to avoid circular imports
from models import User, Job # Import User and Job models
from routes import * # Import all routes from routes.py

# This block ensures that database tables are created if they don't exist.
# It's crucial for initial setup and for the "self-contained monolith" requirement.
# It uses app.app_context() to ensure that Flask's application context is active
# when interacting with the database, which is necessary for SQLAlchemy.
with app.app_context():
    # Create all database tables defined in models.py
    # This will only create tables if they don't already exist.
    db.create_all()

@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
