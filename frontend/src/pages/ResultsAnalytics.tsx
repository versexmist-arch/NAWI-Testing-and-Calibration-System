import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader, SectionCard, StatusBadge, CategoryBadge, OutcomeBadge, LoadingOverlay } from '../components/ui';
import { listTestSessions } from '../services/api';
import type { TestSession } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';

const ResultsAnalytics: React.FC = () => {
  const [sessions, setSessions] = useState<TestSession[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    listTestSessions().then(setSessions).finally(() => setLoading(false));
  }, []);

  const completedSessions = sessions.filter(s => s.has_calculations);

  // Category breakdown
  const categoryData = ['eccentricity', 'linearity', 'repeatability'].map(cat => ({
    name: cat.charAt(0).toUpperCase() + cat.slice(1),
    count: sessions.filter(s => s.test_category === cat).length,
  }));

  // Compliance distribution for completed sessions
  const complianceData = [
    { name: 'PASS', value: completedSessions.filter(s => s.overall_outcome === 'PASS').length, fill: '#10b981' },
    { name: 'FAIL', value: completedSessions.filter(s => s.overall_outcome === 'FAIL').length, fill: '#ef4444' },
    { name: 'Pending', value: completedSessions.filter(s => s.overall_outcome && !['PASS', 'FAIL'].includes(s.overall_outcome)).length, fill: '#f59e0b' },
    { name: 'No Eval', value: sessions.filter(s => !s.overall_outcome).length, fill: '#94a3b8' },
  ].filter(d => d.value > 0);

  if (loading) return <LoadingOverlay />;

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <PageHeader
        title="Results & Analytics"
        breadcrumb={['NAWI', 'Results']}
        subtitle="Summary analytics across all metrological test sessions"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <SectionCard title="Tests by Category" subtitle="Number of sessions per test type">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {categoryData.map((_, i) => (
                  <Cell key={i} fill={['#3b82f6', '#10b981', '#8b5cf6'][i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </SectionCard>

        <SectionCard title="Compliance Outcomes" subtitle="OIML Rule evaluation results">
          {complianceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={complianceData} cx="50%" cy="50%" outerRadius={75} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                  {complianceData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-slate-400 text-center py-10">No evaluated sessions yet.</p>
          )}
        </SectionCard>
      </div>

      {/* All Results Table */}
      <SectionCard
        title={`All Test Results (${completedSessions.length} with calculations)`}
        noPadding
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px]">
            <thead>
              <tr>
                <th className="table-header">Session ID</th>
                <th className="table-header">Instrument</th>
                <th className="table-header">Category</th>
                <th className="table-header">Test Date</th>
                <th className="table-header">Status</th>
                <th className="table-header">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr
                  key={s.id}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/tests/${s.id}`)}
                >
                  <td className="table-cell font-mono text-xs">{s.id}</td>
                  <td className="table-cell">
                    <p className="text-xs font-medium">{s.instrument?.model}</p>
                    <p className="text-xs text-slate-400">{s.instrument?.serial_number}</p>
                  </td>
                  <td className="table-cell"><CategoryBadge category={s.test_category} /></td>
                  <td className="table-cell text-xs">{new Date(s.test_date).toLocaleDateString('en-IN')}</td>
                  <td className="table-cell"><StatusBadge status={s.status} /></td>
                  <td className="table-cell"><OutcomeBadge outcome={s.overall_outcome} /></td>
                </tr>
              ))}
              {sessions.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-sm text-slate-400">No test sessions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
};

export default ResultsAnalytics;

