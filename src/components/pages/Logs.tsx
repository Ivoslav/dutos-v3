import { Filter, Download, FileText } from 'lucide-react';
import { Table } from '../Table';

export function Logs() {
  const logs = [
    { id: 1, timestamp: '2025-11-25 14:32:15', user: 'Maj. Anderson', action: 'Leave request approved', module: 'Leave System', details: 'Approved leave for Sgt. Williams' },
    { id: 2, timestamp: '2025-11-25 14:28:43', user: 'System', action: 'Duty assignment created', module: 'Duties', details: 'Guard Duty assigned to Cpl. Martinez' },
    { id: 3, timestamp: '2025-11-25 13:15:22', user: 'Capt. Wilson', action: 'Soldier profile updated', module: 'Personnel', details: 'Updated rank for Pvt. Johnson' },
    { id: 4, timestamp: '2025-11-25 12:45:10', user: 'Sgt. Williams', action: 'Leave request submitted', module: 'Leave System', details: 'Annual leave request for Dec 15-22' },
    { id: 5, timestamp: '2025-11-25 11:30:05', user: 'Maj. Anderson', action: 'Mission status updated', module: 'Missions', details: 'Operation Sentinel marked as Active' },
    { id: 6, timestamp: '2025-11-25 10:18:33', user: 'System', action: 'Duty reminder sent', module: 'Notifications', details: 'Reminder sent to 12 personnel' },
    { id: 7, timestamp: '2025-11-25 09:45:17', user: 'Lt. Harris', action: 'Team roster modified', module: 'Teams', details: 'Added 2 members to Alpha Squad' },
    { id: 8, timestamp: '2025-11-25 09:12:44', user: 'Capt. Wilson', action: 'Report generated', module: 'Reports', details: 'Monthly personnel readiness report' },
  ];

  const columns = [
    { header: 'Timestamp', accessor: 'timestamp' },
    { header: 'User', accessor: 'user' },
    { header: 'Action', accessor: 'action' },
    { header: 'Module', accessor: 'module', render: (value: string) => (
      <span className="px-2.5 py-1 text-xs bg-slate-100 text-slate-700 border border-slate-200 rounded-md">
        {value}
      </span>
    )},
    { header: 'Details', accessor: 'details', render: (value: string) => (
      <span className="text-slate-600">{value}</span>
    )},
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Activity Logs & Audit Trail</h1>
          <p className="text-slate-600">Track system actions and user activities</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search logs..."
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>
          <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
            <option>All Modules</option>
            <option>Leave System</option>
            <option>Duties</option>
            <option>Personnel</option>
            <option>Missions</option>
            <option>Teams</option>
          </select>
          <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
            <option>All Users</option>
            <option>Maj. Anderson</option>
            <option>Capt. Wilson</option>
            <option>System</option>
          </select>
          <input
            type="date"
            className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
          />
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            <Filter className="w-4 h-4" />
            Advanced
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Total Events Today</div>
          <div className="text-slate-900">247</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Active Users</div>
          <div className="text-slate-900">18</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">System Actions</div>
          <div className="text-slate-900">64</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">User Actions</div>
          <div className="text-slate-900">183</div>
        </div>
      </div>

      {/* Logs Table */}
      <Table columns={columns} data={logs} />
    </div>
  );
}
