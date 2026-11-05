import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, PlusCircle, ChevronRight, Archive, Pencil, Eye } from 'lucide-react';
import {
  PageHeader, SectionCard, Badge, DemoBadge, LoadingOverlay,
  EmptyState, useToast, ConfirmDialog,
} from '../components/ui';
import { listInstruments, archiveInstrument } from '../services/api';
import type { Instrument } from '../types';

const Instruments: React.FC = () => {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [archiving, setArchiving] = useState<string | null>(null);
  const navigate = useNavigate();
  const { showToast } = useToast();

  const load = async () => {
    try {
      setLoading(true);
      const data = await listInstruments({ search: search || undefined, include_archived: showArchived });
      setInstruments(data);
    } catch {
      showToast('Failed to load instruments.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search, showArchived]);

  const handleArchive = async (id: string) => {
    try {
      await archiveInstrument(id);
      showToast('Instrument archived successfully.', 'success');
      load();
    } catch {
      showToast('Failed to archive instrument.', 'error');
    } finally {
      setArchiving(null);
    }
  };

  const accuracyClassColor = (cls: string) => {
    const map: Record<string, string> = {
      'Class I': 'bg-purple-50 text-purple-700 border-purple-200',
      'Class II': 'bg-blue-50 text-blue-700 border-blue-200',
      'Class III': 'bg-emerald-50 text-emerald-700 border-emerald-200',
      'Class IIII': 'bg-amber-50 text-amber-700 border-amber-200',
    };
    return map[cls] ?? 'bg-slate-50 text-slate-600 border-slate-200';
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      {archiving && (
        <ConfirmDialog
          title="Archive Instrument"
          message="Archive this instrument? It will no longer appear in active lists, but its test history is preserved."
          onConfirm={() => handleArchive(archiving)}
          onCancel={() => setArchiving(null)}
          confirmLabel="Archive"
          danger
        />
      )}

      <PageHeader
        title="Instruments"
        breadcrumb={['NAWI', 'Instruments']}
        actions={
          <button onClick={() => navigate('/instruments/register')} className="btn-primary">
            <PlusCircle size={15} /> Register Instrument
          </button>
        }
      />

      <SectionCard
        title={`Registered Instruments (${instruments.length})`}
        subtitle="All NAWI laboratory instruments and weighing devices"
        noPadding
        actions={
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={e => setShowArchived(e.target.checked)}
                className="rounded"
              />
              Show archived
            </label>
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="input-field pl-8 !py-1.5 w-52"
              />
            </div>
          </div>
        }
      >
        {loading ? (
          <LoadingOverlay message="Loading instruments…" />
        ) : instruments.length === 0 ? (
          <EmptyState
            title="No instruments registered"
            description="Register your first weighing instrument to begin metrological testing."
            action={
              <button onClick={() => navigate('/instruments/register')} className="btn-primary">
                <PlusCircle size={15} /> Register Instrument
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead>
                <tr>
                  <th className="table-header">Serial Number</th>
                  <th className="table-header">Model</th>
                  <th className="table-header">Type</th>
                  <th className="table-header">Class</th>
                  <th className="table-header">Max Capacity</th>
                  <th className="table-header">e</th>
                  <th className="table-header">Unit</th>
                  <th className="table-header">Location</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody>
                {instruments.map(inst => (
                  <tr key={inst.id} className="hover:bg-slate-50 transition-colors">
                    <td className="table-cell">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-xs font-semibold text-slate-700">{inst.serial_number}</span>
                        {inst.is_demo && <DemoBadge />}
                      </div>
                    </td>
                    <td className="table-cell">
                      <div>
                        <p className="font-medium text-slate-800">{inst.model}</p>
                        <p className="text-xs text-slate-400">{inst.manufacturer}</p>
                      </div>
                    </td>
                    <td className="table-cell text-xs text-slate-600">{inst.instrument_type}</td>
                    <td className="table-cell">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${accuracyClassColor(inst.accuracy_class)}`}>
                        {inst.accuracy_class}
                      </span>
                    </td>
                    <td className="table-cell font-mono text-xs">{inst.max_capacity}</td>
                    <td className="table-cell font-mono text-xs">{inst.verification_scale_interval}</td>
                    <td className="table-cell text-xs text-slate-500">{inst.unit}</td>
                    <td className="table-cell text-xs text-slate-500 max-w-[120px] truncate">{inst.location}</td>
                    <td className="table-cell">
                      {inst.is_archived ? (
                        <span className="badge-warn">Archived</span>
                      ) : (
                        <span className="badge-pass">Active</span>
                      )}
                    </td>
                    <td className="table-cell">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => navigate(`/instruments/${inst.id}`)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <Eye size={14} />
                        </button>
                        <button
                          onClick={() => navigate(`/instruments/${inst.id}/edit`)}
                          className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Edit"
                        >
                          <Pencil size={14} />
                        </button>
                        {!inst.is_archived && (
                          <button
                            onClick={() => setArchiving(inst.id)}
                            className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            title="Archive"
                          >
                            <Archive size={14} />
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
      </SectionCard>
    </div>
  );
};

export default Instruments;

