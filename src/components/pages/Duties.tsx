import { useState } from 'react';
import { Plus, Filter, Download, Calendar as CalendarIcon, List } from 'lucide-react';
import { Table } from '../Table';
import { StatusBadge } from '../StatusBadge';
import { Modal } from '../Modal';

export function Duties() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'calendar'>('table');

  const duties = [
    { id: 1, type: 'Guard Duty', soldier: 'Sgt. Williams', rank: 'Sergeant', date: '2025-11-26', startTime: '06:00', endTime: '14:00', location: 'Main Gate', status: 'Assigned' },
    { id: 2, type: 'Radio Watch', soldier: 'Cpl. Martinez', rank: 'Corporal', date: '2025-11-26', startTime: '14:00', endTime: '22:00', location: 'Command Center', status: 'Assigned' },
    { id: 3, type: 'Vehicle Patrol', soldier: 'Spc. Thompson', rank: 'Specialist', date: '2025-11-26', startTime: '08:00', endTime: '16:00', location: 'Perimeter', status: 'Completed' },
    { id: 4, type: 'Gate Security', soldier: 'Pvt. Johnson', rank: 'Private', date: '2025-11-27', startTime: '22:00', endTime: '06:00', location: 'East Gate', status: 'Upcoming' },
    { id: 5, type: 'Equipment Check', soldier: 'Cpl. Davis', rank: 'Corporal', date: '2025-11-27', startTime: '09:00', endTime: '12:00', location: 'Armory', status: 'Upcoming' },
    { id: 6, type: 'Guard Duty', soldier: 'Sgt. Brown', rank: 'Sergeant', date: '2025-11-27', startTime: '14:00', endTime: '22:00', location: 'Main Gate', status: 'Upcoming' },
  ];

  const columns = [
    { header: 'Duty Type', accessor: 'type' },
    { header: 'Assigned Soldier', accessor: 'soldier', render: (value: string, row: any) => (
      <div>
        <div className="text-slate-900">{value}</div>
        <div className="text-xs text-slate-500">{row.rank}</div>
      </div>
    )},
    { header: 'Date', accessor: 'date' },
    { header: 'Time', accessor: 'startTime', render: (value: string, row: any) => (
      <span>{value} - {row.endTime}</span>
    )},
    { header: 'Location', accessor: 'location' },
    { header: 'Status', accessor: 'status', render: (value: string) => <StatusBadge status={value} /> },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Duty Assignments & Watch Shifts</h1>
          <p className="text-slate-600">Manage and schedule duty rotations</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create Duty
        </button>
      </div>

      {/* Filters & Actions */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search by soldier, duty type..."
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>
          <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
            <option>All Statuses</option>
            <option>Upcoming</option>
            <option>Assigned</option>
            <option>Completed</option>
          </select>
          <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
            <option>All Types</option>
            <option>Guard Duty</option>
            <option>Radio Watch</option>
            <option>Vehicle Patrol</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            <Filter className="w-4 h-4" />
            More Filters
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
          
          {/* View Toggle */}
          <div className="flex border border-slate-300 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-2 px-4 py-2 ${viewMode === 'table' ? 'bg-slate-700 text-white' : 'bg-white text-slate-700'}`}
            >
              <List className="w-4 h-4" />
              Table
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`flex items-center gap-2 px-4 py-2 border-l border-slate-300 ${viewMode === 'calendar' ? 'bg-slate-700 text-white' : 'bg-white text-slate-700'}`}
            >
              <CalendarIcon className="w-4 h-4" />
              Calendar
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {viewMode === 'table' ? (
        <Table columns={columns} data={duties} />
      ) : (
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="text-center py-12 text-slate-500">
            <CalendarIcon className="w-12 h-12 mx-auto mb-4 text-slate-400" />
            <p>Calendar view - duty schedule visualization</p>
            <p className="text-sm mt-2">Shows weekly/monthly duty assignments in calendar format</p>
          </div>
        </div>
      )}

      {/* Create Duty Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Duty Assignment"
        size="lg"
      >
        <form className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Duty Type</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>Guard Duty</option>
                <option>Radio Watch</option>
                <option>Vehicle Patrol</option>
                <option>Gate Security</option>
                <option>Equipment Check</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Assigned Soldier</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>Select soldier...</option>
                <option>Sgt. Williams</option>
                <option>Cpl. Martinez</option>
                <option>Spc. Thompson</option>
                <option>Pvt. Johnson</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Date</label>
              <input
                type="date"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Start Time</label>
              <input
                type="time"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">End Time</label>
              <input
                type="time"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-700 mb-2">Location</label>
            <input
              type="text"
              placeholder="Enter duty location"
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-700 mb-2">Special Instructions</label>
            <textarea
              rows={4}
              placeholder="Any special requirements or instructions..."
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              Create Duty Assignment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
