import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, AlertCircle, Info } from 'lucide-react';
import { PageHeader, SectionCard, Alert, useToast, Spinner } from '../components/ui';
import { createInstrument } from '../services/api';

const ACCURACY_CLASSES = ['Class I', 'Class II', 'Class III', 'Class IIII'];
const UNITS = ['g', 'kg', 'mg', 't'];
const INSTRUMENT_TYPES = [
  'Analytical Balance', 'Precision Balance', 'Bench Scale',
  'Platform Scale', 'Retail Scale', 'Industrial Scale', 'Jewelry Scale',
];

interface FormData {
  serial_number: string;
  manufacturer: string;
  model: string;
  instrument_type: string;
  accuracy_class: string;
  max_capacity: string;
  min_capacity: string;
  verification_scale_interval: string;
  actual_scale_interval: string;
  unit: string;
  location: string;
  notes: string;
}

const initialForm: FormData = {
  serial_number: '',
  manufacturer: '',
  model: '',
  instrument_type: 'Bench Scale',
  accuracy_class: 'Class III',
  max_capacity: '',
  min_capacity: '',
  verification_scale_interval: '',
  actual_scale_interval: '',
  unit: 'g',
  location: 'Metrology Laboratory',
  notes: '',
};

const RegisterInstrument: React.FC = () => {
  const [form, setForm] = useState<FormData>(initialForm);
  const [errors, setErrors] = useState<Partial<FormData>>({});
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useToast();

  const validate = (): boolean => {
    const errs: Partial<FormData> = {};
    if (!form.serial_number.trim()) errs.serial_number = 'Serial number is required.';
    if (!form.manufacturer.trim()) errs.manufacturer = 'Manufacturer is required.';
    if (!form.model.trim()) errs.model = 'Model is required.';
    if (!form.max_capacity || isNaN(Number(form.max_capacity)) || Number(form.max_capacity) <= 0)
      errs.max_capacity = 'Valid positive maximum capacity required.';
    if (!form.verification_scale_interval || isNaN(Number(form.verification_scale_interval)) || Number(form.verification_scale_interval) <= 0)
      errs.verification_scale_interval = 'Valid positive verification scale interval (e) required.';
    if (form.min_capacity && (isNaN(Number(form.min_capacity)) || Number(form.min_capacity) < 0))
      errs.min_capacity = 'Minimum capacity must be a non-negative number if specified.';
    if (form.actual_scale_interval && (isNaN(Number(form.actual_scale_interval)) || Number(form.actual_scale_interval) <= 0))
      errs.actual_scale_interval = 'Actual scale interval must be positive if specified.';

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    try {
      setSubmitting(true);
      const created = await createInstrument({
        serial_number: form.serial_number.trim(),
        manufacturer: form.manufacturer.trim(),
        model: form.model.trim(),
        instrument_type: form.instrument_type,
        accuracy_class: form.accuracy_class,
        max_capacity: Number(form.max_capacity),
        min_capacity: form.min_capacity ? Number(form.min_capacity) : undefined,
        verification_scale_interval: Number(form.verification_scale_interval),
        actual_scale_interval: form.actual_scale_interval ? Number(form.actual_scale_interval) : undefined,
        unit: form.unit,
        location: form.location || undefined,
        notes: form.notes || undefined,
      });
      showToast(`Instrument "${form.serial_number}" registered successfully.`, 'success');
      navigate(`/instruments/${created.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (msg?.includes('already registered')) {
        setErrors(prev => ({ ...prev, serial_number: msg }));
      } else {
        showToast(msg || 'Failed to register instrument.', 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const setField = (field: keyof FormData, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: undefined }));
  };

  const F = ({ name, label, required, children }: {
    name: keyof FormData;
    label: string;
    required?: boolean;
    children: React.ReactNode;
  }) => (
    <div>
      <label className="label">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      {children}
      {errors[name] && (
        <p className="flex items-center gap-1 text-xs text-red-600 mt-1">
          <AlertCircle size={11} /> {errors[name]}
        </p>
      )}
    </div>
  );

  const Input = ({ name, type = 'text', placeholder }: {
    name: keyof FormData;
    type?: string;
    placeholder?: string;
  }) => (
    <input
      type={type}
      value={form[name]}
      onChange={e => setField(name, e.target.value)}
      placeholder={placeholder}
      className={`input-field ${errors[name] ? 'border-red-400 ring-1 ring-red-200' : ''}`}
    />
  );

  // Computed scale intervals preview
  const nIntervals = form.max_capacity && form.verification_scale_interval
    ? Math.floor(Number(form.max_capacity) / Number(form.verification_scale_interval))
    : null;

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <PageHeader
        title="Register Instrument"
        breadcrumb={['NAWI', 'Instruments', 'Register']}
        subtitle="Create a new weighing instrument profile in the system"
      />

      <Alert type="info">
        <span className="font-semibold">Metrological Accuracy:</span> Enter all parameters exactly as stated on the instrument's approval certificate or documentation. The number of verification scale intervals <code className="bg-blue-100 px-1 rounded text-xs">n = Max / e</code> is computed automatically.
      </Alert>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Identification */}
        <SectionCard title="Instrument Identification">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <F name="serial_number" label="Serial / Identification Number" required>
              <Input name="serial_number" placeholder="e.g. SN-2026-001" />
            </F>
            <F name="manufacturer" label="Manufacturer" required>
              <Input name="manufacturer" placeholder="e.g. Sartorius, Mettler Toledo" />
            </F>
            <F name="model" label="Model / Type Designation" required>
              <Input name="model" placeholder="e.g. Secura 225D" />
            </F>
            <F name="instrument_type" label="Instrument Type" required>
              <select value={form.instrument_type} onChange={e => setField('instrument_type', e.target.value)} className="input-field">
                {INSTRUMENT_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </F>
            <F name="location" label="Laboratory / Location">
              <Input name="location" placeholder="e.g. Calibration Lab Bay 2" />
            </F>
            <F name="accuracy_class" label="Accuracy Class">
              <select value={form.accuracy_class} onChange={e => setField('accuracy_class', e.target.value)} className="input-field">
                {ACCURACY_CLASSES.map(c => <option key={c}>{c}</option>)}
              </select>
            </F>
          </div>
        </SectionCard>

        {/* Metrological Parameters */}
        <SectionCard
          title="Metrological Parameters"
          subtitle="Per OIML R-76-1 Clause 2.1 — enter values in the selected unit"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <F name="unit" label="Measurement Unit" required>
              <select value={form.unit} onChange={e => setField('unit', e.target.value)} className="input-field">
                {UNITS.map(u => <option key={u}>{u}</option>)}
              </select>
            </F>
            <F name="max_capacity" label={`Maximum Capacity (${form.unit})`} required>
              <Input name="max_capacity" type="number" placeholder="e.g. 3000" />
            </F>
            <F name="min_capacity" label={`Minimum Capacity (${form.unit})`}>
              <Input name="min_capacity" type="number" placeholder="e.g. 0.4" />
            </F>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <F name="verification_scale_interval" label={`Verification Interval e (${form.unit})`} required>
              <Input name="verification_scale_interval" type="number" placeholder="e.g. 1" />
            </F>
            <F name="actual_scale_interval" label={`Actual Scale Interval d (${form.unit})`}>
              <Input name="actual_scale_interval" type="number" placeholder="e.g. 1 (optional)" />
            </F>
            <div>
              <label className="label">Scale Intervals Count (n = Max / e)</label>
              <div className={`input-field bg-slate-50 font-mono text-sm ${nIntervals ? 'text-slate-800 font-semibold' : 'text-slate-400'}`}>
                {nIntervals ? nIntervals.toLocaleString() : '—'}
              </div>
            </div>
          </div>
          {nIntervals && (
            <div className="mt-3 flex items-start gap-2 text-xs text-slate-500">
              <Info size={13} className="mt-0.5 flex-shrink-0 text-blue-500" />
              <p>
                n = {nIntervals.toLocaleString()} verification scale intervals. For Class III: 100 ≤ n ≤ 10,000.
                For Class II: 100 ≤ n ≤ 100,000.
              </p>
            </div>
          )}
        </SectionCard>

        {/* Notes */}
        <SectionCard title="Additional Notes">
          <label className="label">Notes / Remarks</label>
          <textarea
            value={form.notes}
            onChange={e => setField('notes', e.target.value)}
            rows={3}
            placeholder="Optional notes about condition, calibration history, special handling instructions…"
            className="input-field resize-none"
          />
        </SectionCard>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate('/instruments')} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="btn-primary">
            {submitting ? <Spinner size="sm" /> : <Save size={15} />}
            Register Instrument
          </button>
        </div>
      </form>
    </div>
  );
};

export default RegisterInstrument;

