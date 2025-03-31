import logging
from datetime import date, datetime
from backend.dao.TaskDAO import TaskDAO
# Import other DAOs needed for validation (assuming they exist)
# from backend.dao.ProjectDAO import ProjectDAO
# from backend.dao.EmployeeDAO import EmployeeDAO
# from backend.dao.TimesheetDAO import TimesheetDAO
from backend.models.Task import Task
from backend.exceptions.BusinessException import BusinessException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TaskService:
    """
    Service layer class for handling business logic related to Tasks.
    It uses TaskDAO for data access and implements validation, business rules,
    and workflow logic for task operations.
    """

    def __init__(self):
        """Initializes the TaskService with its DAO."""
        self.task_dao = TaskDAO()
        # Instantiate other DAOs needed for validation (if available)
        # self.project_dao = ProjectDAO()
        # self.employee_dao = EmployeeDAO()
        # self.timesheet_dao = TimesheetDAO()

    def _validate_task_data(self, task: Task, is_update: bool = False):
        """
        Performs comprehensive validation on task data.
        Args:
            task (Task): The task object to validate.
            is_update (bool): Flag indicating if this is an update operation.
        Raises:
            BusinessException: If validation fails.
        """
        if not task.task_id and not is_update:
             # In a real scenario, task_id might be auto-generated or validated differently
             # For this schema, it seems required upfront.
             raise BusinessException("Task ID is required for creation.")
        if not task.project_id:
            raise BusinessException("Project ID is required.")
        if not task.task_name or len(task.task_name.strip()) == 0:
            raise BusinessException("Task Name cannot be empty.")
        if len(task.task_name) > 255:
            raise BusinessException("Task Name cannot exceed 255 characters.")
        if task.task_description and len(task.task_description) > 1000:
            raise BusinessException("Task Description cannot exceed 1000 characters.")
        if task.expected_outcome and len(task.expected_outcome) > 1000:
            raise BusinessException("Expected Outcome cannot exceed 1000 characters.")

        # Date validations
        if task.start_date and task.completion_date:
            if task.start_date > task.completion_date:
                raise BusinessException("Task Start Date cannot be after Completion Date.")

        # Hours validations
        if task.estimated_hours is not None and task.estimated_hours < 0:
            raise BusinessException("Estimated Hours cannot be negative.")
        if task.actual_hours is not None and task.actual_hours < 0:
            raise BusinessException("Actual Hours cannot be negative.")

        # Foreign Key Validations (Requires other DAOs)
        # Placeholder: Check if Project exists
        # project = self.project_dao.read(task.project_id)
        # if not project:
        #     raise BusinessException(f"Project with ID {task.project_id} does not exist.")
        # Placeholder: Check project status - maybe tasks can only be added to 'open' or 'inprogress' projects
        # if project.project_status == 'completed':
        #     raise BusinessException(f"Cannot add or modify tasks for a completed project (ID: {task.project_id}).")

        # Placeholder: Check if assigned Employee exists
        # if task.emp_id:
        #     employee = self.employee_dao.read_by_emp_id(task.emp_id)
        #     if not employee:
        #         raise BusinessException(f"Employee with ID {task.emp_id} does not exist.")

        # Placeholder: Check if creator/updater Employee exists
        # if task.created_by and not is_update:
        #     creator = self.employee_dao.read_by_emp_id(task.created_by)
        #     if not creator:
        #         raise BusinessException(f"Creator Employee with ID {task.created_by} does not exist.")
        # if task.last_updated_by and is_update:
        #     updater = self.employee_dao.read_by_emp_id(task.last_updated_by)
        #     if not updater:
        #         raise BusinessException(f"Updater Employee with ID {task.last_updated_by} does not exist.")

        logging.info(f"Task data validation successful for Task ID: {task.task_id if is_update else 'New Task'}")

    def delete_task(self, task_id: int, deleter_emp_id: str):
        """
        Deletes a task after checking dependencies.
        Args:
            task_id (int): The ID of the task to delete.
            deleter_emp_id (str): The employee ID of the user deleting the task (for logging/audit).
        Raises:
            BusinessException: If the task is not found or cannot be deleted due to dependencies.
        """
        logging.info(f"Attempting to delete task with ID: {task_id} by user {deleter_emp_id}")

        # Retrieve the existing task to ensure it exists
        existing_task = self.task_dao.read(task_id)
        if not existing_task:
            logging.error(f"Task deletion failed: Task with ID {task_id} not found.")
            raise BusinessException(f"Task with ID {task_id} not found.")

        # Business Rule: Check if task is referenced in Timesheets (Requires TimesheetDAO)
        # Placeholder check:
        # related_timesheets = self.timesheet_dao.find_by_task_id(task_id)
        # if related_timesheets:
        #     logging.error(f"Task deletion failed: Task {task_id} has associated timesheet entries.")
        #     raise BusinessException(f"Cannot delete Task {task_id} because it has associated timesheet entries.")
        # Note: The DAO delete might also fail due to FK constraints if not handled here.

        # Call DAO to delete the task
        success = self.task_dao.delete(task_id)
        if not success:

```python
# [FILE: backend/services/TimesheetService.py]
import logging
from datetime import date, timedelta
from typing import List, Optional

from backend.dao.TimesheetDAO import TimesheetDAO
# Assume existence of other DAOs for validation purposes
from backend.dao.EmployeeDAO import EmployeeDAO
from backend.dao.ProjectDAO import ProjectDAO
from backend.dao.TaskDAO import TaskDAO
from backend.models.Timesheet import Timesheet, TimesheetStatus
from backend.models.Employee import Employee # Assuming Employee model exists
from backend.models.Project import Project # Assuming Project model exists
from backend.models.Task import Task # Assuming Task model exists

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TimesheetService:
    """
    Service layer for Timesheet entity, handling business logic and data validation.
    """

    def _validate_timesheet_data(self, timesheet: Timesheet, is_new: bool = True):
        """Performs comprehensive validation checks on timesheet data."""
        if not timesheet.time_sheet_date:
            raise ValueError("Timesheet date is required.")
        if not isinstance(timesheet.time_sheet_date, date):
             try:
                 timesheet.time_sheet_date = date.fromisoformat(str(timesheet.time_sheet_date))
             except (TypeError, ValueError):
                 raise ValueError("Invalid timesheet date format. Use YYYY-MM-DD.")

        # Business Rule: Timesheet date cannot be in the future.
        if timesheet.time_sheet_date > date.today():
            raise ValueError("Timesheet date cannot be in the future.")

        # Business Rule: Timesheet entries might have a submission deadline (e.g., within the last 14 days)
        # Uncomment and adjust days as needed
        # submission_deadline = date.today() - timedelta(days=14)
        # if timesheet.time_sheet_date < submission_deadline:
        #     raise ValueError(f"Timesheet entries older than {submission_deadline} cannot be created or modified.")

        if not timesheet.project_id:
            raise ValueError("Project ID is required.")
        if not timesheet.task_id:
            raise ValueError("Task ID is required.")
        if not timesheet.employee_id:
            raise ValueError("Employee ID is required.")

        if timesheet.effort_in_hours is None or not isinstance(timesheet.effort_in_hours, (int, float)) or timesheet.effort_in_hours <= 0:
            raise ValueError("Effort in hours must be a positive number.")
        # Business Rule: Effort cannot exceed 24 hours for a single entry.
        if timesheet.effort_in_hours > 24:
            raise ValueError("Effort in hours cannot exceed 24 for a single entry.")

        # Validate Foreign Key Existence
        employee = self.employee_dao.read_by_emp_id(timesheet.employee_id) # Assuming read_by_emp_id exists
        if not employee:
            raise ValueError(f"Employee with ID '{timesheet.employee_id}' does not exist.")
        # Add checks for employee status if applicable (e.g., employee must be active)
        # if employee.status != 'Active':
        #     raise ValueError(f"Employee '{timesheet.employee_id}' is not active.")

        project = self.project_dao.read(timesheet.project_id)
        if not project:
            raise ValueError(f"Project with ID '{timesheet.project_id}' does not exist.")
        # Business Rule: Cannot log time against completed projects (adjust based on exact rules)
        if project.project_status == 'completed':
             raise ValueError(f"Cannot log time against completed project '{project.proj_name}'.")
        # Ensure project_name matches the project_id (or fetch it if not provided)
        if timesheet.project_name != project.proj_name:
             logging.warning(f"Provided project name '{timesheet.project_name}' does not match project ID {timesheet.project_id}. Using name from DB: '{project.proj_name}'.")
             timesheet.project_name = project.proj_name # Auto-correct

        task = self.task_dao.read(timesheet.task_id)
        if not task:
            raise ValueError(f"Task with ID '{timesheet.task_id}' does not exist.")
        # Business Rule: Task must belong to the specified Project.
        if task.project_ID != timesheet.project_id:
            raise ValueError(f"Task ID '{timesheet.task_id}' does not belong to Project ID '{timesheet.project_id}'.")
        # Business Rule: Task might need to be assigned to the employee (optional, based on requirements)
        # if task.emp_id and task.emp_id != timesheet.employee_id:
        #     raise ValueError(f"Task ID '{timesheet.task_id}' is not assigned to employee '{timesheet.employee_id}'.")

        # Business Rule: Total hours logged by an employee for a specific day cannot exceed 24 hours.
        existing_hours_today = self._get_total_hours_for_employee_on_date(timesheet.employee_id, timesheet.time_sheet_date, timesheet.id if not is_new else None)
        if existing_hours_today + timesheet.effort_in_hours > 24:
            raise ValueError(f"Total hours for employee '{timesheet.employee_id}' on {timesheet.time_sheet_date} cannot exceed 24 hours (already logged {existing_hours_today} hours).")

        # Validate Status transitions (handled in specific methods like submit, approve, reject)
        if timesheet.status and timesheet.status not in [TimesheetStatus.SAVED, TimesheetStatus.SUBMITTED, TimesheetStatus.APPROVED, TimesheetStatus.REJECTED]:
            raise ValueError(f"Invalid timesheet status: '{timesheet.status}'.")

        # Validate description length if needed
        if timesheet.description and len(timesheet.description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters.")

        # Validate manager comments length if needed
        if timesheet.manager_comments and len(timesheet.manager_comments) > 500:
            raise ValueError("Manager comments cannot exceed 500 characters.")