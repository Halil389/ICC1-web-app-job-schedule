# app.py
from flask import Flask
from config import Config
from extensions import db, login_manager
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import uuid

# Azure Cosmos DB imports
from azure.cosmos import CosmosClient, PartitionKey, exceptions


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

# ---------- Cosmos DB Setup ----------
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME", "TaskDB")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "Tasks")

cosmos_client = CosmosClient(COSMOS_URI, COSMOS_KEY)
database = cosmos_client.create_database_if_not_exists(id=COSMOS_DB_NAME)
container = database.create_container_if_not_exists(
    id=COSMOS_CONTAINER_NAME,
    partition_key=PartitionKey(path="/userId"),  # adjust partition key as needed
    offer_throughput=400
)

# ---------- New Route to Auto-Create Task ----------
@app.route('/create-task/<string:task_name>', methods=['GET'])
def create_task(task_name):
    try:
        task_item = {
            "id": str(uuid.uuid4()),  # unique ID
            "taskName": task_name,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "userId": "default"  # you can replace with actual logged-in user ID
        }

        container.create_item(body=task_item)

        return jsonify({"message": "Task created", "task": task_item}), 201
    except exceptions.CosmosHttpResponseError as e:
        return jsonify({"error": str(e)}), 500

# This block ensures that database tables are created if they don't exist.
# It's crucial for initial setup and for the "self-contained monolith" requirement.
# It uses app.app_context() to ensure that Flask's application context is active
# when interacting with the database, which is necessary for SQLAlchemy.

@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}


with app.app_context():
    # Create all database tables defined in models.py
    # This will only create tables if they don't already exist.
    db.create_all()



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=8080)
