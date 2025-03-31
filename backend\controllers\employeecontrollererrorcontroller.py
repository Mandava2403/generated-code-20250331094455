from flask import Blueprint, jsonify, request
from backend.services.EmployeeService import EmployeeService
from backend.models.Employee import Employee
from backend.dao.EmployeeDAO import EmployeeDAO

employee_bp = Blueprint('employee', __name__, url_prefix='/api/employees')

employee_service = EmployeeService(EmployeeDAO())

@employee_bp.route('/', methods=['GET'])
def get_employees():
    """
    Retrieves all employees.
    """
    try:
        employees = employee_service.get_all_employees()
        return jsonify([employee.to_dict() for employee in employees]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """
    Retrieves an employee by ID.
    """
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        if employee:
            return jsonify(employee.to_dict()), 200
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/', methods=['POST'])
def create_employee():
    """
    Creates a new employee.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Please provide employee data'}), 400

        new_employee = employee_service.create_employee(data)
        return jsonify(new_employee.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """
    Updates an existing employee.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Please provide employee data'}), 400

        updated_employee = employee_service.update_employee(employee_id, data)
        if updated_employee:
            return jsonify(updated_employee.to_dict()), 200
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """
    Deletes an employee.
    """
    try:
        if employee_service.delete_employee(employee_id):
            return jsonify({'message': 'Employee deleted'}), 200
        else:
            return jsonify({'message': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500