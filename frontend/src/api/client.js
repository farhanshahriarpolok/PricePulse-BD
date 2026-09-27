import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorData = error.response ? error.response.data : { message: error.message };
    console.error('API Error:', errorData);
    return Promise.reject(errorData);
  }
);

export default apiClient;
