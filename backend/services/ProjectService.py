import logging
from datetime import date
from backend.dao.ProjectDAO import ProjectDAO
# Assuming EmployeeDAO exists for validation purposes
# from backend.dao.EmployeeDAO import EmployeeDAO
# Assuming TaskDAO exists for dependency checks
# from backend.dao.TaskDAO import TaskDAO
# Assuming TimesheetDAO exists for dependency checks
# from backend.dao.TimesheetDAO import TimesheetDAO
from backend.models.Project import Project, ProjectStatus
from backend.exceptions.BusinessException import BusinessException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProjectService:
    """
    Service layer class for handling business logic related to Projects.
    """

    def __init__(self):
        self.project_dao = ProjectDAO()
        # self.employee_dao = EmployeeDAO() # Uncomment when EmployeeDAO is available
        # self.task_dao = TaskDAO() # Uncomment when TaskDAO is available
        # self.timesheet_dao = TimesheetDAO() # Uncomment when TimesheetDAO is available

    def _validate_project_data(self, project: Project, is_update: bool = False):
        """
        Validates the project data based on business rules.
        Raises BusinessException if validation fails.
        """
        if not project:
            raise BusinessException("Project data cannot be empty.")
        if not project.id:
             raise BusinessException("Project ID is required.")
        if not project.proj_name or not project.proj_name.strip():
            raise BusinessException("Project Name is required.")
        if len(project.proj_name) > 255:
            raise BusinessException("Project Name cannot exceed 255 characters.")
        if project.project_description and len(project.project_description) > 1000:
            raise BusinessException("Project Description cannot exceed 1000 characters.")

        # Validate status enum
        if project.project_status:
            try:
                ProjectStatus(project.project_status)
            except ValueError:
                valid_statuses = [status.value for status in ProjectStatus]
                raise BusinessException(f"Invalid Project Status '{project.project_status}'. Must be one of {valid_statuses}.")
        else:
             # Default status for new projects if not provided
             if not is_update:
                 project.project_status = ProjectStatus.OPEN.value
             else:
                 # Status is required for updates if it's being changed
                 existing_project = self.get_project_by_id(project.id)
                 if not existing_project:
                     raise BusinessException(f"Cannot validate status for non-existent project ID {project.id}.")
                 if not project.project_status: # If update payload doesn't include status, keep existing
                     project.project_status = existing_project.project_status


        # Validate dates logic
        dates = {
            'dev_start': project.dev_start_date, 'dev_end': project.dev_end_date,
            'qa_start': project.qa_start_date, 'qa_end': project.qa_end_date,
            'uit_start': project.uit_start_date, 'uit_end': project.uit_end_date,
            'go_live': project.go_live_date
        }

        if dates['dev_start'] and dates['dev_end'] and dates['dev_start'] > dates['dev_end']:
            raise BusinessException("Development Start Date cannot be after Development End Date.")
        if dates['qa_start'] and dates['qa_end'] and dates['qa_start'] > dates['qa_end']:
            raise BusinessException("QA Start Date cannot be after QA End Date.")
        if dates['uit_start'] and dates['uit_end'] and dates['uit_start'] > dates['uit_end']:
            raise BusinessException("UIT Start Date cannot be after UIT End Date.")

        # Validate phase sequencing
        if dates['dev_end'] and dates['qa_start'] and dates['dev_end'] > dates['qa_start']:
            raise BusinessException("Development End Date cannot be after QA Start Date.")
        if dates['qa_end'] and dates['uit_start'] and dates['qa_end'] > dates['uit_start']:
            raise BusinessException("QA End Date cannot be after UIT Start Date.")
        if dates['uit_end'] and dates['go_live'] and dates['uit_end'] > dates['go_live']:
            raise BusinessException("UIT End Date cannot be after Go Live Date.")

        # Validate creator/updater existence (requires EmployeeDAO)
        # if not is_update and project.created_by:
        #     if not self.employee_dao.read_by_emp_id(project.created_by):
        #         raise BusinessException(f"Creator employee with emp_Id '{project.created_by}' does not exist.")
        # if is_update and project.last_updated_by:
        #     if not self.employee_dao.read_by_emp_id(project.last_updated_by):
        #         raise BusinessException(f"Updater employee with emp_Id '{project.last_updated_by}' does not exist.")
        # else: # For updates, last_updated_by is mandatory
        #     if is_update and not project.last_updated_by:
        #          raise BusinessException("Last Updated By is required for updating a project.")

        # Placeholder check until EmployeeDAO is integrated
        if not is_update and not project.created_by:
            logging.warning("Created By is missing for new project.")
            # raise BusinessException("Created By is required for creating a project.") # Enable when user context is available
        if is_update and not project.last_updated_by:
            logging.warning(f"Last Updated By is missing for updating project ID {project.id}.")
            # raise BusinessException("Last Updated By is required for updating a project.") # Enable when user context is available