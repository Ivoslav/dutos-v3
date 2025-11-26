import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Users, 
  Calendar, 
  FileText, 
  Target, 
  UsersRound, 
  ClipboardList, 
  Bell, 
  Shield, 
  FileBarChart,
  Menu,
  X,
  Search,
  Settings,
  LogOut,
  ChevronDown
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
}

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'soldiers', label: 'Soldiers', icon: Users },
  { id: 'duties', label: 'Duties & Watch', icon: Calendar },
  { id: 'leave', label: 'Leave System', icon: FileText },
  { id: 'missions', label: 'Missions', icon: Target },
  { id: 'teams', label: 'Teams & Crews', icon: UsersRound },
  { id: 'logs', label: 'Activity Logs', icon: ClipboardList },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'roles', label: 'User Roles', icon: Shield },
  { id: 'reports', label: 'Reports', icon: FileBarChart },
];

export function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <div className="flex h-screen bg-[#f8f9fa]">
      {/* Sidebar */}
      <aside
        className={`bg-[#1a2332] text-white transition-all duration-300 flex flex-col ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[#2d3e50]">
          {sidebarOpen ? (
            <>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-[#4a6741] rounded-md flex items-center justify-center">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <h1 className="text-lg">DUTOS</h1>
                  <p className="text-xs text-gray-400">v2.4.1</p>
                </div>
              </div>
            </>
          ) : (
            <div className="w-8 h-8 bg-[#4a6741] rounded-md flex items-center justify-center mx-auto">
              <Shield className="w-5 h-5" />
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 transition-colors ${
                  isActive
                    ? 'bg-[#2d3e50] border-l-4 border-[#4a6741]'
                    : 'hover:bg-[#2d3e50] border-l-4 border-transparent'
                }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="h-12 flex items-center justify-center border-t border-[#2d3e50] hover:bg-[#2d3e50] transition-colors"
        >
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-16 bg-white border-b border-[#e1e4e8] flex items-center justify-between px-6">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search soldiers, duties, missions..."
                className="w-full pl-10 pr-4 py-2 border border-[#e1e4e8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4a6741] focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications */}
            <button className="relative p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-[#a83232] rounded-full"></span>
            </button>

            {/* Settings */}
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-5 h-5 text-gray-600" />
            </button>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="w-8 h-8 bg-[#4a6741] rounded-full flex items-center justify-center">
                  <span className="text-white text-sm">CO</span>
                </div>
                <div className="text-left hidden md:block">
                  <p className="text-sm text-gray-900">Cdr. Smith</p>
                  <p className="text-xs text-gray-500">Administrator</p>
                </div>
                <ChevronDown className="w-4 h-4 text-gray-500" />
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-[#e1e4e8] py-2 z-50">
                  <button className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Profile Settings
                  </button>
                  <button className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-[#a83232]">
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
