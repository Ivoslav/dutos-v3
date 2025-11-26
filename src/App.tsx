import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { Dashboard } from './components/pages/Dashboard';
import { Duties } from './components/pages/Duties';
import { Soldiers } from './components/pages/Soldiers';
import { SoldierProfile } from './components/pages/SoldierProfile';
import { LeaveSystem } from './components/pages/LeaveSystem';
import { Missions } from './components/pages/Missions';
import { Teams } from './components/pages/Teams';
import { Logs } from './components/pages/Logs';
import { Notifications } from './components/pages/Notifications';
import { UserRoles } from './components/pages/UserRoles';
import { Reports } from './components/pages/Reports';
import { AdminSettings } from './components/pages/AdminSettings';

export default function App() {
  return (
    <Router>
      <div className="flex h-screen bg-slate-100">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <TopBar />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/duties" element={<Duties />} />
              <Route path="/soldiers" element={<Soldiers />} />
              <Route path="/soldiers/:id" element={<SoldierProfile />} />
              <Route path="/leave" element={<LeaveSystem />} />
              <Route path="/missions" element={<Missions />} />
              <Route path="/teams" element={<Teams />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/roles" element={<UserRoles />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<AdminSettings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}
