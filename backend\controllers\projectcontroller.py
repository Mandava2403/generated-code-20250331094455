from flask import Blueprint, request, jsonify
from backend.services.ProjectService import ProjectService
from backend.models.Project import Project  # Assuming you have a Project model
from sqlalchemy.exc import SQLAlchemyError

project_bp = Blueprint('project', __name__, url_prefix='/api/projects')
project_service = ProjectService()  # Instantiate the service class

@project_bp.route('/', methods=['GET'])
def get_projects():
    """
    Retrieves all projects.
    """
    try:
        projects = project_service.get_all_projects()
        # Assuming projects is a list of Project objects
        project_list = [project.to_dict() for project in projects]  # Convert to dictionaries
        return jsonify(project_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """
    Retrieves a specific project by ID.
    """
    try:
        project = project_service.get_project_by_id(project_id)
        if project:
            return jsonify(project.to_dict()), 200
        else:
            return jsonify({'message': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/', methods=['POST'])
def create_project():
    """
    Creates a new project.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), 400

        # Assuming your Project model has attributes like 'name', 'description', etc.
        # Adapt this part based on your actual model attributes
        new_project = Project(
            name=data.get('name'),
            description=data.get('description')
        )
        created_project = project_service.create_project(new_project)
        return jsonify(created_project.to_dict()), 201
    except SQLAlchemyError as e:
        # Handle database errors specifically
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Updates an existing project.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No input data provided'}), 400

        project = project_service.get_project_by_id(project_id)
        if not project:
            return jsonify({'message': 'Project not found'}), 404

        # Update project attributes based on the data received
        project.name = data.get('name', project.name)
        project.description = data.get('description', project.description)

        updated_project = project_service.update_project(project)
        return jsonify(updated_project.to_dict()), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@project_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Deletes a project.
    """
    try:
        project = project_service.get_project_by_id(project_id)
        if not project:
            return jsonify({'message': 'Project not found'}), 404

        project_service.delete_project(project_id)
        return jsonify({'message': 'Project deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500