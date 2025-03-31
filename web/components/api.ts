import axios from 'axios';
import { Employee } from '../types/employee';

const API_BASE_URL = '/api';

export const employeeApi = {
  validateEmployee: async (employee: Employee, isUpdate: boolean = false) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/validate-employee`, {
        employee,
        is_update: isUpdate,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  checkDependencies: async (empId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/check-dependencies/${empId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  validateEmployeeExists: async (empId: string, fieldName: string) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/validate-employee-exists/${empId}/${fieldName}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  createEmployee: async (employee: Employee) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/employees`, employee);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  updateEmployee: async (employee: Employee) => {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/employees/${employee.ID}`,
        employee
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};