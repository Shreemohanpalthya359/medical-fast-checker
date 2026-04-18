import axios from 'axios';

const API_URL = 'http://127.0.0.1:5000/api';

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${API_URL}/upload-document`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const factCheckClaim = async (claim) => {
  const response = await axios.post(`${API_URL}/fact-check`, {
    claim: claim,
  });
  return response.data;
};
