export interface Task {
  task_id: string;
  task_name: string;
  task_description: string;
  expected_outcome: string;
  emp_id: string;
  project_ID: string;
  estimated_hours: number;
  actual_hours: number;
  start_date: string;
  completion_date: string;
  created_date: string;
  created_by: string;
  last_updated_date: string;
  last_updated_by: string;
}

export interface TaskFormData extends Task {}

export interface ApiResponse {
  success: boolean;
  message: string;
  data?: any;
}