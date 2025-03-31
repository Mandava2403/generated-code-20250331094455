from datetime import date

class TimesheetStatus:
    SAVED = 'Saved'
    SUBMITTED = 'Submitted'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

class Timesheet:
    def __init__(self, id: int, time_sheet_date: date, project_id: int, project_name: str, task_id: int, employee_id: str, effort_in_hours: int = None, description: str = None, status: str = None, manager_comments: str = None):
        self.id = id
        self.time_sheet_date = time_sheet_date
        self.project_id = project_id
        self.project_name = project_name
        self.task_id = task_id
        self.effort_in_hours = effort_in_hours
        self.description = description
        self.employee_id = employee_id
        self.status = status
        self.manager_comments = manager_comments