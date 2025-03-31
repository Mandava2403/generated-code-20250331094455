from datetime import date
from enum import Enum

class ProjectStatus(Enum):
    OPEN = 'open'
    INPROGRESS = 'inprogress'
    COMPLETED = 'completed'

class Project:
    def __init__(self, ID: int, proj_name: str = None, project_description: str = None, project_status: ProjectStatus = None, go_live_date: date = None, dev_start_date: date = None, dev_end_date: date = None, QA_start_date: date = None, QA_end_date: date = None, UIT_start_date: date = None, UIT_end_date: date = None, created_by: str = None, created_date: date = None, last_updated_by: str = None, last_updated_date: date = None):
        self.id = ID
        self.proj_name = proj_name
        self.project_description = project_description
        self.project_status = project_status.value if project_status else None
        self.go_live_date = go_live_date
        self.dev_start_date = dev_start_date
        self.dev_end_date = dev_end_date
        self.qa_start_date = QA_start_date
        self.qa_end_date = QA_end_date
        self.uit_start_date = UIT_start_date
        self.uit_end_date = UIT_end_date
        self.created_by = created_by
        self.created_date = created_date
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date