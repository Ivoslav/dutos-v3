import { useParams } from 'react-router-dom';
import { ArrowLeft, Mail, Phone, MapPin, Calendar, Award, FileText, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { StatusBadge } from '../StatusBadge';

export function SoldierProfile() {
  const { id } = useParams();
  const navigate = useNavigate();

  // Mock data
  const soldier = {
    id: 1,
    name: 'James Williams',
    rank: 'Sergeant',
    unit: 'Alpha Company, 1st Battalion',
    specialty: 'Infantry',
    status: 'Active',
    readiness: 'Ready',
    email: 'j.williams@military.unit',
    phone: '+1 (555) 123-4567',
    location: 'Fort Carson, CO',
    dateEnlisted: '2019-03-15',
    yearsService: 6,
    leaveBalance: 18,
  };

  const serviceRecord = [
    { date: '2024-09', event: 'Promoted to Sergeant', type: 'Promotion' },
    { date: '2024-06', event: 'Completed Leadership Course', type: 'Training' },
    { date: '2023-11', event: 'Deployed to Joint Exercise', type: 'Deployment' },
    { date: '2023-03', event: 'Meritorious Service Medal', type: 'Award' },
  ];

  const assignedDuties = [
    { id: 1, type: 'Guard Duty', date: '2025-11-26', time: '06:00 - 14:00', location: 'Main Gate', status: 'Upcoming' },
    { id: 2, type: 'Squad Leader', date: '2025-11-28', time: '08:00 - 17:00', location: 'Training Range', status: 'Upcoming' },
    { id: 3, type: 'Equipment Inspection', date: '2025-11-24', time: '09:00 - 12:00', location: 'Armory', status: 'Completed' },
  ];

  const activityLog = [
    { date: '2025-11-25 14:30', activity: 'Leave request approved', user: 'Maj. Anderson' },
    { date: '2025-11-24 09:15', activity: 'Duty assignment completed', user: 'System' },
    { date: '2025-11-23 16:45', activity: 'Profile updated', user: 'Sgt. Williams' },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/soldiers')}
        className="flex items-center gap-2 text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Personnel
      </button>

      {/* Profile Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-start gap-6">
          {/* Photo */}
          <div className="w-24 h-24 bg-slate-700 rounded-lg flex items-center justify-center text-white text-2xl">
            JW
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-slate-900 mb-2">{soldier.name}</h1>
                <div className="flex items-center gap-4 text-sm text-slate-600">
                  <span>{soldier.rank}</span>
                  <span>•</span>
                  <span>{soldier.unit}</span>
                  <span>•</span>
                  <span>{soldier.specialty}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={soldier.status} variant="large" />
                <StatusBadge status={soldier.readiness} variant="large" />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Mail className="w-4 h-4" />
                {soldier.email}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Phone className="w-4 h-4" />
                {soldier.phone}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <MapPin className="w-4 h-4" />
                {soldier.location}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Calendar className="w-4 h-4" />
                Enlisted: {soldier.dateEnlisted}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Years of Service</div>
          <div className="text-slate-900">{soldier.yearsService} years</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Leave Balance</div>
          <div className="text-slate-900">{soldier.leaveBalance} days</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Upcoming Duties</div>
          <div className="text-slate-900">2 assigned</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-slate-600 text-sm mb-1">Readiness Level</div>
          <div className="text-emerald-600">100%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Record */}
        <div className="bg-white border border-slate-200 rounded-lg">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <Award className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">Service Record</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {serviceRecord.map((record, index) => (
                <div key={index} className="flex items-start gap-4 pb-4 border-b border-slate-200 last:border-0">
                  <div className="text-sm text-slate-600 w-20">{record.date}</div>
                  <div className="flex-1">
                    <div className="text-sm text-slate-900 mb-1">{record.event}</div>
                    <div className="text-xs text-slate-500">{record.type}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Assigned Duties */}
        <div className="bg-white border border-slate-200 rounded-lg">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-slate-600" />
            <h2 className="text-slate-900">Assigned Duties</h2>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {assignedDuties.map((duty) => (
                <div key={duty.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div className="text-sm text-slate-900">{duty.type}</div>
                    <StatusBadge status={duty.status} />
                  </div>
                  <div className="text-xs text-slate-600">{duty.date} • {duty.time}</div>
                  <div className="text-xs text-slate-500 mt-1">{duty.location}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Activity Log */}
      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
          <Clock className="w-5 h-5 text-slate-600" />
          <h2 className="text-slate-900">Activity Log</h2>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {activityLog.map((log, index) => (
              <div key={index} className="flex items-center justify-between py-3 border-b border-slate-200 last:border-0">
                <div>
                  <div className="text-sm text-slate-900 mb-1">{log.activity}</div>
                  <div className="text-xs text-slate-500">{log.date}</div>
                </div>
                <div className="text-xs text-slate-600">{log.user}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
