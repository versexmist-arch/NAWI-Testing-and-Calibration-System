import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import {
  Layers, FlaskConical, CheckCircle2, Clock,
  FileText, PlusCircle, ChevronRight, RefreshCw,
  Scale, ShieldAlert, Sparkles, Activity, AlertTriangle,
  RotateCcw, ExternalLink
} from 'lucide-react';
import {
  PageHeader, MetricCard, SectionCard,
  OutcomeBadge, CategoryBadge, DemoBadge, LoadingOverlay, useToast, Spinner, Modal
} from '../components/ui';
import { getDashboardStats, resetDemoData } from '../services/api';
import type { DashboardStats } from '../types';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'tests' | 'instruments' | 'reports' | 'audit'>('tests');

  const navigate = useNavigate();
  const { showToast } = useToast();

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getDashboardStats();
      setStats(data);
    } catch {
      showToast('Failed to load laboratory statistics from backend.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleResetDemo = async () => {
    try {
      setResetting(true);
      await resetDemoData();
      showToast('Demonstration data refreshed without altering user records.', 'success');
      setShowResetModal(false);
      await loadStats();
    } catch {
      showToast('Failed to reset demo dataset.', 'error');
    } finally {
      setResetting(false);
    }
  };

  if (loading) return <LoadingOverlay message="Loading LIMS laboratory intelligence…" />;
  if (!stats) return null;

  const {
    metrics,
    category_distribution = [],
    compliance_distribution = [],
    accuracy_class_distribution = [],
    recent_tests = [],
    recent_reports = [],
    recent_instruments = [],
    recent_audit_events = []
  } = stats;

  const passRate = metrics.completed_tests > 0
    ? Math.round((metrics.pass_count / metrics.completed_tests) * 100)
    : 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* Top Page Header with LIMS Actions */}
      <PageHeader
        title="Laboratory Intelligence Dashboard"
        subtitle="Non-Automatic Weighing Instruments (NAWI) Metrological Control · OIML R-76"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setShowResetModal(true)}
              className="btn-secondary text-xs"
              title="Reset demonstration data while keeping authentic user records safe"
            >
              <RotateCcw size={14} className="text-slate-500" />
              Reset Demo Data
            </button>
            <button
              onClick={() => navigate('/instruments/register')}
              className="btn-secondary text-xs"
            >
              <PlusCircle size={14} className="text-blue-600" />
              Register Instrument
            </button>
            <button
              onClick={() => navigate('/tests/eccentricity')}
              className="btn-primary text-xs"
            >
              <FlaskConical size={14} />
              Start New Test
            </button>
          </div>
        }
      />

      {/* Demo vs Production Data Callout */}
      {(metrics.demo_instruments > 0 || metrics.demo_tests > 0) && (
        <div className="bg-gradient-to-r from-blue-50/80 via-indigo-50/50 to-white border border-blue-200/70 rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
              <Sparkles size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-800">
                  Dual Data Mode Active:
                </span>
                <span className="text-xs text-slate-600">
                  {metrics.genuine_user_instruments ?? (metrics.user_instruments - (metrics.test_artifact_instruments ?? 0))} user-registered &middot; {metrics.test_artifact_instruments ?? 0} test artifacts &middot; {metrics.demo_instruments} demo reference models
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                User-created records and OIML R-76 demo test suites are isolated. Demo resets will never alter or purge your authentic registered instruments.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/instruments')}
            className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 self-end md:self-auto flex-shrink-0"
          >
            Manage Instruments <ChevronRight size={14} />
          </button>
        </div>
      )}

      {/* Primary 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Registered Instruments"
          value={metrics.total_instruments}
          icon={<Scale size={18} />}
          color="text-blue-600"
          sub={`${metrics.active_instruments} active · ${metrics.genuine_user_instruments ?? 1} user · ${metrics.test_artifact_instruments ?? 4} test artifacts · ${metrics.demo_instruments} demo`}
          trend={{ value: `${metrics.active_instruments} Active`, positive: true }}
        />
        <MetricCard
          label="Total Test Sessions"
          value={metrics.total_tests}
          icon={<FlaskConical size={18} />}
          color="text-indigo-600"
          sub={`${metrics.completed_tests} completed, ${metrics.pending_tests} pending/draft`}
          trend={{ value: `${metrics.completed_tests} Completed`, positive: true }}
        />
        <MetricCard
          label="Test Evaluation Pass Rate"
          value={`${passRate}%`}
          icon={<CheckCircle2 size={18} />}
          color="text-emerald-600"
          sub={`${metrics.pass_count} passed, ${metrics.fail_count} failed criteria`}
          trend={{ value: `${metrics.pass_count} Passed`, positive: metrics.pass_count >= metrics.fail_count }}
        />
        <MetricCard
          label="Generated Reports"
          value={metrics.reports_generated}
          icon={<FileText size={18} />}
          color="text-sky-600"
          sub="OIML R-76 metrological test reports"
          trend={{ value: 'Archived', positive: true }}
        />
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Chart 1: Test Category Distribution */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Test Category Distribution</h2>
              <p className="text-xs text-slate-400">Proportion of OIML R-76 test modules</p>
            </div>
            <Activity size={16} className="text-blue-500" />
          </div>

          <div className="h-52">
            {category_distribution.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={category_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {category_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <FlaskConical size={24} className="mb-2 text-slate-300" />
                No test data recorded yet
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-2 mt-2 pt-3 border-t border-slate-100 text-center">
            {category_distribution.map((cat) => (
              <div key={cat.name} className="px-1">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                  <span className="text-[11px] font-semibold text-slate-600 truncate">{cat.name}</span>
                </div>
                <p className="text-xs font-bold text-slate-800">{cat.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Chart 2: Compliance Outcomes */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Compliance & Tolerances</h2>
              <p className="text-xs text-slate-400">Rule evaluations against OIML Table 6</p>
            </div>
            <CheckCircle2 size={16} className="text-emerald-500" />
          </div>

          <div className="h-52">
            {compliance_distribution.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={compliance_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {compliance_distribution.map((entry, index) => (
                      <Cell key={`cell-comp-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <CheckCircle2 size={24} className="mb-2 text-slate-300" />
                No evaluated sessions yet
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-2 mt-2 pt-3 border-t border-slate-100 text-center">
            {compliance_distribution.map((comp) => (
              <div key={comp.name} className="px-1">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: comp.color }} />
                  <span className="text-[11px] font-semibold text-slate-600 truncate">{comp.name}</span>
                </div>
                <p className="text-xs font-bold text-slate-800">{comp.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Chart 3: Accuracy Class Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Instrument Accuracy Classes</h2>
              <p className="text-xs text-slate-400">Class I Special to Class IIII Ordinary</p>
            </div>
            <Scale size={16} className="text-indigo-500" />
          </div>

          <div className="h-52">
            {accuracy_class_distribution.some(d => d.count > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={accuracy_class_distribution.filter(d => d.count > 0)} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="class_name" tick={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none'
                    }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs">
                <Scale size={24} className="mb-2 text-slate-300" />
                No instruments classified
              </div>
            )}
          </div>

          <div className="mt-2 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 px-2">
            <span>Standard: OIML R-76-1 Table 3</span>
            <span className="font-semibold text-slate-700">{metrics.total_instruments} Total Units</span>
          </div>
        </div>
      </div>

      {/* Quick Testing Workflow Launchers */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-800">Quick Workflow Launchers</h2>
            <p className="text-xs text-slate-400">Direct shortcuts to active metrological verification procedures</p>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <button
            onClick={() => navigate('/instruments/register')}
            className="flex flex-col items-center justify-center p-3.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 transition-all group text-center"
          >
            <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
              <PlusCircle size={20} />
            </div>
            <span className="text-xs font-semibold text-slate-800">Register NAWI</span>
            <span className="text-[10px] text-slate-400 mt-0.5">New instrument</span>
          </button>

          <button
            onClick={() => navigate('/tests/eccentricity')}
            className="flex flex-col items-center justify-center p-3.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 transition-all group text-center"
          >
            <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
              <FlaskConical size={20} />
            </div>
            <span className="text-xs font-semibold text-slate-800">Eccentricity</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Corner load test</span>
          </button>

          <button
            onClick={() => navigate('/tests/linearity')}
            className="flex flex-col items-center justify-center p-3.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 transition-all group text-center"
          >
            <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
              <Activity size={20} />
            </div>
            <span className="text-xs font-semibold text-slate-800">Linearity</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Multi-point load</span>
          </button>

          <button
            onClick={() => navigate('/tests/repeatability')}
            className="flex flex-col items-center justify-center p-3.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 transition-all group text-center"
          >
            <div className="w-10 h-10 rounded-lg bg-violet-100 text-violet-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
              <RefreshCw size={20} />
            </div>
            <span className="text-xs font-semibold text-slate-800">Repeatability</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Standard deviation</span>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="flex flex-col items-center justify-center p-3.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 transition-all group text-center"
          >
            <div className="w-10 h-10 rounded-lg bg-sky-100 text-sky-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
              <FileText size={20} />
            </div>
            <span className="text-xs font-semibold text-slate-800">Certificates</span>
            <span className="text-[10px] text-slate-400 mt-0.5">PDF certificates</span>
          </button>

          <button
            onClick={() => navigate('/audit')}
            className="flex flex-col items-center justify-center p-3.5 rounded-xl border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/50 transition-all group text-center"
          >
            <div className="w-10 h-10 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
              <ShieldAlert size={20} />
            </div>
            <span className="text-xs font-semibold text-slate-800">Audit Logs</span>
            <span className="text-[10px] text-slate-400 mt-0.5">Security trace</span>
          </button>
        </div>
      </div>

      {/* Multi-Tab Recent Activity Workspace */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
          <div>
            <h2 className="text-sm font-bold text-slate-800">Laboratory Activity Stream</h2>
            <p className="text-xs text-slate-400">Real-time log of testing, registration, and reporting events</p>
          </div>

          {/* Activity Tabs */}
          <div className="flex items-center gap-1 bg-slate-200/60 p-1 rounded-xl text-xs font-medium">
            <button
              onClick={() => setActiveTab('tests')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'tests' ? 'bg-white text-blue-700 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Recent Tests ({recent_tests.length})
            </button>
            <button
              onClick={() => setActiveTab('instruments')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'instruments' ? 'bg-white text-blue-700 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              New Instruments ({recent_instruments.length})
            </button>
            <button
              onClick={() => setActiveTab('reports')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'reports' ? 'bg-white text-blue-700 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Reports ({recent_reports.length})
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'audit' ? 'bg-white text-blue-700 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Audit Trail ({recent_audit_events.length})
            </button>
          </div>
        </div>

        {/* Tab 1: Recent Tests */}
        {activeTab === 'tests' && (
          <div className="divide-y divide-slate-100">
            {recent_tests.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">No recent test sessions recorded.</div>
            ) : (
              recent_tests.map((test) => (
                <div
                  key={test.id}
                  onClick={() => navigate(`/tests/${test.id}`)}
                  className="px-5 py-3.5 hover:bg-blue-50/40 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-blue-100/70 text-blue-600 flex items-center justify-center flex-shrink-0">
                      <FlaskConical size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800 truncate">
                          {test.instrument_model || test.instrument_serial}
                        </span>
                        {test.is_demo && <DemoBadge />}
                        <span className="text-[11px] font-mono text-slate-400">SN: {test.instrument_serial}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate">
                        Tested by <span className="font-medium text-slate-700">{test.operator}</span> &middot; {new Date(test.test_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <CategoryBadge category={test.category} />
                    <OutcomeBadge outcome={test.outcome} small />
                    <ChevronRight size={14} className="text-slate-400" />
                  </div>
                </div>
              ))
            )}
            <div className="p-3 bg-slate-50/50 text-center">
              <button
                onClick={() => navigate('/tests')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                View Complete Test Directory &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Tab 2: Recent Instruments */}
        {activeTab === 'instruments' && (
          <div className="divide-y divide-slate-100">
            {recent_instruments.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">No registered instruments found.</div>
            ) : (
              recent_instruments.map((inst) => (
                <div
                  key={inst.id}
                  onClick={() => navigate(`/instruments/${inst.id}`)}
                  className="px-5 py-3.5 hover:bg-blue-50/40 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center flex-shrink-0">
                      <Scale size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800 truncate">
                          {inst.manufacturer} {inst.model}
                        </span>
                        {inst.is_demo && <DemoBadge />}
                        <span className="text-[11px] font-mono text-slate-400">SN: {inst.serial_number}</span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        Accuracy Class: <span className="font-semibold text-blue-600">{inst.accuracy_class}</span> &middot; Max: {inst.max_capacity} {inst.unit}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-[11px] text-slate-400">
                      {new Date(inst.created_at).toLocaleDateString()}
                    </span>
                    <ChevronRight size={14} className="text-slate-400" />
                  </div>
                </div>
              ))
            )}
            <div className="p-3 bg-slate-50/50 text-center">
              <button
                onClick={() => navigate('/instruments')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                Explore Full Instrument Registry &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Recent Reports */}
        {activeTab === 'reports' && (
          <div className="divide-y divide-slate-100">
            {recent_reports.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">No calibration certificates issued yet.</div>
            ) : (
              recent_reports.map((report) => (
                <div
                  key={report.id}
                  onClick={() => navigate('/reports')}
                  className="px-5 py-3.5 hover:bg-blue-50/40 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-red-100 text-red-600 flex items-center justify-center flex-shrink-0">
                      <FileText size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800 truncate">
                          {report.file_name}
                        </span>
                        <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                          {report.instrument_serial}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500">
                        Generated by {report.generated_by} &middot; {new Date(report.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs font-semibold text-blue-600 flex items-center gap-1">
                      Download PDF <ExternalLink size={12} />
                    </span>
                  </div>
                </div>
              ))
            )}
            <div className="p-3 bg-slate-50/50 text-center">
              <button
                onClick={() => navigate('/reports')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                Go to Certificate Vault &rarr;
              </button>
            </div>
          </div>
        )}

        {/* Tab 4: Recent Audit Trail */}
        {activeTab === 'audit' && (
          <div className="divide-y divide-slate-100">
            {recent_audit_events.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">No audit events logged.</div>
            ) : (
              recent_audit_events.map((evt) => (
                <div
                  key={evt.id}
                  className="px-5 py-3.5 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center flex-shrink-0 font-mono text-[10px]">
                      LOG
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800">{evt.action}</p>
                      <p className="text-[11px] text-slate-400">
                        Actor: <span className="text-slate-600">{evt.actor}</span>
                        {evt.instrument_id && ` · Ref: ${evt.instrument_id}`}
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 flex-shrink-0">
                    {new Date(evt.timestamp).toLocaleString()}
                  </span>
                </div>
              ))
            )}
            <div className="p-3 bg-slate-50/50 text-center">
              <button
                onClick={() => navigate('/audit')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                Inspect Full Audit Trail &rarr;
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal for Resetting Demo Data */}
      {showResetModal && (
        <Modal
          title="Reset Demonstration Data"
          onClose={() => setShowResetModal(false)}
        >
          <div className="space-y-4">
            <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl p-3.5 text-xs">
              <AlertTriangle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-amber-950 mb-1">Metrological Verification Safety Guarantee</p>
                <p>
                  Resetting the demo dataset will re-initialize default OIML R-76 reference instruments, standard test sessions, and sample reports.
                </p>
                <p className="mt-1 font-semibold text-amber-800">
                  Your authentic user-registered instruments and test results will NEVER be modified or erased.
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600">
              Do you wish to proceed with refreshing the 3 standard demo instruments and their baseline calibration records?
            </p>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowResetModal(false)}
                className="btn-secondary text-xs"
                disabled={resetting}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleResetDemo}
                className="btn-primary text-xs bg-amber-600 hover:bg-amber-700 text-white"
                disabled={resetting}
              >
                {resetting ? <Spinner size="sm" /> : <RotateCcw size={14} />}
                Confirm Reset Demo
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default Dashboard;
