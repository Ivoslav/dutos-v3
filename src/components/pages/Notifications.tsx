import { Bell, CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

export function Notifications() {
  const notifications = [
    { id: 1, type: 'critical', title: 'Unfilled Duty Position', message: 'Guard duty position for tomorrow 06:00 needs assignment', time: '2 hours ago', read: false },
    { id: 2, type: 'warning', title: 'Leave Request Pending', message: '3 leave requests awaiting your approval', time: '3 hours ago', read: false },
    { id: 3, type: 'info', title: 'Duty Schedule Updated', message: 'December duty roster has been published', time: '5 hours ago', read: true },
    { id: 4, type: 'success', title: 'Mission Completed', message: 'Operation Sentinel Phase 1 completed successfully', time: '1 day ago', read: true },
    { id: 5, type: 'warning', title: 'Equipment Maintenance Due', message: 'Vehicle fleet maintenance scheduled for next week', time: '1 day ago', read: true },
    { id: 6, type: 'info', title: 'Training Reminder', message: 'Annual weapons qualification starts Monday', time: '2 days ago', read: true },
  ];

  const getIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-600" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-emerald-600" />;
      default:
        return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  const getBgColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'success':
        return 'bg-emerald-50 border-emerald-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Notifications Center</h1>
          <p className="text-slate-600">Alerts and system notifications</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            Mark All as Read
          </button>
          <button className="px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
            Settings
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Critical</div>
            <div className="text-slate-900">1</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Warnings</div>
            <div className="text-slate-900">2</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <Info className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Info</div>
            <div className="text-slate-900">2</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-slate-100 rounded-lg flex items-center justify-center">
            <Bell className="w-6 h-6 text-slate-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Unread</div>
            <div className="text-slate-900">2</div>
          </div>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className={`border rounded-lg p-5 ${
              notification.read ? 'bg-white border-slate-200' : getBgColor(notification.type)
            }`}
          >
            <div className="flex items-start gap-4">
              <div className="mt-0.5">{getIcon(notification.type)}</div>
              <div className="flex-1">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-slate-900 mb-1">{notification.title}</h3>
                    <p className="text-sm text-slate-600">{notification.message}</p>
                  </div>
                  <button className="text-slate-400 hover:text-slate-600 transition-colors">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">{notification.time}</span>
                  {!notification.read && (
                    <button className="text-xs text-slate-700 hover:text-slate-900 underline">
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
