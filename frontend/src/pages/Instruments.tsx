import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, PlusCircle, Archive, Pencil, Eye,
  Scale, Filter, ArrowUpDown, ChevronDown, FlaskConical,
  RotateCcw, Sparkles, UserCheck, ShieldCheck
} from 'lucide-react';
import {
  PageHeader, SectionCard, DemoBadge, LoadingOverlay,
  EmptyState, useToast, ConfirmDialog, Pagination, Modal
} from '../components/ui';
import { listInstruments, archiveInstrument, updateInstrument } from '../services/api';
import type { Instrument } from '../types';

export const Instruments: React.FC = () => {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedClass, setSelectedClass] = useState<string>('ALL');
  const [selectedOrigin, setSelectedOrigin] = useState<'ALL' | 'USER' | 'DEMO'>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<'ALL' | 'ACTIVE' | 'ARCHIVED'>('ACTIVE');
  const [sortBy, setSortBy] = useState<'serial_number' | 'model' | 'max_capacity' | 'created_at'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Edit Modal State
  const [editingInst, setEditingInst] = useState<Instrument | null>(null);
  const [editFormData, setEditFormData] = useState<Partial<Instrument>>({});
  const [savingEdit, setSavingEdit] = useState(false);

  // Archive Confirmation
  const [archiving, setArchiving] = useState<string | null>(null);

  const navigate = useNavigate();
  const { showToast } = useToast();

  const load = async () => {
    try {
      setLoading(true);
      const data = await listInstruments({
        search: search || undefined,
        include_archived: true // fetch all so client filter can be responsive
      });
      setInstruments(data);
    } catch {
      showToast('Failed to load instrument registry.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

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

  const handleOpenEdit = (inst: Instrument) => {
    setEditingInst(inst);
    setEditFormData({
      model: inst.model,
      manufacturer: inst.manufacturer,
      instrument_type: inst.instrument_type,
      location: inst.location,
      notes: inst.notes,
    });
  };

  const handleSaveEdit = async () => {
    if (!editingInst) return;
    try {
      setSavingEdit(true);
      await updateInstrument(editingInst.id, editFormData);
      showToast('Instrument metadata updated successfully.', 'success');
      setEditingInst(null);
      load();
    } catch {
      showToast('Failed to update instrument.', 'error');
    } finally {
      setSavingEdit(false);
    }
  };

  // Filter and Sort Pipeline
  const filteredInstruments = useMemo(() => {
    return instruments.filter(inst => {
      // Search
      if (search) {
        const query = search.toLowerCase();
        const matchesSearch =
          inst.serial_number.toLowerCase().includes(query) ||
          inst.model.toLowerCase().includes(query) ||
          inst.manufacturer.toLowerCase().includes(query) ||
          (inst.location && inst.location.toLowerCase().includes(query));
        if (!matchesSearch) return false;
      }

      // Class
      if (selectedClass !== 'ALL' && inst.accuracy_class !== selectedClass) {
        return false;
      }

      // Origin
      if (selectedOrigin === 'USER' && inst.is_demo) return false;
      if (selectedOrigin === 'DEMO' && !inst.is_demo) return false;

      // Status
      if (selectedStatus === 'ACTIVE' && inst.is_archived) return false;
      if (selectedStatus === 'ARCHIVED' && !inst.is_archived) return false;

      return true;
    }).sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'serial_number') {
        comparison = a.serial_number.localeCompare(b.serial_number);
      } else if (sortBy === 'model') {
        comparison = a.model.localeCompare(b.model);
      } else if (sortBy === 'max_capacity') {
        comparison = a.max_capacity - b.max_capacity;
      } else if (sortBy === 'created_at') {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [instruments, search, selectedClass, selectedOrigin, selectedStatus, sortBy, sortOrder]);

  // Pagination calculation
  const totalPages = Math.ceil(filteredInstruments.length / itemsPerPage) || 1;
  const paginatedInstruments = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredInstruments.slice(start, start + itemsPerPage);
  }, [filteredInstruments, currentPage]);

  const accuracyClassBadge = (cls: string) => {
    const map: Record<string, string> = {
      'Class I': 'bg-purple-50 text-purple-700 border-purple-200/80',
      'Class II': 'bg-blue-50 text-blue-700 border-blue-200/80',
      'Class III': 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
      'Class IIII': 'bg-amber-50 text-amber-700 border-amber-200/80',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold border ${map[cls] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
        {cls}
      </span>
    );
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-10">
      {archiving && (
        <ConfirmDialog
          title="Archive Instrument"
          message="Archive this instrument? It will no longer appear in active testing menus, but its complete historical test logs and calibration records remain securely preserved."
          onConfirm={() => handleArchive(archiving)}
          onCancel={() => setArchiving(null)}
          confirmLabel="Archive Instrument"
          danger
        />
      )}

      {/* Page Header */}
      <PageHeader
        title="Weighing Instrument Registry"
        subtitle="Non-Automatic Weighing Instruments (NAWI) Registered for OIML R-76 Metrological Control"
        breadcrumb={['Laboratory', 'Instruments']}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/instruments/register')}
              className="btn-primary text-xs"
            >
              <PlusCircle size={15} /> Register Instrument
            </button>
          </div>
        }
      />

      {/* Filter and Control Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search box */}
          <div className="relative lg:col-span-2">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search serial number, model, manufacturer, location…"
              value={search}
              onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
              className="input-field pl-9 !py-2 text-xs w-full"
            />
          </div>

          {/* Accuracy Class Filter */}
          <div>
            <select
              value={selectedClass}
              onChange={e => { setSelectedClass(e.target.value); setCurrentPage(1); }}
              className="input-field !py-2 text-xs w-full bg-white"
            >
              <option value="ALL">All Accuracy Classes</option>
              <option value="Class I">Class I (Special)</option>
              <option value="Class II">Class II (High)</option>
              <option value="Class III">Class III (Medium)</option>
              <option value="Class IIII">Class IIII (Ordinary)</option>
            </select>
          </div>

          {/* Origin Filter */}
          <div>
            <select
              value={selectedOrigin}
              onChange={e => { setSelectedOrigin(e.target.value as any); setCurrentPage(1); }}
              className="input-field !py-2 text-xs w-full bg-white"
            >
              <option value="ALL">All Data Origins</option>
              <option value="USER">Authentic User Records</option>
              <option value="DEMO">Demo Baseline Reference</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={selectedStatus}
              onChange={e => { setSelectedStatus(e.target.value as any); setCurrentPage(1); }}
              className="input-field !py-2 text-xs w-full bg-white"
            >
              <option value="ACTIVE">Status: Active Only</option>
              <option value="ARCHIVED">Status: Archived Only</option>
              <option value="ALL">Status: All (Active & Archived)</option>
            </select>
          </div>
        </div>

        {/* Sorting and Summary Strip */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>Sort by:</span>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className="border border-slate-200 rounded-lg px-2 py-1 text-xs bg-slate-50 text-slate-700 font-medium"
            >
              <option value="created_at">Registration Date</option>
              <option value="serial_number">Serial Number</option>
              <option value="model">Model Name</option>
              <option value="max_capacity">Maximum Capacity</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="flex items-center gap-1 border border-slate-200 rounded-lg px-2 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium"
              title="Toggle sort direction"
            >
              <ArrowUpDown size={12} />
              {sortOrder.toUpperCase()}
            </button>
          </div>

          <div>
            Showing <span className="font-bold text-slate-800">{filteredInstruments.length}</span> of {instruments.length} registered instruments
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingOverlay message="Querying laboratory instrument database…" />
        ) : filteredInstruments.length === 0 ? (
          <EmptyState
            title="No matching instruments found"
            description="Adjust your search query or filters to find registered instruments."
            action={
              <button
                onClick={() => { setSearch(''); setSelectedClass('ALL'); setSelectedOrigin('ALL'); setSelectedStatus('ALL'); }}
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
                  <th className="table-header">Serial Number</th>
                  <th className="table-header">Model & Manufacturer</th>
                  <th className="table-header">Origin</th>
                  <th className="table-header">Class</th>
                  <th className="table-header">Capacity (Max)</th>
                  <th className="table-header">Interval (e / d)</th>
                  <th className="table-header">Location</th>
                  <th className="table-header">Status</th>
                  <th className="table-header text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedInstruments.map(inst => (
                  <tr key={inst.id} className="hover:bg-blue-50/30 transition-colors">
                    {/* Serial */}
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                          <Scale size={16} />
                        </div>
                        <div>
                          <span className="font-mono text-xs font-bold text-slate-800 block">
                            {inst.serial_number}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ID: {inst.id.slice(0, 10)}...
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Model */}
                    <td className="table-cell">
                      <div>
                        <p className="font-semibold text-xs text-slate-900">{inst.model}</p>
                        <p className="text-[11px] text-slate-500">{inst.manufacturer} &middot; {inst.instrument_type}</p>
                      </div>
                    </td>

                    {/* Origin */}
                    <td className="table-cell">
                      {inst.is_demo ? (
                        <DemoBadge />
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <UserCheck size={10} /> User Record
                        </span>
                      )}
                    </td>

                    {/* Class */}
                    <td className="table-cell">
                      {accuracyClassBadge(inst.accuracy_class)}
                    </td>

                    {/* Capacity */}
                    <td className="table-cell">
                      <span className="font-mono text-xs font-semibold text-slate-800">
                        {inst.max_capacity} {inst.unit}
                      </span>
                      {inst.min_capacity !== undefined && (
                        <span className="block text-[10px] text-slate-400 font-mono">
                          Min: {inst.min_capacity} {inst.unit}
                        </span>
                      )}
                    </td>

                    {/* Intervals */}
                    <td className="table-cell">
                      <span className="font-mono text-xs text-slate-700 block">
                        e = {inst.verification_scale_interval} {inst.unit}
                      </span>
                      {inst.actual_scale_interval && (
                        <span className="text-[10px] font-mono text-slate-400 block">
                          d = {inst.actual_scale_interval} {inst.unit}
                        </span>
                      )}
                    </td>

                    {/* Location */}
                    <td className="table-cell text-xs text-slate-600 max-w-[140px] truncate">
                      {inst.location || <span className="text-slate-300 italic">Not set</span>}
                    </td>

                    {/* Status */}
                    <td className="table-cell">
                      {inst.is_archived ? (
                        <span className="badge-warn text-[10px]">Archived</span>
                      ) : (
                        <span className="badge-pass text-[10px]">Active</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="table-cell text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => navigate(`/instruments/${inst.id}`)}
                          className="p-1.5 text-blue-600 hover:bg-blue-100/70 rounded-lg transition-colors"
                          title="View Details and Test History"
                        >
                          <Eye size={15} />
                        </button>
                        <button
                          onClick={() => handleOpenEdit(inst)}
                          className="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Quick Edit"
                        >
                          <Pencil size={15} />
                        </button>
                        {!inst.is_archived && (
                          <button
                            onClick={() => setArchiving(inst.id)}
                            className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                            title="Archive Instrument"
                          >
                            <Archive size={15} />
                          </button>
                        )}
                        <button
                          onClick={() => navigate(`/tests/eccentricity?instrument_id=${inst.id}`)}
                          className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          title="Start Calibration Test"
                        >
                          <FlaskConical size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {filteredInstruments.length > itemsPerPage && (
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

      {/* Edit Instrument Modal */}
      {editingInst && (
        <Modal
          title={`Edit Instrument — ${editingInst.serial_number}`}
          onClose={() => setEditingInst(null)}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Model Name</label>
                <input
                  type="text"
                  value={editFormData.model || ''}
                  onChange={e => setEditFormData({ ...editFormData, model: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Manufacturer</label>
                <input
                  type="text"
                  value={editFormData.manufacturer || ''}
                  onChange={e => setEditFormData({ ...editFormData, manufacturer: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Instrument Type</label>
              <input
                type="text"
                value={editFormData.instrument_type || ''}
                onChange={e => setEditFormData({ ...editFormData, instrument_type: e.target.value })}
                className="input-field text-xs w-full"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Physical Location</label>
              <input
                type="text"
                value={editFormData.location || ''}
                onChange={e => setEditFormData({ ...editFormData, location: e.target.value })}
                className="input-field text-xs w-full"
                placeholder="e.g. Cleanroom B, Bench 4"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Laboratory Notes</label>
              <textarea
                value={editFormData.notes || ''}
                onChange={e => setEditFormData({ ...editFormData, notes: e.target.value })}
                rows={3}
                className="input-field text-xs w-full resize-none"
                placeholder="Optional metrological maintenance notes"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingInst(null)}
                className="btn-secondary text-xs"
                disabled={savingEdit}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                className="btn-primary text-xs"
                disabled={savingEdit}
              >
                {savingEdit ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default Instruments;
