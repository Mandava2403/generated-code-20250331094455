export interface Employee {
  ID: string;
  emp_Id: string;
  emp_name: string;
  emp_designation: string;
  emp_skills: string[];
  date_of_join: string;
  created_date: string;
  created_by: string;
  last_updated_date: string;
  last_updated_by: string;
}

export interface EmployeeFormData extends Omit<Employee, 'emp_skills'> {
  emp_skills: string;
}

export interface ApiResponse {
  success: boolean;
  message: string;
  data?: any;
}