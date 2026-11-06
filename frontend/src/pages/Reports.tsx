import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, FileText, ExternalLink, Search, Calendar, ShieldCheck } from 'lucide-react';
import { PageHeader, SectionCard, LoadingOverlay, EmptyState, DemoBadge, Pagination, useToast } from '../components/ui';
import { listReports } from '../services/api';
import type { GeneratedReport } from '../types';

export const Reports: React.FC = () => {
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  const navigate = useNavigate();
  const { showToast } = useToast();

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await listReports();
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
  }, [reports, search]);

  const totalPages = Math.ceil(filteredReports.length / itemsPerPage) || 1;
  const paginatedReports = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredReports.slice(start, start + itemsPerPage);
  }, [filteredReports, currentPage]);

  return (
    <div className="max-w-6xl mx-auto space-y-5 pb-10">
      <PageHeader
        title="Calibration Certificates & Metrology Reports"
        breadcrumb={['Laboratory', 'Reports']}
        subtitle="ISO/IEC 17025 accredited metrological test certificates generated via ReportLab"
        actions={
          <button onClick={() => navigate('/tests')} className="btn-primary text-xs">
            <FileText size={14} /> Go to Test Sessions
          </button>
        }
      />

      {/* Search and Filter Strip */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search report ID, certificate file, serial number…"
            value={search}
            onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
            className="input-field pl-9 !py-2 text-xs w-full"
          />
        </div>

        <div className="text-xs text-slate-500">
          Showing <span className="font-bold text-slate-800">{filteredReports.length}</span> of {reports.length} generated certificates
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingOverlay message="Querying certificate archives…" />
        ) : filteredReports.length === 0 ? (
          <EmptyState
            title="No reports found"
            description="Complete a test session and generate a formal PDF certificate to view it here."
            action={
              <button onClick={() => navigate('/tests')} className="btn-primary text-xs">
                <FileText size={14} /> Go to Tests
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px]">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200/80">
                  <th className="table-header">Certificate ID</th>
                  <th className="table-header">Instrument Model & Serial</th>
                  <th className="table-header">Test Session Reference</th>
                  <th className="table-header">Verification Officer</th>
                  <th className="table-header">Issue Date</th>
                  <th className="table-header text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedReports.map(r => (
                  <tr key={r.id} className="hover:bg-blue-50/30 transition-colors">
                    {/* Certificate ID */}
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-red-50 text-red-600 flex items-center justify-center flex-shrink-0">
                          <FileText size={16} />
                        </div>
                        <div>
                          <span className="font-mono text-xs font-bold text-slate-800 block">
                            {r.file_name}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            ID: {r.id}
                          </span>
                        </div>
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
                          href={`/api/reports/${r.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-primary py-1 px-3 text-xs flex items-center gap-1.5"
                        >
                          <Download size={13} />
                          <span>PDF</span>
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {filteredReports.length > itemsPerPage && (
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

export default Reports;
