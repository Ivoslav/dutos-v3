import { Plus, Users, Shield, Award } from 'lucide-react';
import { StatusBadge } from '../StatusBadge';

export function Teams() {
  const teams = [
    {
      id: 1,
      name: 'Alpha Squad',
      unit: 'Alpha Company',
      leader: 'Sgt. Williams',
      members: 12,
      readiness: 'Ready',
      specialty: 'Infantry',
      status: 'Active'
    },
    {
      id: 2,
      name: 'Bravo Fire Team',
      unit: 'Bravo Company',
      leader: 'Cpl. Martinez',
      members: 8,
      readiness: 'Ready',
      specialty: 'Combat Support',
      status: 'Active'
    },
    {
      id: 3,
      name: 'Charlie Recon',
      unit: 'Charlie Company',
      leader: 'Sgt. Brown',
      members: 6,
      readiness: 'Limited',
      specialty: 'Reconnaissance',
      status: 'Training'
    },
    {
      id: 4,
      name: 'Medical Response Team',
      unit: 'HQ Support',
      leader: 'Spc. Davis',
      members: 5,
      readiness: 'Ready',
      specialty: 'Medical',
      status: 'Active'
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Teams & Crews</h1>
          <p className="text-slate-600">Manage squad formations and crew readiness</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
          <Plus className="w-5 h-5" />
          Create Team
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Total Teams</div>
          <div className="text-slate-900">18</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Combat Ready</div>
          <div className="text-emerald-600">15 teams</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">In Training</div>
          <div className="text-amber-600">3 teams</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Avg. Team Size</div>
          <div className="text-slate-900">8.5 members</div>
        </div>
      </div>

      {/* Teams Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {teams.map((team) => (
          <div key={team.id} className="bg-white border border-slate-200 rounded-lg p-6">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-slate-900 mb-1">{team.name}</h3>
                  <div className="text-sm text-slate-600">{team.unit}</div>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <StatusBadge status={team.status} />
                <StatusBadge status={team.readiness} />
              </div>
            </div>

            {/* Details */}
            <div className="space-y-3 py-4 border-t border-slate-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Team Leader</span>
                <span className="text-slate-900">{team.leader}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Members</span>
                <span className="text-slate-900">{team.members} personnel</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Specialty</span>
                <span className="text-slate-900">{team.specialty}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 pt-4 border-t border-slate-200">
              <button className="flex-1 px-3 py-2 text-sm bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
                View Details
              </button>
              <button className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                Manage Roster
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Readiness Matrix */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-6">
          <Award className="w-5 h-5 text-slate-600" />
          <h2 className="text-slate-900">Readiness Overview</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="text-emerald-900 mb-1">Fully Ready</div>
            <div className="text-emerald-700">15 teams (83%)</div>
          </div>
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="text-amber-900 mb-1">Limited Readiness</div>
            <div className="text-amber-700">3 teams (17%)</div>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="text-slate-900 mb-1">Not Ready</div>
            <div className="text-slate-700">0 teams (0%)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
