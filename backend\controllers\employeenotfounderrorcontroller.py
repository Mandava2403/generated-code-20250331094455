from flask import Blueprint, jsonify, request
from backend.services.EmployeeService import EmployeeService, EmployeeNotFoundError, EmployeeServiceError
from backend.models.Employee import Employee  # Assuming you have an Employee model
from typing import Optional, Dict, Any
from datetime import datetime

employee_not_found_bp = Blueprint('employee_not_found', __name__, url_prefix='/api/employees')

# Instantiate the EmployeeService
employee_service = EmployeeService()


@employee_not_found_bp.errorhandler(EmployeeNotFoundError)
def handle_employee_not_found_error(error: EmployeeNotFoundError):
    """Handles EmployeeNotFoundError and returns a JSON response."""
    return jsonify({"error": str(error), "message": "Employee not found"}), 404


@employee_not_found_bp.errorhandler(EmployeeServiceError)
def handle_employee_service_error(error: EmployeeServiceError):
    """Handles EmployeeServiceError and returns a JSON response."""
    return jsonify({"error": str(error), "message": "An error occurred with the employee service"}), 500


@employee_not_found_bp.route('/<int:emp_id>', methods=['GET'])
def get_employee(emp_id: int):
    """
    Retrieves an employee by ID.

    :param emp_id: The ID of the employee.
    :return: JSON representation of the employee or an error message.
    """
    try:
        employee = employee_service.get_employee(emp_id)
        return jsonify(employee.to_dict()), 200  # Assuming to_dict() method exists in Employee model
    except EmployeeNotFoundError as e:
        return handle_employee_not_found_error(e)
    except EmployeeServiceError as e:
        return handle_employee_service_error(e)
    except Exception as e:
        return jsonify({"error": str(e), "message": "An unexpected error occurred"}), 500


@employee_not_found_bp.route('/', methods=['POST'])
def create_employee():
    """
    Creates a new employee.

    :return: JSON representation of the created employee or an error message.
    """
    try:
        data: Dict[str, Any] = request.get_json()
        # Assuming your Employee model has fields corresponding to the request data
        employee = employee_service.create_employee(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            # Add other fields as needed
        )
        return jsonify(employee.to_dict()), 201  # Assuming to_dict() method exists in Employee model
    except EmployeeServiceError as e:
        return handle_employee_service_error(e)
    except Exception as e:
        return jsonify({"error": str(e), "message": "An unexpected error occurred"}), 500


@employee_not_found_bp.route('/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id: int):
    """
    Updates an existing employee.

    :param emp_id: The ID of the employee to update.
    :return: JSON representation of the updated employee or an error message.
    """
    try:
        data: Dict[str, Any] = request.get_json()
        employee = employee_service.update_employee(
            emp_id=emp_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            # Add other fields as needed
        )
        return jsonify(employee.to_dict()), 200  # Assuming to_dict() method exists in Employee model
    except EmployeeNotFoundError as e:
        return handle_employee_not_found_error(e)
    except EmployeeServiceError as e:
        return handle_employee_service_error(e)
    except Exception as e:
        return jsonify({"error": str(e), "message": "An unexpected error occurred"}), 500


@employee_not_found_bp.route('/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id: int):
    """
    Deletes an employee.

    :param emp_id: The ID of the employee to delete.
    :return: A success message or an error message.
    """
    try:
        employee_service.delete_employee(emp_id)
        return jsonify({"message": "Employee deleted successfully"}), 200
    except EmployeeNotFoundError as e:
        return handle_employee_not_found_error(e)
    except EmployeeServiceError as e:
        return handle_employee_service_error(e)
    except Exception as e:
        return jsonify({"error": str(e), "message": "An unexpected error occurred"}), 500