import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, PlusCircle, ChevronRight, FlaskConical } from 'lucide-react';
import {
  PageHeader, SectionCard, StatusBadge, CategoryBadge,
  OutcomeBadge, DemoBadge, LoadingOverlay, EmptyState,
} from '../components/ui';
import { listTestSessions } from '../services/api';
import type { TestSession } from '../types';

const TestManagement: React.FC = () => {
  const [sessions, setSessions] = useState<TestSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    try {
      setLoading(true);
      const data = await listTestSessions({
        search: search || undefined,
        category: categoryFilter || undefined,
        status: statusFilter || undefined,
      });
      setSessions(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search, categoryFilter, statusFilter]);

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      <PageHeader
        title="Test Management"
        breadcrumb={['NAWI', 'Tests']}
        subtitle="Create, manage, and review metrological test sessions"
        actions={
          <div className="flex gap-2">
            <button onClick={() => navigate('/tests/eccentricity')} className="btn-primary text-xs">
              <FlaskConical size={14} /> New Eccentricity
            </button>
            <button onClick={() => navigate('/tests/linearity')} className="btn-secondary text-xs">
              New Linearity
            </button>
            <button onClick={() => navigate('/tests/repeatability')} className="btn-secondary text-xs">
              New Repeatability
            </button>
          </div>
        }
      />

      <SectionCard
        title={`Test Sessions (${sessions.length})`}
        subtitle="All metrological test records"
        noPadding
        actions={
          <div className="flex items-center gap-2">
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="input-field !py-1.5 w-36 text-xs"
            >
              <option value="">All Categories</option>
              <option value="eccentricity">Eccentricity</option>
              <option value="linearity">Linearity</option>
              <option value="repeatability">Repeatability</option>
            </select>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="input-field !py-1.5 w-32 text-xs"
            >
              <option value="">All Status</option>
              <option value="Draft">Draft</option>
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="Incomplete">Incomplete</option>
            </select>
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input-field pl-8 !py-1.5 w-44 text-xs"
              />
            </div>
          </div>
        }
      >
        {loading ? (
          <LoadingOverlay />
        ) : sessions.length === 0 ? (
          <EmptyState
            title="No test sessions found"
            description="Start a new test session by selecting a test category above."
            action={
              <button onClick={() => navigate('/tests/eccentricity')} className="btn-primary text-xs">
                <PlusCircle size={14} /> Create Test Session
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr>
                  <th className="table-header">Session ID</th>
                  <th className="table-header">Instrument</th>
                  <th className="table-header">Category</th>
                  <th className="table-header">Test Date</th>
                  <th className="table-header">Operator</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Outcome</th>
                  <th className="table-header">Data</th>
                  <th className="table-header"></th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => (
                  <tr
                    key={s.id}
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/tests/${s.id}`)}
                  >
                    <td className="table-cell">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-xs text-slate-600">{s.id}</span>
                        {s.is_demo && <DemoBadge />}
                      </div>
                    </td>
                    <td className="table-cell">
                      <div>
                        <p className="text-xs font-medium text-slate-800">{s.instrument?.model ?? '—'}</p>
                        <p className="font-mono text-xs text-slate-400">{s.instrument?.serial_number ?? s.instrument_id}</p>
                      </div>
                    </td>
                    <td className="table-cell"><CategoryBadge category={s.test_category} /></td>
                    <td className="table-cell text-xs text-slate-600">
                      {new Date(s.test_date).toLocaleDateString('en-IN')}
                    </td>
                    <td className="table-cell text-xs text-slate-500 max-w-[120px] truncate">{s.operator_name}</td>
                    <td className="table-cell"><StatusBadge status={s.status} /></td>
                    <td className="table-cell"><OutcomeBadge outcome={s.overall_outcome} small /></td>
                    <td className="table-cell">
                      <div className="flex gap-1 text-xs">
                        <span className={`px-1.5 py-0.5 rounded ${s.has_observations ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-400'}`}>Obs</span>
                        <span className={`px-1.5 py-0.5 rounded ${s.has_calculations ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-400'}`}>Calc</span>
                        <span className={`px-1.5 py-0.5 rounded ${s.has_rule_evaluations ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-400'}`}>Rule</span>
                      </div>
                    </td>
                    <td className="table-cell">
                      <button className="btn-secondary py-1 text-xs" onClick={e => { e.stopPropagation(); navigate(`/tests/${s.id}`); }}>
                        Open <ChevronRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
};

export default TestManagement;

