from datetime import date

class Task:
    def __init__(self, task_id: int, project_ID: int = None, task_name: str = None, task_description: str = None, expected_outcome: str = None, start_date: date = None, completion_date: date = None, estimated_hours: int = None, actual_hours: int = None, emp_id: str = None, created_by: str = None, created_date: date = None, last_updated_by: str = None, last_updated_date: date = None):
        self.task_id = task_id
        self.project_id = project_ID
        self.task_name = task_name
        self.task_description = task_description
        self.expected_outcome = expected_outcome
        self.start_date = start_date
        self.completion_date = completion_date
        self.estimated_hours = estimated_hours
        self.actual_hours = actual_hours
        self.emp_id = emp_id
        self.created_by = created_by
        self.created_date = created_date
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date