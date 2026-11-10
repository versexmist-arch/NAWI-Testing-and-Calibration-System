import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, FileText, ExternalLink, Search, Calendar, ShieldCheck, History, CheckCircle2, AlertTriangle } from 'lucide-react';
import { PageHeader, SectionCard, LoadingOverlay, EmptyState, DemoBadge, Pagination, useToast } from '../components/ui';
import { listReports, getReportDownloadUrl } from '../services/api';
import type { GeneratedReport } from '../types';

export const Reports: React.FC = () => {
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'superseded'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  const navigate = useNavigate();
  const { showToast } = useToast();

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await listReports({ include_superseded: true });
      setReports(data);
    } catch {
      showToast('Failed to load calibration report archives.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const filteredReports = useMemo(() => {
    return reports.filter(r => {
      // Status filter
      if (statusFilter === 'active' && r.is_superseded) return false;
      if (statusFilter === 'superseded' && !r.is_superseded) return false;

      // Text search
      if (!search) return true;
      const q = search.toLowerCase();
      return (
        r.id.toLowerCase().includes(q) ||
        r.file_name.toLowerCase().includes(q) ||
        r.generated_by.toLowerCase().includes(q) ||
        r.test_session_id.toLowerCase().includes(q) ||
        (r.instrument?.serial_number && r.instrument.serial_number.toLowerCase().includes(q)) ||
        (r.instrument?.model && r.instrument.model.toLowerCase().includes(q))
      );
    });
  }, [reports, search, statusFilter]);

  const totalPages = Math.ceil(filteredReports.length / itemsPerPage) || 1;
  const paginatedReports = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredReports.slice(start, start + itemsPerPage);
  }, [filteredReports, currentPage]);

  const activeCount = reports.filter(r => !r.is_superseded).length;
  const supersededCount = reports.filter(r => r.is_superseded).length;

  return (
    <div className="max-w-6xl mx-auto space-y-5 pb-10">
      <PageHeader
        title="Calibration Certificates & Metrology Reports"
        breadcrumb={['Laboratory', 'Reports']}
        subtitle="ISO/IEC 17025 accredited metrological test certificates with complete revision and superseding traceability"
        actions={
          <button onClick={() => navigate('/tests')} className="btn-primary text-xs">
            <FileText size={14} /> Go to Test Sessions
          </button>
        }
      />

      {/* Search and Filter Strip */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative w-full md:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search report ID, certificate file, serial number…"
            value={search}
            onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
            className="input-field pl-9 !py-2 text-xs w-full"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => { setStatusFilter('all'); setCurrentPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              statusFilter === 'all'
                ? 'bg-blue-50 text-blue-700 border border-blue-200'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            All Certificates
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-700">
              {reports.length}
            </span>
          </button>

          <button
            onClick={() => { setStatusFilter('active'); setCurrentPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              statusFilter === 'active'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <CheckCircle2 size={12} className="text-emerald-600" />
            Active Only
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800">
              {activeCount}
            </span>
          </button>

          <button
            onClick={() => { setStatusFilter('superseded'); setCurrentPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
              statusFilter === 'superseded'
                ? 'bg-amber-50 text-amber-800 border border-amber-200'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <History size={12} className="text-amber-600" />
            Superseded Archives
            <span className="font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-800">
              {supersededCount}
            </span>
          </button>
        </div>

        <div className="text-xs text-slate-500 whitespace-nowrap">
          Showing <span className="font-bold text-slate-800">{filteredReports.length}</span> certificates
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingOverlay message="Querying certificate archives…" />
        ) : filteredReports.length === 0 ? (
          <EmptyState
            title="No reports match your filters"
            description="Complete a test session and generate a formal PDF certificate, or adjust your filter selection."
            action={
              <button onClick={() => navigate('/tests')} className="btn-primary text-xs">
                <FileText size={14} /> Go to Tests
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200/80">
                  <th className="table-header">Certificate & Revision</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Instrument Model & Serial</th>
                  <th className="table-header">Test Session Reference</th>
                  <th className="table-header">Verification Officer</th>
                  <th className="table-header">Issue Date</th>
                  <th className="table-header text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedReports.map(r => {
                  const isSuperseded = Boolean(r.is_superseded);
                  return (
                    <tr
                      key={r.id}
                      className={`hover:bg-blue-50/30 transition-colors ${
                        isSuperseded ? 'bg-slate-50/40 text-slate-500' : ''
                      }`}
                    >
                      {/* Certificate ID & Version */}
                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                              isSuperseded ? 'bg-slate-100 text-slate-500' : 'bg-red-50 text-red-600'
                            }`}
                          >
                            <FileText size={16} />
                          </div>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono text-xs font-bold text-slate-800 block">
                                {r.file_name}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">
                              ID: {r.id}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Status & Version Badge */}
                      <td className="table-cell">
                        <div className="flex flex-col items-start gap-1">
                          <span
                            className={`px-2 py-0.5 rounded-full font-mono font-bold text-[10px] border ${
                              isSuperseded
                                ? 'bg-amber-50 text-amber-800 border-amber-200'
                                : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            }`}
                          >
                            Rev {r.version || 1} · {isSuperseded ? 'SUPERSEDED' : 'ACTIVE'}
                          </span>
                          {isSuperseded && r.superseded_by && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              by {r.superseded_by}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Instrument */}
                      <td className="table-cell">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <p className="font-semibold text-xs text-slate-900">
                              {r.instrument?.model || 'NAWI Standard'}
                            </p>
                            {r.instrument?.is_demo && <DemoBadge />}
                          </div>
                          <p className="text-[11px] text-slate-500 font-mono">
                            SN: {r.instrument?.serial_number ?? r.instrument_id}
                          </p>
                        </div>
                      </td>

                      {/* Test Session */}
                      <td className="table-cell">
                        <button
                          onClick={() => navigate(`/tests/${r.test_session_id}`)}
                          className="font-mono text-xs text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1"
                        >
                          {r.test_session_id}
                          <ExternalLink size={11} />
                        </button>
                      </td>

                      {/* Generated By */}
                      <td className="table-cell text-xs text-slate-700">
                        <span className="font-medium">{r.generated_by}</span>
                      </td>

                      {/* Issue Date */}
                      <td className="table-cell text-xs text-slate-600">
                        <div className="flex items-center gap-1.5">
                          <Calendar size={13} className="text-slate-400" />
                          <span>{new Date(r.created_at).toLocaleDateString()}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="table-cell text-right">
                        <div className="flex items-center justify-end gap-2">
                          <a
                            href={getReportDownloadUrl(r.id)}
                            target="_blank"
                            rel="noreferrer"
                            className={`py-1 px-3 text-xs flex items-center gap-1.5 rounded-lg font-semibold transition-colors ${
                              isSuperseded
                                ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300'
                                : 'btn-primary'
                            }`}
                            title={isSuperseded ? 'Download archived superseded report' : 'Download current certificate'}
                          >
                            <Download size={13} />
                            <span>PDF</span>
                          </a>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          totalItems={filteredReports.length}
          pageSize={itemsPerPage}
        />
      </div>
    </div>
  );
};

export default Reports;
