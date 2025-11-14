
import axios from 'axios';

const API_URL = 'http://localhost:5001/api';

export const getFiles = () => {
  return axios.get(`${API_URL}/files`);
};

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_URL}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const downloadFile = (fileId) => {
  return axios.get(`${API_URL}/files/${fileId}`, {
    responseType: 'blob',
  });
};
