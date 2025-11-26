import { useState } from 'react';
import { Plus, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Table } from '../Table';
import { StatusBadge } from '../StatusBadge';
import { Modal } from '../Modal';

export function LeaveSystem() {
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'history'>('pending');

  const pendingRequests = [
    { id: 1, soldier: 'Sgt. Williams', rank: 'Sergeant', type: 'Annual Leave', startDate: '2025-12-15', endDate: '2025-12-22', days: 7, reason: 'Family vacation', status: 'Pending', submitted: '2025-11-20' },
    { id: 2, soldier: 'Cpl. Martinez', rank: 'Corporal', type: 'Emergency Leave', startDate: '2025-11-28', endDate: '2025-11-30', days: 2, reason: 'Family emergency', status: 'Pending', submitted: '2025-11-25' },
    { id: 3, soldier: 'Spc. Thompson', rank: 'Specialist', type: 'Sick Leave', startDate: '2025-11-26', endDate: '2025-11-27', days: 1, reason: 'Medical appointment', status: 'Pending', submitted: '2025-11-24' },
  ];

  const approvedRequests = [
    { id: 4, soldier: 'Pvt. Johnson', rank: 'Private', type: 'Annual Leave', startDate: '2025-12-01', endDate: '2025-12-05', days: 4, reason: 'Personal travel', status: 'Approved', approved: '2025-11-18', approver: 'Maj. Anderson' },
    { id: 5, soldier: 'Cpl. Davis', rank: 'Corporal', type: 'Compassionate Leave', startDate: '2025-11-30', endDate: '2025-12-02', days: 2, reason: 'Family matter', status: 'Approved', approved: '2025-11-22', approver: 'Capt. Wilson' },
  ];

  const historyRequests = [
    { id: 6, soldier: 'Sgt. Brown', rank: 'Sergeant', type: 'Annual Leave', startDate: '2025-11-10', endDate: '2025-11-15', days: 5, reason: 'Rest and recuperation', status: 'Completed', approved: '2025-10-28', approver: 'Maj. Anderson' },
    { id: 7, soldier: 'Spc. Davis', rank: 'Specialist', type: 'Annual Leave', startDate: '2025-10-20', endDate: '2025-10-22', days: 2, reason: 'Personal', status: 'Completed', approved: '2025-10-15', approver: 'Capt. Wilson' },
    { id: 8, soldier: 'Pvt. Moore', rank: 'Private', type: 'Sick Leave', startDate: '2025-11-05', endDate: '2025-11-06', days: 1, reason: 'Illness', status: 'Rejected', rejected: '2025-11-04', rejector: 'Maj. Anderson' },
  ];

  const getPendingColumns = () => [
    { header: 'Soldier', accessor: 'soldier', render: (value: string, row: any) => (
      <div>
        <div className="text-slate-900">{value}</div>
        <div className="text-xs text-slate-500">{row.rank}</div>
      </div>
    )},
    { header: 'Type', accessor: 'type' },
    { header: 'Start Date', accessor: 'startDate' },
    { header: 'End Date', accessor: 'endDate' },
    { header: 'Days', accessor: 'days' },
    { header: 'Submitted', accessor: 'submitted' },
    { header: 'Actions', accessor: 'id', render: () => (
      <div className="flex items-center gap-2">
        <button className="p-1 text-emerald-600 hover:bg-emerald-50 rounded">
          <CheckCircle className="w-5 h-5" />
        </button>
        <button className="p-1 text-red-600 hover:bg-red-50 rounded">
          <XCircle className="w-5 h-5" />
        </button>
      </div>
    )},
  ];

  const getApprovedColumns = () => [
    { header: 'Soldier', accessor: 'soldier', render: (value: string, row: any) => (
      <div>
        <div className="text-slate-900">{value}</div>
        <div className="text-xs text-slate-500">{row.rank}</div>
      </div>
    )},
    { header: 'Type', accessor: 'type' },
    { header: 'Start Date', accessor: 'startDate' },
    { header: 'End Date', accessor: 'endDate' },
    { header: 'Days', accessor: 'days' },
    { header: 'Approved By', accessor: 'approver' },
    { header: 'Status', accessor: 'status', render: (value: string) => <StatusBadge status={value} /> },
  ];

  const getHistoryColumns = () => [
    { header: 'Soldier', accessor: 'soldier', render: (value: string, row: any) => (
      <div>
        <div className="text-slate-900">{value}</div>
        <div className="text-xs text-slate-500">{row.rank}</div>
      </div>
    )},
    { header: 'Type', accessor: 'type' },
    { header: 'Start Date', accessor: 'startDate' },
    { header: 'End Date', accessor: 'endDate' },
    { header: 'Days', accessor: 'days' },
    { header: 'Status', accessor: 'status', render: (value: string) => <StatusBadge status={value} /> },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Leave Management System</h1>
          <p className="text-slate-600">Process and track leave requests</p>
        </div>
        <button
          onClick={() => setShowRequestModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Request Leave
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
            <Clock className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Pending Approval</div>
            <div className="text-slate-900">3</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
            <CheckCircle className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Approved</div>
            <div className="text-slate-900">12</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Personnel on Leave</div>
          <div className="text-slate-900">8 soldiers</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Avg. Leave Balance</div>
          <div className="text-slate-900">16.5 days</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="border-b border-slate-200">
          <div className="flex gap-1 p-2">
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'pending'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Pending Approval ({pendingRequests.length})
            </button>
            <button
              onClick={() => setActiveTab('approved')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'approved'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Approved ({approvedRequests.length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'history'
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              History
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'pending' && (
            <Table columns={getPendingColumns()} data={pendingRequests} />
          )}
          {activeTab === 'approved' && (
            <Table columns={getApprovedColumns()} data={approvedRequests} />
          )}
          {activeTab === 'history' && (
            <Table columns={getHistoryColumns()} data={historyRequests} />
          )}
        </div>
      </div>

      {/* Request Leave Modal */}
      <Modal
        isOpen={showRequestModal}
        onClose={() => setShowRequestModal(false)}
        title="Submit Leave Request"
        size="lg"
      >
        <form className="space-y-6">
          <div>
            <label className="block text-sm text-slate-700 mb-2">Leave Type</label>
            <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
              <option>Annual Leave</option>
              <option>Sick Leave</option>
              <option>Emergency Leave</option>
              <option>Compassionate Leave</option>
              <option>Maternity/Paternity Leave</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Start Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">End Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-700 mb-2">Reason for Leave</label>
            <textarea
              rows={4}
              placeholder="Provide details about your leave request..."
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-700 mb-2">Contact During Leave</label>
            <input
              type="text"
              placeholder="Emergency contact number"
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-900 mb-1">Leave Balance: 18 days</div>
            <div className="text-xs text-blue-700">Days requested will be calculated automatically</div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setShowRequestModal(false)}
              className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              Submit Request
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
