import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText, Download, ArrowLeft, ChevronRight, History,
  Lock, AlertTriangle, ShieldCheck, CheckCircle2, RotateCcw,
  FileCheck, Clock, ExternalLink, Eye, Info
} from 'lucide-react';
import {
  PageHeader, SectionCard, StatusBadge, CategoryBadge,
  OutcomeBadge, DemoBadge, LoadingOverlay, useToast, Spinner, Alert,
  Modal, Badge
} from '../components/ui';
import {
  getTestSession, generateReport, getTestAuditLogs,
  amendTestSession, getTestRevisions, listUsers, getReportDownloadUrl
} from '../services/api';
import { RuleEvaluationPanel } from './TestWorkflows';
import type {
  AuditLog, RuleEvaluationSummary, CalculationResult,
  TestRevision, GeneratedReport, User
} from '../types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Legend } from 'recharts';

export const TestDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reportId, setReportId] = useState<string | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [showAudit, setShowAudit] = useState(false);

  // Revision & Amendment State
  const [revisions, setRevisions] = useState<TestRevision[]>([]);
  const [showAmendModal, setShowAmendModal] = useState(false);
  const [amendReason, setAmendReason] = useState('');
  const [amendOperator, setAmendOperator] = useState('');
  const [amendAction, setAmendAction] = useState<'reopen' | 'recalculate'>('reopen');
  const [amending, setAmending] = useState(false);
  const [selectedSnapshot, setSelectedSnapshot] = useState<TestRevision | null>(null);
  const [usersList, setUsersList] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  const load = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [sessionData, logs, revs, users] = await Promise.all([
        getTestSession(id),
        getTestAuditLogs(id),
        getTestRevisions(id).catch(() => []),
        listUsers().catch(() => []),
      ]);
      setData(sessionData);
      setAuditLogs(logs);
      setRevisions(revs);
      setUsersList(users);

      // Resolve active user from localStorage
      const savedUserStr = localStorage.getItem('nawi_active_user');
      let active = users.length > 0 ? users[0] : null;
      if (savedUserStr) {
        try {
          const parsed = JSON.parse(savedUserStr);
          const match = users.find(u => u.id === parsed.id || u.username === parsed.username);
          if (match) active = match;
        } catch {
          // ignore
        }
      }
      setCurrentUser(active);
      if (active) {
        setAmendOperator(active.full_name);
      }

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
      await load(); // reload to get new report in reports list
    } catch {
      showToast('Report generation failed. Ensure calculations are complete.', 'error');
    } finally {
      setGenerating(false);
    }
  };

  const handleAmendSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    if (!amendReason.trim() || amendReason.trim().length < 5) {
      showToast('Amendment reason must be at least 5 characters.', 'error');
      return;
    }
    if (!amendOperator.trim()) {
      showToast('Operator identification is required.', 'error');
      return;
    }

    try {
      setAmending(true);
      const payload: {
        reason: string;
        operator_name: string;
        observations?: unknown[];
      } = {
        reason: amendReason.trim(),
        operator_name: amendOperator.trim(),
      };

      if (amendAction === 'recalculate' && data?.observations) {
        payload.observations = data.observations as unknown[];
      }

      const res = await amendTestSession(id, payload);
      showToast(`Test session successfully amended to Revision ${res.new_version || (session.version ? Number(session.version) + 1 : 2)}.`, 'success');
      setShowAmendModal(false);
      setAmendReason('');
      await load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to amend test session.';
      showToast(msg, 'error');
    } finally {
      setAmending(false);
    }
  };

  if (loading) return <LoadingOverlay message="Loading test session…" />;
  if (!data) return <p className="text-slate-500 text-sm">Test session not found.</p>;

  const session = data.session as Record<string, unknown>;
  const instrument = (session.instrument ?? {}) as Record<string, unknown>;
  const calcResult = data.calculation_result as CalculationResult | null;
  const ruleEval = data.rule_evaluation as RuleEvaluationSummary | null;
  const category = session.test_category as string;
  const reportsList = (data.reports as GeneratedReport[]) || [];
  const sessionVersion = Number(session.version || 1);
  const isCompleted = session.status === 'Completed';

  // Role capability check
  const isUserAuthorizedToAmend = Boolean(
    currentUser &&
    ['Administrator', 'Laboratory Manager', 'Reviewer', 'Admin', 'Manager'].some(
      r => (currentUser.role || '').toLowerCase().includes(r.toLowerCase())
    )
  );

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
    <div className="max-w-5xl mx-auto space-y-5 pb-12">
      <PageHeader
        title={`Test Session ${id}`}
        breadcrumb={['NAWI', 'Tests', id ?? '']}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={() => navigate('/tests')} className="btn-secondary text-xs">
              <ArrowLeft size={13} /> Back
            </button>

            {/* If completed, show Amendment Action Button */}
            {isCompleted && (
              <button
                onClick={() => setShowAmendModal(true)}
                className="btn-secondary text-xs border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100 flex items-center gap-1.5"
                title="Initiate controlled revision/amendment for completed test"
              >
                <History size={13} className="text-amber-600" />
                Amend Session (Rev {sessionVersion})
              </button>
            )}

            {calcResult && (
              <button onClick={handleGenerateReport} disabled={generating} className="btn-primary text-xs">
                {generating ? <Spinner size="sm" /> : <FileText size={13} />}
                Generate Report
              </button>
            )}
            {reportId && (
              <a href={getReportDownloadUrl(reportId)} target="_blank" rel="noreferrer" className="btn-secondary text-xs">
                <Download size={13} /> Download Latest PDF
              </a>
            )}
          </div>
        }
      />

      {/* Revision & Immutability Status Banner */}
      {sessionVersion > 1 ? (
        <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/80 flex items-start gap-3 shadow-xs">
          <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center flex-shrink-0 mt-0.5">
            <History size={18} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold text-amber-900">AMENDED TEST RECORD — Revision {sessionVersion}</h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-200 text-amber-900 uppercase">
                Amended
              </span>
            </div>
            <p className="text-xs text-amber-800 mt-1 leading-relaxed">
              This session was amended under ISO/IEC 17025 metrological change control. Historical measurements from Revision 1 to {sessionVersion - 1} are archived immutably in the revision history below.
            </p>
          </div>
        </div>
      ) : isCompleted ? (
        <div className="p-3.5 rounded-xl border border-blue-200/80 bg-blue-50/60 flex items-center justify-between text-xs text-blue-900">
          <div className="flex items-center gap-2">
            <Lock size={15} className="text-blue-700" />
            <span className="font-semibold">Completed & Certified Session (Revision 1 — Original)</span>
            <span className="text-blue-700/80 text-[11px]">· Protected from direct overwrites. Use "Amend Session" for formal corrections.</span>
          </div>
          <span className="font-mono text-[11px] bg-blue-100/80 px-2 py-0.5 rounded text-blue-800">
            Immutable Record
          </span>
        </div>
      ) : null}

      {/* Session Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SectionCard title="Session Info" className="md:col-span-2">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            {[
              ['Session ID', String(session.id ?? '')],
              ['Category', <CategoryBadge key="cat" category={category} />],
              [
                'Status & Version',
                <div key="st-ver" className="flex items-center gap-1.5 flex-wrap">
                  <StatusBadge status={String(session.status ?? '')} />
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-bold">
                    v{sessionVersion} {sessionVersion > 1 ? '(Amended)' : '(Original)'}
                  </span>
                </div>
              ],
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
            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2">
              <DemoBadge />
              <span className="text-xs text-amber-700">Demonstration session. Results generated for verification illustration.</span>
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
        <SectionCard
          title={`Recorded Observations (Active Session — Rev ${sessionVersion})`}
          subtitle="Measurements entered and validated against instrument capacity and scale divisions"
        >
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
        <SectionCard
          title={`Calculation Summary — ${category.charAt(0).toUpperCase() + category.slice(1)} (Rev ${sessionVersion})`}
          subtitle="OIML R-76 verified calculation algorithms with standard rounding and MPE evaluations"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {Object.entries(calcResult)
              .filter(([k, v]) => typeof v === 'number' && !['runs_count', 'points_count', 'positions_evaluated'].includes(k))
              .slice(0, 8)
              .map(([k, v]) => (
                <div key={k} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                  <p className="text-xs text-slate-500 mb-1">{k.replace(/_/g, ' ')}</p>
                  <p className="font-mono font-semibold text-slate-800 text-sm">{(v as number).toFixed(5)}</p>
                </div>
              ))}
          </div>

          {/* Chart */}
          {getChartData().length > 0 && (
            <div className="pt-2">
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

      {/* Generated Reports & Version Control */}
      <SectionCard
        title={`Calibration Certificates & Reports (${reportsList.length})`}
        subtitle="Immutable PDF certificates linked to exact calculation revisions"
      >
        {reportsList.length === 0 ? (
          <p className="text-xs text-slate-400">No calibration report generated yet for this session.</p>
        ) : (
          <div className="space-y-2.5">
            {reportsList.map((rep) => {
              const isSuperseded = Boolean(rep.is_superseded);
              return (
                <div
                  key={rep.id}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl border text-xs gap-3 ${
                    isSuperseded
                      ? 'bg-slate-50/70 border-slate-200 text-slate-500'
                      : 'bg-emerald-50/40 border-emerald-200 text-slate-800'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        isSuperseded ? 'bg-slate-200 text-slate-500' : 'bg-emerald-100 text-emerald-700'
                      }`}
                    >
                      <FileCheck size={16} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-slate-900">{rep.file_name}</span>
                        <span
                          className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                            isSuperseded
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          Rev {rep.version || 1} {isSuperseded ? '· SUPERSEDED' : '· ACTIVE'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Issued: {new Date(rep.created_at).toLocaleString('en-IN')}
                        {isSuperseded && rep.superseded_by && (
                          <span className="text-amber-700 ml-1 font-medium">
                            (Superseded by {rep.superseded_by})
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    <a
                      href={getReportDownloadUrl(rep.id)}
                      target="_blank"
                      rel="noreferrer"
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold inline-flex items-center gap-1.5 transition-colors ${
                        isSuperseded
                          ? 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
                          : 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-xs'
                      }`}
                    >
                      <Download size={13} />
                      {isSuperseded ? 'Download Superseded PDF' : 'Download Active Certificate'}
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </SectionCard>

      {/* Revision History & Traceability */}
      <SectionCard
        title={`Amendment History & Traceability (${revisions.length} historical revisions)`}
        subtitle="Complete immutable snapshots preserved in accordance with ISO/IEC 17025"
      >
        {revisions.length === 0 ? (
          <p className="text-xs text-slate-400">
            No amendments have been recorded. This session is currently on its original creation revision (v1).
          </p>
        ) : (
          <div className="space-y-3">
            {revisions.map((rev) => (
              <div
                key={rev.id}
                className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs space-y-2"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-1 rounded-md bg-blue-100 text-blue-800 font-mono font-bold text-xs">
                      Rev {rev.revision_number} Snapshot
                    </span>
                    <span className="text-xs font-bold text-slate-800">
                      Amended by {rev.amended_by}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={12} />
                    <span>{new Date(rev.created_at).toLocaleString('en-IN')}</span>
                    {rev.overall_outcome && (
                      <OutcomeBadge outcome={rev.overall_outcome} small />
                    )}
                  </div>
                </div>

                <div className="text-xs">
                  <span className="font-semibold text-slate-700">Amendment Reason / Justification: </span>
                  <span className="text-slate-600 italic">"{rev.amendment_reason}"</span>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-[11px] text-slate-400 font-mono">
                    Snapshot ID: {rev.id}
                  </span>
                  <button
                    type="button"
                    onClick={() => setSelectedSnapshot(selectedSnapshot?.id === rev.id ? null : rev)}
                    className="text-xs text-blue-600 hover:text-blue-800 font-semibold inline-flex items-center gap-1"
                  >
                    <Eye size={12} />
                    {selectedSnapshot?.id === rev.id ? 'Hide Snapshot Data' : 'Inspect Archived Snapshot'}
                  </button>
                </div>

                {/* Expanded Snapshot Inspection */}
                {selectedSnapshot?.id === rev.id && (
                  <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono space-y-2">
                    <div className="flex justify-between items-center text-slate-700 font-bold border-b pb-1">
                      <span>Archived Revision {rev.revision_number} Data Snapshot</span>
                      <span className="text-[10px] text-slate-400 font-normal">Read-only historical view</span>
                    </div>
                    {rev.calculation_result ? (
                      <div>
                        <p className="text-[11px] text-slate-500 font-sans font-semibold mb-1">Archived Calculations:</p>
                        <pre className="text-[11px] bg-white p-2 rounded border border-slate-200 max-h-40 overflow-auto">
                          {JSON.stringify(rev.calculation_result, null, 2)}
                        </pre>
                      </div>
                    ) : null}
                    {rev.observations ? (
                      <div>
                        <p className="text-[11px] text-slate-500 font-sans font-semibold mb-1">Archived Observations:</p>
                        <pre className="text-[11px] bg-white p-2 rounded border border-slate-200 max-h-40 overflow-auto">
                          {JSON.stringify(rev.observations, null, 2)}
                        </pre>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Audit Log */}
      <SectionCard
        title={`Audit Trail (${auditLogs.length} events)`}
        subtitle="Traceable chronological timeline of actions performed on this session"
        actions={
          <button onClick={() => setShowAudit(!showAudit)} className="text-xs text-blue-600 hover:underline font-semibold">
            {showAudit ? 'Hide' : 'Show'} Events
          </button>
        }
      >
        {showAudit && auditLogs.length > 0 && (
          <div className="space-y-2 mt-2">
            {auditLogs.map(log => (
              <div key={log.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-bold text-slate-800">{log.action}</p>
                    <span className="text-[10px] text-slate-400">{new Date(log.timestamp).toLocaleString('en-IN')}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">By <span className="font-medium text-slate-700">{log.actor}</span></p>
                  {log.details && Object.keys(log.details).length > 0 && (
                    <div className="mt-1 text-[11px] text-slate-500 font-mono bg-white p-1.5 rounded border border-slate-200">
                      {JSON.stringify(log.details)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {!showAudit && (
          <p className="text-xs text-slate-400">Click "Show Events" to view the full audit trail.</p>
        )}
      </SectionCard>

      {/* Amendment Initiation Modal */}
      {showAmendModal && (
        <Modal
          title="Initiate Controlled Test Session Amendment"
          subtitle={`Test Session ${id} · Current Revision: v${sessionVersion}`}
          onClose={() => setShowAmendModal(false)}
        >
          <form onSubmit={handleAmendSubmit} className="space-y-4">
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 leading-relaxed flex items-start gap-2.5">
              <Info size={16} className="text-amber-700 flex-shrink-0 mt-0.5" />
              <div>
                <strong>Metrological Integrity Notice (ISO/IEC 17025 & OIML R-76):</strong> Completed test sessions cannot be silently overwritten. Submitting this amendment will:
                <ul className="list-disc ml-4 mt-1 space-y-0.5">
                  <li>Archive current state (observations, calculations, outcome) as Revision {sessionVersion}.</li>
                  <li>Increment session version to <strong>v{sessionVersion + 1}</strong>.</li>
                  <li>Mark previously issued certificates as superseded.</li>
                  <li>Create a permanent, non-repudiable audit trail entry.</li>
                </ul>
              </div>
            </div>

            {/* Authenticated Identity & RBAC Status */}
            <div className={`p-3 rounded-xl border text-xs ${
              isUserAuthorizedToAmend
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}>
              <div className="flex items-center justify-between">
                <span className="font-bold flex items-center gap-1.5">
                  {isUserAuthorizedToAmend ? (
                    <>
                      <CheckCircle2 size={14} className="text-emerald-600" />
                      Authorized Calibration Signatory
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={14} className="text-rose-600" />
                      Role-Based Access Control Restriction
                    </>
                  )}
                </span>
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-white font-bold border border-current">
                  {currentUser?.role || 'Operator'}
                </span>
              </div>
              <p className="mt-1 text-[11px] leading-relaxed">
                {isUserAuthorizedToAmend ? (
                  <>Active user <strong>{currentUser?.full_name}</strong> holds required authority to execute formal metrological revisions.</>
                ) : (
                  <>Active user <strong>{currentUser?.full_name}</strong> is logged in as <em>"{currentUser?.role}"</em>. Routine laboratory operators are prohibited from unilaterally amending certified test sessions. Switch to a <strong>Reviewer</strong>, <strong>Laboratory Manager</strong>, or <strong>Administrator</strong> in the topbar to authorize this change.</>
                )}
              </p>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Amendment Signatory Attribution
              </label>
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-700 flex items-center justify-between">
                <span className="font-medium">{currentUser?.full_name || 'Dr. Sarah Jenkins'}</span>
                <span className="text-slate-400 font-mono text-[11px]">ID: {currentUser?.id || 'USR-01'}</span>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Amendment Justification / Reason <span className="text-red-500">* (min 5 characters)</span>
              </label>
              <textarea
                value={amendReason}
                onChange={e => setAmendReason(e.target.value)}
                rows={3}
                placeholder="State the technical reason for this amendment (e.g., 'Corrected tare weight after instrument zero verification failure in run 2', 'Re-evaluation requested by technical auditor')..."
                className="input-field text-xs w-full font-sans"
                required
              />
              <span className="text-[10px] text-slate-400 block mt-0.5">
                Characters: {amendReason.length} (minimum 5 required)
              </span>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Amendment Workflow Action
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 bg-slate-50 cursor-pointer text-xs">
                  <input
                    type="radio"
                    name="amendAction"
                    checked={amendAction === 'reopen'}
                    onChange={() => setAmendAction('reopen')}
                    className="text-blue-600"
                  />
                  <div>
                    <span className="font-semibold text-slate-800">Reopen session for observation re-entry</span>
                    <p className="text-[11px] text-slate-500">
                      Changes status back to "In Progress" so technician can re-record measurements.
                    </p>
                  </div>
                </label>

                <label className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 bg-slate-50 cursor-pointer text-xs">
                  <input
                    type="radio"
                    name="amendAction"
                    checked={amendAction === 'recalculate'}
                    onChange={() => setAmendAction('recalculate')}
                    className="text-blue-600"
                  />
                  <div>
                    <span className="font-semibold text-slate-800">Recalculate immediately under new revision</span>
                    <p className="text-[11px] text-slate-500">
                      Applies amended version counter and recalculates without changing raw observations.
                    </p>
                  </div>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAmendModal(false)}
                className="btn-secondary text-xs"
                disabled={amending}
              >
                Cancel
              </button>
              <button
                type="submit"
                className={`text-xs py-2 px-4 rounded-xl font-bold flex items-center gap-1.5 transition-colors ${
                  !isUserAuthorizedToAmend
                    ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                    : 'bg-amber-600 hover:bg-amber-700 text-white shadow-xs'
                }`}
                disabled={amending || !isUserAuthorizedToAmend || amendReason.trim().length < 5}
              >
                {amending ? <Spinner size="sm" /> : <History size={13} />}
                Confirm & Record Revision
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default TestDetail;
