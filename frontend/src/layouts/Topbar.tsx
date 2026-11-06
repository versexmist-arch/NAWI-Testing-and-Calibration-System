import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Menu, Bell, Search, ShieldCheck, UserCheck, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';
import { getLabSettings, listUsers } from '../services/api';
import type { LaboratorySettings, User } from '../types';

const PAGE_METADATA: Record<string, { title: string; breadcrumb: string[] }> = {
  '/': { title: 'Laboratory Dashboard', breadcrumb: ['LIMS', 'Dashboard'] },
  '/instruments': { title: 'Instrument Management', breadcrumb: ['LIMS', 'Instruments'] },
  '/instruments/register': { title: 'Register Weighing Instrument', breadcrumb: ['LIMS', 'Instruments', 'Register'] },
  '/tests': { title: 'Test Management Hub', breadcrumb: ['LIMS', 'Testing', 'All Sessions'] },
  '/tests/eccentricity': { title: 'Eccentricity Test Workflow', breadcrumb: ['LIMS', 'Testing', 'Eccentricity (3.6.2)'] },
  '/tests/linearity': { title: 'Linearity & Weighing Test', breadcrumb: ['LIMS', 'Testing', 'Linearity (3.5.1)'] },
  '/tests/repeatability': { title: 'Repeatability Test Workflow', breadcrumb: ['LIMS', 'Testing', 'Repeatability (3.6.1)'] },
  '/history': { title: 'Historical Test Records', breadcrumb: ['LIMS', 'Test History'] },
  '/results': { title: 'Results & Analytics', breadcrumb: ['LIMS', 'Results'] },
  '/reports': { title: 'Report Management', breadcrumb: ['LIMS', 'Reports'] },
  '/analytics': { title: 'Laboratory Analytics & Insights', breadcrumb: ['LIMS', 'Analytics'] },
  '/audit': { title: 'Audit Trail & Traceability', breadcrumb: ['LIMS', 'Audit Logs'] },
  '/users': { title: 'Users & Personnel Management', breadcrumb: ['LIMS', 'Administration', 'Users'] },
  '/settings': { title: 'Laboratory Profile & OIML Settings', breadcrumb: ['LIMS', 'Administration', 'Settings'] },
};

interface TopbarProps {
  onMenuClick: () => void;
  isCollapsed: boolean;
}

export const Topbar: React.FC<TopbarProps> = ({ onMenuClick, isCollapsed }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [labSettings, setLabSettings] = useState<LaboratorySettings | null>(null);
  const [activeUser, setActiveUser] = useState<User | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    getLabSettings().then(setLabSettings).catch(() => {});
    listUsers().then(users => {
      if (users.length > 0) setActiveUser(users[0]);
    }).catch(() => {});
  }, []);

  const now = new Date();
  const dateStr = now.toLocaleDateString('en-IN', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  });

  const matchedKey = Object.keys(PAGE_METADATA)
    .filter(k => location.pathname === k || (k !== '/' && location.pathname.startsWith(k)))
    .sort((a, b) => b.length - a.length)[0] || '/';

  const { title } = PAGE_METADATA[matchedKey] || PAGE_METADATA['/'];

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/instruments?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between h-16 px-6 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
      {/* Left: Mobile menu toggle + Page title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl"
        >
          <Menu size={20} />
        </button>
        <div className="min-w-0">
          <h2 className="text-base font-bold text-slate-900 truncate tracking-tight">{title}</h2>
          <p className="text-[11px] text-slate-400 font-medium truncate hidden sm:block">
            {labSettings?.lab_name || 'VisionVerity Standards Facility'} · {dateStr}
          </p>
        </div>
      </div>

      {/* Middle: Global Search */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search instruments, serials, test records..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="input-field pl-9 !py-1.5 text-xs bg-slate-50/80 border-slate-200/80 focus:bg-white"
          />
        </form>
      </div>

      {/* Right: Laboratory Accreditation pill + User info */}
      <div className="flex items-center gap-3">
        {/* Accreditation status chip */}
        <div className="hidden xl:flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200/70 rounded-full text-[11px] font-semibold">
          <ShieldCheck size={13} className="text-emerald-600" />
          <span>OIML R-76 Testing System</span>
        </div>

        {/* Demo data indicator */}
        <button
          onClick={() => navigate('/settings')}
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200/60 rounded-full text-[11px] font-semibold hover:bg-blue-100/70 transition-colors"
          title="OIML R-76 Rules Version"
        >
          <Sparkles size={12} className="text-blue-500" />
          <span>OIML R-76</span>
        </button>

        {/* User Pill */}
        <div
          onClick={() => navigate('/users')}
          className="flex items-center gap-2.5 pl-3 py-1 pr-1.5 border border-slate-200 rounded-full hover:bg-slate-50 cursor-pointer transition-colors"
        >
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-slate-800 leading-tight">
              {activeUser?.full_name || 'Dr. Sarah Jenkins'}
            </p>
            <p className="text-[10px] text-blue-600 font-medium">
              {activeUser?.role || 'Laboratory Manager'}
            </p>
          </div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-700 to-blue-500 text-white flex items-center justify-center text-xs font-bold shadow-xs">
            {activeUser ? activeUser.full_name.charAt(0) : 'S'}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
