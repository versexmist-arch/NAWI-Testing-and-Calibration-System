import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';
import {
  Layers, FlaskConical, CheckCircle2, Clock,
  TrendingUp, FileText, PlusCircle, ChevronRight, RefreshCw,
} from 'lucide-react';
import {
  PageHeader, MetricCard, SectionCard, StatusBadge,
  OutcomeBadge, CategoryBadge, DemoBadge, LoadingOverlay, useToast, Spinner,
} from '../components/ui';
import { getDashboardStats, resetDemoData } from '../services/api';
import type { DashboardStats } from '../types';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useToast();

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getDashboardStats();
      setStats(data);
    } catch {
      showToast('Failed to load dashboard data. Is the backend running?', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadStats(); }, []);

  const handleResetDemo = async () => {
    if (!confirm('Reset all demonstration data? Real records will not be affected.')) return;
    try {
      setResetting(true);
      await resetDemoData();
      showToast('Demo data reset successfully.', 'success');
      await loadStats();
    } catch {
      showToast('Failed to reset demo data.', 'error');
    } finally {
      setResetting(false);
    }
  };

  if (loading) return <LoadingOverlay message="Loading dashboard…" />;
  if (!stats) return null;

  const { metrics, category_distribution, compliance_distribution, recent_tests, recent_reports } = stats;

  // Build chart data for sessions (use category + compliance combined)
  const activityData = [
    { name: 'Eccentricity', tests: category_distribution.find(c => c.name === 'Eccentricity')?.value ?? 0 },
    { name: 'Linearity', tests: category_distribution.find(c => c.name === 'Linearity')?.value ?? 0 },
    { name: 'Repeatability', tests: category_distribution.find(c => c.name === 'Repeatability')?.value ?? 0 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Dashboard"
        subtitle="NAWI Testing & Calibration Management System · SIH26035"
        actions={
          <div className="flex gap-2">
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="btn-secondary text-xs"
            >
              {resetting ? <Spinner size="sm" /> : <RefreshCw size={14} />}
              Reset Demo
            </button>
            <button onClick={() => navigate('/instruments/register')} className="btn-primary text-xs">
              <PlusCircle size={14} /> Register Instrument
            </button>
            <button onClick={() => navigate('/tests')} className="btn-primary text-xs bg-emerald-600 hover:bg-emerald-700">
              <FlaskConical size={14} /> New Test
            </button>
          </div>
        }
      />

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Instruments"
          value={metrics.total_instruments}
          icon={<Layers size={16} />}
          color="text-blue-600"
        />
        <MetricCard
          label="Total Tests"
          value={metrics.total_tests}
          icon={<FlaskConical size={16} />}
          color="text-indigo-600"
        />
        <MetricCard
          label="Completed"
          value={metrics.completed_tests}
          icon={<CheckCircle2 size={16} />}
          color="text-emerald-600"
          sub={`of ${metrics.total_tests} sessions`}
        />
        <MetricCard
          label="In Progress / Draft"
          value={metrics.pending_tests}
          icon={<Clock size={16} />}
          color="text-amber-600"
        />
      </div>

      {/* Compliance Row */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="PASS"
          value={metrics.pass_count}
          icon={<CheckCircle2 size={16} />}
          color="text-emerald-600"
          sub="Verified OIML criteria met"
        />
        <MetricCard
          label="FAIL"
          value={metrics.fail_count}
          icon={<TrendingUp size={16} />}
          color="text-red-600"
          sub="Verified criteria violated"
        />
        <MetricCard
          label="Pending / Incomplete"
          value={metrics.pending_eval_count}
          icon={<Clock size={16} />}
          color="text-amber-600"
          sub="Awaiting evaluation or data"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Bar Chart: Category distribution */}
        <div className="md:col-span-2">
          <SectionCard title="Test Category Distribution" subtitle="Number of test sessions per category (from database)">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={activityData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="tests" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </SectionCard>
        </div>

        {/* Pie Chart: Compliance */}
        <SectionCard title="Compliance Summary" subtitle="Configured rule evaluation results">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={compliance_distribution.filter(d => d.value > 0)}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {compliance_distribution.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </SectionCard>
      </div>

      {/* Recent Tests + Reports */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recent Tests */}
        <SectionCard
          title="Recent Test Sessions"
          subtitle="Latest metrological testing activities"
          noPadding
          actions={
            <button onClick={() => navigate('/tests')} className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
              View all <ChevronRight size={12} />
            </button>
          }
        >
          <div className="divide-y divide-slate-100">
            {recent_tests.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">No test sessions yet</p>
            ) : (
              recent_tests.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between px-5 py-3 hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/tests/${t.id}`)}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-mono text-xs text-slate-500">{t.id}</span>
                      {t.is_demo && <DemoBadge />}
                    </div>
                    <p className="text-sm font-medium text-slate-800 truncate">{t.instrument_model || t.instrument_serial}</p>
                    <p className="text-xs text-slate-400">{t.operator}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0 ml-3">
                    <CategoryBadge category={t.category} />
                    <OutcomeBadge outcome={t.outcome} small />
                  </div>
                </div>
              ))
            )}
          </div>
        </SectionCard>

        {/* Recent Reports */}
        <SectionCard
          title="Recent Reports"
          subtitle="Generated PDF metrological test reports"
          noPadding
          actions={
            <button onClick={() => navigate('/reports')} className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
              View all <ChevronRight size={12} />
            </button>
          }
        >
          <div className="divide-y divide-slate-100">
            {recent_reports.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">No reports generated yet</p>
            ) : (
              recent_reports.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between px-5 py-3 hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/reports`)}
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <FileText size={12} className="text-blue-500 flex-shrink-0" />
                      <span className="font-mono text-xs text-slate-500 truncate">{r.id}</span>
                    </div>
                    <p className="text-sm font-medium text-slate-800 truncate">{r.instrument_serial}</p>
                    <p className="text-xs text-slate-400">By {r.generated_by}</p>
                  </div>
                  <span className="text-xs text-slate-400 flex-shrink-0 ml-2">
                    {new Date(r.created_at).toLocaleDateString('en-IN')}
                  </span>
                </div>
              ))
            )}
          </div>
        </SectionCard>
      </div>

      {/* Quick Actions */}
      <SectionCard title="Quick Actions" subtitle="Common workflow shortcuts">
        <div className="flex flex-wrap gap-3">
          <button onClick={() => navigate('/instruments/register')} className="btn-primary">
            <PlusCircle size={15} /> Register Instrument
          </button>
          <button onClick={() => navigate('/tests/eccentricity')} className="btn-secondary">
            <FlaskConical size={15} /> New Eccentricity Test
          </button>
          <button onClick={() => navigate('/tests/linearity')} className="btn-secondary">
            <TrendingUp size={15} /> New Linearity Test
          </button>
          <button onClick={() => navigate('/tests/repeatability')} className="btn-secondary">
            <FlaskConical size={15} /> New Repeatability Test
          </button>
          <button onClick={() => navigate('/reports')} className="btn-secondary">
            <FileText size={15} /> View Reports
          </button>
          <button onClick={() => navigate('/audit')} className="btn-secondary">
            <ChevronRight size={15} /> Audit History
          </button>
        </div>
      </SectionCard>
    </div>
  );
};

export default Dashboard;

