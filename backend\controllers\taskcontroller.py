from flask import Blueprint, request, jsonify
from backend.services.TaskService import TaskService
from backend.models.Task import Task  # Assuming you have a Task model
from http import HTTPStatus

task_bp = Blueprint('task', __name__, url_prefix='/api/tasks')
task_service = TaskService()  # Instantiate the service class

@task_bp.route('/', methods=['GET'])
def get_tasks():
    """
    Retrieves all tasks.
    """
    try:
        tasks = task_service.get_all_tasks()
        return jsonify([task.to_dict() for task in tasks]), HTTPStatus.OK
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    Retrieves a specific task by ID.
    """
    try:
        task = task_service.get_task_by_id(task_id)
        if task:
            return jsonify(task.to_dict()), HTTPStatus.OK
        else:
            return jsonify({'message': 'Task not found'}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@task_bp.route('/', methods=['POST'])
def create_task():
    """
    Creates a new task.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), HTTPStatus.BAD_REQUEST

        # Assuming your Task model has fields like 'name', 'description', etc.
        new_task = task_service.create_task(data)
        return jsonify(new_task.to_dict()), HTTPStatus.CREATED
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@task_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Updates an existing task.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), HTTPStatus.BAD_REQUEST

        updated_task = task_service.update_task(task_id, data)
        if updated_task:
            return jsonify(updated_task.to_dict()), HTTPStatus.OK
        else:
            return jsonify({'message': 'Task not found'}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Deletes a task.
    """
    try:
        if task_service.delete_task(task_id):
            return jsonify({'message': 'Task deleted'}), HTTPStatus.OK
        else:
            return jsonify({'message': 'Task not found'}), HTTPStatus.NOT_FOUND
    except Exception as e:
        return jsonify({'error': str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR