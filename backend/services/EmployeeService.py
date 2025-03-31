import logging
from datetime import date, datetime
from backend.models.Employee import Employee
from backend.dao.EmployeeDAO import EmployeeDAO
# Import other DAOs if needed for dependency checks, e.g.:
# from backend.dao.ProjectDAO import ProjectDAO
# from backend.dao.TaskDAO import TaskDAO
# from backend.dao.TimesheetDAO import TimesheetDAO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Custom Exceptions for Service Layer
class EmployeeServiceError(Exception):
    """Base class for exceptions in EmployeeService."""
    pass

class ValidationError(EmployeeServiceError):
    """Raised when data validation fails."""
    pass

class DuplicateEmployeeError(EmployeeServiceError):
    """Raised when trying to create an employee with an existing emp_Id."""
    pass

class EmployeeNotFoundError(EmployeeServiceError):
    """Raised when an employee is not found."""
    pass

class DependencyError(EmployeeServiceError):
    """Raised when an operation cannot be completed due to dependencies."""
    pass

class PermissionError(EmployeeServiceError):
    """Raised when a user lacks permission for an action."""
    # Note: Actual permission checking might happen in a higher layer (e.g., Controller/Auth Middleware)
    pass


class EmployeeService:
    """
    Service layer class for handling business logic related to Employees.
    """
    def __init__(self):
        self.employee_dao = EmployeeDAO()
        # Instantiate other DAOs if needed for dependency checks
        # self.project_dao = ProjectDAO()
        # self.task_dao = TaskDAO()
        # self.timesheet_dao = TimesheetDAO()

    def _validate_employee_data(self, employee_data: dict, is_update: bool = False, existing_emp_id: str = None):
        """
        Validates employee data for creation or update.
        Raises ValidationError if validation fails.
        """
        required_fields_create = ['ID', 'emp_Id', 'emp_name', 'emp_designation', 'date_of_join']
        required_fields_update = ['emp_name', 'emp_designation', 'date_of_join'] # emp_Id cannot be updated

        required_fields = required_fields_update if is_update else required_fields_create

        missing_fields = [field for field in required_fields if field not in employee_data or employee_data[field] is None or str(employee_data[field]).strip() == ""]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

        if not is_update:
            # Validate emp_Id format/uniqueness on create
            emp_id = employee_data.get('emp_Id')
            if not emp_id or not isinstance(emp_id, str) or len(emp_id) > 50:
                 raise ValidationError("Invalid emp_Id: Must be a non-empty string up to 50 characters.")
            if self.employee_dao.read(emp_id):
                raise DuplicateEmployeeError(f"Employee with emp_Id '{emp_id}' already exists.")
            # Validate ID uniqueness on create (assuming ID is not auto-generated based on schema)
            emp_db_id = employee_data.get('ID')
            if not isinstance(emp_db_id, int):
                 raise ValidationError("Invalid ID: Must be an integer.")
            # Simple check if an employee with this primary key ID exists (might need a specific DAO method)
            # This check is often redundant if the DB enforces PK constraints well.
            # if self.employee_dao.read_by_pk(emp_db_id): # Assuming read_by_pk exists
            #     raise DuplicateEmployeeError(f"Employee with primary key ID '{emp_db_id}' already exists.")

        # Validate emp_name
        emp_name = employee_data.get('emp_name')
        if emp_name and (not isinstance(emp_name, str) or len(emp_name) > 50):
            raise ValidationError("Invalid emp_name: Must be a string up to 50 characters.")

        # Validate emp_designation
        emp_designation = employee_data.get('emp_designation')
        if emp_designation and (not isinstance(emp_designation, str) or len(emp_designation) > 100):
            raise ValidationError("Invalid emp_designation: Must be a string up to 100 characters.")

        # Validate emp_skills
        emp_skills = employee_data.get('emp_skills')
        if emp_skills and (not isinstance(emp_skills, str) or len(emp_skills) > 500):
            raise ValidationError("Invalid emp_skills: Must be a string up to 500 characters.")

        # Validate date_of_join
        date_of_join_str = employee_data.get('date_of_join')
        if date_of_join_str:
            try:
                doj = date.fromisoformat(str(date_of_join_str))
                # Optional: Add rule like date_of_join cannot be in the future
                # if doj > date.today():
                #     raise ValidationError("Date of join cannot be in the future.")
            except (ValueError, TypeError):
                raise ValidationError("Invalid date_of_join: Must be a valid date in YYYY-MM-DD format.")

        # Validate creator/updater IDs if provided (they should exist)
        creator_id = employee_data.get('created_by')
        updater_id = employee_data.get('last_updated_by')

        if creator_id and not self.employee_dao.read(creator_id):
             raise ValidationError(f"Invalid created_by: Employee with emp_Id '{creator_id}' does not exist.")

        if updater_id and not self.employee_dao.read(updater_id):
             raise ValidationError(f"Invalid last_updated_by: Employee with emp_Id '{updater_id}' does not exist.")