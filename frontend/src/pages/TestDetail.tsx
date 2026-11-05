import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, Download, ArrowLeft, ChevronRight } from 'lucide-react';
import {
  PageHeader, SectionCard, StatusBadge, CategoryBadge,
  OutcomeBadge, DemoBadge, LoadingOverlay, useToast, Spinner, Alert,
} from '../components/ui';
import { getTestSession, generateReport, getTestAuditLogs } from '../services/api';
import { RuleEvaluationPanel } from './TestWorkflows';
import type { AuditLog, RuleEvaluationSummary, CalculationResult } from '../types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Legend } from 'recharts';

const TestDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [showAudit, setShowAudit] = useState(false);

  const load = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [sessionData, logs] = await Promise.all([
        getTestSession(id),
        getTestAuditLogs(id),
      ]);
      setData(sessionData);
      setAuditLogs(logs);
      if (sessionData.latest_report) {
        setReportId((sessionData.latest_report as Record<string, unknown>).id as string);
      }
    } catch {
      showToast('Failed to load test session.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleGenerateReport = async () => {
    if (!id) return;
    try {
      setGenerating(true);
      const rep = await generateReport(id);
      setReportId(rep.report_id);
      showToast('PDF report generated successfully.', 'success');
    } catch {
      showToast('Report generation failed. Ensure calculations are complete.', 'error');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <LoadingOverlay message="Loading test session…" />;
  if (!data) return <p className="text-slate-500 text-sm">Test session not found.</p>;

  const session = data.session as Record<string, unknown>;
  const instrument = (session.instrument ?? {}) as Record<string, unknown>;
  const calcResult = data.calculation_result as CalculationResult | null;
  const ruleEval = data.rule_evaluation as RuleEvaluationSummary | null;
  const category = session.test_category as string;

  // Build chart data based on category
  const getChartData = () => {
    if (!calcResult) return [];
    if (category === 'eccentricity') {
      return calcResult.position_results?.map(p => ({
        name: p.position_name.split('(')[0].trim(),
        deviation: p.eccentricity_deviation,
        error: p.indication_error,
      })) ?? [];
    }
    if (category === 'linearity') {
      return calcResult.point_results?.map(p => ({
        load: p.load,
        corrected_error: p.corrected_error,
        direction: p.direction,
      })) ?? [];
    }
    if (category === 'repeatability') {
      return calcResult.run_records?.map(r => ({
        run: `R${r.run_number}`,
        indication: r.indication,
      })) ?? [];
    }
    return [];
  };

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <PageHeader
        title={`Test Session ${id}`}
        breadcrumb={['NAWI', 'Tests', id ?? '']}
        actions={
          <div className="flex gap-2">
            <button onClick={() => navigate('/tests')} className="btn-secondary text-xs"><ArrowLeft size={13} /> Back</button>
            {calcResult && (
              <button onClick={handleGenerateReport} disabled={generating} className="btn-primary text-xs">
                {generating ? <Spinner size="sm" /> : <FileText size={13} />}
                Generate Report
              </button>
            )}
            {reportId && (
              <a href={`/api/reports/${reportId}/download`} target="_blank" rel="noreferrer" className="btn-secondary text-xs">
                <Download size={13} /> Download PDF
              </a>
            )}
          </div>
        }
      />

      {/* Session Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SectionCard title="Session Info" className="md:col-span-2">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            {[
              ['Session ID', String(session.id ?? '')],
              ['Category', <CategoryBadge key="cat" category={category} />],
              ['Status', <StatusBadge key="st" status={String(session.status ?? '')} />],
              ['Operator', String(session.operator_name ?? '')],
              ['Test Date', new Date(session.test_date as string).toLocaleString('en-IN')],
              ['Laboratory', String(session.laboratory_location ?? '—')],
              ['Service Type', String(session.service_type ?? '—')],
              ['Temp / RH', `${session.ambient_temperature ?? '—'} °C / ${session.relative_humidity ?? '—'} %`],
            ].map(([k, v]) => (
              <React.Fragment key={String(k)}>
                <dt className="text-slate-500 font-medium text-xs">{String(k)}</dt>
                <dd className="text-slate-800 font-semibold text-xs">{v as React.ReactNode}</dd>
              </React.Fragment>
            ))}
          </dl>
          {(session.is_demo as boolean) && (
            <div className="mt-3 pt-3 border-t border-slate-100">
              <DemoBadge />
              <span className="ml-2 text-xs text-amber-700">This is a demonstration session. Results are for illustration purposes.</span>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Instrument">
          <dl className="space-y-2 text-sm">
            {[
              ['Model', instrument.model],
              ['Serial No.', instrument.serial_number],
              ['Class', instrument.accuracy_class],
              ['Max Cap.', `${instrument.max_capacity} ${instrument.unit}`],
              ['e', `${instrument.verification_scale_interval} ${instrument.unit}`],
            ].map(([k, v]) => (
              <div key={String(k)} className="flex justify-between">
                <span className="text-slate-500 text-xs">{String(k)}</span>
                <span className="font-semibold text-xs text-slate-800">{String(v ?? '—')}</span>
              </div>
            ))}
          </dl>
          <button
            onClick={() => navigate(`/instruments/${instrument.id}`)}
            className="mt-3 btn-secondary w-full justify-center text-xs"
          >
            View Instrument <ChevronRight size={12} />
          </button>
        </SectionCard>
      </div>

      {/* Observations */}
      {Boolean(data.observations) ? (
        <SectionCard title="Recorded Observations">
          <div className="overflow-x-auto">
            <pre className="text-xs text-slate-600 font-mono bg-slate-50 rounded-lg p-4 overflow-auto max-h-60 leading-relaxed">
              {JSON.stringify(data.observations, null, 2)}
            </pre>
          </div>
        </SectionCard>
      ) : (
        <Alert type="warn">
          No observations recorded yet for this session. Use the test workflow pages to enter observations.
        </Alert>
      )}

      {/* Calculation Summary */}
      {calcResult && (
        <SectionCard title={`Calculation Summary — ${category.charAt(0).toUpperCase() + category.slice(1)}`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {Object.entries(calcResult)
              .filter(([k, v]) => typeof v === 'number' && !['runs_count', 'points_count', 'positions_evaluated'].includes(k))
              .slice(0, 8)
              .map(([k, v]) => (
                <div key={k} className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">{k.replace(/_/g, ' ')}</p>
                  <p className="font-mono font-semibold text-slate-800 text-sm">{(v as number).toFixed(5)}</p>
                </div>
              ))}
          </div>

          {/* Chart */}
          {getChartData().length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-600 mb-2">Measurement Data Visualization</p>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={getChartData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey={category === 'eccentricity' ? 'name' : category === 'linearity' ? 'load' : 'run'} tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 2" />
                  <Line
                    type="monotone"
                    dataKey={category === 'eccentricity' ? 'deviation' : category === 'linearity' ? 'corrected_error' : 'indication'}
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Legend iconSize={10} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </SectionCard>
      )}

      {/* Rule Evaluation */}
      {ruleEval && <RuleEvaluationPanel ruleResult={ruleEval} />}

      {/* Audit Log */}
      <SectionCard
        title={`Audit Trail (${auditLogs.length} events)`}
        actions={
          <button onClick={() => setShowAudit(!showAudit)} className="text-xs text-blue-600 hover:underline">
            {showAudit ? 'Hide' : 'Show'} Events
          </button>
        }
      >
        {showAudit && auditLogs.length > 0 && (
          <div className="space-y-2 mt-2">
            {auditLogs.map(log => (
              <div key={log.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-slate-700">{log.action}</p>
                  <p className="text-xs text-slate-500">By {log.actor} · {new Date(log.timestamp).toLocaleString('en-IN')}</p>
                </div>
              </div>
            ))}
          </div>
        )}
        {!showAudit && (
          <p className="text-xs text-slate-400">Click "Show Events" to view the full audit trail.</p>
        )}
      </SectionCard>
    </div>
  );
};

export default TestDetail;

