import os
import logging
from logging.handlers import RotatingFileHandler
import mysql.connector
from mysql.connector import Error
from flask import Flask, jsonify, request, g
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

# Import Service Classes
# Assuming services are in a 'services' directory/package
# Adjust the import paths based on your project structure
try:
    from services.employee_service import EmployeeService
    from services.project_service import ProjectService
    from services.task_service import TaskService
    from services.timesheet_service import TimesheetService
except ImportError as e:
    print(f"Error importing services: {e}. Please ensure service files exist and paths are correct.")
    # Depending on the setup, you might want to exit or handle this differently
    # For now, we'll proceed but note that services won't be available.
    EmployeeService = None
    ProjectService = None
    TaskService = None
    TimesheetService = None


# Load environment variables from .env file
load_dotenv()

# Initialize Flask App
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
app.config['DB_HOST'] = os.environ.get('DB_HOST', 'localhost')
app.config['DB_USER'] = os.environ.get('DB_USER', 'root')
app.config['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', '')
app.config['DB_NAME'] = os.environ.get('DB_NAME', 'timesheet_mindlinks')
app.config['DB_PORT'] = os.environ.get('DB_PORT', 3306) # Default MySQL port
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Logging Configuration
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
log_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

if not app.debug:
    app.logger.addHandler(log_handler)
else:
    # Also log to console when debugging
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    stream_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(stream_handler)

app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
app.logger.info('Flask application starting...')
app.logger.info(f"Database configured for: {app.config['DB_NAME']} on {app.config['DB_HOST']}")

# Database Connection Pool (Optional but recommended for production)
# Using a simple connection per request for now
def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host=app.config['DB_HOST'],
                user=app.config['DB_USER'],
                password=app.config['DB_PASSWORD'],
                database=app.config['DB_NAME'],
                port=app.config['DB_PORT']
            )
            app.logger.debug("New database connection established.")
        except Error as e:
            app.logger.error(f"Database connection failed: {e}")
            # Propagate the error or handle it gracefully
            raise ConnectionError(f"Could not connect to the database: {e}") from e
    return g.db

# Middleware
@app.before_request
def before_request():
    """Get database connection before each request."""
    try:
        # Store db connection in Flask's application context 'g'
        g.db = get_db()
        # You could also instantiate services here if they need the connection per request
        # g.employee_service = EmployeeService(g.db)
        # ... etc.
    except ConnectionError as e:
        # If DB connection fails on request start, return a 503 Service Unavailable
        app.logger.error(f"Database unavailable for request {request.path}: {e}")
        return jsonify({"error": "Database service is temporarily unavailable. Please try again later."}), 503
    except Exception as e:
        app.logger.error(f"Error in before_request for {request.path}: {e}")
        return jsonify({"error": "An unexpected error occurred before processing the request."}), 500


@app.teardown_request
def teardown_request(exception=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
            app.logger.debug("Database connection closed.")
        except Error as e:
            app.logger.error(f"Error closing database connection: {e}")
    if exception:
        # Log exceptions that occurred during the request handling
        app.logger.error(f"Exception occurred during request teardown: {exception}")


# Error Handlers
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = jsonify({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    app.logger.error(f"{e.code} {e.name}: {e.description} for {request.path}")
    return response

@app.errorhandler(404)
def not_found_error(error):
    """Handler for 404 Not Found errors."""
    app.logger.warning(f"404 Not Found: {request.path} ({error})")
    return jsonify({"error": "Resource not found", "message": str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler for 500 Internal Server Error."""
    # If a DB connection was open and caused the error, try to close it
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Error as db_close_err:
            app.logger.error(f"Error closing DB connection during 500 handling: {db_close_err}")

    app.logger.error(f"500 Internal Server Error: {request.path} ({error})")
    # Log the stack trace for debugging
    import traceback
    app.logger.error(traceback.format_exc())
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred. Please try again later."}), 500

@app.errorhandler(Exception)
def handle_generic_exception(e):
    """Handler for any other unhandled exceptions."""
     # If a DB connection was open and caused the error, try to close it
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Error as db_close_err:
            app.logger.error(f"Error closing DB connection during generic exception handling: {db_close_err}")

    # Log the exception and stack trace
    app.logger.error(f"Unhandled Exception: {request.path} ({e})")
    import traceback
    app.logger.error(traceback.format_exc())

    # Check if it's an HTTPException instance and handle accordingly
    if isinstance(e, HTTPException):
        return handle_http_exception(e)

    # For non-HTTP exceptions, return a generic 500 response
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred."}), 500


# Instantiate Services (if needed globally, otherwise instantiate within routes or before_request)
# For now, we just ensure they are imported. Actual usage will depend on route implementations.
# Example (if services don't need request-specific context like db connection passed at init):
# if EmployeeService: employee_service = EmployeeService()
# if ProjectService: project_service = ProjectService()
# if TaskService: task_service = TaskService()
# if TimesheetService: timesheet_service = TimesheetService()

app.logger.info("Application setup complete. Ready to handle requests.")

# --- ROUTES WILL BE ADDED BELOW THIS LINE ---
# (Do not add routes here as per instructions)

# --- MAIN EXECUTION ---
# (Typically only used for local development)
if __name__ == '__main__':
    # IMPORTANT: Use a production-ready WSGI server like Gunicorn or uWSGI for deployment
    # The Flask development server is not suitable for production.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=app.config['DEBUG'])


# --------------------
# Employee Routes
# --------------------

```python
import datetime
from flask import Blueprint, request, jsonify
from services.employee_service import EmployeeService
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError, Conflict

# Assuming EmployeeService is correctly implemented and imported
# from services.employee_service import EmployeeService

employee_api = Blueprint('employee_api', __name__)
employee_service = EmployeeService()

@employee_api.route('/employees', methods=['POST'])
def create_employee():
    """
    Creates a new employee.
    Expects JSON payload with employee details.
    Required fields: emp_Id, emp_name, created_by.
    Optional fields: emp_designation, emp_skills, date_of_join.
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("Request body must be JSON.")

        # --- Input Validation ---
        required_fields = ['emp_Id', 'emp_name', 'created_by']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

        emp_id = data.get('emp_Id')
        emp_name = data.get('emp_name')
        emp_designation = data.get('emp_designation')
        emp_skills = data.get('emp_skills')
        date_of_join_str = data.get('date_of_join')
        created_by = data.get('created_by')
        created_date = datetime.date.today() # Set creation date automatically
        last_updated_by = created_by # Initially, creator is also the last updater
        last_updated_date = created_date # Initially, creation date is also the last update date

        # Validate date format if provided
        date_of_join = None
        if date_of_join_str:
            try:
                date_of_join = datetime.datetime.strptime(date_of_join_str, '%Y-%m-%d').date()
            except ValueError:
                raise BadRequest("Invalid date format for date_of_join. Use YYYY-MM-DD.")

        # --- Service Call ---
        new_employee_data = {
            'emp_Id': emp_id,
            'emp_name': emp_name,
            'emp_designation': emp_designation,
            'emp_skills': emp_skills,
            'date_of_join': date_of_join,
            'created_by': created_by,
            'created_date': created_date,
            'last_updated_by': last_updated_by,
            'last_updated_date': last_updated_date
        }
        created_employee = employee_service.create_employee(new_employee_data)

        if created_employee:
             # Convert date objects to strings for JSON serialization
            if 'date_of_join' in created_employee and created_employee['date_of_join']:
                created_employee['date_of_join'] = created_employee['date_of_join'].isoformat()
            if 'created_date' in created_employee and created_employee['created_date']:
                created_employee['created_date'] = created_employee['created_date'].isoformat()
            if 'last_updated_date' in created_employee and created_employee['last_updated_date']:
                created_employee['last_updated_date'] = created_employee['last_updated_date'].isoformat()
            return jsonify(created_employee), 201
        else:
            # This case might indicate a service-level issue not caught by exceptions
            raise InternalServerError("Employee creation failed for an unknown reason.")

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Conflict as e: # Assuming service raises Conflict for duplicate emp_Id
        return jsonify({"error": str(e)}), 409
    except NotFound as e: # Assuming service raises NotFound if created_by/last_updated_by emp_Id doesn't exist
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # Log the exception e
        print(f"Error creating employee: {e}") # Replace with proper logging
        raise InternalServerError("An unexpected error occurred during employee creation.")


@employee_api.route('/employees', methods=['GET'])
def get_all_employees():
    """Retrieves all employees."""
    try:
        employees = employee_service.get_all_employees()
        # Convert date objects to strings for JSON serialization
        for emp in employees:
            if 'date_of_join' in emp and emp['date_of_join']:
                emp['date_of_join'] = emp['date_of_join'].isoformat()
            if 'created_date' in emp and emp['created_date']:
                emp['created_date'] = emp['created_date'].isoformat()
            if 'last_updated_date' in emp and emp['last_updated_date']:
                emp['last_updated_date'] = emp['last_updated_date'].isoformat()
        return jsonify(employees), 200
    except Exception as e:
        # Log the exception e
        print(f"Error retrieving employees: {e}") # Replace with proper logging
        raise InternalServerError("An unexpected error occurred while retrieving employees.")

@employee_api.route('/employees/<string:emp_id>', methods=['GET'])
def get_employee_by_id(emp_id):
    """Retrieves a specific employee by their emp_Id."""
    try:
        if not emp_id:
             raise BadRequest("Employee ID (emp_Id) is required.")

        employee = employee_service.get_employee_by_emp_id(emp_id)
        if employee:
            # Convert date objects to strings for JSON serialization
            if 'date_of_join' in employee and employee['date_of_join']:
                employee['date_of_join'] = employee['date_of_join'].isoformat()
            if 'created_date' in employee and employee['created_date']:
                employee['created_date'] = employee['created_date'].isoformat()
            if 'last_updated_date' in employee and employee['last_updated_date']:
                employee['last_updated_date'] = employee['last_updated_date'].isoformat()
            return jsonify(employee), 200
        else:
            raise NotFound(f"Employee with emp_Id '{emp_id}' not found.")
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # Log the exception e
        print(f"Error retrieving employee {emp_id}: {e}") # Replace with proper logging
        raise InternalServerError(f"An unexpected error occurred while retrieving employee {emp_id}.")


@employee_api.route('/employees/<string:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    """
    Updates an existing employee.
    Expects JSON payload with fields to update.
    Requires 'last_updated_by' field in the payload.
    Cannot update 'emp_Id', 'created_by', 'created_date'.
    """
    try:
        if not emp_id:
             raise BadRequest("Employee ID (emp_Id) is required for update.")

        data = request.get_json()
        if not data:
            raise BadRequest("Request body must be JSON.")

        # --- Input Validation ---
        if 'last_updated_by' not in data or not data['last_updated_by']:
            raise BadRequest("Missing required field: last_updated_by")

        # Prevent updating immutable fields
        immutable_fields = ['emp_Id', 'created_by', 'created_date']
        for field in immutable_fields:
            if field in data:
                raise BadRequest(f"Field '{field}' cannot be updated.")

        update_data = data.copy() # Create a copy to modify
        update_data['last_updated_date'] = datetime.date.today() # Set update date automatically

        # Validate date format if provided
        if 'date_of_join' in update_data and update_data['date_of_join']:
            try:
                update_data['date_of_join'] = datetime.datetime.strptime(update_data['date_of_join'], '%Y-%m-%d').date()
            except (ValueError, TypeError): # Added TypeError for None case
                 raise BadRequest("Invalid date format for date_of_join. Use YYYY-MM-DD.")
        elif 'date_of_join' in update_data and update_data['date_of_join'] is None:
             # Allow setting date_of_join to null if needed
             pass


        # --- Service Call ---
        updated_employee = employee_service.update_employee(emp_id, update_data)

        if updated_employee:
             # Convert date objects to strings for JSON serialization
            if 'date_of_join' in updated_employee and updated_employee['date_of_join']:
                updated_employee['date_of_join'] = updated_employee['date_of_join'].isoformat()
            if 'created_date' in updated_employee and updated_employee['created_date']:
                updated_employee['created_date'] = updated_employee['created_date'].isoformat()
            if 'last_updated_date' in updated_employee and updated_employee['last_updated_date']:
                updated_employee['last_updated_date'] = updated_employee['last_updated_date'].isoformat()
            return jsonify(updated_employee), 200
        else:
            # Service should raise NotFound if employee doesn't exist
            raise NotFound(f"Employee with emp_Id '{emp_id}' not found or update failed.")

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except NotFound as e: # Handles employee not found or last_updated_by not found
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # Log the exception e
        print(f"Error updating employee {emp_id}: {e}") # Replace with proper logging
        raise InternalServerError(f"An unexpected error occurred during employee update for {emp_id}.")


@employee_api.route('/employees/<string:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    """Deletes an employee by their emp_Id."""
    try:
        if not emp_id:
             raise BadRequest("Employee ID (emp_Id) is required for deletion.")

        # --- Service Call ---
        deleted = employee_service.delete_employee(emp_id)

        if deleted:
            return jsonify({"message": f"Employee with emp_Id '{emp_id}' deleted successfully."}), 200
            # Or return 204 No Content
            # return '', 204
        else:
            # Service should raise NotFound if employee doesn't exist
             raise NotFound(f"Employee with emp_Id '{emp_id}' not found or deletion failed.")

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Conflict as e: # Assuming service raises Conflict due to FK constraints
         return jsonify({"error": f"Cannot delete employee '{emp_id}'. It might be referenced by other records (e.g., Projects, Tasks, Timesheets). Details: {str(e)}"}), 409
    except Exception as e:
        # Log the exception e
        print(f"Error deleting employee {emp_id}: {e}") # Replace with proper logging
        raise InternalServerError(f"An unexpected error occurred during employee deletion for {emp_id}.")

# Add other specific employee routes if required by business logic later
# For example:
# - /employees/search?skill=python
# - /employees/<emp_id>/projects
# - /employees/<emp_id>/tasks
# - /employees/designation/<designation_name>

# Note: Authentication/Authorization (JWT checks) should be added as decorators
# to these routes in a real application, likely using Flask extensions like Flask-JWT-Extended.
# Example: @jwt_required() before the function definition.
```


# --------------------
# Project Routes
# --------------------

```python
from flask import Blueprint, request, jsonify
from services.project_service import ProjectService
from datetime import datetime

# Assuming ProjectService is correctly implemented and imported
# from services.project_service import ProjectService

# Instantiate the service
project_service = ProjectService()

# Create a Blueprint for project routes
project_bp = Blueprint('project_bp', __name__, url_prefix='/projects')

# --- Project Routes ---

@project_bp.route('', methods=['POST'])
def create_project():
    """
    Creates a new project.
    Expects JSON payload with project details.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON payload required"}), 400

    # --- Input Validation ---
    required_fields = ['proj_name', 'project_description', 'project_status', 'created_by']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Validate project_status enum
    allowed_statuses = ['open', 'inprogress', 'completed']
    if data.get('project_status') not in allowed_statuses:
        return jsonify({"error": f"Invalid project_status. Must be one of: {', '.join(allowed_statuses)}"}), 400

    # Validate date fields if present
    date_fields = ['go_live_date', 'dev_start_date', 'dev_end_date', 'QA_start_date', 'QA_end_date', 'UIT_start_date', 'UIT_end_date']
    for field in date_fields:
        if field in data and data[field]:
            try:
                datetime.strptime(data[field], '%Y-%m-%d')
            except (ValueError, TypeError):
                return jsonify({"error": f"Invalid date format for {field}. Use YYYY-MM-DD."}), 400
        elif field in data and not data[field]: # Handle empty string dates as None
             data[field] = None


    # Prepare data for service layer (handle optional fields)
    project_data = {
        'proj_name': data['proj_name'],
        'project_description': data['project_description'],
        'project_status': data['project_status'],
        'go_live_date': data.get('go_live_date'),
        'dev_start_date': data.get('dev_start_date'),
        'dev_end_date': data.get('dev_end_date'),
        'QA_start_date': data.get('QA_start_date'),
        'QA_end_date': data.get('QA_end_date'),
        'UIT_start_date': data.get('UIT_start_date'),
        'UIT_end_date': data.get('UIT_end_date'),
        'created_by': data['created_by'],
        # last_updated_by is not needed on creation, service might handle created_date/last_updated_date
    }

    try:
        new_project = project_service.create_project(project_data)
        if new_project:
            # Convert date objects to strings for JSON serialization if service returns them
            if isinstance(new_project.get('created_date'), datetime):
                new_project['created_date'] = new_project['created_date'].strftime('%Y-%m-%d')
            if isinstance(new_project.get('last_updated_date'), datetime):
                 new_project['last_updated_date'] = new_project['last_updated_date'].strftime('%Y-%m-%d')
            for field in date_fields:
                 if field in new_project and isinstance(new_project[field], datetime):
                     new_project[field] = new_project[field].strftime('%Y-%m-%d')

            return jsonify(new_project), 201 # 201 Created
        else:
            # This case might indicate a validation error handled within the service
            return jsonify({"error": "Failed to create project, possibly due to invalid foreign key (created_by)"}), 400
    except ValueError as ve: # Catch specific validation errors from service
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Log the exception e
        print(f"Error creating project: {e}") # Replace with proper logging
        return jsonify({"error": "An unexpected error occurred"}), 500

@project_bp.route('', methods=['GET'])
def get_all_projects():
    """
    Retrieves all projects.
    Optionally filters by status using query parameter `status`.
    """
    status_filter = request.args.get('status')
    allowed_statuses = ['open', 'inprogress', 'completed']

    if status_filter and status_filter not in allowed_statuses:
         return jsonify({"error": f"Invalid status filter. Must be one of: {', '.join(allowed_statuses)}"}), 400

    try:
        projects = project_service.get_all_projects(status=status_filter)
        # Convert date objects to strings for JSON serialization
        for project in projects:
            for key, value in project.items():
                if isinstance(value, datetime):
                    project[key] = value.strftime('%Y-%m-%d')
        return jsonify(projects), 200
    except Exception as e:
        # Log the exception e
        print(f"Error retrieving projects: {e}") # Replace with proper logging
        return jsonify({"error": "An unexpected error occurred"}), 500

@project_bp.route('/<int:project_id>', methods=['GET'])
def get_project_by_id(project_id):
    """
    Retrieves a specific project by its ID.
    """
    if not isinstance(project_id, int) or project_id <= 0:
        return jsonify({"error": "Invalid project ID format"}), 400

    try:
        project = project_service.get_project_by_id(project_id)
        if project:
            # Convert date objects to strings for JSON serialization
            for key, value in project.items():
                if isinstance(value, datetime):
                    project[key] = value.strftime('%Y-%m-%d')
            return jsonify(project), 200
        else:
            return jsonify({"error": f"Project with ID {project_id} not found"}), 404
    except Exception as e:
        # Log the exception e
        print(f"Error retrieving project {project_id}: {e}") # Replace with proper logging
        return jsonify({"error": "An unexpected error occurred"}), 500

@project_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Updates an existing project by its ID.
    Expects JSON payload with fields to update.
    Requires 'last_updated_by' field in the payload.
    """
    if not isinstance(project_id, int) or project_id <= 0:
        return jsonify({"error": "Invalid project ID format"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input, JSON payload required"}), 400

    # --- Input Validation ---
    if 'last_updated_by' not in data or not data['last_updated_by']:
        return jsonify({"error": "Missing required field: last_updated_by"}), 400

    # Validate project_status enum if present
    allowed_statuses = ['open', 'inprogress', 'completed']
    if 'project_status' in data and data['project_status'] not in allowed_statuses:
        return jsonify({"error": f"Invalid project_status. Must be one of: {', '.join(allowed_statuses)}"}), 400

    # Validate date fields if present
    date_fields = ['go_live_date', 'dev_start_date', 'dev_end_date', 'QA_start_date', 'QA_end_date', 'UIT_start_date', 'UIT_end_date']
    update_data = {}
    for field in data:
        if field in date_fields:
            if data[field]:
                try:
                    datetime.strptime(data[field], '%Y-%m-%d')
                    update_data[field] = data[field]
                except (ValueError, TypeError):
                    return jsonify({"error": f"Invalid date format for {field}. Use YYYY-MM-DD."}), 400
            else: # Handle empty string dates as None
                update_data[field] = None
        elif field != 'ID' and field != 'created_by' and field != 'created_date': # Exclude non-updatable fields
             update_data[field] = data[field]


    if not update_data or len(update_data) == 1 and 'last_updated_by' in update_data : # Check if there's anything to update besides the mandatory last_updated_by
         return jsonify({"error": "No update data provided"}), 400


    try:
        updated_project = project_service.update_project(project_id, update_data)
        if updated_project:
             # Convert date objects to strings for JSON serialization if service returns them
            if isinstance(updated_project.get('created_date'), datetime):
                updated_project['created_date'] = updated_project['created_date'].strftime('%Y-%m-%d')
            if isinstance(updated_project.get('last_updated_date'), datetime):
                 updated_project['last_updated_date'] = updated_project['last_updated_date'].strftime('%Y-%m-%d')
            for field in date_fields:
                 if field in updated_project and isinstance(updated_project[field], datetime):
                     updated_project[field] = updated_project[field].strftime('%Y-%m-%d')

            return jsonify(updated_project), 200
        else:
            # This could mean project not found or a validation error in the service
             # Check if project exists first to give a more specific error
            if project_service.get_project_by_id(project_id) is None:
                 return jsonify({"error": f"Project with ID {project_id} not found"}), 404
            else:
                 # Assume validation error from service (e.g., invalid foreign key)
                 return jsonify({"error": "Failed to update project, possibly due to invalid foreign key (last_updated_by)"}), 400

    except ValueError as ve: # Catch specific validation errors from service
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Log the exception e
        print(f"Error updating project {project_id}: {e}") # Replace with proper logging
        return jsonify({"error": "An unexpected error occurred"}), 500

@project_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Deletes a project by its ID.
    """
    if not isinstance(project_id, int) or project_id <= 0:
        return jsonify({"error": "Invalid project ID format"}), 400

    try:
        success = project_service.delete_project(project_id)
        if success:
            return jsonify({"message": f"Project with ID {project_id} deleted successfully"}), 200
        else:
            # Check if project exists first to give a more specific error
            if project_service.get_project_by_id(project_id) is None:
                 return jsonify({"error": f"Project with ID {project_id} not found"}), 404
            else:
                 # If not found error wasn't raised, it might be a constraint issue
                 return jsonify({"error": f"Failed to delete project {project_id}. It might be referenced by Tasks or Timesheets."}), 400 # Or 409 Conflict
    except ValueError as ve: # Catch specific errors like dependencies
         return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Log the exception e
        print(f"Error deleting project {project_id}: {e}") # Replace with proper logging
        return jsonify({"error": "An unexpected error occurred"}), 500

# --- Special Routes (Example - if needed based on more specific requirements) ---
# Add any other project-specific routes here if required by the full specification.
# For example:
# @project_bp.route('/employee/<string:emp_id>', methods=['GET'])
# def get_projects_by_employee(emp_id):
#     """ Retrieves projects associated with a specific employee """
#     # Implementation using project_service...
#     pass

# Note: The actual Flask app setup (app = Flask(__name__), app.register_blueprint(project_bp), etc.)
# is intentionally omitted as per the instructions.
```


# --------------------
# Task Routes
# --------------------

```python
from flask import Blueprint, request, jsonify
# Assuming TaskService is in a 'services' directory
from services.task_service import TaskService
# Assuming a custom exception class exists for validation errors etc.
# from exceptions import ValidationError, NotFoundError
import logging
from datetime import datetime

# Initialize Blueprint for Task routes
task_api = Blueprint('task_api', __name__)

# Initialize TaskService
# Dependency injection might be a better approach in a larger application
task_service = TaskService()

# Configure logging
# In a real app, this would likely be configured globally
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Function for Error Handling ---
def handle_error(e, status_code=500):
    """Handles exceptions and returns a JSON error response."""
    error_message = str(e)
    # Log the full error for debugging
    logger.error(f"Error occurred: {error_message}", exc_info=True)
    # Customize status code for specific exceptions if needed
    # if isinstance(e, NotFoundError):
    #     status_code = 404
    # elif isinstance(e, ValidationError):
    #     status_code = 400
    # elif isinstance(e, ValueError): # Catch potential type conversion errors
    #      status_code = 400
    #      error_message = f"Invalid input data: {e}"

    # For now, use generic messages for common exceptions
    if isinstance(e, ValueError):
        status_code = 400
        error_message = f"Invalid input data provided: {e}"
    elif "not found" in error_message.lower(): # Basic check for not found errors from service
         status_code = 404
    elif "validation failed" in error_message.lower() or "required" in error_message.lower(): # Basic check for validation
         status_code = 400

    return jsonify({"error": error_message}), status_code

# --- Task CRUD Routes ---

@task_api.route('/tasks', methods=['POST'])
def create_task():
    """
    Creates a new task.
    Expects JSON data with task details.
    Required fields: task_id, project_ID, task_name, emp_id, created_by
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Basic Validation - Ensure required fields are present
        required_fields = ['task_id', 'project_ID', 'task_name', 'emp_id', 'created_by']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Add creation timestamp
        data['created_date'] = datetime.now().date()
        data['last_updated_by'] = data['created_by'] # Set last_updated_by on creation
        data['last_updated_date'] = data['created_date'] # Set last_updated_date on creation

        # Call service layer to create task
        new_task = task_service.create_task(data)
        if new_task:
             # Convert task object/dict to JSON serializable format if needed
             # Assuming service returns a dict or an object easily convertible
            return jsonify(new_task), 201
        else:
            # This case might indicate a service-level issue not raising an exception
            return jsonify({"error": "Task creation failed for an unknown reason"}), 500

    except ValueError as ve: # Catch potential type errors during data processing
        return handle_error(ve, 400)
    except Exception as e:
        return handle_error(e)


@task_api.route('/tasks', methods=['GET'])
def get_all_tasks():
    """Retrieves all tasks."""
    try:
        tasks = task_service.get_all_tasks()
        # Convert task objects/dicts to JSON serializable format if needed
        return jsonify(tasks), 200
    except Exception as e:
        return handle_error(e)


@task_api.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Retrieves a specific task by its ID."""
    try:
        task = task_service.get_task_by_id(task_id)
        if task:
            # Convert task object/dict to JSON serializable format if needed
            return jsonify(task), 200
        else:
            return jsonify({"error": f"Task with ID {task_id} not found"}), 404
    except Exception as e:
        return handle_error(e)


@task_api.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Updates an existing task.
    Expects JSON data with fields to update.
    Requires 'last_updated_by' field in the JSON body.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Validation - Ensure last_updated_by is provided for audit trail
        if 'last_updated_by' not in data or not data['last_updated_by']:
             return jsonify({"error": "Missing required field for update: 'last_updated_by'"}), 400

        # Add update timestamp
        data['last_updated_date'] = datetime.now().date()

        # Call service layer to update task
        updated_task = task_service.update_task(task_id, data)
        if updated_task:
            # Convert task object/dict to JSON serializable format if needed
            return jsonify(updated_task), 200
        else:
            # Service should raise NotFoundError if task doesn't exist
            return jsonify({"error": f"Task with ID {task_id} not found or update failed"}), 404

    except ValueError as ve: # Catch potential type errors during data processing
        return handle_error(ve, 400)
    except Exception as e:
        # Check if the error message indicates "not found" to return 404
        if "not found" in str(e).lower():
            return handle_error(e, 404)
        return handle_error(e)


@task_api.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Deletes a task by its ID."""
    try:
        deleted = task_service.delete_task(task_id)
        if deleted:
            return jsonify({"message": f"Task with ID {task_id} deleted successfully"}), 200
        else:
            # Service should raise NotFoundError if task doesn't exist
            return jsonify({"error": f"Task with ID {task_id} not found or delete failed"}), 404
    except Exception as e:
         # Check if the error message indicates "not found" to return 404
        if "not found" in str(e).lower():
            return handle_error(e, 404)
        # Handle potential foreign key constraint errors if timesheets reference this task
        if "foreign key constraint" in str(e).lower():
             logger.warning(f"Attempted to delete task {task_id} with existing references.")
             return jsonify({"error": f"Cannot delete task {task_id} because it is referenced by other records (e.g., Timesheets)"}), 409 # 409 Conflict
        return handle_error(e)

# --- Special Task Routes ---

@task_api.route('/projects/<int:project_id>/tasks', methods=['GET'])
def get_tasks_by_project(project_id):
    """Retrieves all tasks associated with a specific project ID."""
    try:
        # Optional: Add validation to check if project_id exists first
        # project = project_service.get_project_by_id(project_id)
        # if not project:
        #     return jsonify({"error": f"Project with ID {project_id} not found"}), 404

        tasks = task_service.get_tasks_by_project_id(project_id)
        # If tasks is an empty list, it's a valid response (no tasks for this project)
        return jsonify(tasks), 200
    except Exception as e:
        return handle_error(e)


@task_api.route('/employees/<string:emp_id>/tasks', methods=['GET'])
def get_tasks_by_employee(emp_id):
    """Retrieves all tasks assigned to a specific employee ID."""
    try:
        # Optional: Add validation to check if emp_id exists first
        # employee = employee_service.get_employee_by_emp_id(emp_id)
        # if not employee:
        #     return jsonify({"error": f"Employee with ID {emp_id} not found"}), 404

        tasks = task_service.get_tasks_by_employee_id(emp_id)
         # If tasks is an empty list, it's a valid response (no tasks for this employee)
        return jsonify(tasks), 200
    except Exception as e:
        return handle_error(e)

# Note: Authentication/Authorization (e.g., using @jwt_required decorator)
# would typically wrap these route functions in a real application.
# Example:
# from flask_jwt_extended import jwt_required
# @task_api.route('/tasks', methods=['POST'])
# @jwt_required()
#
def create_timesheet():
    """
    Creates a new timesheet entry.
    Expects JSON payload with timesheet details.
    """
    try:
        data = request.get_json()
        if not data:
            raise InvalidInputException("Request body cannot be empty.")

        # Basic Input Validation
        required_fields = ['time_sheet_date', 'project_id', 'project_name', 'task_id', 'employee_id', 'status']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise InvalidInputException(f"Missing required field: {field}")

        # Optional fields validation (type check if present)
        if 'effort_in_hours' in data and data['effort_in_hours'] is not None and not isinstance(data['effort_in_hours'], int):
             raise InvalidInputException("Field 'effort_in_hours' must be an integer.")
        if 'description' in data and data['description'] is not None and not isinstance(data['description'], str):
             raise InvalidInputException("Field 'description' must be a string.")
        if 'manager_comments' in data and data['manager_comments'] is not None and not isinstance(data['manager_comments'], str):
             raise InvalidInputException("Field 'manager_comments' must be a string.")

        # Validate status value
        allowed_statuses = ['Saved', 'Submitted', 'Approved', 'Rejected']
        if data['status'] not in allowed_statuses:
            raise InvalidInputException(f"Invalid status value. Allowed values are: {', '.join(allowed_statuses)}")

        # Call service layer to create timesheet
        new_timesheet_id = timesheet_service.create_timesheet(data)
        logger.info(f"Timesheet created successfully with ID: {new_timesheet_id}")

        # Fetch the created timesheet to return it
        created_timesheet = timesheet_service.get_timesheet_by_id(new_timesheet_id)
        return jsonify(created_timesheet.to_dict()), 201

    except InvalidInputException as e:
        logger.warning(f"Invalid input for creating timesheet: {e}")
        return jsonify({"error": str(e)}), 400
    except DataNotFoundException as e: # e.g., if project_id, task_id, or employee_id doesn't exist
        logger.warning(f"Data not found during timesheet creation: {e}")
        return jsonify({"error": str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Database error creating timesheet: {e}")
        return jsonify({"error": "Failed to create timesheet due to a database issue."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error creating timesheet: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@timesheet_bp.route('', methods=['GET'])
# @jwt_required()
def get_all_timesheets():
    """
    Retrieves all timesheet entries.
    Supports filtering via query parameters (e.g., employee_id, project_id, date_range).
    """
    try:
        # Extract query parameters for filtering (example)
        filters = {
            'employee_id': request.args.get('employee_id'),
            'project_id': request.args.get('project_id', type=int),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'status': request.args.get('status')
        }
        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}

        timesheets = timesheet_service.get_all_timesheets(filters=filters)
        timesheet_list = [ts.to_dict() for ts in timesheets]
        logger.info(f"Retrieved {len(timesheet_list)} timesheets with filters: {filters}")
        return jsonify(timesheet_list), 200

    except DatabaseError as e:
        logger.error(f"Database error retrieving all timesheets: {e}")
        return jsonify({"error": "Failed to retrieve timesheets due to a database issue."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error retrieving all timesheets: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@timesheet_bp.route('/<int:timesheet_id>', methods=['GET'])
# @jwt_required()
def get_timesheet(timesheet_id):
    """
    Retrieves a specific timesheet entry by its ID.
    """
    try:
        timesheet = timesheet_service.get_timesheet_by_id(timesheet_id)
        logger.info(f"Retrieved timesheet with ID: {timesheet_id}")
        return jsonify(timesheet.to_dict()), 200
    except DataNotFoundException as e:
        logger.warning(f"Timesheet not found with ID {timesheet_id}: {e}")
        return jsonify({"error": str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Database error retrieving timesheet {timesheet_id}: {e}")
        return jsonify({"error": "Failed to retrieve timesheet due to a database issue."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error retrieving timesheet {timesheet_id}: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@timesheet_bp.route('/<int:timesheet_id>', methods=['PUT'])
# @jwt_required()
def update_timesheet(timesheet_id):
    """
    Updates an existing timesheet entry.
    Expects JSON payload with fields to update.
    Only allows updating certain fields depending on status (e.g., 'Saved').
    """
    try:
        data = request.get_json()
        if not data:
            raise InvalidInputException("Request body cannot be empty.")

        # Basic type validation for provided fields
        if 'effort_in_hours' in data and data['effort_in_hours'] is not None and not isinstance(data['effort_in_hours'], int):
             raise InvalidInputException("Field 'effort_in_hours' must be an integer.")
        if 'description' in data and data['description'] is not None and not isinstance(data['description'], str):
             raise InvalidInputException("Field 'description' must be a string.")
        # Add validation for other updatable fields if necessary (project, task, date etc.)
        # Note: Status updates might have dedicated endpoints or specific logic here/in service.

        updated_timesheet = timesheet_service.update_timesheet(timesheet_id, data)
        logger.info(f"Timesheet updated successfully with ID: {timesheet_id}")
        return jsonify(updated_timesheet.to_dict()), 200

    except InvalidInputException as e:
        logger.warning(f"Invalid input for updating timesheet {timesheet_id}: {e}")
        return jsonify({"error": str(e)}), 400
    except DataNotFoundException as e:
        logger.warning(f"Timesheet not found for update with ID {timesheet_id}: {e}")
        return jsonify({"error": str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Database error updating timesheet {timesheet_id}: {e}")
        return jsonify({"error": "Failed to update timesheet due to a database issue."}), 500
    except PermissionError as e: # If service layer enforces status-based update rules
        logger.warning(f"Permission denied updating timesheet {timesheet_id}: {e}")
        return jsonify({"error": str(e)}), 403 # Forbidden
    except Exception as e:
        logger.exception(f"Unexpected error updating timesheet {timesheet_id}: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@timesheet_bp.route('/<int:timesheet_id>', methods=['DELETE'])
# @jwt_required()
def delete_timesheet(timesheet_id):
    """
    Deletes a timesheet entry by its ID.
    Deletion might be restricted based on status (e.g., cannot delete 'Approved').
    """
    try:
        timesheet_service.delete_timesheet(timesheet_id)
        logger.info(f"Timesheet deleted successfully with ID: {timesheet_id}")
        return '', 204 # No Content response for successful deletion
    except DataNotFoundException as e:
        logger.warning(f"Timesheet not found for deletion with ID {timesheet_id}: {e}")
        return jsonify({"error": str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Database error deleting timesheet {timesheet_id}: {e}")
        return jsonify({"error": "Failed to delete timesheet due to a database issue."}), 500
    except PermissionError as e: # If service layer enforces status-based deletion rules
        logger.warning(f"Permission denied deleting timesheet {timesheet_id}: {e}")
        return jsonify({"error": str(e)}), 403 # Forbidden
    except Exception as e:
        logger.exception(f"Unexpected error deleting timesheet {timesheet_id}: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

# --- Special Timesheet Routes ---

@timesheet_bp.route('/employee/<string:employee_id>', methods=['GET'])
# @jwt_required()
def get_timesheets_by_employee(employee_id):
    """
    Retrieves all timesheet entries for a specific employee.
    Supports filtering via query parameters (e.g., project_id, date_range, status).
    """
    try:
        # Extract query parameters for filtering
        filters = {
            'project_id': request.args.get('project_id', type=int),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'status': request.args.get('status')
        }
        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}

        timesheets = timesheet_service.get_timesheets_by_employee_id(employee_id, filters=filters)
        timesheet_list = [ts.to_dict() for ts in timesheets]
        logger.info(f"Retrieved {len(timesheet_list)} timesheets for employee {employee_id} with filters: {filters}")
        return jsonify(timesheet_list), 200
    except DataNotFoundException as e: # If employee_id itself is not found
         logger.warning(f"Cannot get timesheets, employee not found: {employee_id}")
         return jsonify({"error": str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Database error retrieving timesheets for employee {employee_id}: {e}")
        return jsonify({"error": "Failed to retrieve timesheets due to a database issue."}), 500
    except Exception as e:
        logger.exception(f"Unexpected error retrieving timesheets for employee {employee_id}: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@timesheet_bp.route('/project/<int:project_id>', methods=['GET'])
# @jwt_required()
def get_timesheets_by_project(project_id):
    """
    Retrieves all timesheet entries for a specific project.
    Supports filtering via query parameters (e.g., employee_id, date_range, status).
    """
    try:
        # Extract query parameters for filtering
        filters = {
            'employee_id': request.args.get('employee_id'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'status': request.args.get('status')
        }
        # Remove None values from filters
        filters = {k: v for k, v in filters.items() if v is not None}

        timesheets = timesheet



if __name__ == '__main__':
    # Set debug=True for development environment
    # Host '0.0.0.0' makes the server accessible externally
    # Port 5000 is the default Flask port, change if needed
    app.run(host='0.0.0.0', port=5000, debug=True)
### END APP EXECUTION CODE ###