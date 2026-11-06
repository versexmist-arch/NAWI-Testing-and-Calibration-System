import React, { useEffect, useState, useMemo } from 'react';
import {
  Users, UserPlus, Search, Pencil, Trash2,
  ShieldCheck, Mail, CheckCircle2, XCircle, Award, UserCheck
} from 'lucide-react';
import {
  PageHeader, RoleBadge, DemoBadge, LoadingOverlay,
  EmptyState, useToast, Modal, ConfirmDialog
} from '../components/ui';
import { listUsers, createUser, updateUser, deleteUser } from '../services/api';
import type { User } from '../types';

export const UsersManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('ALL');

  // Modal State
  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    role: 'Metrologist/Operator' as User['role'],
    qualification: '',
    department: 'Metrological Verification',
    is_active: true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [deactivatingId, setDeactivatingId] = useState<string | null>(null);

  const { showToast } = useToast();

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await listUsers();
      setUsers(data);
    } catch {
      showToast('Failed to load laboratory personnel directory.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleOpenCreate = () => {
    setSelectedUser(null);
    setFormData({
      username: '',
      full_name: '',
      email: '',
      role: 'Metrologist/Operator',
      qualification: 'B.Tech Metrology / Calibration Specialist',
      department: 'Metrological Verification',
      is_active: true,
    });
    setModalMode('create');
  };

  const handleOpenEdit = (user: User) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      full_name: user.full_name,
      email: user.email,
      role: user.role,
      qualification: user.qualification || '',
      department: user.department || '',
      is_active: user.is_active,
    });
    setModalMode('edit');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.username || !formData.full_name || !formData.email) {
      showToast('Please fill in all required fields.', 'error');
      return;
    }

    try {
      setSubmitting(true);
      if (modalMode === 'create') {
        await createUser(formData);
        showToast('Operator / User created successfully.', 'success');
      } else if (modalMode === 'edit' && selectedUser) {
        await updateUser(selectedUser.id, formData);
        showToast('User profile updated successfully.', 'success');
      }
      setModalMode(null);
      await loadUsers();
    } catch {
      showToast('Operation failed. Username or email may already be in use.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivate = async (id: string) => {
    try {
      await deleteUser(id);
      showToast('User status updated.', 'success');
      setDeactivatingId(null);
      await loadUsers();
    } catch {
      showToast('Failed to deactivate user.', 'error');
    }
  };

  const filteredUsers = useMemo(() => {
    return users.filter(u => {
      if (search) {
        const q = search.toLowerCase();
        const matches =
          u.full_name.toLowerCase().includes(q) ||
          u.username.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          (u.department && u.department.toLowerCase().includes(q));
        if (!matches) return false;
      }
      if (roleFilter !== 'ALL' && u.role !== roleFilter) return false;
      return true;
    });
  }, [users, search, roleFilter]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {deactivatingId && (
        <ConfirmDialog
          title="Deactivate Operator"
          message="Deactivate this operator? They will no longer be assignable to new calibration sessions, but historical audit trails remain preserved."
          onConfirm={() => handleDeactivate(deactivatingId)}
          onCancel={() => setDeactivatingId(null)}
          confirmLabel="Deactivate"
          danger
        />
      )}

      <PageHeader
        title="Personnel & Metrology Operators"
        subtitle="Qualified metrologists, verification officers, and laboratory managers authorized under ISO/IEC 17025"
        breadcrumb={['Laboratory', 'Users & Operators']}
        actions={
          <button onClick={handleOpenCreate} className="btn-primary text-xs">
            <UserPlus size={15} /> Add Operator
          </button>
        }
      />

      {/* Filter Strip */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search operator name, email, department…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field pl-9 !py-2 text-xs w-full"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="input-field !py-2 text-xs w-full sm:w-48 bg-white"
          >
            <option value="ALL">All Laboratory Roles</option>
            <option value="Administrator">Administrator</option>
            <option value="Laboratory Manager">Laboratory Manager</option>
            <option value="Metrologist/Operator">Metrologist/Operator</option>
            <option value="Reviewer">Reviewer</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingOverlay message="Loading laboratory personnel roster…" />
        ) : filteredUsers.length === 0 ? (
          <EmptyState
            title="No personnel found"
            description="Add laboratory operators or adjust search parameters."
            action={
              <button onClick={handleOpenCreate} className="btn-primary text-xs">
                <UserPlus size={14} /> Add First Operator
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200/80">
                  <th className="table-header">Operator Name</th>
                  <th className="table-header">Role & Authorization</th>
                  <th className="table-header">Department</th>
                  <th className="table-header">Qualifications</th>
                  <th className="table-header">Contact Email</th>
                  <th className="table-header">Status</th>
                  <th className="table-header text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredUsers.map(u => (
                  <tr key={u.id} className="hover:bg-blue-50/30 transition-colors">
                    {/* Name */}
                    <td className="table-cell">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                          {u.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-bold text-slate-800">{u.full_name}</span>
                            {u.is_demo && <DemoBadge />}
                          </div>
                          <span className="text-[11px] font-mono text-slate-400">@{u.username}</span>
                        </div>
                      </div>
                    </td>

                    {/* Role */}
                    <td className="table-cell">
                      <RoleBadge role={u.role} />
                    </td>

                    {/* Department */}
                    <td className="table-cell text-xs text-slate-600">
                      {u.department || 'General Laboratory'}
                    </td>

                    {/* Qualification */}
                    <td className="table-cell text-xs text-slate-600">
                      <span className="truncate block max-w-[200px]" title={u.qualification}>
                        {u.qualification || 'Certified Calibration Tech'}
                      </span>
                    </td>

                    {/* Email */}
                    <td className="table-cell text-xs text-slate-500 font-mono">
                      {u.email}
                    </td>

                    {/* Status */}
                    <td className="table-cell">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                          <CheckCircle2 size={11} /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                          <XCircle size={11} /> Inactive
                        </span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="table-cell text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => handleOpenEdit(u)}
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Edit User"
                        >
                          <Pencil size={14} />
                        </button>
                        {u.is_active && (
                          <button
                            onClick={() => setDeactivatingId(u.id)}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Deactivate User"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Modal */}
      {modalMode && (
        <Modal
          title={modalMode === 'create' ? 'Register New Laboratory Operator' : 'Edit Personnel Profile'}
          onClose={() => setModalMode(null)}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="e.g. Dr. Sarah Jenkins"
                  className="input-field text-xs w-full"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Username *</label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={e => setFormData({ ...formData, username: e.target.value })}
                  placeholder="e.g. sjenkins"
                  className="input-field text-xs w-full font-mono"
                  disabled={modalMode === 'edit'}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  placeholder="e.g. sjenkins@visionverity.lab"
                  className="input-field text-xs w-full"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Role & Authorization *</label>
                <select
                  value={formData.role}
                  onChange={e => setFormData({ ...formData, role: e.target.value as any })}
                  className="input-field text-xs w-full bg-white"
                >
                  <option value="Metrologist/Operator">Metrologist/Operator</option>
                  <option value="Reviewer">Reviewer</option>
                  <option value="Laboratory Manager">Laboratory Manager</option>
                  <option value="Administrator">Administrator</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={e => setFormData({ ...formData, department: e.target.value })}
                  placeholder="e.g. Metrological Verification"
                  className="input-field text-xs w-full"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Qualifications / Certifications</label>
                <input
                  type="text"
                  value={formData.qualification}
                  onChange={e => setFormData({ ...formData, qualification: e.target.value })}
                  placeholder="e.g. Lead Metrologist (ISO 17025)"
                  className="input-field text-xs w-full"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded text-blue-600"
                />
                <span>Active operator authorized to conduct calibrations</span>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setModalMode(null)}
                className="btn-secondary text-xs"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary text-xs"
                disabled={submitting}
              >
                {submitting ? 'Saving…' : modalMode === 'create' ? 'Create Operator' : 'Save Changes'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default UsersManagement;

