import api from './api';

export const bankService = {
  getAll: async () => {
    const response = await api.get('/banks');
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/banks', data);
    return response.data;
  },

  uploadStatement: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/banks/upload-statement', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getStatements: async () => {
    const response = await api.get('/banks/statements');
    return response.data;
  },
};

export default bankService;