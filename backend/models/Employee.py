from datetime import date

class Employee:
    def __init__(self, ID: int, emp_Id: str, emp_name: str = None, emp_designation: str = None, emp_skills: str = None, date_of_join: date = None, created_by: str = None, created_date: date = None, last_updated_by: str = None, last_updated_date: date = None):
        self.id = ID
        self.emp_id = emp_Id
        self.emp_name = emp_name
        self.emp_designation = emp_designation
        self.emp_skills = emp_skills
        self.date_of_join = date_of_join
        self.created_by = created_by
        self.created_date = created_date
        self.last_updated_by = last_updated_by
        self.last_updated_date = last_updated_date