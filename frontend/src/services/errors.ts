export class APIError extends Error {
  endpoint: string;
  status?: number;
  detail?: string;

  constructor(endpoint: string, message: string, status?: number, detail?: string) {
    super(message);
    this.name = 'APIError';
    this.endpoint = endpoint;
    this.status = status;
    this.detail = detail;
  }
}

export function formatApiError(endpoint: string, status?: number, statusText?: string, detail?: string): string {
  const base = `Erro ao buscar ${endpoint}`;
  const http = status ? ` (HTTP ${status}${statusText ? ` ${statusText}` : ''})` : '';
  const det = detail ? `: ${detail}` : '';
  return `${base}${http}${det}`;
}