import React from 'react';
import { clsx } from 'clsx';
import { CheckCircle2, XCircle, AlertTriangle, Clock, ChevronLeft, ChevronRight, X, TrendingUp, TrendingDown } from 'lucide-react';

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
  const map: Record<string, { variant: BadgeProps['variant']; icon: React.ReactNode; label: string }> = {
    PASS: { variant: 'pass', icon: <CheckCircle2 size={12} />, label: 'PASS' },
    FAIL: { variant: 'fail', icon: <XCircle size={12} />, label: 'FAIL' },
    INCOMPLETE: { variant: 'warn', icon: <AlertTriangle size={12} />, label: 'INCOMPLETE' },
    NOT_APPLICABLE: { variant: 'muted', icon: null, label: 'N/A' },
    PENDING_VERIFICATION: { variant: 'pending', icon: <Clock size={12} />, label: 'PENDING' },
  };
  const cfg = map[outcome] ?? { variant: 'muted' as const, icon: null, label: outcome };
  return (
    <Badge variant={cfg.variant}>
      {!small && cfg.icon}
      <span>{cfg.label}</span>
    </Badge>
  );
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
  <span className="badge-demo">
    DEMO
  </span>
);

export const RoleBadge: React.FC<{ role: string }> = ({ role }) => {
  const map: Record<string, string> = {
    Administrator: 'bg-purple-50 text-purple-700 border-purple-200',
    'Laboratory Manager': 'bg-blue-50 text-blue-700 border-blue-200',
    'Metrologist/Operator': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    Reviewer: 'bg-amber-50 text-amber-700 border-amber-200',
  };
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border', map[role] || 'bg-slate-50 text-slate-700 border-slate-200')}>
      {role}
    </span>
  );
};

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

export const LoadingOverlay: React.FC<{ message?: string }> = ({ message = 'Loading laboratory data…' }) => (
  <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
    <Spinner size="lg" />
    <p className="text-sm font-medium">{message}</p>
  </div>
);

// ─── Empty State ──────────────────────────────────────────────────────────────

export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center gap-3.5 py-16 text-center">
    {icon && <div className="p-3.5 rounded-2xl bg-blue-50/70 text-blue-600 mb-1">{icon}</div>}
    <div>
      <p className="text-sm font-bold text-slate-800">{title}</p>
      {description && <p className="text-xs text-slate-500 mt-1 max-w-sm leading-relaxed">{description}</p>}
    </div>
    {action && <div className="mt-2">{action}</div>}
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
    info: 'bg-blue-50/80 border-blue-200 text-blue-900',
    warn: 'bg-amber-50/80 border-amber-200 text-amber-900',
    error: 'bg-rose-50/80 border-rose-200 text-rose-900',
    success: 'bg-emerald-50/80 border-emerald-200 text-emerald-900',
  };
  return (
    <div className={clsx('border rounded-2xl p-4 text-xs leading-relaxed', styles[type], className)}>
      {title && <span className="font-bold mr-1">{title}:</span>}
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
    success: 'bg-emerald-700',
    error: 'bg-rose-700',
    info: 'bg-blue-700',
  };

  return (
    <div
      className={clsx(
        'fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3 rounded-2xl text-white text-sm font-medium shadow-2xl animate-fade-in',
        styles[type]
      )}
    >
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 opacity-75 hover:opacity-100 text-lg leading-none">×</button>
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
  <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 border border-slate-100">
      <h3 className="font-bold text-slate-900 mb-2">{title}</h3>
      <p className="text-xs text-slate-500 mb-6 leading-relaxed">{message}</p>
      <div className="flex gap-3 justify-end">
        <button onClick={onCancel} className="btn-secondary text-xs">Cancel</button>
        <button
          onClick={onConfirm}
          className={clsx('text-xs', danger ? 'btn-danger' : 'btn-primary')}
        >
          {confirmLabel}
        </button>
      </div>
    </div>
  </div>
);

// ─── Modal ────────────────────────────────────────────────────────────────────

export const Modal: React.FC<{
  isOpen?: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: string;
}> = ({ isOpen = true, onClose, title, subtitle, children, maxWidth = 'max-w-2xl' }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className={clsx('bg-white rounded-2xl shadow-2xl w-full border border-slate-100 my-8 overflow-hidden', maxWidth)}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div>
            <h3 className="text-base font-bold text-slate-900">{title}</h3>
            {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        <div className="p-6 max-h-[80vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
};

// ─── Page Header ──────────────────────────────────────────────────────────────

export const PageHeader: React.FC<{
  title: string;
  breadcrumb?: string[];
  actions?: React.ReactNode;
  subtitle?: string;
}> = ({ title, breadcrumb, actions, subtitle }) => (
  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
    <div>
      {breadcrumb && (
        <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1 font-medium">
          {breadcrumb.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span className="text-slate-300">/</span>}
              <span className={clsx(idx === breadcrumb.length - 1 && 'text-blue-600 font-semibold')}>
                {crumb}
              </span>
            </React.Fragment>
          ))}
        </div>
      )}
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
      {subtitle && <p className="text-xs text-slate-500 mt-1 leading-relaxed">{subtitle}</p>}
    </div>
    {actions && <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">{actions}</div>}
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-6 py-4.5 border-b border-slate-100">
        <div>
          {title && <h3 className="text-sm font-bold text-slate-800">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
      </div>
    )}
    <div className={noPadding ? '' : 'p-6'}>{children}</div>
  </div>
);

// ─── Metric Card (LIMS Modern Reference Style) ────────────────────────────────

export const MetricCard: React.FC<{
  label: string;
  value: number | string;
  icon?: React.ReactNode;
  accentColor?: string;
  color?: string;
  sub?: string;
  badge?: React.ReactNode;
  breakdown?: string;
  trend?: { value: string; positive: boolean };
}> = ({ label, value, icon, accentColor, color, sub, badge, breakdown, trend }) => {
  const iconBg = accentColor || (color ? 'bg-blue-600' : 'bg-blue-600');
  return (
    <div className="card p-5 relative overflow-hidden card-hover">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
        {icon && (
          <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-xs', iconBg)}>
            {icon}
          </div>
        )}
      </div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">{value}</span>
        {badge}
        {trend && (
          <span
            className={clsx(
              'inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full',
              trend.positive ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
            )}
          >
            {trend.positive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {trend.value}
          </span>
        )}
      </div>
      {(sub || breakdown) && (
        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
          <span>{sub}</span>
          {breakdown && <span className="font-medium text-slate-600">{breakdown}</span>}
        </div>
      )}
    </div>
  );
};

// ─── Pagination ───────────────────────────────────────────────────────────────

export const Pagination: React.FC<{
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalItems?: number;
  pageSize?: number;
}> = ({ currentPage, totalPages, onPageChange, totalItems, pageSize }) => {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-6 py-3.5 border-t border-slate-100 text-xs text-slate-500">
      {totalItems !== undefined && pageSize !== undefined ? (
        <span>
          Showing <strong className="text-slate-700">{(currentPage - 1) * pageSize + 1}</strong> to <strong className="text-slate-700">{Math.min(currentPage * pageSize, totalItems)}</strong> of <strong className="text-slate-700">{totalItems}</strong> entries
        </span>
      ) : (
        <span>
          Page <strong className="text-slate-700">{currentPage}</strong> of <strong className="text-slate-700">{totalPages}</strong>
        </span>
      )}
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={14} />
        </button>
        <span className="px-2 font-medium text-slate-700">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
};
