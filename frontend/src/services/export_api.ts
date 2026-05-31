import apiClient from './api';

export const exportSVG = async (executionId: string): Promise<Blob> => {
  const response = await apiClient.post(
    '/api/export/svg',
    { execution_id: executionId },
    { responseType: 'blob' },
  );
  return response.data as Blob;
};

export const exportPDF = async (executionId: string): Promise<Blob> => {
  const response = await apiClient.post(
    '/api/export/pdf',
    { execution_id: executionId },
    { responseType: 'blob' },
  );
  return response.data as Blob;
};

export const exportParameters = async (executionId: string): Promise<object> => {
  const response = await apiClient.post('/api/export/parameters', {
    execution_id: executionId,
  });
  return response.data as object;
};
