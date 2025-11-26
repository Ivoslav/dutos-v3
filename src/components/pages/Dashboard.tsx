import { Users, Calendar, Plane, AlertTriangle, CheckCircle, Clock, UserCheck } from 'lucide-react';
import { KPICard } from '../KPICard';
import { StatusBadge } from '../StatusBadge';

export function Dashboard() {
  const upcomingDuties = [
    { id: 1, soldier: 'Sgt. Williams', duty: 'Guard Duty', date: '2025-11-26', time: '06:00 - 14:00', status: 'Upcoming' },
    { id: 2, soldier: 'Cpl. Martinez', duty: 'Radio Watch', date: '2025-11-26', time: '14:00 - 22:00', status: 'Upcoming' },
    { id: 3, soldier: 'Pvt. Johnson', duty: 'Gate Security', date: '2025-11-27', time: '22:00 - 06:00', status: 'Upcoming' },
    { id: 4, soldier: 'Spc. Davis', duty: 'Vehicle Maintenance', date: '2025-11-27', time: '08:00 - 17:00', status: 'Upcoming' },
  ];

  const alerts = [
    { id: 1, type: 'warning', message: '3 leave requests pending approval', time: '2 hours ago' },
    { id: 2, type: 'info', message: 'Duty schedule updated for December', time: '4 hours ago' },
    { id: 3, type: 'critical', message: 'Guard duty position unfilled for tomorrow 06:00', time: '5 hours ago' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-slate-900 mb-2">Command Dashboard</h1>
        <p className="text-slate-600">Overview of current operations and personnel status</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon={Users}
          label="Total Personnel"
          value="142"
          change="+2 this week"
          changeType="positive"
          iconColor="bg-slate-700"
        />
        <KPICard
          icon={UserCheck}
          label="Ready / Active"
          value="128"
          change="90% readiness"
          changeType="positive"
          iconColor="bg-emerald-600"
        />
        <KPICard
          icon={Plane}
          label="On Leave"
          value="8"
          change="5.6% of force"
          changeType="neutral"
          iconColor="bg-blue-600"
        />
        <KPICard
          icon={Calendar}
          label="Active Duties Today"
          value="24"
          change="6 shifts remaining"
          changeType="neutral"
          iconColor="bg-purple-600"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Duties */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-600" />
              <h2 className="text-slate-900">Upcoming Duties</h2>
            </div>
            <button className="text-sm text-slate-600 hover:text-slate-900">View All</button>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {upcomingDuties.map((duty) => (
                <div
                  key={duty.id}
                  className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <div className="flex-1">
                    <div className="text-slate-900 mb-1">{duty.soldier}</div>
                    <div className="text-sm text-slate-600">{duty.duty}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm text-slate-900">{duty.date}</div>
                      <div className="text-xs text-slate-600">{duty.time}</div>
                    </div>
                    <StatusBadge status={duty.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="bg-white border border-slate-200 rounded-lg">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">Alerts & Notifications</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="pb-4 border-b border-slate-200 last:border-0 last:pb-0">
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-2 h-2 rounded-full mt-2 ${
                        alert.type === 'critical'
                          ? 'bg-red-500'
                          : alert.type === 'warning'
                          ? 'bg-amber-500'
                          : 'bg-blue-500'
                      }`}
                    ></div>
                    <div className="flex-1">
                      <p className="text-sm text-slate-900 mb-1">{alert.message}</p>
                      <p className="text-xs text-slate-500">{alert.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-slate-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
            <Calendar className="w-5 h-5" />
            Create Duty Assignment
          </button>
          <button className="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors">
            <Plane className="w-5 h-5" />
            Process Leave Request
          </button>
          <button className="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors">
            <Users className="w-5 h-5" />
            Add New Soldier
          </button>
          <button className="flex items-center justify-center gap-2 px-4 py-3 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors">
            <CheckCircle className="w-5 h-5" />
            Generate Report
          </button>
        </div>
      </div>
    </div>
  );
}
