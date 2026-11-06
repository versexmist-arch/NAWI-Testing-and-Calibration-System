import React, { useEffect, useState, useMemo } from 'react';
import { Search, ShieldAlert, Filter, ArrowUpDown, Calendar } from 'lucide-react';
import { PageHeader, LoadingOverlay, EmptyState, Pagination, useToast } from '../components/ui';
import { listAuditLogs } from '../services/api';
import type { AuditLog } from '../types';

const ACTION_META: Record<string, { dot: string; label: string }> = {
  INSTRUMENT_REGISTERED:  { dot: 'bg-blue-500',   label: 'Instrument Registered' },
  INSTRUMENT_UPDATED:     { dot: 'bg-indigo-400',  label: 'Instrument Updated' },
  INSTRUMENT_ARCHIVED:    { dot: 'bg-amber-500',   label: 'Instrument Archived' },
  TEST_SESSION_CREATED:   { dot: 'bg-emerald-500', label: 'Test Session Created' },
  OBSERVATIONS_SAVED:     { dot: 'bg-teal-500',    label: 'Observations Saved' },
  CALCULATION_EXECUTED:   { dot: 'bg-purple-500',  label: 'Calculation Executed' },
  RULES_EVALUATED:        { dot: 'bg-violet-500',  label: 'OIML Rules Evaluated' },
  REPORT_GENERATED:       { dot: 'bg-blue-700',    label: 'Report Generated' },
  DEMO_DATA_RESET:        { dot: 'bg-rose-400',    label: 'Demo Data Reset' },
  DEMO_DATA_SEEDED:       { dot: 'bg-slate-400',   label: 'Demo Data Seeded' },
};

export const AuditHistory: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  const { showToast } = useToast();

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await listAuditLogs({ limit: 200, action: actionFilter || undefined });
      setLogs(data);
    } catch {
      showToast('Failed to load audit trail data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [actionFilter]);

  const uniqueActions = useMemo(() => Array.from(new Set(logs.map(l => l.action))).sort(), [logs]);

  const filteredLogs = useMemo(() => {
    if (!search) return logs;
    const q = search.toLowerCase();
    return logs.filter(l =>
      l.action.toLowerCase().includes(q) ||
      l.actor.toLowerCase().includes(q) ||
      (l.test_session_id && l.test_session_id.toLowerCase().includes(q)) ||
      (l.instrument_id && l.instrument_id.toLowerCase().includes(q))
    );
  }, [logs, search]);

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage) || 1;
  const paginatedLogs = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredLogs.slice(start, start + itemsPerPage);
  }, [filteredLogs, currentPage]);

  return (
    <div className="space-y-5 max-w-6xl mx-auto pb-10">
      <PageHeader
        title="Metrological Audit Trail"
        breadcrumb={['Laboratory', 'Audit Logs']}
        subtitle="Immutable chronological record of all significant system operations — instrument registration, test activities, calculations, evaluations, and certificate generation"
      />

      {/* Filter Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search action, actor, session ID, instrument…"
            value={search}
            onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
            className="input-field pl-9 !py-2 text-xs w-full"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter size={14} className="text-slate-400 flex-shrink-0" />
          <select
            value={actionFilter}
            onChange={e => { setActionFilter(e.target.value); setCurrentPage(1); }}
            className="input-field !py-2 text-xs w-full sm:w-56 bg-white"
          >
            <option value="">All Event Types</option>
            {uniqueActions.map(a => (
              <option key={a} value={a}>
                {ACTION_META[a]?.label || a}
              </option>
            ))}
          </select>

          <div className="text-xs text-slate-500 flex-shrink-0">
            <span className="font-bold text-slate-800">{filteredLogs.length}</span> events
          </div>
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingOverlay message="Loading ISO 17025 audit trail…" />
        ) : filteredLogs.length === 0 ? (
          <EmptyState
            title="No audit events found"
            description="Audit events are recorded automatically as instruments are registered, tests are run, and reports are generated."
          />
        ) : (
          <div className="divide-y divide-slate-100">
            {/* Table Header */}
            <div className="grid grid-cols-12 px-5 py-3 bg-slate-50/75 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200/80">
              <div className="col-span-1">Type</div>
              <div className="col-span-3">Event</div>
              <div className="col-span-2">Actor / Operator</div>
              <div className="col-span-2">Reference IDs</div>
              <div className="col-span-2">Details</div>
              <div className="col-span-2 text-right">Timestamp</div>
            </div>

            {paginatedLogs.map(log => {
              const meta = ACTION_META[log.action];
              return (
                <div
                  key={log.id}
                  className="grid grid-cols-12 px-5 py-3.5 hover:bg-blue-50/20 transition-colors items-start gap-2"
                >
                  {/* Dot indicator */}
                  <div className="col-span-1 flex items-center pt-1">
                    <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${meta?.dot ?? 'bg-slate-400'}`} />
                  </div>

                  {/* Event Name */}
                  <div className="col-span-3">
                    <p className="text-xs font-bold text-slate-800">
                      {meta?.label || log.action}
                    </p>
                    <p className="text-[10px] font-mono text-slate-400 mt-0.5">{log.action}</p>
                  </div>

                  {/* Actor */}
                  <div className="col-span-2 text-xs text-slate-600 font-medium">
                    {log.actor}
                  </div>

                  {/* Reference IDs */}
                  <div className="col-span-2 space-y-0.5">
                    {log.test_session_id && (
                      <p className="text-[10px] font-mono text-blue-600 truncate" title={log.test_session_id}>
                        SID: {log.test_session_id}
                      </p>
                    )}
                    {log.instrument_id && (
                      <p className="text-[10px] font-mono text-indigo-600 truncate" title={log.instrument_id}>
                        IID: {log.instrument_id}
                      </p>
                    )}
                    {!log.test_session_id && !log.instrument_id && (
                      <span className="text-[10px] text-slate-300">—</span>
                    )}
                  </div>

                  {/* Details collapsible */}
                  <div className="col-span-2">
                    {log.details && Object.keys(log.details).length > 0 ? (
                      <details>
                        <summary className="text-[10px] text-blue-500 cursor-pointer hover:underline font-semibold">
                          View details
                        </summary>
                        <pre className="text-[10px] font-mono bg-slate-50 rounded-lg p-2 mt-1 overflow-auto max-h-20 text-slate-600 border border-slate-200/80">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    ) : (
                      <span className="text-[10px] text-slate-300">No metadata</span>
                    )}
                  </div>

                  {/* Timestamp */}
                  <div className="col-span-2 text-right">
                    <div className="flex items-center justify-end gap-1 text-[10px] text-slate-400">
                      <Calendar size={11} />
                      <span>{new Date(log.timestamp).toLocaleDateString()}</span>
                    </div>
                    <p className="text-[10px] text-slate-400 font-mono text-right mt-0.5">
                      {new Date(log.timestamp).toLocaleTimeString('en-IN', { hour12: false })}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {filteredLogs.length > itemsPerPage && (
          <div className="border-t border-slate-100">
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

export default AuditHistory;
