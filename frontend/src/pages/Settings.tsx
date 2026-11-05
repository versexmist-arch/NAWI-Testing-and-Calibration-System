import React, { useEffect, useState } from 'react';
import { PageHeader, SectionCard, Alert, useToast, Spinner } from '../components/ui';
import { getRulesConfig } from '../services/api';

const Settings: React.FC = () => {
  const [rulesConfig, setRulesConfig] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    getRulesConfig()
      .then(setRulesConfig)
      .catch(() => showToast('Failed to load rules configuration.', 'error'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <PageHeader
        title="Settings & Configuration"
        breadcrumb={['NAWI', 'Settings']}
        subtitle="System configuration, OIML rule definitions, and application metadata"
      />

      <Alert type="info">
        Rule definitions are stored in <code className="bg-blue-100 px-1 rounded text-xs">rules/configurations/oiml_r76_2006_rules.json</code>. 
        To update rules, edit the JSON file and restart the backend. Rule versions are recorded with every test evaluation for full traceability.
      </Alert>

      <SectionCard title="Application Identity">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
          {[
            ['Project', 'NAWI Testing & Calibration Management System'],
            ['Problem ID', 'SIH26035'],
            ['Team', 'VisionVerity'],
            ['Framework', 'OIML R-76:2006 (Metrological Requirements)'],
            ['Backend', 'FastAPI + SQLAlchemy + SQLite'],
            ['Frontend', 'React + TypeScript + Vite + Tailwind CSS'],
            ['PDF Engine', 'ReportLab v5'],
            ['Calculation Version', 'OIML-R76-ECC/LIN/REP-v1.0'],
          ].map(([k, v]) => (
            <React.Fragment key={k}>
              <dt className="text-slate-500 font-medium">{k}</dt>
              <dd className="text-slate-800 font-semibold">{v}</dd>
            </React.Fragment>
          ))}
        </dl>
      </SectionCard>

      <SectionCard title="OIML R-76 Rule Configuration">
        {loading ? <Spinner /> : rulesConfig ? (
          <div>
            <div className="flex items-center gap-4 mb-4 p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="text-sm font-semibold text-slate-800">{rulesConfig.name as string}</p>
                <p className="text-xs text-slate-500">Version: <span className="font-mono font-semibold">{rulesConfig.rule_configuration_version as string}</span></p>
                <p className="text-xs text-slate-500 mt-0.5">{rulesConfig.description as string}</p>
              </div>
              <div className="ml-auto text-right">
                <p className="text-2xl font-bold text-blue-600">{rulesConfig.rules_count as number}</p>
                <p className="text-xs text-slate-500">Configured Rules</p>
              </div>
            </div>
            <div className="space-y-2">
              {(rulesConfig.rules as Array<Record<string, unknown>>).map(rule => (
                <div key={rule.rule_id as string} className="border border-slate-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{rule.name as string}</p>
                      <p className="font-mono text-xs text-blue-600">{rule.rule_id as string}</p>
                    </div>
                    <div className="flex gap-2">
                      {rule.verification_status === 'VERIFIED' ? (
                        <span className="badge-pass">✓ Verified</span>
                      ) : (
                        <span className="badge-warn">⚠ Pending Verification</span>
                      )}
                      <span className="badge-info capitalize">{rule.test_category as string}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 mb-1">{rule.description as string}</p>
                  <p className="text-xs text-slate-400">Source: {rule.source_reference as string} · Version: {rule.version as string}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">Rules configuration not available.</p>
        )}
      </SectionCard>

      <SectionCard title="Regulatory Disclaimer">
        <Alert type="warn">
          <span className="font-semibold">Important Notice:</span> This application is a metrological testing support prototype developed for SIH 2026. It assists with structured test workflows, traceable calculations, and OIML R-76 rule-based evaluation. <strong>It does not replace authorized verification or certification by an accredited legal metrology authority.</strong> Rules marked as "PENDING VERIFICATION" must be reviewed by a qualified metrologist before any compliance conclusion is drawn.
        </Alert>
      </SectionCard>
    </div>
  );
};

export default Settings;

