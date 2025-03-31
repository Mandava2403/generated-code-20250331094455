import logging
from datetime import date, timedelta
from flask import Blueprint, request, jsonify, current_app
from backend.services.TimesheetService import TimesheetService  # Assuming correct import path
from backend.models.Timesheet import Timesheet  # Assuming correct import path
from backend.models.Timesheet import TimesheetStatus # Assuming correct import path
from backend.dao.EmployeeDAO import EmployeeDAO
from backend.dao.ProjectDAO import ProjectDAO
from backend.dao.TaskDAO import TaskDAO

# Create a blueprint for the timesheet controller
timesheet_bp = Blueprint('timesheet', __name__, url_prefix='/api/timesheets')

# Dependency Injection: Instantiate services and DAOs (or inject them via constructor)
def get_timesheet_service():
    """Helper function to get the TimesheetService instance."""
    # Assuming you have a way to access your DAOs (e.g., from the app context)
    employee_dao = EmployeeDAO()  # Or however you instantiate your DAOs
    project_dao = ProjectDAO()
    task_dao = TaskDAO()
    return TimesheetService(employee_dao, project_dao, task_dao)

@timesheet_bp.route('/', methods=['POST'])
def create_timesheet():
    """
    Creates a new timesheet entry.
    """
    try:
        timesheet_service = get_timesheet_service()
        data = request.get_json()
        # Assuming the request body contains the timesheet data
        timesheet = Timesheet(**data)  # Assuming Timesheet model can accept a dictionary
        created_timesheet = timesheet_service.create(timesheet)
        return jsonify(created_timesheet.to_dict()), 201  # Assuming to_dict() method exists in Timesheet model
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error creating timesheet")
        return jsonify({'error': 'Failed to create timesheet entry.'}), 500

@timesheet_bp.route('/<int:timesheet_id>', methods=['GET'])
def get_timesheet(timesheet_id):
    """
    Retrieves a timesheet entry by ID.
    """
    try:
        timesheet_service = get_timesheet_service()
        timesheet = timesheet_service.read(timesheet_id)
        if timesheet:
            return jsonify(timesheet.to_dict()), 200
        else:
            return jsonify({'message': 'Timesheet entry not found.'}), 404
    except Exception as e:
        logging.exception("Error getting timesheet")
        return jsonify({'error': 'Failed to retrieve timesheet entry.'}), 500

@timesheet_bp.route('/', methods=['GET'])
def list_timesheets():
    """
    Lists all timesheet entries (with optional filtering).
    Supports filtering by employee_id, project_id, and date.
    """
    try:
        timesheet_service = get_timesheet_service()
        employee_id = request.args.get('employee_id', type=int)
        project_id = request.args.get('project_id', type=int)
        date_str = request.args.get('date')  # Expecting date in YYYY-MM-DD format
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        # Convert date strings to date objects if provided
        date_obj = date.fromisoformat(date_str) if date_str else None
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None

        timesheets = timesheet_service.list(employee_id=employee_id, project_id=project_id, date=date_obj, start_date=start_date, end_date=end_date)
        timesheet_dicts = [timesheet.to_dict() for timesheet in timesheets]
        return jsonify(timesheet_dicts), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error listing timesheets")
        return jsonify({'error': 'Failed to retrieve timesheet entries.'}), 500

@timesheet_bp.route('/<int:timesheet_id>', methods=['PUT'])
def update_timesheet(timesheet_id):
    """
    Updates an existing timesheet entry.
    """
    try:
        timesheet_service = get_timesheet_service()
        data = request.get_json()
        # Assuming the request body contains the updated timesheet data
        timesheet = Timesheet(**data)
        timesheet.id = timesheet_id  # Ensure the ID is set for the update
        updated_timesheet = timesheet_service.update(timesheet)
        if updated_timesheet:
            return jsonify(updated_timesheet.to_dict()), 200
        else:
            return jsonify({'message': 'Timesheet entry not found.'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error updating timesheet")
        return jsonify({'error': 'Failed to update timesheet entry.'}), 500

@timesheet_bp.route('/<int:timesheet_id>', methods=['DELETE'])
def delete_timesheet(timesheet_id):
    """
    Deletes a timesheet entry.
    """
    try:
        timesheet_service = get_timesheet_service()
        if timesheet_service.delete(timesheet_id):
            return jsonify({'message': 'Timesheet entry deleted.'}), 200
        else:
            return jsonify({'message': 'Timesheet entry not found.'}), 404
    except Exception as e:
        logging.exception("Error deleting timesheet")
        return jsonify({'error': 'Failed to delete timesheet entry.'}), 500

@timesheet_bp.route('/<int:timesheet_id>/submit', methods=['POST'])
def submit_timesheet(timesheet_id):
    """
    Submits a timesheet entry.
    """
    try:
        timesheet_service = get_timesheet_service()
        if timesheet_service.submit(timesheet_id):
            return jsonify({'message': 'Timesheet submitted successfully.'}), 200
        else:
            return jsonify({'message': 'Timesheet entry not found or could not be submitted.'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error submitting timesheet")
        return jsonify({'error': 'Failed to submit timesheet entry.'}), 500

@timesheet_bp.route('/<int:timesheet_id>/approve', methods=['POST'])
def approve_timesheet(timesheet_id):
    """
    Approves a timesheet entry.
    """
    try:
        timesheet_service = get_timesheet_service()
        if timesheet_service.approve(timesheet_id):
            return jsonify({'message': 'Timesheet approved successfully.'}), 200
        else:
            return jsonify({'message': 'Timesheet entry not found or could not be approved.'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error approving timesheet")
        return jsonify({'error': 'Failed to approve timesheet entry.'}), 500

@timesheet_bp.route('/<int:timesheet_id>/reject', methods=['POST'])
def reject_timesheet(timesheet_id):
    """
    Rejects a timesheet entry.
    """
    try:
        timesheet_service = get_timesheet_service()
        data = request.get_json()
        reason = data.get('reason', '') # Get the rejection reason from the request body
        if timesheet_service.reject(timesheet_id, reason):
            return jsonify({'message': 'Timesheet rejected successfully.'}), 200
        else:
            return jsonify({'message': 'Timesheet entry not found or could not be rejected.'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.exception("Error rejecting timesheet")
        return jsonify({'error': 'Failed to reject timesheet entry.'}), 500