import { Shield, Plus, Edit } from 'lucide-react';

export function UserRoles() {
  const roles = [
    {
      id: 1,
      name: 'Administrator',
      description: 'Full system access and control',
      users: 2,
      permissions: ['All permissions', 'System configuration', 'User management', 'Data export'],
      color: 'bg-red-100 text-red-700 border-red-200'
    },
    {
      id: 2,
      name: 'Commander',
      description: 'Unit command and oversight',
      users: 5,
      permissions: ['View all personnel', 'Approve leaves', 'Create missions', 'Assign duties'],
      color: 'bg-purple-100 text-purple-700 border-purple-200'
    },
    {
      id: 3,
      name: 'Officer',
      description: 'Section and squad management',
      users: 12,
      permissions: ['Manage own section', 'Assign duties', 'View reports', 'Request leaves'],
      color: 'bg-blue-100 text-blue-700 border-blue-200'
    },
    {
      id: 4,
      name: 'Personnel Clerk',
      description: 'Personnel and records management',
      users: 3,
      permissions: ['Manage soldier profiles', 'Update records', 'Process documents', 'View reports'],
      color: 'bg-emerald-100 text-emerald-700 border-emerald-200'
    },
    {
      id: 5,
      name: 'Soldier',
      description: 'Basic personnel access',
      users: 120,
      permissions: ['View own profile', 'Request leaves', 'View duty schedule', 'Submit reports'],
      color: 'bg-slate-100 text-slate-700 border-slate-200'
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">User Roles & Permissions</h1>
          <p className="text-slate-600">Manage access control and security</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
          <Plus className="w-5 h-5" />
          Create Role
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Total Roles</div>
          <div className="text-slate-900">5</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Active Users</div>
          <div className="text-slate-900">142</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Administrators</div>
          <div className="text-slate-900">2</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Permission Groups</div>
          <div className="text-slate-900">8</div>
        </div>
      </div>

      {/* Roles Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {roles.map((role) => (
          <div key={role.id} className="bg-white border border-slate-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center">
                  <Shield className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-slate-900 mb-1">{role.name}</h3>
                  <p className="text-sm text-slate-600">{role.description}</p>
                </div>
              </div>
              <button className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                <Edit className="w-4 h-4" />
              </button>
            </div>

            <div className="mb-4 pb-4 border-b border-slate-200">
              <div className="text-sm text-slate-600 mb-1">Assigned Users</div>
              <div className="text-slate-900">{role.users} personnel</div>
            </div>

            <div>
              <div className="text-sm text-slate-600 mb-3">Permissions</div>
              <div className="space-y-2">
                {role.permissions.map((permission, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 text-sm text-slate-700"
                  >
                    <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                    {permission}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-200">
              <button className="w-full px-4 py-2 text-sm bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
                Manage Role
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Permissions Matrix */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-slate-900 mb-4">Permissions Matrix</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left text-slate-700">Permission</th>
                <th className="px-4 py-3 text-center text-slate-700">Admin</th>
                <th className="px-4 py-3 text-center text-slate-700">Commander</th>
                <th className="px-4 py-3 text-center text-slate-700">Officer</th>
                <th className="px-4 py-3 text-center text-slate-700">Clerk</th>
                <th className="px-4 py-3 text-center text-slate-700">Soldier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              <tr>
                <td className="px-4 py-3 text-slate-900">View Personnel</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-slate-900">Edit Personnel</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-slate-900">Approve Leaves</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-slate-900">Create Missions</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-slate-900">Assign Duties</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
              </tr>
              <tr>
                <td className="px-4 py-3 text-slate-900">System Configuration</td>
                <td className="px-4 py-3 text-center">✓</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
                <td className="px-4 py-3 text-center text-slate-300">–</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
