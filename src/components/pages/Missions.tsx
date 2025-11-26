import { Plus, MapPin, Users, Calendar } from 'lucide-react';
import { StatusBadge } from '../StatusBadge';

export function Missions() {
  const missions = [
    { 
      id: 1, 
      name: 'Operation Sentinel', 
      type: 'Security Operation',
      status: 'Active', 
      location: 'Sector 7-A', 
      startDate: '2025-11-20', 
      endDate: '2025-12-15',
      commander: 'Capt. Wilson',
      personnel: 24,
      priority: 'High'
    },
    { 
      id: 2, 
      name: 'Joint Training Exercise', 
      type: 'Training',
      status: 'Planning', 
      location: 'Training Range Delta', 
      startDate: '2025-12-01', 
      endDate: '2025-12-05',
      commander: 'Maj. Anderson',
      personnel: 48,
      priority: 'Medium'
    },
    { 
      id: 3, 
      name: 'Humanitarian Support', 
      type: 'Support Mission',
      status: 'Completed', 
      location: 'Region 4', 
      startDate: '2025-10-15', 
      endDate: '2025-11-10',
      commander: 'Lt. Col. Harris',
      personnel: 32,
      priority: 'High'
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Missions & Deployments</h1>
          <p className="text-slate-600">Track and manage operational missions</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
          <Plus className="w-5 h-5" />
          Create Mission
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Active Missions</div>
          <div className="text-slate-900">5</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Deployed Personnel</div>
          <div className="text-slate-900">86 soldiers</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Planning Phase</div>
          <div className="text-slate-900">3 missions</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Completed This Month</div>
          <div className="text-slate-900">2</div>
        </div>
      </div>

      {/* Mission Cards */}
      <div className="space-y-4">
        {missions.map((mission) => (
          <div key={mission.id} className="bg-white border border-slate-200 rounded-lg p-6 hover:border-slate-300 transition-colors">
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-slate-900">{mission.name}</h2>
                  <StatusBadge status={mission.status} variant="large" />
                  <span className={`px-2.5 py-1 text-xs rounded-md ${
                    mission.priority === 'High'
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : mission.priority === 'Medium'
                      ? 'bg-amber-100 text-amber-700 border border-amber-200'
                      : 'bg-slate-100 text-slate-700 border border-slate-200'
                  }`}>
                    {mission.priority} Priority
                  </span>
                </div>
                <div className="text-sm text-slate-600">{mission.type}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-900 mb-1">Commander</div>
                <div className="text-sm text-slate-600">{mission.commander}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 py-4 border-t border-slate-200">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-xs text-slate-500">Location</div>
                  <div className="text-sm text-slate-900">{mission.location}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-xs text-slate-500">Personnel</div>
                  <div className="text-sm text-slate-900">{mission.personnel} deployed</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <div className="text-xs text-slate-500">Duration</div>
                  <div className="text-sm text-slate-900">{mission.startDate} to {mission.endDate}</div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-4 border-t border-slate-200">
              <button className="px-4 py-2 text-sm bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
                View Details
              </button>
              <button className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                Manage Personnel
              </button>
              <button className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                Reports
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
