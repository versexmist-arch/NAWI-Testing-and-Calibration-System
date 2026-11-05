import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Plus, Trash2, Save, Calculator, FileText, AlertCircle, ChevronRight, ArrowLeft } from 'lucide-react';
import {
  PageHeader, SectionCard, Alert, OutcomeBadge, StatusBadge,
  CategoryBadge, useToast, Spinner, LoadingOverlay,
} from '../components/ui';
import {
  listInstruments, createTestSession, saveObservations,
  runCalculations, generateReport, getTestSession,
} from '../services/api';
import type { Instrument, CalculationResult, RuleEvaluationSummary } from '../types';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, ScatterChart, Scatter, Legend,
} from 'recharts';

// ─── ECCENTRICITY TEST ────────────────────────────────────────────────────────

const DEFAULT_ECCENTRICITY_POSITIONS = [
  { position_id: 'pos_1', position_name: 'Center (1)', indication: '', zero_indication: '0' },
  { position_id: 'pos_2', position_name: 'Front-Left (2)', indication: '', zero_indication: '0' },
  { position_id: 'pos_3', position_name: 'Back-Left (3)', indication: '', zero_indication: '0' },
  { position_id: 'pos_4', position_name: 'Back-Right (4)', indication: '', zero_indication: '0' },
  { position_id: 'pos_5', position_name: 'Front-Right (5)', indication: '', zero_indication: '0' },
];

export const EccentricityTest: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selectedInst, setSelectedInst] = useState<string>(
    (location.state as { instrument_id?: string })?.instrument_id ?? ''
  );
  const [testLoad, setTestLoad] = useState('');
  const [operatorName, setOperatorName] = useState('Lead Metrologist');
  const [ambientTemp, setAmbientTemp] = useState('20.0');
  const [humidity, setHumidity] = useState('50');
  const [positions, setPositions] = useState(DEFAULT_ECCENTRICITY_POSITIONS.map(p => ({ ...p })));
  const [loading, setLoading] = useState(false);
  const [calcResult, setCalcResult] = useState<CalculationResult | null>(null);
  const [ruleResult, setRuleResult] = useState<RuleEvaluationSummary | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);

  useEffect(() => {
    listInstruments().then(setInstruments).catch(() => showToast('Could not load instruments.', 'error'));
  }, []);

  const instrument = instruments.find(i => i.id === selectedInst);

  const setPosition = (idx: number, field: string, value: string) => {
    setPositions(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p));
  };

  const addPosition = () => {
    const n = positions.length + 1;
    setPositions(prev => [...prev, { position_id: `pos_${n}`, position_name: `Position ${n}`, indication: '', zero_indication: '0' }]);
  };

  const removePosition = (idx: number) => {
    if (positions.length <= 2) { showToast('At least 2 positions required (Center + 1 eccentric).', 'info'); return; }
    setPositions(prev => prev.filter((_, i) => i !== idx));
  };

  const handleCalculate = async () => {
    if (!selectedInst) { showToast('Select an instrument first.', 'error'); return; }
    if (!testLoad || isNaN(Number(testLoad)) || Number(testLoad) <= 0) {
      showToast('Enter a valid test load.', 'error'); return;
    }
    for (const p of positions) {
      if (!p.indication || isNaN(Number(p.indication))) {
        showToast(`Enter a valid indication for position "${p.position_name}".`, 'error'); return;
      }
    }

    try {
      setLoading(true);
      // 1. Create session
      const session = await createTestSession({
        instrument_id: selectedInst,
        test_category: 'eccentricity',
        operator_name: operatorName,
        ambient_temperature: Number(ambientTemp),
        relative_humidity: Number(humidity),
        service_type: 'initial',
        test_configuration: { test_load: Number(testLoad) },
      });
      setSessionId(session.id);

      // 2. Save observations
      const obs = positions.map(p => ({
        position_id: p.position_id,
        position_name: p.position_name,
        indication: Number(p.indication),
        zero_indication: Number(p.zero_indication || 0),
      }));
      await saveObservations(session.id, obs, { test_load: Number(testLoad) });

      // 3. Run calculations
      const { calculation_result, rule_evaluation } = await runCalculations(session.id);
      setCalcResult(calculation_result);
      setRuleResult(rule_evaluation);
      showToast('Calculation complete.', 'success');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast(msg || 'Calculation failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const rep = await generateReport(sessionId);
      setReportId(rep.report_id);
      showToast('PDF report generated.', 'success');
    } catch {
      showToast('Report generation failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const chartData = calcResult?.position_results?.map(p => ({
    name: p.position_name.split('(')[0].trim(),
    deviation: Number(p.eccentricity_deviation?.toFixed(4) ?? 0),
    error: Number(p.indication_error?.toFixed(4) ?? 0),
  })) ?? [];

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <PageHeader
        title="Eccentricity Test"
        breadcrumb={['NAWI', 'Tests', 'Eccentricity']}
        subtitle="OIML R-76-1:2006 Clause 3.6.2 — Load receptor eccentricity evaluation"
        actions={
          <button onClick={() => navigate('/tests')} className="btn-secondary text-xs">
            <ArrowLeft size={13} /> All Tests
          </button>
        }
      />

      <Alert type="info">
        <span className="font-semibold">Method:</span> OIML R-76-1:2006 Clause 3.6.2. Apply a load of approximately ⅓ Max at each specified position. The indication errors must not exceed the MPE for the applied load.
      </Alert>

      {/* Configuration */}
      <SectionCard title="Test Configuration">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <label className="label">Weighing Instrument <span className="text-red-500">*</span></label>
            <select
              value={selectedInst}
              onChange={e => {
                setSelectedInst(e.target.value);
                const inst = instruments.find(i => i.id === e.target.value);
                if (inst) setTestLoad(String(Math.round(inst.max_capacity / 3)));
              }}
              className="input-field"
            >
              <option value="">— Select instrument —</option>
              {instruments.map(i => (
                <option key={i.id} value={i.id}>{i.serial_number} · {i.model}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Test Load ({instrument?.unit ?? 'unit'}) <span className="text-red-500">*</span></label>
            <input type="number" value={testLoad} onChange={e => setTestLoad(e.target.value)} className="input-field" placeholder={instrument ? `Recommended: ${Math.round(instrument.max_capacity / 3)}` : '—'} />
          </div>
          <div>
            <label className="label">Operator</label>
            <input type="text" value={operatorName} onChange={e => setOperatorName(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="label">Ambient Temperature (°C)</label>
            <input type="number" value={ambientTemp} onChange={e => setAmbientTemp(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="label">Relative Humidity (%)</label>
            <input type="number" value={humidity} onChange={e => setHumidity(e.target.value)} className="input-field" />
          </div>
          {instrument && (
            <div className="flex flex-col justify-end">
              <div className="bg-slate-50 rounded-lg p-3 text-xs space-y-1">
                <p><span className="font-semibold">Class:</span> {instrument.accuracy_class}</p>
                <p><span className="font-semibold">Max:</span> {instrument.max_capacity} {instrument.unit}</p>
                <p><span className="font-semibold">e:</span> {instrument.verification_scale_interval} {instrument.unit}</p>
              </div>
            </div>
          )}
        </div>
      </SectionCard>

      {/* Observation Table */}
      <SectionCard
        title="Receptor Position Observations"
        subtitle="Enter the instrument indication for each receptor position"
        actions={
          <button onClick={addPosition} className="btn-secondary text-xs">
            <Plus size={13} /> Add Position
          </button>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr>
                <th className="table-header w-8">#</th>
                <th className="table-header">Position ID</th>
                <th className="table-header">Position Name</th>
                <th className="table-header">Zero Indication ({instrument?.unit ?? 'unit'})</th>
                <th className="table-header">Indication ({instrument?.unit ?? 'unit'})</th>
                <th className="table-header w-10"></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos, idx) => (
                <tr key={idx}>
                  <td className="table-cell text-xs text-slate-400">{idx + 1}</td>
                  <td className="table-cell">
                    <input value={pos.position_id} onChange={e => setPosition(idx, 'position_id', e.target.value)} className="input-field text-xs font-mono" />
                  </td>
                  <td className="table-cell">
                    <input value={pos.position_name} onChange={e => setPosition(idx, 'position_name', e.target.value)} className="input-field text-xs" />
                  </td>
                  <td className="table-cell">
                    <input type="number" value={pos.zero_indication} onChange={e => setPosition(idx, 'zero_indication', e.target.value)} className="input-field text-xs font-mono" />
                  </td>
                  <td className="table-cell">
                    <input type="number" value={pos.indication} onChange={e => setPosition(idx, 'indication', e.target.value)} placeholder="Required" className={`input-field text-xs font-mono ${!pos.indication ? 'border-amber-300 ring-1 ring-amber-200' : ''}`} />
                  </td>
                  <td className="table-cell">
                    <button onClick={() => removePosition(idx)} className="p-1.5 text-red-400 hover:bg-red-50 rounded"><Trash2 size={13} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex justify-end gap-3">
          <button onClick={handleCalculate} disabled={loading} className="btn-primary">
            {loading ? <Spinner size="sm" /> : <Calculator size={15} />}
            Calculate & Evaluate
          </button>
        </div>
      </SectionCard>

      {/* Results */}
      {calcResult && ruleResult && (
        <>
          <SectionCard title="Calculation Results — Eccentricity">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              {[
                { label: 'Reference Load', value: `${calcResult.reference_load} ${calcResult.unit}` },
                { label: 'Center Error', value: `${calcResult.center_error?.toFixed(4)} ${calcResult.unit}` },
                { label: 'Max Eccentricity Deviation', value: `${calcResult.max_absolute_eccentricity_deviation?.toFixed(4)} ${calcResult.unit}` },
                { label: 'Max Indication Error', value: `${calcResult.max_absolute_indication_error?.toFixed(4)} ${calcResult.unit}` },
              ].map(m => (
                <div key={m.label} className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">{m.label}</p>
                  <p className="font-mono font-semibold text-slate-800">{m.value}</p>
                </div>
              ))}
            </div>

            {/* Chart */}
            {chartData.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-600 mb-2">Eccentricity Deviation per Position</p>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                    <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 2" />
                    <Line type="monotone" dataKey="deviation" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} name="Eccentricity Deviation" />
                    <Line type="monotone" dataKey="error" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} name="Indication Error" />
                    <Legend iconSize={10} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Per-Position Table */}
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="table-header">Position</th>
                    <th className="table-header">Indication</th>
                    <th className="table-header">Zero</th>
                    <th className="table-header">Indication Error</th>
                    <th className="table-header">Eccentricity Dev. (ΔE)</th>
                  </tr>
                </thead>
                <tbody>
                  {calcResult.position_results?.map(p => (
                    <tr key={p.position_id} className="border-b border-slate-100">
                      <td className="table-cell font-medium">{p.position_name}</td>
                      <td className="table-cell font-mono">{p.indication.toFixed(4)}</td>
                      <td className="table-cell font-mono">{p.zero_indication.toFixed(4)}</td>
                      <td className={`table-cell font-mono font-semibold ${p.indication_error > 0 ? 'text-blue-600' : p.indication_error < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                        {p.indication_error > 0 ? '+' : ''}{p.indication_error.toFixed(4)}
                      </td>
                      <td className={`table-cell font-mono font-semibold ${Math.abs(p.eccentricity_deviation) > 0.001 ? 'text-amber-600' : 'text-emerald-600'}`}>
                        {p.eccentricity_deviation > 0 ? '+' : ''}{p.eccentricity_deviation.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>

          <RuleEvaluationPanel ruleResult={ruleResult} />

          <div className="flex justify-end gap-3">
            <button onClick={handleGenerateReport} disabled={loading || !sessionId} className="btn-primary">
              {loading ? <Spinner size="sm" /> : <FileText size={15} />}
              Generate PDF Report
            </button>
            {reportId && (
              <a href={`/api/reports/${reportId}/download`} target="_blank" rel="noreferrer" className="btn-secondary">
                Download PDF
              </a>
            )}
            {sessionId && (
              <button onClick={() => navigate(`/tests/${sessionId}`)} className="btn-secondary">
                View Session <ChevronRight size={14} />
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
};

// ─── LINEARITY TEST ───────────────────────────────────────────────────────────

const DEFAULT_LINEARITY_OBS = [
  { load: '', indication: '', direction: 'increasing', zero_indication: '0' },
  { load: '', indication: '', direction: 'increasing', zero_indication: '0' },
  { load: '', indication: '', direction: 'increasing', zero_indication: '0' },
  { load: '', indication: '', direction: 'increasing', zero_indication: '0' },
  { load: '', indication: '', direction: 'increasing', zero_indication: '0' },
];

export const LinearityTest: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selectedInst, setSelectedInst] = useState<string>((location.state as { instrument_id?: string })?.instrument_id ?? '');
  const [operatorName, setOperatorName] = useState('Lead Metrologist');
  const [ambientTemp, setAmbientTemp] = useState('20.0');
  const [observations, setObservations] = useState(DEFAULT_LINEARITY_OBS.map(o => ({ ...o })));
  const [loading, setLoading] = useState(false);
  const [calcResult, setCalcResult] = useState<CalculationResult | null>(null);
  const [ruleResult, setRuleResult] = useState<RuleEvaluationSummary | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);

  useEffect(() => { listInstruments().then(setInstruments); }, []);

  const instrument = instruments.find(i => i.id === selectedInst);

  const setObs = (idx: number, field: string, value: string) => {
    setObservations(prev => prev.map((o, i) => i === idx ? { ...o, [field]: value } : o));
  };

  const addRow = () => setObservations(prev => [...prev, { load: '', indication: '', direction: 'increasing', zero_indication: '0' }]);
  const removeRow = (idx: number) => {
    if (observations.length <= 2) { showToast('At least 2 observation rows required.', 'info'); return; }
    setObservations(prev => prev.filter((_, i) => i !== idx));
  };

  const handleCalculate = async () => {
    if (!selectedInst) { showToast('Select an instrument.', 'error'); return; }
    for (let i = 0; i < observations.length; i++) {
      const o = observations[i];
      if (!o.load || !o.indication || isNaN(Number(o.load)) || isNaN(Number(o.indication))) {
        showToast(`Row ${i + 1}: Enter valid load and indication.`, 'error'); return;
      }
    }
    try {
      setLoading(true);
      const session = await createTestSession({
        instrument_id: selectedInst, test_category: 'linearity',
        operator_name: operatorName, ambient_temperature: Number(ambientTemp), service_type: 'initial',
      });
      setSessionId(session.id);
      const obs = observations.map(o => ({
        load: Number(o.load), indication: Number(o.indication),
        direction: o.direction, zero_indication: Number(o.zero_indication || 0),
      }));
      await saveObservations(session.id, obs);
      const { calculation_result, rule_evaluation } = await runCalculations(session.id);
      setCalcResult(calculation_result);
      setRuleResult(rule_evaluation);
      showToast('Linearity calculation complete.', 'success');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast(msg || 'Calculation failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const rep = await generateReport(sessionId);
      setReportId(rep.report_id);
      showToast('PDF report generated.', 'success');
    } finally {
      setLoading(false);
    }
  };

  const chartData = calcResult?.point_results?.map(p => ({
    load: p.load,
    corrected_error: Number(p.corrected_error.toFixed(5)),
    indication_error: Number(p.indication_error.toFixed(5)),
    direction: p.direction,
  })) ?? [];

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <PageHeader
        title="Linearity Test"
        breadcrumb={['NAWI', 'Tests', 'Linearity']}
        subtitle="OIML R-76-1:2006 Clause 3.5.1 — Errors of indication across load range"
        actions={<button onClick={() => navigate('/tests')} className="btn-secondary text-xs"><ArrowLeft size={13} /> All Tests</button>}
      />
      <Alert type="info">
        <span className="font-semibold">Method:</span> OIML R-76-1:2006 Clause 3.5.1. The error Ec = (I − I₀) − L − E₀ must not exceed the MPE at each test load point per OIML Table 6.
      </Alert>

      <SectionCard title="Test Configuration">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <label className="label">Instrument <span className="text-red-500">*</span></label>
            <select value={selectedInst} onChange={e => setSelectedInst(e.target.value)} className="input-field">
              <option value="">— Select instrument —</option>
              {instruments.map(i => <option key={i.id} value={i.id}>{i.serial_number} · {i.model}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Operator</label>
            <input type="text" value={operatorName} onChange={e => setOperatorName(e.target.value)} className="input-field" />
          </div>
          <div>
            <label className="label">Temperature (°C)</label>
            <input type="number" value={ambientTemp} onChange={e => setAmbientTemp(e.target.value)} className="input-field" />
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Load Point Observations"
        subtitle="Add all test load points (increasing and decreasing passes)"
        actions={<button onClick={addRow} className="btn-secondary text-xs"><Plus size={13} /> Add Row</button>}
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr>
                <th className="table-header">#</th>
                <th className="table-header">Ref. Load ({instrument?.unit ?? 'unit'})</th>
                <th className="table-header">Indication ({instrument?.unit ?? 'unit'})</th>
                <th className="table-header">Direction</th>
                <th className="table-header">Zero Ind.</th>
                <th className="table-header w-8"></th>
              </tr>
            </thead>
            <tbody>
              {observations.map((obs, idx) => (
                <tr key={idx}>
                  <td className="table-cell text-xs text-slate-400">{idx + 1}</td>
                  <td className="table-cell">
                    <input type="number" value={obs.load} onChange={e => setObs(idx, 'load', e.target.value)} className="input-field text-xs font-mono" placeholder="e.g. 1000" />
                  </td>
                  <td className="table-cell">
                    <input type="number" value={obs.indication} onChange={e => setObs(idx, 'indication', e.target.value)} className="input-field text-xs font-mono" placeholder="Required" />
                  </td>
                  <td className="table-cell">
                    <select value={obs.direction} onChange={e => setObs(idx, 'direction', e.target.value)} className="input-field text-xs">
                      <option value="increasing">↑ Increasing</option>
                      <option value="decreasing">↓ Decreasing</option>
                    </select>
                  </td>
                  <td className="table-cell">
                    <input type="number" value={obs.zero_indication} onChange={e => setObs(idx, 'zero_indication', e.target.value)} className="input-field text-xs font-mono" />
                  </td>
                  <td className="table-cell">
                    <button onClick={() => removeRow(idx)} className="p-1.5 text-red-400 hover:bg-red-50 rounded"><Trash2 size={13} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex justify-end">
          <button onClick={handleCalculate} disabled={loading} className="btn-primary">
            {loading ? <Spinner size="sm" /> : <Calculator size={15} />}
            Calculate & Evaluate
          </button>
        </div>
      </SectionCard>

      {calcResult && ruleResult && (
        <>
          <SectionCard title="Linearity Results">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              {[
                { label: 'Max Positive Error', value: `${calcResult.max_positive_error?.toFixed(5)}` },
                { label: 'Max Negative Error', value: `${calcResult.max_negative_error?.toFixed(5)}` },
                { label: 'Max Absolute Error', value: `${calcResult.max_absolute_error?.toFixed(5)}` },
                { label: 'Max Hysteresis', value: calcResult.has_hysteresis_data ? `${calcResult.max_hysteresis?.toFixed(5)}` : '—' },
              ].map(m => (
                <div key={m.label} className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">{m.label}</p>
                  <p className="font-mono font-semibold text-slate-800">{m.value} {instrument?.unit ?? ''}</p>
                </div>
              ))}
            </div>

            {/* Error Chart */}
            {chartData.length > 0 && (
              <div className="mb-5">
                <p className="text-xs font-semibold text-slate-600 mb-2">Corrected Indication Error vs Applied Load</p>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartData.filter(d => d.direction === 'increasing')}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="load" tick={{ fontSize: 10 }} label={{ value: `Load (${instrument?.unit ?? ''})`, position: 'insideBottom', offset: -4, fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                    <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 2" />
                    <Line type="monotone" dataKey="corrected_error" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="Corrected Error Ec" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Results Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="table-header">#</th>
                    <th className="table-header">Load</th>
                    <th className="table-header">Indication</th>
                    <th className="table-header">Direction</th>
                    <th className="table-header">Ind. Error (E)</th>
                    <th className="table-header">Corrected Error (Ec)</th>
                    {calcResult.point_results?.[0]?.corrected_error_in_e !== undefined && <th className="table-header">Error in e</th>}
                  </tr>
                </thead>
                <tbody>
                  {calcResult.point_results?.map(p => (
                    <tr key={p.index} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="table-cell">{p.index}</td>
                      <td className="table-cell font-mono">{p.load}</td>
                      <td className="table-cell font-mono">{p.indication.toFixed(5)}</td>
                      <td className="table-cell">{p.direction === 'increasing' ? '↑' : '↓'} {p.direction}</td>
                      <td className={`table-cell font-mono font-semibold ${p.indication_error > 0 ? 'text-blue-600' : 'text-red-600'}`}>
                        {p.indication_error > 0 ? '+' : ''}{p.indication_error.toFixed(5)}
                      </td>
                      <td className={`table-cell font-mono font-semibold ${p.corrected_error > 0 ? 'text-blue-600' : 'text-red-600'}`}>
                        {p.corrected_error > 0 ? '+' : ''}{p.corrected_error.toFixed(5)}
                      </td>
                      {p.corrected_error_in_e !== undefined && (
                        <td className="table-cell font-mono">{p.corrected_error_in_e.toFixed(2)} e</td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>

          <RuleEvaluationPanel ruleResult={ruleResult} />

          <div className="flex justify-end gap-3">
            <button onClick={handleGenerateReport} disabled={loading || !sessionId} className="btn-primary">
              {loading ? <Spinner size="sm" /> : <FileText size={15} />}
              Generate PDF Report
            </button>
            {reportId && <a href={`/api/reports/${reportId}/download`} target="_blank" rel="noreferrer" className="btn-secondary">Download PDF</a>}
            {sessionId && <button onClick={() => navigate(`/tests/${sessionId}`)} className="btn-secondary">View Session <ChevronRight size={14} /></button>}
          </div>
        </>
      )}
    </div>
  );
};

// ─── REPEATABILITY TEST ───────────────────────────────────────────────────────

export const RepeatabilityTest: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [selectedInst, setSelectedInst] = useState<string>((location.state as { instrument_id?: string })?.instrument_id ?? '');
  const [testLoad, setTestLoad] = useState('');
  const [operatorName, setOperatorName] = useState('Lead Metrologist');
  const [runs, setRuns] = useState(
    Array.from({ length: 10 }, (_, i) => ({ run_number: i + 1, indication: '' }))
  );
  const [loading, setLoading] = useState(false);
  const [calcResult, setCalcResult] = useState<CalculationResult | null>(null);
  const [ruleResult, setRuleResult] = useState<RuleEvaluationSummary | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);

  useEffect(() => { listInstruments().then(setInstruments); }, []);

  const instrument = instruments.find(i => i.id === selectedInst);

  const setRun = (idx: number, value: string) => {
    setRuns(prev => prev.map((r, i) => i === idx ? { ...r, indication: value } : r));
  };

  const addRun = () => setRuns(prev => [...prev, { run_number: prev.length + 1, indication: '' }]);
  const removeRun = (idx: number) => {
    if (runs.length <= 2) { showToast('At least 2 repeated weighings required.', 'info'); return; }
    setRuns(prev => prev.filter((_, i) => i !== idx).map((r, i) => ({ ...r, run_number: i + 1 })));
  };

  const handleCalculate = async () => {
    if (!selectedInst) { showToast('Select an instrument.', 'error'); return; }
    if (!testLoad || isNaN(Number(testLoad)) || Number(testLoad) <= 0) { showToast('Enter a valid test load.', 'error'); return; }
    for (let i = 0; i < runs.length; i++) {
      if (!runs[i].indication || isNaN(Number(runs[i].indication))) { showToast(`Run ${i + 1}: Enter a valid indication.`, 'error'); return; }
    }
    try {
      setLoading(true);
      const session = await createTestSession({
        instrument_id: selectedInst, test_category: 'repeatability',
        operator_name: operatorName, service_type: 'initial',
        test_configuration: { test_load: Number(testLoad), runs_count: runs.length },
      });
      setSessionId(session.id);
      const obs = runs.map(r => ({ run_number: r.run_number, indication: Number(r.indication) }));
      await saveObservations(session.id, obs, { test_load: Number(testLoad) });
      const { calculation_result, rule_evaluation } = await runCalculations(session.id);
      setCalcResult(calculation_result);
      setRuleResult(rule_evaluation);
      showToast('Repeatability calculation complete.', 'success');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showToast(msg || 'Calculation failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const rep = await generateReport(sessionId);
      setReportId(rep.report_id);
      showToast('PDF report generated.', 'success');
    } finally {
      setLoading(false);
    }
  };

  const chartData = calcResult?.run_records?.map(r => ({
    run: `R${r.run_number}`,
    indication: r.indication,
    error: Number(r.error.toFixed(5)),
  })) ?? [];

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <PageHeader
        title="Repeatability Test"
        breadcrumb={['NAWI', 'Tests', 'Repeatability']}
        subtitle="OIML R-76-1:2006 Clause 3.6.1 — Repeated load consistency evaluation"
        actions={<button onClick={() => navigate('/tests')} className="btn-secondary text-xs"><ArrowLeft size={13} /> All Tests</button>}
      />
      <Alert type="info">
        <span className="font-semibold">Method:</span> OIML R-76-1:2006 Clause 3.6.1. Load and unload the same reference weight ≥10 times. The span (I_max − I_min) must not exceed |MPE| at the applied load.
      </Alert>

      <SectionCard title="Test Configuration">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <label className="label">Instrument <span className="text-red-500">*</span></label>
            <select value={selectedInst} onChange={e => {
              setSelectedInst(e.target.value);
              const inst = instruments.find(i => i.id === e.target.value);
              if (inst) setTestLoad(String(Math.round(inst.max_capacity * 0.5)));
            }} className="input-field">
              <option value="">— Select instrument —</option>
              {instruments.map(i => <option key={i.id} value={i.id}>{i.serial_number} · {i.model}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Test Load ({instrument?.unit ?? 'unit'}) <span className="text-red-500">*</span></label>
            <input type="number" value={testLoad} onChange={e => setTestLoad(e.target.value)} className="input-field" placeholder={instrument ? `Recommended: ${Math.round(instrument.max_capacity * 0.5)}` : '—'} />
          </div>
          <div>
            <label className="label">Operator</label>
            <input type="text" value={operatorName} onChange={e => setOperatorName(e.target.value)} className="input-field" />
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title={`Repeated Weighing Results (${runs.length} runs)`}
        subtitle="Enter the instrument indication for each repeated load cycle"
        actions={<button onClick={addRun} className="btn-secondary text-xs"><Plus size={13} /> Add Run</button>}
      >
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {runs.map((run, idx) => (
            <div key={idx} className="relative">
              <label className="label text-center">Run {run.run_number}</label>
              <input
                type="number"
                value={run.indication}
                onChange={e => setRun(idx, e.target.value)}
                placeholder="Indication"
                className={`input-field text-xs font-mono text-center ${!run.indication ? 'border-amber-300' : ''}`}
              />
              {runs.length > 2 && (
                <button
                  onClick={() => removeRun(idx)}
                  className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600"
                >×</button>
              )}
            </div>
          ))}
        </div>
        <div className="mt-4 flex justify-end">
          <button onClick={handleCalculate} disabled={loading} className="btn-primary">
            {loading ? <Spinner size="sm" /> : <Calculator size={15} />}
            Calculate & Evaluate
          </button>
        </div>
      </SectionCard>

      {calcResult && ruleResult && (
        <>
          <SectionCard title="Repeatability Statistics">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              {[
                { label: 'Reference Load', value: `${calcResult.reference_load} ${calcResult.unit}` },
                { label: 'Range (Max − Min)', value: `${calcResult.repeatability_range?.toFixed(5)} ${calcResult.unit}` },
                { label: 'Mean Indication', value: `${calcResult.mean_indication?.toFixed(5)} ${calcResult.unit}` },
                { label: 'Standard Deviation', value: `${calcResult.standard_deviation?.toFixed(6)} ${calcResult.unit}` },
              ].map(m => (
                <div key={m.label} className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-1">{m.label}</p>
                  <p className="font-mono font-semibold text-slate-800">{m.value}</p>
                </div>
              ))}
            </div>

            {chartData.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-slate-600 mb-2">Repeated Indications</p>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="run" tick={{ fontSize: 10 }} />
                    <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                    <ReferenceLine y={calcResult.reference_load} stroke="#94a3b8" strokeDasharray="4 2" label={{ value: 'Ref. Load', fontSize: 10 }} />
                    <Line type="monotone" dataKey="indication" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} name="Indication" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="table-header">Run #</th>
                    <th className="table-header">Indication</th>
                    <th className="table-header">Error (I − L)</th>
                    <th className="table-header">Deviation from Mean</th>
                  </tr>
                </thead>
                <tbody>
                  {calcResult.run_records?.map(r => (
                    <tr key={r.run_number} className="border-b border-slate-100">
                      <td className="table-cell">{r.run_number}</td>
                      <td className="table-cell font-mono">{r.indication.toFixed(5)}</td>
                      <td className={`table-cell font-mono ${Math.abs(r.error) > 0.001 ? 'text-amber-600' : 'text-emerald-600'}`}>
                        {r.error > 0 ? '+' : ''}{r.error.toFixed(5)}
                      </td>
                      <td className={`table-cell font-mono ${Math.abs(r.deviation_from_mean) > 0.001 ? 'text-blue-600' : 'text-slate-600'}`}>
                        {r.deviation_from_mean > 0 ? '+' : ''}{r.deviation_from_mean.toFixed(5)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>

          <RuleEvaluationPanel ruleResult={ruleResult} />

          <div className="flex justify-end gap-3">
            <button onClick={handleGenerateReport} disabled={loading || !sessionId} className="btn-primary">
              {loading ? <Spinner size="sm" /> : <FileText size={15} />}
              Generate PDF Report
            </button>
            {reportId && <a href={`/api/reports/${reportId}/download`} target="_blank" rel="noreferrer" className="btn-secondary">Download PDF</a>}
            {sessionId && <button onClick={() => navigate(`/tests/${sessionId}`)} className="btn-secondary">View Session <ChevronRight size={14} /></button>}
          </div>
        </>
      )}
    </div>
  );
};

// ─── Shared Rule Evaluation Panel ─────────────────────────────────────────────

export const RuleEvaluationPanel: React.FC<{ ruleResult: RuleEvaluationSummary }> = ({ ruleResult }) => {
  const outcomeColor = {
    PASS: 'bg-green-50 border-green-200',
    FAIL: 'bg-red-50 border-red-200',
    INCOMPLETE: 'bg-amber-50 border-amber-200',
    PENDING_VERIFICATION: 'bg-amber-50 border-amber-200',
    NOT_APPLICABLE: 'bg-slate-50 border-slate-200',
  }[ruleResult.overall_outcome] ?? 'bg-slate-50 border-slate-200';

  return (
    <SectionCard title="OIML R-76 Configured Rule Evaluation">
      {/* Summary Banner */}
      <div className={`border rounded-lg p-4 mb-4 ${outcomeColor}`}>
        <div className="flex items-center justify-between mb-1">
          <span className="font-semibold text-sm text-slate-800">Overall Evaluation Outcome</span>
          <OutcomeBadge outcome={ruleResult.overall_outcome} />
        </div>
        <p className="text-xs text-slate-600">{ruleResult.summary_text}</p>
        <p className="text-xs text-slate-400 mt-1">Rule Configuration Version: {ruleResult.rule_version}</p>
      </div>

      {/* Per-Rule Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="table-header">Rule</th>
              <th className="table-header">Source / Version</th>
              <th className="table-header">Criterion</th>
              <th className="table-header">Observed</th>
              <th className="table-header">Tolerance</th>
              <th className="table-header">Verification</th>
              <th className="table-header">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {ruleResult.evaluations?.map(ev => (
              <tr key={ev.rule_id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="table-cell">
                  <p className="font-mono font-semibold text-xs text-slate-700">{ev.rule_id}</p>
                  <p className="text-slate-500 text-xs mt-0.5">{ev.rule_name}</p>
                </td>
                <td className="table-cell text-slate-500">{ev.source_reference}</td>
                <td className="table-cell text-slate-700 max-w-[140px]">{ev.applicable_criterion}</td>
                <td className="table-cell font-mono text-slate-700">{ev.observed_value}</td>
                <td className="table-cell font-mono text-slate-700">{ev.tolerance_limit}</td>
                <td className="table-cell">
                  {ev.verification_status === 'VERIFIED' ? (
                    <span className="badge-pass">Verified</span>
                  ) : (
                    <span className="badge-warn">⚠ Pending</span>
                  )}
                </td>
                <td className="table-cell">
                  <OutcomeBadge outcome={ev.outcome} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Explanation column */}
      {ruleResult.evaluations?.some(e => e.explanation) && (
        <div className="mt-4 space-y-2">
          {ruleResult.evaluations.map(ev => (
            <div key={ev.rule_id} className="bg-slate-50 rounded-lg p-3">
              <p className="font-semibold text-xs text-slate-700 mb-0.5">{ev.rule_id}</p>
              <p className="text-xs text-slate-500">{ev.explanation}</p>
            </div>
          ))}
        </div>
      )}

      <Alert type="warn" className="mt-4">
        <span className="font-semibold">Limitation:</span> Rules marked "PENDING VERIFICATION" do not render authoritative compliance conclusions. This prototype supports metrological testing workflows and is not a legal certification instrument.
      </Alert>
    </SectionCard>
  );
};

