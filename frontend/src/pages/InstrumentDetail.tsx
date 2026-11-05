import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FlaskConical, FileText, ChevronRight, ArrowLeft } from 'lucide-react';
import { PageHeader, SectionCard, StatusBadge, CategoryBadge, OutcomeBadge, DemoBadge, LoadingOverlay } from '../components/ui';
import { getInstrument } from '../services/api';

const InstrumentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<{ instrument: ReturnType<typeof Object>; test_sessions: unknown[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getInstrument(id).then(setData).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingOverlay message="Loading instrument…" />;
  if (!data) return <p className="text-slate-500 text-sm">Instrument not found.</p>;

  const inst = data.instrument as Record<string, unknown>;

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <PageHeader
        title={`${inst.model as string}`}
        breadcrumb={['NAWI', 'Instruments', inst.serial_number as string]}
        subtitle={`${inst.manufacturer as string} · ${inst.instrument_type as string}`}
        actions={
          <button onClick={() => navigate('/instruments')} className="btn-secondary">
            <ArrowLeft size={14} /> Back
          </button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <SectionCard title="Instrument Profile">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            {[
              ['Serial Number', inst.serial_number],
              ['Manufacturer', inst.manufacturer],
              ['Model', inst.model],
              ['Type', inst.instrument_type],
              ['Accuracy Class', inst.accuracy_class],
              ['Max Capacity', `${inst.max_capacity} ${inst.unit}`],
              ['Min Capacity', inst.min_capacity ? `${inst.min_capacity} ${inst.unit}` : '—'],
              ['Verification Interval (e)', `${inst.verification_scale_interval} ${inst.unit}`],
              ['Actual Interval (d)', inst.actual_scale_interval ? `${inst.actual_scale_interval} ${inst.unit}` : '—'],
              ['Scale Intervals (n)', inst.scale_intervals_count?.toLocaleString() ?? '—'],
              ['Location', inst.location],
              ['Registration Date', new Date(inst.registration_date as string).toLocaleDateString('en-IN')],
            ].map(([k, v]) => (
              <React.Fragment key={String(k)}>
                <dt className="text-slate-500 font-medium">{String(k)}</dt>
                <dd className="text-slate-800 font-semibold">{String(v ?? '—')}</dd>
              </React.Fragment>
            ))}
          </dl>
          {Boolean(inst.notes) && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <p className="text-xs text-slate-500 font-medium mb-1">Notes</p>
              <p className="text-sm text-slate-700">{String(inst.notes)}</p>
            </div>
          )}
        </SectionCard>

        <SectionCard title="Instrument Status">
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-600">Status</span>
              <span className={`font-semibold text-sm ${inst.is_archived ? 'text-amber-600' : 'text-emerald-600'}`}>
                {inst.is_archived ? 'Archived' : 'Active'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-600">Test Sessions</span>
              <span className="font-bold text-blue-600 text-lg">{(data.test_sessions as unknown[]).length}</span>
            </div>
            {(inst.is_demo as boolean) && (
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-sm text-slate-600">Data Origin</span>
                <DemoBadge />
              </div>
            )}
          </div>
          <div className="mt-4 flex flex-col gap-2">
            <button
              onClick={() => navigate('/tests/eccentricity', { state: { instrument_id: id } })}
              className="btn-primary w-full justify-center text-xs"
            >
              <FlaskConical size={14} /> New Eccentricity Test
            </button>
            <button
              onClick={() => navigate('/tests/linearity', { state: { instrument_id: id } })}
              className="btn-secondary w-full justify-center text-xs"
            >
              New Linearity Test
            </button>
            <button
              onClick={() => navigate('/tests/repeatability', { state: { instrument_id: id } })}
              className="btn-secondary w-full justify-center text-xs"
            >
              New Repeatability Test
            </button>
          </div>
        </SectionCard>
      </div>

      {/* Test History */}
      <SectionCard title="Test History" noPadding>
        {(data.test_sessions as unknown[]).length === 0 ? (
          <p className="text-sm text-slate-400 text-center py-8">No test sessions for this instrument.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-header">Session ID</th>
                <th className="table-header">Category</th>
                <th className="table-header">Test Date</th>
                <th className="table-header">Operator</th>
                <th className="table-header">Status</th>
                <th className="table-header">Outcome</th>
                <th className="table-header"></th>
              </tr>
            </thead>
            <tbody>
              {(data.test_sessions as Array<Record<string, unknown>>).map(t => (
                <tr key={String(t.id)} className="hover:bg-slate-50 transition-colors">
                  <td className="table-cell font-mono text-xs">{String(t.id)}</td>
                  <td className="table-cell"><CategoryBadge category={String(t.test_category)} /></td>
                  <td className="table-cell text-xs">{new Date(String(t.test_date)).toLocaleDateString('en-IN')}</td>
                  <td className="table-cell text-xs text-slate-500">{String(t.operator_name)}</td>
                  <td className="table-cell"><StatusBadge status={String(t.status)} /></td>
                  <td className="table-cell"><OutcomeBadge outcome={t.overall_outcome as string | undefined} /></td>
                  <td className="table-cell">
                    <button
                      onClick={() => navigate(`/tests/${t.id}`)}
                      className="btn-secondary py-1 text-xs"
                    >
                      View <ChevronRight size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </SectionCard>
    </div>
  );
};

export default InstrumentDetail;

