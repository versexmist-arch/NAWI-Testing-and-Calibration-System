import React from 'react';
import { useLocation } from 'react-router-dom';
import { Menu, Bell, User, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';

const PAGE_TITLES: Record<string, { title: string; breadcrumb: string[] }> = {
  '/': { title: 'Dashboard', breadcrumb: ['NAWI', 'Dashboard'] },
  '/instruments': { title: 'Instruments', breadcrumb: ['NAWI', 'Instruments'] },
  '/instruments/register': { title: 'Register Instrument', breadcrumb: ['NAWI', 'Instruments', 'Register'] },
  '/tests': { title: 'Test Management', breadcrumb: ['NAWI', 'Tests'] },
  '/tests/eccentricity': { title: 'Eccentricity Test', breadcrumb: ['NAWI', 'Tests', 'Eccentricity'] },
  '/tests/linearity': { title: 'Linearity Test', breadcrumb: ['NAWI', 'Tests', 'Linearity'] },
  '/tests/repeatability': { title: 'Repeatability Test', breadcrumb: ['NAWI', 'Tests', 'Repeatability'] },
  '/results': { title: 'Results & Analytics', breadcrumb: ['NAWI', 'Results'] },
  '/reports': { title: 'Reports', breadcrumb: ['NAWI', 'Reports'] },
  '/audit': { title: 'Audit History', breadcrumb: ['NAWI', 'Audit'] },
  '/settings': { title: 'Settings', breadcrumb: ['NAWI', 'Settings'] },
};

interface TopbarProps {
  onMenuClick: () => void;
}

const Topbar: React.FC<TopbarProps> = ({ onMenuClick }) => {
  const location = useLocation();
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-IN', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  });

  // Find the best-matching route for breadcrumbs
  const matchedKey = Object.keys(PAGE_TITLES)
    .filter(k => location.pathname === k || (k !== '/' && location.pathname.startsWith(k)))
    .sort((a, b) => b.length - a.length)[0] || '/';

  const { title, breadcrumb } = PAGE_TITLES[matchedKey] || PAGE_TITLES['/'];

  return (
    <header className="sticky top-0 z-20 flex items-center gap-4 h-14 px-5 bg-white border-b border-slate-200 shadow-sm">
      {/* Mobile menu toggle */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
      >
        <Menu size={18} />
      </button>

      {/* Breadcrumb + Title */}
      <div className="flex items-center gap-1.5 min-w-0">
        {breadcrumb.map((crumb, idx) => (
          <React.Fragment key={idx}>
            {idx > 0 && <ChevronRight size={12} className="text-slate-300 flex-shrink-0" />}
            <span
              className={clsx(
                'text-sm font-medium truncate',
                idx === breadcrumb.length - 1 ? 'text-slate-800' : 'text-slate-400'
              )}
            >
              {crumb}
            </span>
          </React.Fragment>
        ))}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Date */}
      <span className="hidden sm:block text-xs text-slate-400 font-medium">{dateStr}</span>

      {/* Notification Bell */}
      <button className="relative p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors">
        <Bell size={16} />
        <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-blue-500 rounded-full" />
      </button>

      {/* User Avatar */}
      <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
        <div className="w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
          <User size={13} />
        </div>
        <span className="hidden sm:block text-xs font-semibold text-slate-700">Lead Metrologist</span>
      </div>
    </header>
  );
};

export default Topbar;

