import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5001/api';

// Create instance with auth header
const api = axios.create({
  baseURL: API_URL
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (username, password) => {
  const response = await api.post('/auth/login', { username, password });
  if (response.data.access_token) {
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('username', response.data.username);
  }
  return response.data;
};

export const register = async (username, password) => {
  return (await api.post('/auth/register', { username, password })).data;
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return (await api.post('/upload-document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })).data;
};

export const factCheckClaim = async (claim) => {
  return (await api.post('/fact-check', { claim })).data;
};

export const analyzeImage = async (image, query) => {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('query', query);
  return (await api.post('/analyze-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })).data;
};

export const getHistory = async () => {
  return (await api.get('/history')).data;
};

export const batchFactCheck = async (claims) => {
  return (await api.post('/batch-check', { claims })).data;
};

export const getStats = async () => {
  return (await api.get('/stats')).data;
};

export const getKbStatus = async () => {
  return (await api.get('/kb-status')).data;
};

export const downloadReport = async (checkId) => {
  const response = await api.get(`/download-report/${checkId}`, {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `medical_report_${checkId}.pdf`);
  document.body.appendChild(link);
  link.click();
};
