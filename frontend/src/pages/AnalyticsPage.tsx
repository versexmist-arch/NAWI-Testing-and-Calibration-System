import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, AreaChart, Area, Legend
} from 'recharts';
import {
  Calendar, BarChart3, TrendingUp, CheckCircle2,
  XCircle, Award, Users, Filter, RotateCcw
} from 'lucide-react';
import {
  PageHeader, MetricCard, SectionCard,
  LoadingOverlay, useToast, Spinner
} from '../components/ui';
import { getAnalytics } from '../services/api';
import type { AnalyticsData } from '../types';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const { showToast } = useToast();

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const res = await getAnalytics({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
      setData(res);
    } catch {
      showToast('Failed to load laboratory analytics.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [startDate, endDate]);

  const handleResetFilters = () => {
    setStartDate('');
    setEndDate('');
  };

  if (loading && !data) return <LoadingOverlay message="Computing laboratory analytics…" />;
  if (!data) return null;

  const {
    summary,
    monthly_trend = [],
    category_distribution = [],
    compliance_distribution = [],
    accuracy_class_distribution = [],
    operator_distribution = [],
  } = data;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      <PageHeader
        title="Quality & Performance Analytics"
        subtitle="Aggregate metrics, compliance trends, and operator throughput for Non-Automatic Weighing Instruments"
        breadcrumb={['Laboratory', 'Analytics']}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 bg-white border border-slate-200/80 rounded-xl px-2.5 py-1.5 text-xs shadow-sm">
              <Calendar size={13} className="text-slate-400" />
              <input
                type="date"
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                className="text-xs text-slate-700 bg-transparent focus:outline-none"
                placeholder="Start Date"
              />
              <span className="text-slate-400">to</span>
              <input
                type="date"
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                className="text-xs text-slate-700 bg-transparent focus:outline-none"
                placeholder="End Date"
              />
            </div>
            {(startDate || endDate) && (
              <button
                onClick={handleResetFilters}
                className="btn-secondary text-xs"
                title="Clear date range filter"
              >
                <RotateCcw size={13} />
                Clear Dates
              </button>
            )}
          </div>
        }
      />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Total Test Sessions"
          value={summary.total_tests}
          icon={<BarChart3 size={18} />}
          color="text-blue-600"
          sub={`${summary.completed_tests} completed tests`}
        />
        <MetricCard
          label="Compliance Pass Rate"
          value={`${summary.pass_rate_percentage}%`}
          icon={<CheckCircle2 size={18} />}
          color="text-emerald-600"
          sub={`${summary.passed_tests} pass, ${summary.failed_tests} fail`}
          trend={{ value: `${summary.pass_rate_percentage}% Compliant`, positive: summary.pass_rate_percentage >= 80 }}
        />
        <MetricCard
          label="Pending Sessions"
          value={summary.pending_tests}
          icon={<TrendingUp size={18} />}
          color="text-amber-600"
          sub="Drafts or incomplete evaluations"
        />
        <MetricCard
          label="Certificates Issued"
          value={summary.total_reports_generated}
          icon={<Award size={18} />}
          color="text-indigo-600"
          sub="ISO/IEC 17025 accredited PDFs"
        />
      </div>

      {/* Charts Row 1: Monthly Trends & Category Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Monthly Trend Area Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Monthly Testing Volume & Outcomes</h2>
              <p className="text-xs text-slate-400">Total sessions executed vs verified passing tests</p>
            </div>
            <TrendingUp size={16} className="text-blue-500" />
          </div>

          <div className="h-64">
            {monthly_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthly_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorTests" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorPassed" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Area type="monotone" dataKey="tests" name="Total Sessions" stroke="#3b82f6" fillOpacity={1} fill="url(#colorTests)" />
                  <Area type="monotone" dataKey="passed" name="Passed Criteria" stroke="#10b981" fillOpacity={1} fill="url(#colorPassed)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No monthly trend data available
              </div>
            )}
          </div>
        </div>

        {/* Test Category Distribution */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Test Procedure Mix</h2>
              <p className="text-xs text-slate-400">Share of calibration procedures</p>
            </div>
            <BarChart3 size={16} className="text-indigo-500" />
          </div>

          <div className="h-48">
            {category_distribution.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={category_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {category_distribution.map((entry, index) => (
                      <Cell key={`cat-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No tests recorded
              </div>
            )}
          </div>

          <div className="space-y-1.5 pt-3 border-t border-slate-100">
            {category_distribution.map(cat => (
              <div key={cat.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                  <span className="text-slate-600 font-medium">{cat.name}</span>
                </div>
                <span className="font-bold text-slate-800">{cat.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts Row 2: Accuracy Class & Operator Throughput */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Accuracy Class Distribution */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Tested Instruments by Accuracy Class</h2>
              <p className="text-xs text-slate-400">OIML R-76 Class I Special to Class IIII Ordinary</p>
            </div>
          </div>

          <div className="h-56">
            {accuracy_class_distribution.some(d => d.count > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={accuracy_class_distribution} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="class_name" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No instrument class distribution available
              </div>
            )}
          </div>
        </div>

        {/* Operator Throughput */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-800">Metrologist & Operator Productivity</h2>
              <p className="text-xs text-slate-400">Sessions recorded per laboratory operator</p>
            </div>
            <Users size={16} className="text-emerald-500" />
          </div>

          <div className="h-56">
            {operator_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={operator_distribution}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} allowDecimals={false} />
                  <YAxis dataKey="operator" type="category" tick={{ fontSize: 10, fill: '#64748b' }} width={90} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                  <Bar dataKey="tests_count" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No operator records available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;

