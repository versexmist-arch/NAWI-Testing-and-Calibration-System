import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  ClipboardList,
  PlusCircle,
  FlaskConical,
  CircleDot,
  TrendingUp,
  Repeat,
  BarChart2,
  FileText,
  History,
  Settings,
  Scale,
  ChevronRight,
  X,
} from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  dividerBefore?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: <LayoutDashboard size={16} /> },
  { to: '/instruments', label: 'Instruments', icon: <ClipboardList size={16} />, dividerBefore: true },
  { to: '/instruments/register', label: 'Register Instrument', icon: <PlusCircle size={16} /> },
  { to: '/tests', label: 'Test Management', icon: <FlaskConical size={16} />, dividerBefore: true },
  { to: '/tests/eccentricity', label: 'Eccentricity Test', icon: <CircleDot size={16} /> },
  { to: '/tests/linearity', label: 'Linearity Test', icon: <TrendingUp size={16} /> },
  { to: '/tests/repeatability', label: 'Repeatability Test', icon: <Repeat size={16} /> },
  { to: '/results', label: 'Results & Analytics', icon: <BarChart2 size={16} />, dividerBefore: true },
  { to: '/reports', label: 'Reports', icon: <FileText size={16} /> },
  { to: '/audit', label: 'Audit History', icon: <History size={16} /> },
  { to: '/settings', label: 'Settings', icon: <Settings size={16} />, dividerBefore: true },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onClose }) => {
  const location = useLocation();

  const isActive = (to: string) => {
    if (to === '/') return location.pathname === '/';
    return location.pathname.startsWith(to);
  };

  return (
    <aside
      className={clsx(
        'fixed inset-y-0 left-0 z-30 flex flex-col w-64 transition-transform duration-200',
        'bg-navy-900',
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}
    >
      {/* Logo Header */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-700/60">
        <div className="p-2 bg-blue-600 rounded-lg">
          <Scale size={18} className="text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-white font-bold text-sm leading-tight truncate">NAWI Cal. System</p>
          <p className="text-slate-400 text-[10px] font-medium">SIH26035 · VisionVerity</p>
        </div>
        {onClose && (
          <button onClick={onClose} className="ml-auto text-slate-400 hover:text-white lg:hidden">
            <X size={18} />
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <React.Fragment key={item.to}>
            {item.dividerBefore && <div className="border-t border-slate-700/50 my-2 mx-1" />}
            <NavLink
              to={item.to}
              end={item.to === '/'}
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive(item.to)
                    ? 'sidebar-item-active'
                    : 'sidebar-item-inactive'
                )
              }
            >
              <span className="flex-shrink-0">{item.icon}</span>
              <span className="flex-1 truncate">{item.label}</span>
              {isActive(item.to) && <ChevronRight size={12} className="opacity-60" />}
            </NavLink>
          </React.Fragment>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="px-4 py-3 border-t border-slate-700/60">
        <p className="text-[10px] text-slate-500 font-medium leading-relaxed">
          OIML R-76 Compliance Prototype<br />
          Not for legal certification use
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;

