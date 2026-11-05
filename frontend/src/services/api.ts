import axios from 'axios';
import type {
  Instrument, TestSession, GeneratedReport, AuditLog,
  DashboardStats, CalculationResult, RuleEvaluationSummary
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// --- Health ---
export const checkHealth = () => api.get('/health');

// --- Dashboard ---
export const getDashboardStats = (): Promise<DashboardStats> =>
  api.get<DashboardStats>('/dashboard/stats').then(r => r.data);

// --- Instruments ---
export const listInstruments = (params?: {
  search?: string;
  accuracy_class?: string;
  include_archived?: boolean;
}): Promise<Instrument[]> =>
  api.get<Instrument[]>('/instruments', { params }).then(r => r.data);

export const getInstrument = (id: string) =>
  api.get(`/instruments/${id}`).then(r => r.data);

export const createInstrument = (data: Partial<Instrument>) =>
  api.post<Instrument>('/instruments', data).then(r => r.data);

export const updateInstrument = (id: string, data: Partial<Instrument>) =>
  api.put<Instrument>(`/instruments/${id}`, data).then(r => r.data);

export const archiveInstrument = (id: string) =>
  api.delete(`/instruments/${id}`).then(r => r.data);

// --- Test Sessions ---
export const listTestSessions = (params?: {
  category?: string;
  status?: string;
  instrument_id?: string;
  search?: string;
}): Promise<TestSession[]> =>
  api.get<TestSession[]>('/tests', { params }).then(r => r.data);

export const getTestSession = (id: string) =>
  api.get(`/tests/${id}`).then(r => r.data);

export const createTestSession = (data: {
  instrument_id: string;
  test_category: string;
  operator_name: string;
  laboratory_location?: string;
  ambient_temperature?: number;
  relative_humidity?: number;
  service_type?: string;
  test_configuration?: Record<string, unknown>;
}) => api.post<TestSession>('/tests', data).then(r => r.data);

export const updateTestSession = (id: string, data: Partial<TestSession>) =>
  api.put(`/tests/${id}`, data).then(r => r.data);

export const saveObservations = (
  testId: string,
  observations: unknown[],
  test_configuration?: Record<string, unknown>
) => api.post(`/tests/${testId}/observations`, { observations, test_configuration }).then(r => r.data);

export const runCalculations = (testId: string): Promise<{
  calculation_result: CalculationResult;
  rule_evaluation: RuleEvaluationSummary;
  status: string;
}> => api.post(`/tests/${testId}/calculate`).then(r => r.data);

export const getTestResults = (testId: string) =>
  api.get(`/tests/${testId}/results`).then(r => r.data);

export const generateReport = (testId: string) =>
  api.post(`/tests/${testId}/report`).then(r => r.data);

export const getTestAuditLogs = (testId: string): Promise<AuditLog[]> =>
  api.get<AuditLog[]>(`/tests/${testId}/audit`).then(r => r.data);

// --- Reports ---
export const listReports = (instrument_id?: string): Promise<GeneratedReport[]> =>
  api.get<GeneratedReport[]>('/reports', { params: instrument_id ? { instrument_id } : undefined }).then(r => r.data);

export const getReport = (id: string): Promise<GeneratedReport> =>
  api.get<GeneratedReport>(`/reports/${id}`).then(r => r.data);

export const getReportDownloadUrl = (id: string) => `/api/reports/${id}/download`;

// --- Audit ---
export const listAuditLogs = (params?: {
  limit?: number;
  offset?: number;
  action?: string;
}): Promise<AuditLog[]> =>
  api.get<AuditLog[]>('/audit', { params }).then(r => r.data);

// --- Rules ---
export const getRulesConfig = () =>
  api.get('/rules').then(r => r.data);

// --- Demo Data ---
export const resetDemoData = () =>
  api.post('/demo/reset').then(r => r.data);

export const seedDemoData = () =>
  api.post('/demo/seed').then(r => r.data);

export default api;

