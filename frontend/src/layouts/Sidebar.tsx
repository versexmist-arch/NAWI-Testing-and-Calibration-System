import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Scale,
  FlaskConical,
  CircleDot,
  TrendingUp,
  Repeat,
  History,
  FileText,
  BarChart3,
  ShieldAlert,
  Users,
  Settings2,
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  X,
  ShieldCheck,
} from 'lucide-react';

interface SidebarProps {
  mobileOpen: boolean;
  onClose: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  mobileOpen,
  onClose,
  isCollapsed,
  onToggleCollapse,
}) => {
  const location = useLocation();
  const [testMenuOpen, setTestMenuOpen] = useState(
    location.pathname.startsWith('/tests')
  );

  const isActive = (to: string) => {
    if (to === '/') return location.pathname === '/';
    return location.pathname.startsWith(to);
  };

  return (
    <aside
      className={clsx(
        'fixed inset-y-0 left-0 z-30 flex flex-col lims-sidebar select-none transition-all duration-300',
        isCollapsed ? 'w-20' : 'w-64',
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-[#d8e4f5]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white flex-shrink-0 shadow-md shadow-blue-500/20">
            <Scale size={20} />
          </div>
          {!isCollapsed && (
            <div className="min-w-0">
              <h1 className="text-sm font-extrabold text-slate-900 tracking-tight truncate leading-tight">
                NAWI LIMS
              </h1>
              <p className="text-[10px] font-semibold text-blue-700/80 truncate">
                OIML R-76 Laboratory
              </p>
            </div>
          )}
        </div>

        {/* Mobile close button */}
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-blue-100"
        >
          <X size={18} />
        </button>

        {/* Desktop collapse toggle */}
        <button
          onClick={onToggleCollapse}
          className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-blue-100/70 transition-colors"
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {isCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
        </button>
      </div>

      {/* Navigation Body */}
      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {/* Core Section */}
        <div>
          {!isCollapsed && (
            <p className="px-3 mb-2 text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
              Main Navigation
            </p>
          )}
          <div className="space-y-1">
            <NavLink
              to="/"
              end
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/') && location.pathname === '/'
                    ? 'sidebar-item-active'
                    : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Dashboard"
            >
              <LayoutDashboard size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Dashboard</span>}
            </NavLink>

            <NavLink
              to="/instruments"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/instruments')
                    ? 'sidebar-item-active'
                    : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Instruments"
            >
              <Scale size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Instruments</span>}
            </NavLink>
          </div>
        </div>

        {/* Testing Workflows Section */}
        <div>
          {!isCollapsed && (
            <p className="px-3 mb-2 text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
              Testing & Calibration
            </p>
          )}
          <div className="space-y-1">
            {/* Test Management parent item */}
            {!isCollapsed ? (
              <div>
                <button
                  onClick={() => setTestMenuOpen(!testMenuOpen)}
                  className={clsx(
                    'w-full sidebar-item justify-between',
                    isActive('/tests')
                      ? 'bg-blue-100/50 text-blue-900 font-semibold'
                      : 'sidebar-item-inactive'
                  )}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FlaskConical size={18} className="flex-shrink-0 text-blue-600" />
                    <span className="truncate">Test Management</span>
                  </div>
                  {testMenuOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>

                {/* Submenu */}
                {testMenuOpen && (
                  <div className="ml-5 pl-3 border-l-2 border-blue-200 mt-1 space-y-1">
                    <NavLink
                      to="/tests"
                      end
                      onClick={onClose}
                      className={({ isActive }) =>
                        clsx(
                          'flex items-center gap-2 py-1.5 px-2.5 rounded-lg text-xs transition-colors',
                          isActive ? 'sidebar-subitem-active' : 'sidebar-subitem-inactive'
                        )
                      }
                    >
                      <span>All Sessions</span>
                    </NavLink>
                    <NavLink
                      to="/tests/eccentricity"
                      onClick={onClose}
                      className={({ isActive }) =>
                        clsx(
                          'flex items-center gap-2 py-1.5 px-2.5 rounded-lg text-xs transition-colors',
                          isActive ? 'sidebar-subitem-active' : 'sidebar-subitem-inactive'
                        )
                      }
                    >
                      <CircleDot size={13} className="text-blue-500" />
                      <span>Eccentricity</span>
                    </NavLink>
                    <NavLink
                      to="/tests/linearity"
                      onClick={onClose}
                      className={({ isActive }) =>
                        clsx(
                          'flex items-center gap-2 py-1.5 px-2.5 rounded-lg text-xs transition-colors',
                          isActive ? 'sidebar-subitem-active' : 'sidebar-subitem-inactive'
                        )
                      }
                    >
                      <TrendingUp size={13} className="text-emerald-500" />
                      <span>Linearity</span>
                    </NavLink>
                    <NavLink
                      to="/tests/repeatability"
                      onClick={onClose}
                      className={({ isActive }) =>
                        clsx(
                          'flex items-center gap-2 py-1.5 px-2.5 rounded-lg text-xs transition-colors',
                          isActive ? 'sidebar-subitem-active' : 'sidebar-subitem-inactive'
                        )
                      }
                    >
                      <Repeat size={13} className="text-violet-500" />
                      <span>Repeatability</span>
                    </NavLink>
                  </div>
                )}
              </div>
            ) : (
              <NavLink
                to="/tests"
                onClick={onClose}
                className={() =>
                  clsx(
                    'sidebar-item justify-center px-0',
                    isActive('/tests') ? 'sidebar-item-active' : 'sidebar-item-inactive'
                  )
                }
                title="Test Management"
              >
                <FlaskConical size={18} />
              </NavLink>
            )}

            <NavLink
              to="/history"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/history') ? 'sidebar-item-active' : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Test History"
            >
              <History size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Test History</span>}
            </NavLink>
          </div>
        </div>

        {/* Quality & Reporting Section */}
        <div>
          {!isCollapsed && (
            <p className="px-3 mb-2 text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
              Quality & Records
            </p>
          )}
          <div className="space-y-1">
            <NavLink
              to="/reports"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/reports') ? 'sidebar-item-active' : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Reports"
            >
              <FileText size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Reports</span>}
            </NavLink>

            <NavLink
              to="/analytics"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/analytics') ? 'sidebar-item-active' : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Analytics"
            >
              <BarChart3 size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Analytics</span>}
            </NavLink>

            <NavLink
              to="/audit"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/audit') ? 'sidebar-item-active' : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Audit Logs"
            >
              <ShieldAlert size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Audit Logs</span>}
            </NavLink>
          </div>
        </div>

        {/* Administration Section */}
        <div>
          {!isCollapsed && (
            <p className="px-3 mb-2 text-[10px] font-extrabold tracking-wider text-slate-400 uppercase">
              Administration
            </p>
          )}
          <div className="space-y-1">
            <NavLink
              to="/users"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/users') ? 'sidebar-item-active' : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Users & Operators"
            >
              <Users size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Users & Operators</span>}
            </NavLink>

            <NavLink
              to="/settings"
              onClick={onClose}
              className={() =>
                clsx(
                  'sidebar-item',
                  isActive('/settings') ? 'sidebar-item-active' : 'sidebar-item-inactive',
                  isCollapsed && 'justify-center px-0'
                )
              }
              title="Laboratory Settings"
            >
              <Settings2 size={18} className="flex-shrink-0" />
              {!isCollapsed && <span className="flex-1 truncate">Laboratory Settings</span>}
            </NavLink>
          </div>
        </div>
      </nav>

      {/* Footer / Metrological Status */}
      <div className="p-3 border-t border-[#d8e4f5] bg-white/40">
        {!isCollapsed ? (
          <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-xl bg-blue-50/80 border border-blue-200/60">
            <ShieldCheck size={18} className="text-blue-600 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-[11px] font-bold text-slate-800 leading-tight truncate">
                OIML R-76 Edition
              </p>
              <p className="text-[10px] text-slate-500 truncate">
                OIML R-76 Testing System
              </p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-1 text-blue-600" title="OIML R-76 Verified">
            <ShieldCheck size={20} />
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
