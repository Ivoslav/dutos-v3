import React from 'react';
import { Users, ClipboardCheck, Calendar, AlertTriangle, TrendingUp, UserCheck } from 'lucide-react';
import { KPICard } from './ui/KPICard';
import { StatusBadge } from './ui/StatusBadge';

export function Dashboard() {
  const upcomingDuties = [
    { id: 1, type: 'Night Watch', date: '2025-11-26', time: '20:00-04:00', soldier: 'Sgt. Martinez', status: 'assigned' },
    { id: 2, type: 'Guard Duty', date: '2025-11-26', time: '08:00-16:00', soldier: 'Cpl. Anderson', status: 'assigned' },
    { id: 3, type: 'Patrol', date: '2025-11-27', time: '06:00-12:00', soldier: 'Pvt. Williams', status: 'pending' },
    { id: 4, type: 'Communications', date: '2025-11-27', time: '16:00-00:00', soldier: 'Spc. Thompson', status: 'assigned' },
  ];

  const alerts = [
    { id: 1, type: 'alert', message: 'Duty coverage needed for Dec 1st', time: '2 hours ago' },
    { id: 2, type: 'pending', message: '3 leave requests pending approval', time: '4 hours ago' },
    { id: 3, type: 'info', message: 'Monthly readiness report due in 3 days', time: '1 day ago' },
  ];

  const recentActivity = [
    { id: 1, action: 'Leave approved', user: 'Capt. Roberts', target: 'Sgt. Davis', time: '1 hour ago' },
    { id: 2, action: 'Duty assigned', user: 'Lt. Parker', target: 'Cpl. Brown', time: '2 hours ago' },
    { id: 3, action: 'Mission updated', user: 'Maj. Wilson', target: 'Operation Eagle', time: '3 hours ago' },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Personnel"
          value="142"
          icon={Users}
          color="blue"
          trend={{ value: '+3 this month', isPositive: true }}
        />
        <KPICard
          title="Active Duties"
          value="18"
          icon={ClipboardCheck}
          color="green"
        />
        <KPICard
          title="On Leave"
          value="7"
          icon={Calendar}
          color="amber"
        />
        <KPICard
          title="Readiness Level"
          value="94%"
          icon={TrendingUp}
          color="green"
          trend={{ value: '+2% from last week', isPositive: true }}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Duties */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="text-slate-900">Upcoming Duties</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {upcomingDuties.map((duty) => (
                <div key={duty.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h4 className="text-slate-900">{duty.type}</h4>
                      <StatusBadge status={duty.status === 'assigned' ? 'active' : 'pending'} label={duty.status} />
                    </div>
                    <p className="text-sm text-slate-600">{duty.soldier}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-900">{duty.date}</p>
                    <p className="text-xs text-slate-500">{duty.time}</p>
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-4 px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition-colors">
              View All Duties
            </button>
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="text-slate-900">Alerts & Notifications</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="pb-4 border-b border-slate-100 last:border-0 last:pb-0">
                  <div className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                      alert.type === 'alert' ? 'bg-red-500' : 
                      alert.type === 'pending' ? 'bg-amber-500' : 
                      'bg-blue-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm text-slate-900">{alert.message}</p>
                      <p className="text-xs text-slate-500 mt-1">{alert.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="text-slate-900">Quick Actions</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4">
              <button className="p-4 border-2 border-slate-200 rounded-lg hover:border-slate-800 hover:bg-slate-50 transition-all">
                <ClipboardCheck className="w-6 h-6 text-slate-700 mb-2" />
                <p className="text-sm text-slate-900">Assign Duty</p>
              </button>
              <button className="p-4 border-2 border-slate-200 rounded-lg hover:border-slate-800 hover:bg-slate-50 transition-all">
                <UserCheck className="w-6 h-6 text-slate-700 mb-2" />
                <p className="text-sm text-slate-900">Add Soldier</p>
              </button>
              <button className="p-4 border-2 border-slate-200 rounded-lg hover:border-slate-800 hover:bg-slate-50 transition-all">
                <Calendar className="w-6 h-6 text-slate-700 mb-2" />
                <p className="text-sm text-slate-900">Approve Leave</p>
              </button>
              <button className="p-4 border-2 border-slate-200 rounded-lg hover:border-slate-800 hover:bg-slate-50 transition-all">
                <Users className="w-6 h-6 text-slate-700 mb-2" />
                <p className="text-sm text-slate-900">View Teams</p>
              </button>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="text-slate-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-xs text-white">{activity.user.charAt(0)}</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-slate-900">
                      <span className="font-medium">{activity.user}</span> {activity.action.toLowerCase()} <span className="font-medium">{activity.target}</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
