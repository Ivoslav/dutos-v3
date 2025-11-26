import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Filter, Download, UserPlus } from 'lucide-react';
import { Table } from '../Table';
import { StatusBadge } from '../StatusBadge';

export function Soldiers() {
  const navigate = useNavigate();

  const soldiers = [
    { id: 1, name: 'James Williams', rank: 'Sergeant', unit: 'Alpha Company', specialty: 'Infantry', status: 'Active', readiness: 'Ready', yearsService: 6 },
    { id: 2, name: 'Carlos Martinez', rank: 'Corporal', unit: 'Alpha Company', specialty: 'Communications', status: 'On Duty', readiness: 'Ready', yearsService: 4 },
    { id: 3, name: 'Michael Thompson', rank: 'Specialist', unit: 'Bravo Company', specialty: 'Vehicle Ops', status: 'Active', readiness: 'Ready', yearsService: 3 },
    { id: 4, name: 'Robert Johnson', rank: 'Private', unit: 'Alpha Company', specialty: 'Infantry', status: 'Active', readiness: 'Ready', yearsService: 1 },
    { id: 5, name: 'David Brown', rank: 'Sergeant', unit: 'Charlie Company', specialty: 'Medical', status: 'Active', readiness: 'Ready', yearsService: 8 },
    { id: 6, name: 'Sarah Davis', rank: 'Corporal', unit: 'Bravo Company', specialty: 'Logistics', status: 'On Leave', readiness: 'Limited', yearsService: 5 },
    { id: 7, name: 'Jennifer Wilson', rank: 'Specialist', unit: 'Charlie Company', specialty: 'Intelligence', status: 'Active', readiness: 'Ready', yearsService: 2 },
    { id: 8, name: 'Thomas Moore', rank: 'Private First Class', unit: 'Alpha Company', specialty: 'Infantry', status: 'Active', readiness: 'Ready', yearsService: 2 },
  ];

  const columns = [
    { header: 'Name', accessor: 'name', render: (value: string, row: any) => (
      <div>
        <div className="text-slate-900">{value}</div>
        <div className="text-xs text-slate-500">{row.rank}</div>
      </div>
    )},
    { header: 'Unit', accessor: 'unit' },
    { header: 'Specialty', accessor: 'specialty' },
    { header: 'Status', accessor: 'status', render: (value: string) => <StatusBadge status={value} /> },
    { header: 'Readiness', accessor: 'readiness', render: (value: string) => <StatusBadge status={value} /> },
    { header: 'Service Years', accessor: 'yearsService' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Personnel Management</h1>
          <p className="text-slate-600">View and manage soldier profiles and readiness status</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
          <UserPlus className="w-5 h-5" />
          Add Soldier
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Total Personnel</div>
          <div className="text-slate-900">142</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Ready Status</div>
          <div className="text-emerald-600">128</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">On Leave</div>
          <div className="text-blue-600">8</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Deployed</div>
          <div className="text-orange-600">6</div>
        </div>
      </div>

      {/* Filters & Actions */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search by name, rank, specialty..."
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
            />
          </div>
          <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
            <option>All Units</option>
            <option>Alpha Company</option>
            <option>Bravo Company</option>
            <option>Charlie Company</option>
          </select>
          <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
            <option>All Statuses</option>
            <option>Active</option>
            <option>On Duty</option>
            <option>On Leave</option>
            <option>Deployed</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            <Filter className="w-4 h-4" />
            More Filters
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Table */}
      <Table 
        columns={columns} 
        data={soldiers}
        onRowClick={(soldier) => navigate(`/soldiers/${soldier.id}`)}
      />
    </div>
  );
}
