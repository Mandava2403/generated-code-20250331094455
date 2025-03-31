import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Save, X } from 'lucide-react';
import { Employee, EmployeeFormData } from '../types/employee';
import { employeeApi } from '../services/api';

interface EmployeeFormProps {
  employee?: Employee;
  onSubmit: () => void;
  onCancel: () => void;
}

const initialFormData: EmployeeFormData = {
  ID: '',
  emp_Id: '',
  emp_name: '',
  emp_designation: '',
  emp_skills: '',
  date_of_join: '',
  created_date: new Date().toISOString(),
  created_by: 'current_user', // Replace with actual logged-in user
  last_updated_date: new Date().toISOString(),
  last_updated_by: 'current_user', // Replace with actual logged-in user
};

export const EmployeeForm: React.FC<EmployeeFormProps> = ({
  employee,
  onSubmit,
  onCancel,
}) => {
  const [formData, setFormData] = useState<EmployeeFormData>(initialFormData);
  const [errors, setErrors] = useState<Partial<Record<keyof EmployeeFormData, string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (employee) {
      setFormData({
        ...employee,
        emp_skills: employee.emp_skills.join(', '),
      });
    }
  }, [employee]);

  const validateForm = async (): Promise<boolean> => {
    const newErrors: Partial<Record<keyof EmployeeFormData, string>> = {};

    // Basic validation
    if (!formData.emp_Id.trim()) {
      newErrors.emp_Id = 'Employee ID is required';
    }
    if (!formData.emp_name.trim()) {
      newErrors.emp_name = 'Employee name is required';
    }
    if (!formData.emp_designation.trim()) {
      newErrors.emp_designation = 'Designation is required';
    }
    if (!formData.date_of_join) {
      newErrors.date_of_join = 'Date of joining is required';
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length > 0) {
      return false;
    }

    try {
      // API validation
      const employeeData: Employee = {
        ...formData,
        emp_skills: formData.emp_skills.split(',').map(skill => skill.trim()),
      };

      await employeeApi.validateEmployee(employeeData, !!employee);
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

      const employeeData: Employee = {
        ...formData,
        emp_skills: formData.emp_skills.split(',').map(skill => skill.trim()),
        last_updated_date: new Date().toISOString(),
      };

      if (employee) {
        await employeeApi.updateEmployee(employeeData);
        toast.success('Employee updated successfully');
      } else {
        await employeeApi.createEmployee(employeeData);
        toast.success('Employee created successfully');
      }

      onSubmit();
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Operation failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (errors[name as keyof EmployeeFormData]) {
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
            Employee ID
            <input
              type="text"
              name="emp_Id"
              value={formData.emp_Id}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.emp_Id ? 'border-red-500' : ''
              }`}
              disabled={!!employee}
            />
          </label>
          {errors.emp_Id && (
            <p className="mt-1 text-sm text-red-600">{errors.emp_Id}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Employee Name
            <input
              type="text"
              name="emp_name"
              value={formData.emp_name}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.emp_name ? 'border-red-500' : ''
              }`}
            />
          </label>
          {errors.emp_name && (
            <p className="mt-1 text-sm text-red-600">{errors.emp_name}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Designation
            <input
              type="text"
              name="emp_designation"
              value={formData.emp_designation}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.emp_designation ? 'border-red-500' : ''
              }`}
            />
          </label>
          {errors.emp_designation && (
            <p className="mt-1 text-sm text-red-600">{errors.emp_designation}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Skills (comma-separated)
            <input
              type="text"
              name="emp_skills"
              value={formData.emp_skills}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="React, TypeScript, Node.js"
            />
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Date of Joining
            <input
              type="date"
              name="date_of_join"
              value={formData.date_of_join}
              onChange={handleChange}
              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 ${
                errors.date_of_join ? 'border-red-500' : ''
              }`}
            />
          </label>
          {errors.date_of_join && (
            <p className="mt-1 text-sm text-red-600">{errors.date_of_join}</p>
          )}
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
          {isSubmitting ? 'Saving...' : employee ? 'Update' : 'Create'}
        </button>
      </div>
    </form>
  );
};