import api from './api';

export const aiService = {
  getPredictions: async () => {
    try {
      const response = await api.get('/ai/predictions');
      return response.data;
    } catch (error) {
      console.error('getPredictions error:', error);
      throw error;
    }
  },

  getAdvice: async (query) => {
    try {
      console.log('Calling AI advice API with query:', query);
      const response = await api.post('/ai/advice', { query });
      console.log('AI advice response:', response.data);
      return response.data;
    } catch (error) {
      console.error('getAdvice error:', error);
      throw error;
    }
  },

  getInsights: async () => {
    try {
      const response = await api.get('/ai/insights');
      return response.data;
    } catch (error) {
      console.error('getInsights error:', error);
      throw error;
    }
  },
};

// Export as default as well
export default aiService;