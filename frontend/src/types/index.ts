// Shared TypeScript types for NAWI Testing & Calibration LIMS Platform

export interface Instrument {
  id: string;
  serial_number: string;
  manufacturer: string;
  model: string;
  instrument_type: string;
  accuracy_class: string;
  max_capacity: number;
  min_capacity?: number;
  verification_scale_interval: number;
  actual_scale_interval?: number;
  unit: string;
  scale_intervals_count?: number;
  location?: string;
  registration_date: string;
  notes?: string;
  is_demo: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: 'Administrator' | 'Laboratory Manager' | 'Metrologist/Operator' | 'Reviewer';
  qualification?: string;
  department?: string;
  is_active: boolean;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface LaboratorySettings {
  id: number;
  lab_name: string;
  organization: string;
  accreditation_number: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  contact_email?: string;
  contact_phone?: string;
  default_temperature: number;
  default_humidity: number;
  default_mass_unit: string;
  report_header_title: string;
  report_disclaimer: string;
  updated_at: string;
}

export interface TestSession {
  id: string;
  instrument_id: string;
  test_category: 'eccentricity' | 'linearity' | 'repeatability';
  operator_name: string;
  laboratory_location?: string;
  ambient_temperature?: number;
  relative_humidity?: number;
  service_type: string;
  status: string;
  version: number;
  test_configuration?: Record<string, unknown>;
  is_demo: boolean;
  test_date: string;
  created_at: string;
  updated_at: string;
  instrument?: Instrument;
  has_observations: boolean;
  has_calculations: boolean;
  has_rule_evaluations: boolean;
  overall_outcome?: string;
}

export interface ObservationEntry {
  position_id?: string;
  position_name?: string;
  indication: number;
  zero_indication?: number;
  reference_load?: number;
  load?: number;
  direction?: 'increasing' | 'decreasing';
  run_number?: number;
  delta_load?: number;
  [key: string]: unknown;
}

export interface PositionResult {
  position_id: string;
  position_name: string;
  reference_load: number;
  indication: number;
  zero_indication: number;
  indication_error: number;
  eccentricity_deviation: number;
  abs_eccentricity_deviation: number;
  unit: string;
  indication_error_in_e?: number;
  eccentricity_deviation_in_e?: number;
}

export interface LinearityPoint {
  index: number;
  load: number;
  indication: number;
  direction: string;
  zero_indication: number;
  delta_load: number;
  indication_error: number;
  corrected_error: number;
  abs_corrected_error: number;
  unit: string;
  load_in_e?: number;
  corrected_error_in_e?: number;
}

export interface RepeatabilityRun {
  run_number: number;
  indication: number;
  reference_load: number;
  error: number;
  deviation_from_mean: number;
  unit: string;
}

export interface CalculationResult {
  calculation_version: string;
  method: string;
  test_category: string;
  unit: string;
  verification_scale_interval_e?: number;
  // Eccentricity
  reference_load?: number;
  center_indication?: number;
  center_error?: number;
  max_absolute_eccentricity_deviation?: number;
  max_eccentricity_deviation_position?: string;
  max_absolute_indication_error?: number;
  positions_evaluated?: number;
  position_results?: PositionResult[];
  // Linearity
  points_count?: number;
  zero_load_error?: number;
  max_positive_error?: number;
  max_negative_error?: number;
  max_absolute_error?: number;
  max_hysteresis?: number;
  has_hysteresis_data?: boolean;
  hysteresis_results?: unknown[];
  point_results?: LinearityPoint[];
  use_changeover_points?: boolean;
  // Repeatability
  runs_count?: number;
  min_indication?: number;
  max_indication?: number;
  repeatability_range?: number;
  mean_indication?: number;
  sample_variance?: number;
  standard_deviation?: number;
  mean_error?: number;
  repeatability_range_in_e?: number;
  run_records?: RepeatabilityRun[];
}

export interface RuleItemEvaluation {
  rule_id: string;
  rule_name: string;
  source_reference: string;
  rule_version: string;
  verification_status: 'VERIFIED' | 'PENDING_VERIFICATION';
  outcome: 'PASS' | 'FAIL' | 'INCOMPLETE' | 'NOT_APPLICABLE' | 'PENDING_VERIFICATION';
  applicable_criterion: string;
  observed_value: string;
  tolerance_limit: string;
  explanation: string;
  details?: unknown[];
}

export interface RuleEvaluationSummary {
  overall_outcome: string;
  rule_version: string;
  rules_evaluated_count: number;
  passed_count: number;
  failed_count: number;
  incomplete_count: number;
  not_applicable_count: number;
  pending_verification_count: number;
  evaluations: RuleItemEvaluation[];
  summary_text: string;
}

export interface GeneratedReport {
  id: string;
  test_session_id: string;
  instrument_id: string;
  file_name: string;
  generated_by: string;
  report_type: string;
  created_at: string;
  instrument?: Instrument;
}

export interface AuditLog {
  id: string;
  test_session_id?: string;
  instrument_id?: string;
  actor: string;
  action: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface DashboardMetrics {
  total_instruments: number;
  active_instruments: number;
  total_tests: number;
  completed_tests: number;
  pending_tests: number;
  pass_count: number;
  fail_count: number;
  pending_eval_count: number;
  reports_generated: number;
  demo_instruments: number;
  user_instruments: number;
  test_artifact_instruments: number;
  genuine_user_instruments: number;
  demo_tests: number;
  user_tests: number;
  test_artifact_tests: number;
  genuine_user_tests: number;
}

export interface RecentInstrumentItem {
  id: string;
  serial_number: string;
  manufacturer: string;
  model: string;
  accuracy_class: string;
  max_capacity: number;
  unit: string;
  is_demo: boolean;
  created_at: string;
}

export interface RecentTestItem {
  id: string;
  instrument_serial: string;
  instrument_model: string;
  category: string;
  operator: string;
  status: string;
  outcome?: string;
  test_date: string;
  is_demo: boolean;
}

export interface RecentReportItem {
  id: string;
  file_name: string;
  test_session_id: string;
  instrument_serial: string;
  generated_by: string;
  created_at: string;
}

export interface RecentAuditItem {
  id: string;
  action: string;
  actor: string;
  test_session_id?: string;
  instrument_id?: string;
  timestamp: string;
}

export interface DashboardStats {
  metrics: DashboardMetrics;
  category_distribution: Array<{ name: string; value: number; color: string }>;
  compliance_distribution: Array<{ name: string; value: number; color: string }>;
  accuracy_class_distribution: Array<{ class_name: string; count: number }>;
  recent_instruments: RecentInstrumentItem[];
  recent_tests: RecentTestItem[];
  recent_reports: RecentReportItem[];
  recent_audit_events: RecentAuditItem[];
}

export interface AnalyticsData {
  summary: {
    total_tests: number;
    completed_tests: number;
    passed_tests: number;
    failed_tests: number;
    pending_tests: number;
    pass_rate_percentage: number;
    total_reports_generated: number;
  };
  monthly_trend: Array<{ month: string; tests: number; passed: number; failed: number }>;
  category_distribution: Array<{ name: string; value: number; color: string }>;
  compliance_distribution: Array<{ name: string; value: number; color: string }>;
  accuracy_class_distribution: Array<{ class_name: string; count: number }>;
  operator_distribution: Array<{ operator: string; tests_count: number }>;
}

export type TestCategory = 'eccentricity' | 'linearity' | 'repeatability';
export type SessionStatus = 'Draft' | 'In Progress' | 'Calculated' | 'Completed' | 'Incomplete';
export type Outcome = 'PASS' | 'FAIL' | 'INCOMPLETE' | 'NOT_APPLICABLE' | 'PENDING_VERIFICATION';
