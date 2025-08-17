# app.py
from flask import Flask
from config import Config
from extensions import db, login_manager
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from azure.cosmos import CosmosClient, PartitionKey
import uuid

# Load environment variables from .env file
load_dotenv()

# Initialise Flask application
app = Flask(__name__)

COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
COSMOS_KEY = os.environ.get('COSMOS_KEY')
COSMOS_DB = 'BritEdge'
COSMOS_CONTAINER = 'Tasks'

# Initialize Cosmos client and container
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(id=COSMOS_DB)
container = database.create_container_if_not_exists(
    id=COSMOS_CONTAINER,
    partition_key=PartitionKey(path="/sid")
)



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

@app.route('/tasks')
def tasks():
    try:
        # Generate a unique ID for the new task and for the partition key 'sid'
        new_task_uuid = str(uuid.uuid4())
        new_task = {
            "id": new_task_uuid,
            "sid": new_task_uuid, # Using the UUID as the partition key value for this example
            "task_name": "Automatically Created Task: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": "This is a Simulation.",
            "status": "pending",
            "created_at": str(datetime.now(timezone.utc))
        }

        return f"Successfully created task: {new_task['task_name']} with ID: {new_task['id']}"
    except Exception as e:
        # Basic error handling in case of issues connecting or creating the item
        return f"Error creating task: {e}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=8080)
