import React, { useEffect, useState } from 'react';
import { PageHeader, SectionCard, LoadingOverlay } from '../components/ui';
import { listAuditLogs } from '../services/api';
import type { AuditLog } from '../types';

const ACTION_COLORS: Record<string, string> = {
  INSTRUMENT_REGISTERED: 'bg-blue-500',
  INSTRUMENT_UPDATED: 'bg-indigo-400',
  INSTRUMENT_ARCHIVED: 'bg-amber-500',
  TEST_SESSION_CREATED: 'bg-emerald-500',
  OBSERVATIONS_SAVED: 'bg-teal-500',
  CALCULATION_EXECUTED: 'bg-purple-500',
  RULES_EVALUATED: 'bg-violet-500',
  REPORT_GENERATED: 'bg-blue-700',
};

const AuditHistory: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');

  useEffect(() => {
    listAuditLogs({ limit: 100, action: actionFilter || undefined })
      .then(setLogs)
      .finally(() => setLoading(false));
  }, [actionFilter]);

  const uniqueActions = Array.from(new Set(logs.map(l => l.action)));

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <PageHeader
        title="Audit History"
        breadcrumb={['NAWI', 'Audit']}
        subtitle="Immutable record of all significant system actions and metrological events"
      />

      <SectionCard
        title={`Audit Events (${logs.length})`}
        noPadding
        actions={
          <select
            value={actionFilter}
            onChange={e => setActionFilter(e.target.value)}
            className="input-field !py-1 w-52 text-xs"
          >
            <option value="">All Actions</option>
            {uniqueActions.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        }
      >
        {loading ? <LoadingOverlay /> : (
          <div className="divide-y divide-slate-100">
            {logs.map(log => (
              <div key={log.id} className="flex items-start gap-4 px-5 py-3 hover:bg-slate-50 transition-colors">
                <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${ACTION_COLORS[log.action] ?? 'bg-slate-400'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-semibold text-slate-700 font-mono">{log.action}</span>
                    <span className="text-xs text-slate-400">·</span>
                    <span className="text-xs text-slate-500">By {log.actor}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    {log.test_session_id && (
                      <span className="font-mono">Session: {log.test_session_id}</span>
                    )}
                    {log.instrument_id && (
                      <span className="font-mono">Instrument: {log.instrument_id}</span>
                    )}
                  </div>
                  {log.details && Object.keys(log.details).length > 0 && (
                    <details className="mt-1">
                      <summary className="text-xs text-blue-500 cursor-pointer hover:underline">View details</summary>
                      <pre className="text-xs font-mono bg-slate-50 rounded p-2 mt-1 overflow-auto max-h-28 text-slate-600">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
                <span className="text-xs text-slate-400 flex-shrink-0">
                  {new Date(log.timestamp).toLocaleString('en-IN', { hour12: false })}
                </span>
              </div>
            ))}
            {logs.length === 0 && (
              <p className="text-sm text-slate-400 text-center py-8">No audit events found.</p>
            )}
          </div>
        )}
      </SectionCard>
    </div>
  );
};

export default AuditHistory;

