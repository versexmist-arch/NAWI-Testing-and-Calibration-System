import React, { useEffect, useState } from 'react';
import {
  Building2, Award, Thermometer, ShieldAlert,
  Save, CheckCircle2, RefreshCw, FileText, Scale
} from 'lucide-react';
import {
  PageHeader, SectionCard, Alert, useToast, Spinner
} from '../components/ui';
import { getLabSettings, updateLabSettings, getRulesConfig } from '../services/api';
import type { LaboratorySettings } from '../types';

export const Settings: React.FC = () => {
  const [labSettings, setLabSettings] = useState<LaboratorySettings | null>(null);
  const [rulesConfig, setRulesConfig] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'lab' | 'rules' | 'identity'>('lab');

  const { showToast } = useToast();

  const loadData = async () => {
    try {
      setLoading(true);
      const [settingsData, rulesData] = await Promise.all([
        getLabSettings(),
        getRulesConfig()
      ]);
      setLabSettings(settingsData);
      setRulesConfig(rulesData || {});
    } catch {
      showToast('Failed to load settings data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveLabSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!labSettings) return;

    try {
      setSaving(true);
      const updated = await updateLabSettings(labSettings);
      setLabSettings(updated);
      showToast('Laboratory configuration updated successfully.', 'success');
    } catch {
      showToast('Failed to save laboratory settings.', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      <PageHeader
        title="Laboratory & Metrological Settings"
        breadcrumb={['Laboratory', 'Settings']}
        subtitle="Configure laboratory profiles, default test environments, and OIML R-76 rule definitions"
      />

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-slate-200/60 p-1 rounded-xl text-xs font-semibold w-fit">
        <button
          onClick={() => setActiveTab('lab')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            activeTab === 'lab' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Building2 size={15} />
          Laboratory Profile & Metrological Config
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            activeTab === 'rules' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Scale size={15} />
          OIML R-76 Rule Set
        </button>
        <button
          onClick={() => setActiveTab('identity')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            activeTab === 'identity' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <FileText size={15} />
          System Identity & Disclaimer
        </button>
      </div>

      {/* Tab 1: Laboratory Profile & Metrological Config */}
      {activeTab === 'lab' && labSettings && (
        <form onSubmit={handleSaveLabSettings} className="space-y-5">
          <SectionCard
            title="Laboratory Profile & Identity"
            subtitle="Details printed on generated metrological test reports"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Laboratory Facility Name *</label>
                <input
                  type="text"
                  required
                  value={labSettings.lab_name}
                  onChange={e => setLabSettings({ ...labSettings, lab_name: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Parent Organization / Institute *</label>
                <input
                  type="text"
                  required
                  value={labSettings.organization}
                  onChange={e => setLabSettings({ ...labSettings, organization: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Accreditation / Certificate Reference Number
                </label>
                <input
                  type="text"
                  required
                  value={labSettings.accreditation_number}
                  onChange={e => setLabSettings({ ...labSettings, accreditation_number: e.target.value })}
                  className="input-field text-xs w-full font-mono font-semibold"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Report Header Document Title *</label>
                <input
                  type="text"
                  required
                  value={labSettings.report_header_title}
                  onChange={e => setLabSettings({ ...labSettings, report_header_title: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Physical Facility & Contact Coordinates"
            subtitle="Geographical location and verification officer dispatch info"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Address Line 1</label>
                <input
                  type="text"
                  value={labSettings.address_line1 || ''}
                  onChange={e => setLabSettings({ ...labSettings, address_line1: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Address Line 2 / Suite</label>
                <input
                  type="text"
                  value={labSettings.address_line2 || ''}
                  onChange={e => setLabSettings({ ...labSettings, address_line2: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">City / Region</label>
                <input
                  type="text"
                  value={labSettings.city || ''}
                  onChange={e => setLabSettings({ ...labSettings, city: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Postal Code</label>
                  <input
                    type="text"
                    value={labSettings.postal_code || ''}
                    onChange={e => setLabSettings({ ...labSettings, postal_code: e.target.value })}
                    className="input-field text-xs w-full"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Country</label>
                  <input
                    type="text"
                    value={labSettings.country || ''}
                    onChange={e => setLabSettings({ ...labSettings, country: e.target.value })}
                    className="input-field text-xs w-full"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Official Contact Email</label>
                <input
                  type="email"
                  value={labSettings.contact_email || ''}
                  onChange={e => setLabSettings({ ...labSettings, contact_email: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Telephone Contact</label>
                <input
                  type="text"
                  value={labSettings.contact_phone || ''}
                  onChange={e => setLabSettings({ ...labSettings, contact_phone: e.target.value })}
                  className="input-field text-xs w-full"
                />
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Environmental & Metrological Baseline Defaults"
            subtitle="Pre-populated test conditions for new calibration sessions"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Default Temperature (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  value={labSettings.default_temperature}
                  onChange={e => setLabSettings({ ...labSettings, default_temperature: parseFloat(e.target.value) || 20.0 })}
                  className="input-field text-xs w-full font-mono"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">OIML reference standard: 20.0°C</span>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Default Relative Humidity (%RH)</label>
                <input
                  type="number"
                  step="0.5"
                  value={labSettings.default_humidity}
                  onChange={e => setLabSettings({ ...labSettings, default_humidity: parseFloat(e.target.value) || 50.0 })}
                  className="input-field text-xs w-full font-mono"
                />
                <span className="text-[10px] text-slate-400 mt-1 block">Standard laboratory RH: 45 - 55%</span>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Default Mass Measurement Unit</label>
                <select
                  value={labSettings.default_mass_unit}
                  onChange={e => setLabSettings({ ...labSettings, default_mass_unit: e.target.value })}
                  className="input-field text-xs w-full bg-white font-mono"
                >
                  <option value="g">Grams (g)</option>
                  <option value="kg">Kilograms (kg)</option>
                  <option value="mg">Milligrams (mg)</option>
                  <option value="t">Metric Tons (t)</option>
                </select>
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Custom Report Disclaimer"
            subtitle="Mandatory metrological notice appended to all PDF certificates"
          >
            <div>
              <textarea
                rows={3}
                value={labSettings.report_disclaimer}
                onChange={e => setLabSettings({ ...labSettings, report_disclaimer: e.target.value })}
                className="input-field text-xs w-full font-mono"
              />
            </div>
          </SectionCard>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="btn-primary text-xs flex items-center gap-2"
            >
              {saving ? <Spinner size="sm" /> : <Save size={15} />}
              Save Laboratory Settings
            </button>
          </div>
        </form>
      )}

      {/* Tab 2: OIML R-76 Rules */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          <Alert type="info">
            Metrological rules conform to <strong>OIML R-76-1:2006</strong>. Step intervals and Maximum Permissible Errors (mpe) are computed deterministically per accuracy class and test load.
          </Alert>

          <SectionCard title="Active Rule Set">
            <div className="flex items-center justify-between mb-4 p-3.5 bg-slate-50 rounded-xl border border-slate-200/80">
              <div>
                <p className="text-sm font-bold text-slate-800">{String(rulesConfig.name || 'OIML R-76-1:2006 Standard Rules')}</p>
                <p className="text-xs text-slate-500">Version: <span className="font-mono font-semibold text-blue-600">{String(rulesConfig.rule_configuration_version || '1.0.0')}</span></p>
                <p className="text-xs text-slate-500 mt-0.5">{String(rulesConfig.description || 'Verified metrological rules')}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-black text-blue-600">{Number(rulesConfig.rules_count || 3)}</p>
                <p className="text-[11px] text-slate-500 font-medium">Configured Rules</p>
              </div>
            </div>

            <div className="space-y-3">
              {Array.isArray(rulesConfig.rules) && (rulesConfig.rules as Array<Record<string, unknown>>).map((rule) => (
                <div key={String(rule.rule_id)} className="border border-slate-200/80 rounded-xl p-4 bg-white">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{String(rule.name)}</p>
                      <p className="font-mono text-xs text-blue-600">{String(rule.rule_id)}</p>
                    </div>
                    <div className="flex gap-2">
                      {rule.verification_status === 'VERIFIED' ? (
                        <span className="badge-pass text-xs">✓ Verified</span>
                      ) : (
                        <span className="badge-warn text-xs">⚠ Pending Verification</span>
                      )}
                      <span className="badge-info capitalize text-xs">{String(rule.test_category)}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 mb-1.5">{String(rule.description)}</p>
                  <p className="text-[11px] text-slate-400">
                    Source: {String(rule.source_reference)} &middot; Engine Version: {String(rule.version)}
                  </p>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      )}

      {/* Tab 3: System Identity */}
      {activeTab === 'identity' && (
        <div className="space-y-4">
          <SectionCard title="Application & Metrological Architecture">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
              {[
                ['Project Name', 'NAWI Testing & Calibration Management System (LIMS)'],
                ['Smart India Hackathon ID', 'SIH26035'],
                ['Team Identity', 'VisionVerity'],
                ['Metrological Standard', 'OIML R-76-1:2006 (Non-Automatic Weighing Instruments)'],
                ['Laboratory Quality Framework', 'OIML R-76-1:2006 Metrological Testing'],
                ['Backend Server', 'FastAPI 0.115+ with Pydantic v2 & SQLAlchemy ORM'],
                ['Database Engine', 'SQLite with PostgreSQL-ready schema separation'],
                ['Reporting Subsystem', 'ReportLab High-Fidelity PDF Engine'],
                ['Frontend Architecture', 'React 18 + TypeScript + Vite + Tailwind CSS'],
                ['Calculation Module', 'Verified Python Pure-Math Engine (12 Automated Tests)'],
              ].map(([k, v]) => (
                <React.Fragment key={k}>
                  <dt className="text-slate-500 font-medium">{k}</dt>
                  <dd className="text-slate-900 font-semibold">{v}</dd>
                </React.Fragment>
              ))}
            </dl>
          </SectionCard>

          <SectionCard title="Legal Metrology Notice">
            <Alert type="warn">
              <span className="font-bold">Metrological Notice:</span> This application assists with structured testing workflows, traceable calculation formulas, and OIML R-76 rule evaluations. While implemented strictly according to OIML R-76 Table 6 formulas, official legal metrology verification requires authorization by an accredited national weights and measures authority.
            </Alert>
          </SectionCard>
        </div>
      )}
    </div>
  );
};

export default Settings;
