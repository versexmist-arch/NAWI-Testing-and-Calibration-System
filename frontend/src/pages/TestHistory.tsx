import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Filter, FlaskConical, Calendar,
  Eye, FileText, ChevronRight, Download, CheckCircle2,
  XCircle, Clock, AlertTriangle, ArrowUpDown
} from 'lucide-react';
import {
  PageHeader, OutcomeBadge, CategoryBadge,
  DemoBadge, StatusBadge, LoadingOverlay, EmptyState,
  Pagination, useToast
} from '../components/ui';
import { listTestSessions } from '../services/api';
import type { TestSession } from '../types';

export const TestHistory: React.FC = () => {
  const [sessions, setSessions] = useState<TestSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedOutcome, setSelectedOutcome] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedOrigin, setSelectedOrigin] = useState<'ALL' | 'USER' | 'DEMO'>('ALL');
  const [sortBy, setSortBy] = useState<'test_date' | 'created_at' | 'serial' | 'outcome'>('test_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const navigate = useNavigate();
  const { showToast } = useToast();

  const loadSessions = async () => {
    try {
      setLoading(true);
      const data = await listTestSessions();
      setSessions(data);
    } catch {
      showToast('Failed to load test history from database.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const filteredSessions = useMemo(() => {
    return sessions.filter(s => {
      // Search
      if (search) {
        const q = search.toLowerCase();
        const matches =
          s.id.toLowerCase().includes(q) ||
          s.operator_name.toLowerCase().includes(q) ||
          (s.instrument?.serial_number && s.instrument.serial_number.toLowerCase().includes(q)) ||
          (s.instrument?.model && s.instrument.model.toLowerCase().includes(q));
        if (!matches) return false;
      }

      // Category
      if (selectedCategory !== 'ALL' && s.test_category !== selectedCategory) return false;

      // Outcome
      if (selectedOutcome !== 'ALL') {
        if (selectedOutcome === 'NONE' && s.overall_outcome) return false;
        if (selectedOutcome !== 'NONE' && s.overall_outcome !== selectedOutcome) return false;
      }

      // Status
      if (selectedStatus !== 'ALL' && s.status !== selectedStatus) return false;

      // Origin
      if (selectedOrigin === 'USER' && s.is_demo) return false;
      if (selectedOrigin === 'DEMO' && !s.is_demo) return false;

      return true;
    }).sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'test_date') {
        comparison = new Date(a.test_date).getTime() - new Date(b.test_date).getTime();
      } else if (sortBy === 'created_at') {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortBy === 'serial') {
        const sA = a.instrument?.serial_number || '';
        const sB = b.instrument?.serial_number || '';
        comparison = sA.localeCompare(sB);
      } else if (sortBy === 'outcome') {
        const oA = a.overall_outcome || '';
        const oB = b.overall_outcome || '';
        comparison = oA.localeCompare(oB);
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [sessions, search, selectedCategory, selectedOutcome, selectedStatus, selectedOrigin, sortBy, sortOrder]);

  const totalPages = Math.ceil(filteredSessions.length / itemsPerPage) || 1;
  const paginatedSessions = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredSessions.slice(start, start + itemsPerPage);
  }, [filteredSessions, currentPage]);

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-10">
      <PageHeader
        title="Historical Test Sessions"
        subtitle="Complete archive of Non-Automatic Weighing Instruments calibration procedures, measurements, and evaluations"
        breadcrumb={['Laboratory', 'Test History']}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/tests/eccentricity')}
              className="btn-primary text-xs"
            >
              <FlaskConical size={14} /> New Test Session
            </button>
          </div>
        }
      />

      {/* Filter and Query Strip */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative lg:col-span-2">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search session ID, serial number, model, operator…"
              value={search}
              onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
              className="input-field pl-9 !py-2 text-xs w-full"
            />
          </div>

          {/* Category */}
          <div>
            <select
              value={selectedCategory}
              onChange={e => { setSelectedCategory(e.target.value); setCurrentPage(1); }}
              className="input-field !py-2 text-xs w-full bg-white"
            >
              <option value="ALL">All Test Modules</option>
              <option value="eccentricity">Eccentricity (Corner Load)</option>
              <option value="linearity">Linearity (Increasing/Decreasing)</option>
              <option value="repeatability">Repeatability (Series)</option>
            </select>
          </div>

          {/* Outcome */}
          <div>
            <select
              value={selectedOutcome}
              onChange={e => { setSelectedOutcome(e.target.value); setCurrentPage(1); }}
              className="input-field !py-2 text-xs w-full bg-white"
            >
              <option value="ALL">All Evaluation Outcomes</option>
              <option value="PASS">PASS (Compliant)</option>
              <option value="FAIL">FAIL (Tolerance Exceeded)</option>
              <option value="PENDING_VERIFICATION">Pending Verification</option>
              <option value="INCOMPLETE">Incomplete Observation</option>
              <option value="NONE">Not Yet Evaluated</option>
            </select>
          </div>

          {/* Origin */}
          <div>
            <select
              value={selectedOrigin}
              onChange={e => { setSelectedOrigin(e.target.value as any); setCurrentPage(1); }}
              className="input-field !py-2 text-xs w-full bg-white"
            >
              <option value="ALL">All Data Origins</option>
              <option value="USER">User Sessions Only</option>
              <option value="DEMO">Demo Baseline Sessions</option>
            </select>
          </div>
        </div>

        {/* Sorting and Metadata */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>Sort by:</span>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className="border border-slate-200 rounded-lg px-2 py-1 text-xs bg-slate-50 text-slate-700 font-medium"
            >
              <option value="test_date">Test Execution Date</option>
              <option value="created_at">Record Creation Date</option>
              <option value="serial">Instrument Serial</option>
              <option value="outcome">Outcome Status</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="flex items-center gap-1 border border-slate-200 rounded-lg px-2 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium"
            >
              <ArrowUpDown size={12} />
              {sortOrder.toUpperCase()}
            </button>
          </div>

          <div>
            Showing <span className="font-bold text-slate-800">{filteredSessions.length}</span> of {sessions.length} sessions recorded
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingOverlay message="Querying metrological test database…" />
        ) : filteredSessions.length === 0 ? (
          <EmptyState
            title="No matching test records found"
            description="Adjust your search filters or start a new metrological calibration session."
            action={
              <button
                onClick={() => { setSearch(''); setSelectedCategory('ALL'); setSelectedOutcome('ALL'); setSelectedOrigin('ALL'); }}
                className="btn-secondary text-xs"
              >
                Reset All Filters
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[950px]">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200/80">
                  <th className="table-header">Session ID</th>
                  <th className="table-header">Instrument</th>
                  <th className="table-header">Category</th>
                  <th className="table-header">Test Date</th>
                  <th className="table-header">Operator</th>
                  <th className="table-header">Stage Status</th>
                  <th className="table-header">OIML Outcome</th>
                  <th className="table-header text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedSessions.map(session => (
                  <tr
                    key={session.id}
                    className="hover:bg-blue-50/30 transition-colors"
                  >
                    {/* Session ID */}
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-800">
                          {session.id}
                        </span>
                        {session.is_demo && <DemoBadge />}
                      </div>
                    </td>

                    {/* Instrument */}
                    <td className="table-cell">
                      <div>
                        <p className="font-semibold text-xs text-slate-900">
                          {session.instrument?.model || 'Unknown Model'}
                        </p>
                        <p className="text-[11px] text-slate-500 font-mono">
                          SN: {session.instrument?.serial_number || 'N/A'} &middot; {session.instrument?.accuracy_class || ''}
                        </p>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="table-cell">
                      <CategoryBadge category={session.test_category} />
                    </td>

                    {/* Test Date */}
                    <td className="table-cell text-xs text-slate-600">
                      <div className="flex items-center gap-1.5">
                        <Calendar size={13} className="text-slate-400" />
                        <span>{new Date(session.test_date).toLocaleDateString()}</span>
                      </div>
                    </td>

                    {/* Operator */}
                    <td className="table-cell text-xs text-slate-700">
                      <span className="font-medium">{session.operator_name}</span>
                      {session.laboratory_location && (
                        <span className="block text-[10px] text-slate-400">{session.laboratory_location}</span>
                      )}
                    </td>

                    {/* Stage Status */}
                    <td className="table-cell">
                      <StatusBadge status={session.status} />
                    </td>

                    {/* Outcome */}
                    <td className="table-cell">
                      <OutcomeBadge outcome={session.overall_outcome} />
                    </td>

                    {/* Actions */}
                    <td className="table-cell text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => navigate(`/tests/${session.id}`)}
                          className="px-2.5 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors flex items-center gap-1"
                          title="Open Session Details & Data"
                        >
                          <Eye size={13} />
                          <span>View</span>
                        </button>
                        {session.has_calculations && (
                          <button
                            onClick={() => navigate(`/reports`)}
                            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                            title="Reports"
                          >
                            <FileText size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {filteredSessions.length > itemsPerPage && (
          <div className="p-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Page {currentPage} of {totalPages}
            </span>
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={page => setCurrentPage(page)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default TestHistory;

