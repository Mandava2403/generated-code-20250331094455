import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Save, X, Clock, Calendar } from 'lucide-react';
import { Task, TaskFormData } from '../types/task';
import { taskApi } from '../services/taskApi';

interface TaskFormProps {
  task?: Task;
  onSubmit: () => void;
  onCancel: () => void;
}

const initialFormData: TaskFormData = {
  task_id: '',
  task_name: '',
  task_description: '',
  expected_outcome: '',
  emp_id: '',
  project_ID: '',
  estimated_hours: 0,
  actual_hours: 0,
  start_date: '',
  completion_date: '',
  created_date: new Date().toISOString(),
  created_by: 'current_user', // Replace with actual logged-in user
  last_updated_date: new Date().toISOString(),
  last_updated_by: 'current_user', // Replace with actual logged-in user
};

export const TaskForm: React.FC<TaskFormProps> = ({
  task,
  onSubmit,
  onCancel,
}) => {
  const [formData, setFormData] = useState<TaskFormData>(initialFormData);
  const [errors, setErrors] = useState<Partial<Record<keyof TaskFormData, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (task) {
      setFormData(task);
    }
  }, [task]);

  const validateForm = async (): Promise<boolean> => {
    const newErrors: Partial<Record<keyof TaskFormData, string>> = {};

    if (!formData.task_name.trim()) {
      newErrors.task_name = 'Task name is required';
    }
    if (!formData.emp_id.trim()) {
      newErrors.emp_id = 'Employee ID is required';
    }
    if (!formData.project_ID.trim()) {
      newErrors.project_ID = 'Project ID is required';
    }
    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required';
    }
    if (formData.estimated_hours <= 0) {
      newErrors.estimated_hours = 'Estimated hours must be greater than 0';
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length > 0) {
      return false;
    }

    try {
      await taskApi.validateTask(formData, !!task);
      return true;
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Validation failed');
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const isValid = await validateForm();
      if (!isValid) {
        return;
      }

      const taskData: Task = {
        ...formData,
        last_updated_date: new Date().toISOString(),
      };

      if (task) {
        await taskApi.updateTask(taskData);
        toast.success('Task updated successfully');
      } else {
        await taskApi.createTask(taskData);
        toast.success('Task created successfully');
      }

      onSubmit();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));

    if (errors[name as keyof TaskFormData]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow-lg">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Task Name
            <input
              type="text"
              name="task_name"
              value={formData.task_name}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.task_name ? 'border-red-500' : ''
              }`}
            />
          </label>
          {errors.task_name && (
            <p className="mt-1 text-sm text-red-600">{errors.task_name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Employee ID
            <input
              type="text"
              name="emp_id"
              value={formData.emp_id}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.emp_id ? 'border-red-500' : ''
              }`}
            />
          </label>
          {errors.emp_id && (
            <p className="mt-1 text-sm text-red-600">{errors.emp_id}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Project ID
            <input
              type="text"
              name="project_ID"
              value={formData.project_ID}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.project_ID ? 'border-red-500' : ''
              }`}
            />
          </label>
          {errors.project_ID && (
            <p className="mt-1 text-sm text-red-600">{errors.project_ID}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Estimated Hours
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Clock className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="number"
                name="estimated_hours"
                value={formData.estimated_hours}
                onChange={handleChange}
                min="0"
                step="0.5"
                className={`pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                  errors.estimated_hours ? 'border-red-500' : ''
                }`}
              />
            </div>
          </label>
          {errors.estimated_hours && (
            <p className="mt-1 text-sm text-red-600">{errors.estimated_hours}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Start Date
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Calendar className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                className={`pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                  errors.start_date ? 'border-red-500' : ''
                }`}
              />
            </div>
          </label>
          {errors.start_date && (
            <p className="mt-1 text-sm text-red-600">{errors.start_date}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Completion Date
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Calendar className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="date"
                name="completion_date"
                value={formData.completion_date}
                onChange={handleChange}
                className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </label>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Task Description
            <textarea
              name="task_description"
              value={formData.task_description}
              onChange={handleChange}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </label>
        </div>

        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Expected Outcome
            <textarea
              name="expected_outcome"
              value={formData.expected_outcome}
              onChange={handleChange}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </label>
        </div>
      </div>

      <div className="flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <X className="h-4 w-4 mr-2" />
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <Save className="h-4 w-4 mr-2" />
          {isSubmitting ? 'Saving...' : task ? 'Update Task' : 'Create Task'}
        </button>
      </div>
    </form>
  );
};