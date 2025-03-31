from flask import Blueprint, jsonify, request
from backend.services.EmployeeService import EmployeeService, EmployeeServiceError
from backend.models.Employee import Employee
from backend.dao.EmployeeDAO import EmployeeDAO

# Create a blueprint for the controller
duplicate_employee_error_bp = Blueprint('duplicate_employee_error', __name__, url_prefix='/api/employees')

# Instantiate the EmployeeService and EmployeeDAO
employee_dao = EmployeeDAO()
employee_service = EmployeeService(employee_dao)


@duplicate_employee_error_bp.route('/<int:emp_id>', methods=['GET'])
def get_employee(emp_id):
    """
    Retrieves an employee by their ID.
    """
    try:
        employee = employee_service.get_employee_by_id(emp_id)
        if employee:
            return jsonify(employee.to_dict()), 200  # Convert Employee object to dictionary
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@duplicate_employee_error_bp.route('', methods=['POST'])
def create_employee():
    """
    Creates a new employee.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request body'}), 400

        # Assuming the request body contains the employee data
        employee = employee_service.create_employee(data)
        return jsonify(employee.to_dict()), 201  # Convert Employee object to dictionary
    except EmployeeServiceError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@duplicate_employee_error_bp.route('/<int:emp_id>', methods=['PUT'])
def update_employee(emp_id):
    """
    Updates an existing employee.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request body'}), 400

        employee = employee_service.update_employee(emp_id, data)
        if employee:
            return jsonify(employee.to_dict()), 200  # Convert Employee object to dictionary
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except EmployeeServiceError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@duplicate_employee_error_bp.route('/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    """
    Deletes an employee.
    """
    try:
        if employee_service.delete_employee(emp_id):
            return jsonify({'message': 'Employee deleted'}), 200
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@duplicate_employee_error_bp.route('', methods=['GET'])
def get_all_employees():
    """
    Retrieves all employees.
    """
    try:
        employees = employee_service.get_all_employees()
        employee_dicts = [employee.to_dict() for employee in employees]
        return jsonify(employee_dicts), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500