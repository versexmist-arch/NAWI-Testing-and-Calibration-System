import React from 'react';
import { clsx } from 'clsx';

// ─── Status & Outcome Badges ──────────────────────────────────────────────────

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'pass' | 'fail' | 'warn' | 'info' | 'muted' | 'pending';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'muted', className }) => {
  const cls = {
    pass: 'badge-pass',
    fail: 'badge-fail',
    warn: 'badge-warn',
    info: 'badge-info',
    muted: 'badge-muted',
    pending: 'badge-warn',
  }[variant];
  return <span className={clsx(cls, className)}>{children}</span>;
};

export const OutcomeBadge: React.FC<{ outcome?: string; small?: boolean }> = ({ outcome, small }) => {
  if (!outcome) return <Badge variant="muted">—</Badge>;
  const map: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    PASS: { variant: 'pass', label: '✓ PASS' },
    FAIL: { variant: 'fail', label: '✗ FAIL' },
    INCOMPLETE: { variant: 'warn', label: '⚠ INCOMPLETE' },
    NOT_APPLICABLE: { variant: 'muted', label: 'N/A' },
    PENDING_VERIFICATION: { variant: 'pending', label: '⏳ PENDING' },
  };
  const cfg = map[outcome] ?? { variant: 'muted' as const, label: outcome };
  return <Badge variant={cfg.variant}>{small ? cfg.label.replace(/^[✓✗⚠⏳] /, '') : cfg.label}</Badge>;
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, BadgeProps['variant']> = {
    Draft: 'muted',
    'In Progress': 'info',
    Calculated: 'info',
    Completed: 'pass',
    Incomplete: 'warn',
  };
  return <Badge variant={map[status] ?? 'muted'}>{status}</Badge>;
};

export const CategoryBadge: React.FC<{ category: string }> = ({ category }) => {
  const map: Record<string, { label: string; cls: string }> = {
    eccentricity: { label: 'Eccentricity', cls: 'bg-blue-50 text-blue-700 border-blue-200' },
    linearity: { label: 'Linearity', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    repeatability: { label: 'Repeatability', cls: 'bg-violet-50 text-violet-700 border-violet-200' },
  };
  const cfg = map[category?.toLowerCase()] ?? { label: category, cls: 'bg-slate-100 text-slate-600 border-slate-200' };
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border', cfg.cls)}>
      {cfg.label}
    </span>
  );
};

export const DemoBadge: React.FC = () => (
  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 uppercase tracking-wide">
    DEMO
  </span>
);

// ─── Loading Spinner ──────────────────────────────────────────────────────────

export const Spinner: React.FC<{ size?: 'sm' | 'md' | 'lg'; className?: string }> = ({
  size = 'md',
  className,
}) => {
  const sz = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' }[size];
  return (
    <div
      className={clsx(
        'border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin',
        sz,
        className
      )}
    />
  );
};

export const LoadingOverlay: React.FC<{ message?: string }> = ({ message = 'Loading…' }) => (
  <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
    <Spinner size="lg" />
    <p className="text-sm">{message}</p>
  </div>
);

// ─── Empty State ──────────────────────────────────────────────────────────────

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
    {icon && <div className="text-slate-300">{icon}</div>}
    <div>
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description && <p className="text-xs text-slate-400 mt-1 max-w-sm">{description}</p>}
    </div>
    {action && <div>{action}</div>}
  </div>
);

// ─── Alert Boxes ─────────────────────────────────────────────────────────────

export const Alert: React.FC<{
  type: 'info' | 'warn' | 'error' | 'success';
  title?: string;
  children: React.ReactNode;
  className?: string;
}> = ({ type, title, children, className }) => {
  const styles = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    warn: 'bg-amber-50 border-amber-200 text-amber-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    success: 'bg-green-50 border-green-200 text-green-800',
  };
  return (
    <div className={clsx('border rounded-lg px-4 py-3 text-sm', styles[type], className)}>
      {title && <span className="font-semibold">{title}: </span>}
      {children}
    </div>
  );
};

// ─── Toast Notification ───────────────────────────────────────────────────────

export const Toast: React.FC<{
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}> = ({ message, type, onClose }) => {
  React.useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const styles = {
    success: 'bg-green-700',
    error: 'bg-red-700',
    info: 'bg-blue-700',
  };

  return (
    <div
      className={clsx(
        'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3 rounded-xl text-white text-sm font-medium shadow-2xl',
        styles[type]
      )}
    >
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100 text-lg leading-none">×</button>
    </div>
  );
};

// ─── Toast Context ────────────────────────────────────────────────────────────

interface ToastState { message: string; type: 'success' | 'error' | 'info' }
interface ToastCtx { showToast: (message: string, type?: ToastState['type']) => void }

const ToastContext = React.createContext<ToastCtx>({ showToast: () => {} });

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toast, setToast] = React.useState<ToastState | null>(null);
  const showToast = React.useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ message, type });
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </ToastContext.Provider>
  );
};

export const useToast = () => React.useContext(ToastContext);

// ─── Confirm Dialog ───────────────────────────────────────────────────────────

export const ConfirmDialog: React.FC<{
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  danger?: boolean;
}> = ({ title, message, onConfirm, onCancel, confirmLabel = 'Confirm', danger = false }) => (
  <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
    <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
      <h3 className="font-semibold text-slate-900 mb-2">{title}</h3>
      <p className="text-sm text-slate-600 mb-6">{message}</p>
      <div className="flex gap-3 justify-end">
        <button onClick={onCancel} className="btn-secondary">{`Cancel`}</button>
        <button
          onClick={onConfirm}
          className={danger ? 'btn-danger' : 'btn-primary'}
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  </div>
);

// ─── Page Header ──────────────────────────────────────────────────────────────

export const PageHeader: React.FC<{
  title: string;
  breadcrumb?: string[];
  actions?: React.ReactNode;
  subtitle?: string;
}> = ({ title, breadcrumb, actions, subtitle }) => (
  <div className="flex items-start justify-between mb-6">
    <div>
      {breadcrumb && (
        <p className="text-xs text-slate-400 mb-1 font-medium">
          {breadcrumb.join(' / ')}
        </p>
      )}
      <h1 className="text-xl font-bold text-slate-900">{title}</h1>
      {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
    </div>
    {actions && <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>}
  </div>
);

// ─── Section Card ─────────────────────────────────────────────────────────────

export const SectionCard: React.FC<{
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}> = ({ title, subtitle, children, actions, className, noPadding }) => (
  <div className={clsx('card', className)}>
    {(title || actions) && (
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
        <div>
          {title && <h3 className="text-sm font-semibold text-slate-800">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    )}
    <div className={noPadding ? '' : 'p-5'}>{children}</div>
  </div>
);

// ─── Metric Card ──────────────────────────────────────────────────────────────

export const MetricCard: React.FC<{
  label: string;
  value: number | string;
  icon?: React.ReactNode;
  color?: string;
  sub?: string;
}> = ({ label, value, icon, color = 'text-blue-600', sub }) => (
  <div className="metric-card">
    <div className="flex items-start justify-between mb-3">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
      {icon && <div className={clsx('p-2 rounded-lg bg-slate-50', color)}>{icon}</div>}
    </div>
    <p className={clsx('text-3xl font-bold', color)}>{value}</p>
    {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
  </div>
);

