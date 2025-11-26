import { FileBarChart, Download, Calendar, TrendingUp } from 'lucide-react';

export function Reports() {
  const reportTypes = [
    {
      id: 1,
      name: 'Personnel Readiness Report',
      description: 'Current readiness status of all personnel',
      category: 'Personnel',
      frequency: 'Weekly',
      lastGenerated: '2025-11-24'
    },
    {
      id: 2,
      name: 'Duty Assignment Summary',
      description: 'Duty roster and completion statistics',
      category: 'Operations',
      frequency: 'Monthly',
      lastGenerated: '2025-11-20'
    },
    {
      id: 3,
      name: 'Leave Analytics',
      description: 'Leave requests and approval trends',
      category: 'Personnel',
      frequency: 'Monthly',
      lastGenerated: '2025-11-18'
    },
    {
      id: 4,
      name: 'Mission Status Report',
      description: 'Active and completed mission overview',
      category: 'Operations',
      frequency: 'Weekly',
      lastGenerated: '2025-11-22'
    },
    {
      id: 5,
      name: 'Team Readiness Matrix',
      description: 'Squad and crew readiness assessment',
      category: 'Teams',
      frequency: 'Bi-weekly',
      lastGenerated: '2025-11-15'
    },
    {
      id: 6,
      name: 'Training Completion Report',
      description: 'Training requirements and completion rates',
      category: 'Training',
      frequency: 'Monthly',
      lastGenerated: '2025-11-10'
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-slate-900 mb-2">Reports & Analytics</h1>
          <p className="text-slate-600">Generate and export system reports</p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <FileBarChart className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Total Reports</div>
            <div className="text-slate-900">24</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
            <Calendar className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Generated This Month</div>
            <div className="text-slate-900">18</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Scheduled Reports</div>
            <div className="text-slate-900">6 active</div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-4">
          <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
            <Download className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <div className="text-slate-600 text-sm mb-1">Downloads</div>
            <div className="text-slate-900">142</div>
          </div>
        </div>
      </div>

      {/* Report Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {reportTypes.map((report) => (
          <div key={report.id} className="bg-white border border-slate-200 rounded-lg p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center flex-shrink-0">
                <FileBarChart className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-slate-900 mb-1">{report.name}</h3>
                <p className="text-sm text-slate-600 mb-3">{report.description}</p>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="px-2 py-1 bg-slate-100 rounded">
                    {report.category}
                  </span>
                  <span>{report.frequency}</span>
                  <span>Last: {report.lastGenerated}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-4 border-t border-slate-200">
              <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
                <FileBarChart className="w-4 h-4" />
                Generate
              </button>
              <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
                <Download className="w-4 h-4" />
                Download Latest
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Custom Report Builder */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-slate-900 mb-4">Custom Report Builder</h2>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Report Name</label>
              <input
                type="text"
                placeholder="Enter report name"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Category</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>Personnel</option>
                <option>Operations</option>
                <option>Teams</option>
                <option>Training</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-2">Date Range</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>Last 7 days</option>
                <option>Last 30 days</option>
                <option>Last 90 days</option>
                <option>Custom range</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-2">Export Format</label>
              <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-700">
                <option>PDF</option>
                <option>Excel (XLSX)</option>
                <option>CSV</option>
              </select>
            </div>
          </div>

          <button className="flex items-center gap-2 px-6 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
            <FileBarChart className="w-5 h-5" />
            Generate Custom Report
          </button>
        </div>
      </div>
    </div>
  );
}
