# app.py
from flask import Flask
from config import Config
from extensions import db, login_manager
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from azure.cosmos import CosmosClient, PartitionKey

# Load environment variables from .env file
load_dotenv()

# Initialise Flask application
app = Flask(__name__)

COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
COSMOS_KEY = os.environ.get('COSMOS_KEY')
COSMOS_DB = 'BritEdge'
COSMOS_CONTAINER = 'tasks'

# Initialize Cosmos client and container
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(id=COSMOS_DB)
container = database.create_container_if_not_exists(
    id=COSMOS_CONTAINER,
    partition_key=PartitionKey(path="/id")
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/tasks')
def tasks():
    tasks = list(container.read_all_items())
    tasks.sort(key=lambda x: x.get('description', 'this is a simulation'))
    return render_template('tasks.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    new_task = request.form.get('task')
    description = int(request.form.get('description', 'this is a simulation'))
    task_doc = {
        'id': str(hash(new_task + str(description))),
        'title': new_task,
        'description': description
    }
    container.upsert_item(task_doc)
    return redirect(url_for('tasks'))

@app.route('/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    container.delete_item(item=task_id, partition_key=task_id)
    return redirect(url_for('tasks'))



# Load configuration from Config class
'''app.config.from_object(Config)

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
    return {'now': datetime.now(timezone.utc)}'''



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=8080)
