import axios from 'axios';
import { Task } from '../types/task';

const API_BASE_URL = '/api';

export const taskApi = {
  validateTask: async (task: Task, isUpdate: boolean = false) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/validate-task`, {
        task,
        is_update: isUpdate,
      });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getTasksByProject: async (projectId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tasks/project/${projectId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  findByEmpId: async (empId: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/tasks/employee/${empId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  updateActualHours: async (taskId: string, hoursToAdd: number) => {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/tasks/${taskId}/hours`,
        { hours_to_add: hoursToAdd }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  createTask: async (task: Task) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/tasks`, task);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  updateTask: async (task: Task) => {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/tasks/${task.task_id}`,
        task
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};