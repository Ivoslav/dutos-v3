import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  iconColor?: string;
}

export function KPICard({ 
  icon: Icon, 
  label, 
  value, 
  change, 
  changeType = 'neutral',
  iconColor = 'bg-slate-700'
}: KPICardProps) {
  const changeColors = {
    positive: 'text-emerald-600',
    negative: 'text-red-600',
    neutral: 'text-slate-600'
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="text-slate-600 text-sm mb-2">{label}</div>
          <div className="text-slate-900 mb-1">{value}</div>
          {change && (
            <div className={`text-xs ${changeColors[changeType]}`}>
              {change}
            </div>
          )}
        </div>
        <div className={`${iconColor} rounded-lg p-3`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}
