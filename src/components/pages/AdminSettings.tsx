import { Settings, Database, Bell, Shield, Sliders } from 'lucide-react';

export function AdminSettings() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-slate-900 mb-2">System Settings</h1>
        <p className="text-slate-600">Configure system parameters and reference data</p>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* General Settings */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-6">
            <Sliders className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">General Settings</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Unit Name</label>
              <input
                type="text"
                defaultValue="1st Battalion, Alpha Company"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Time Zone</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>UTC -5:00 (Eastern Time)</option>
                <option>UTC -6:00 (Central Time)</option>
                <option>UTC -7:00 (Mountain Time)</option>
                <option>UTC -8:00 (Pacific Time)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Date Format</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>YYYY-MM-DD</option>
                <option>MM/DD/YYYY</option>
                <option>DD/MM/YYYY</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-6">
            <Bell className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">Notification Settings</h2>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-900 mb-1">Duty Reminders</div>
                <div className="text-xs text-slate-600">Send reminders 24h before duties</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-slate-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-700"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-900 mb-1">Leave Notifications</div>
                <div className="text-xs text-slate-600">Notify on leave request changes</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-slate-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-700"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-900 mb-1">Mission Updates</div>
                <div className="text-xs text-slate-600">Alert on mission status changes</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-slate-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-700"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-900 mb-1">System Alerts</div>
                <div className="text-xs text-slate-600">Critical system notifications</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-slate-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-700"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-6">
            <Shield className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">Security Settings</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Session Timeout</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>15 minutes</option>
                <option>30 minutes</option>
                <option>1 hour</option>
                <option>2 hours</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Password Policy</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>Strong (12+ chars, mixed case, numbers, symbols)</option>
                <option>Medium (8+ chars, mixed case, numbers)</option>
                <option>Basic (6+ characters)</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-900 mb-1">Two-Factor Authentication</div>
                <div className="text-xs text-slate-600">Require 2FA for all users</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-slate-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-700"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Database Settings */}
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-6">
            <Database className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">Database Management</h2>
          </div>
          <div className="space-y-4">
            <button className="w-full px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
              Backup Database
            </button>
            <button className="w-full px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors">
              Export Data
            </button>
            <button className="w-full px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors">
              Import Data
            </button>
            <div className="pt-4 border-t border-slate-200">
              <div className="text-xs text-slate-600 mb-2">Last Backup</div>
              <div className="text-sm text-slate-900">2024-01-15 14:30:00</div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-6 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
          Save Changes
        </button>
      </div>
    </div>
  );
}