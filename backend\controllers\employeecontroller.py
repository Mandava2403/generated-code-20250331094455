from flask import Blueprint, request, jsonify
from backend.services.EmployeeService import EmployeeService
from backend.models.Employee import Employee  # Assuming you have an Employee model
from typing import Optional, List, Dict, Any

employee_bp = Blueprint('employee', __name__, url_prefix='/api/employees')
employee_service = EmployeeService()  # Instantiate the service class

@employee_bp.route('/', methods=['GET'])
def get_employees():
    """
    Retrieves all employees.
    """
    try:
        employees = employee_service.get_all_employees()
        # Assuming get_all_employees returns a list of Employee objects or a list of dictionaries
        if employees is None:
            return jsonify({'message': 'No employees found'}), 200
        
        # Convert Employee objects to dictionaries if necessary
        if isinstance(employees, list) and employees and isinstance(employees[0], Employee):
            employee_list = [employee.to_dict() for employee in employees]  # Assuming to_dict() method exists in Employee model
        elif isinstance(employees, list):
            employee_list = employees
        else:
            employee_list = [employees] # Handle single employee case

        return jsonify(employee_list), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@employee_bp.route('/<int:employee_id>', methods=['GET'])
def get_employee(employee_id: int):
    """
    Retrieves an employee by ID.
    """
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        if employee is None:
            return jsonify({'message': 'Employee not found'}), 404
        # Convert Employee object to dictionary if necessary
        if isinstance(employee, Employee):
            employee_dict = employee.to_dict()
        else:
            employee_dict = employee
        return jsonify(employee_dict), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@employee_bp.route('/', methods=['POST'])
def create_employee():
    """
    Creates a new employee.
    """
    try:
        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request body'}), 400

        # Assuming the service expects a dictionary
        new_employee = employee_service.create_employee(data)
        if new_employee is None:
            return jsonify({'message': 'Failed to create employee'}), 400

        # Convert Employee object to dictionary if necessary
        if isinstance(new_employee, Employee):
            employee_dict = new_employee.to_dict()
        else:
            employee_dict = new_employee

        return jsonify(employee_dict), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@employee_bp.route('/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id: int):
    """
    Updates an existing employee.
    """
    try:
        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request body'}), 400

        updated_employee = employee_service.update_employee(employee_id, data)
        if updated_employee is None:
            return jsonify({'message': 'Employee not found or update failed'}), 404

        # Convert Employee object to dictionary if necessary
        if isinstance(updated_employee, Employee):
            employee_dict = updated_employee.to_dict()
        else:
            employee_dict = updated_employee

        return jsonify(employee_dict), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@employee_bp.route('/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id: int):
    """
    Deletes an employee.
    """
    try:
        if employee_service.delete_employee(employee_id):
            return jsonify({'message': 'Employee deleted'}), 204  # No Content
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500