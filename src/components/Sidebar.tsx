import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Calendar, 
  Plane, 
  Briefcase, 
  UsersRound, 
  FileText, 
  Bell, 
  Shield, 
  FileBarChart,
  Settings
} from 'lucide-react';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: Users, label: 'Soldiers', path: '/soldiers' },
  { icon: Calendar, label: 'Duties & Shifts', path: '/duties' },
  { icon: Plane, label: 'Leave System', path: '/leave' },
  { icon: Briefcase, label: 'Missions', path: '/missions' },
  { icon: UsersRound, label: 'Teams & Crews', path: '/teams' },
  { icon: FileText, label: 'Activity Logs', path: '/logs' },
  { icon: Bell, label: 'Notifications', path: '/notifications' },
  { icon: Shield, label: 'User Roles', path: '/roles' },
  { icon: FileBarChart, label: 'Reports', path: '/reports' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-slate-800 text-slate-100 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-slate-700 bg-slate-900">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-emerald-500" />
          <div>
            <div className="tracking-widest">DUTOS</div>
            <div className="text-xs text-slate-400">Duty & Operations</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-3">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-300 hover:bg-slate-700/50 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="text-sm">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700 text-xs text-slate-400">
        <div>Version 2.4.1</div>
        <div>© 2025 Military Unit</div>
      </div>
    </aside>
  );
}
