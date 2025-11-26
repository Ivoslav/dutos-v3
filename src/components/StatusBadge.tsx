interface StatusBadgeProps {
  status: string;
  variant?: 'default' | 'large';
}

export function StatusBadge({ status, variant = 'default' }: StatusBadgeProps) {
  const getStatusColor = (status: string) => {
    const normalized = status.toLowerCase();
    if (normalized.includes('active') || normalized.includes('approved') || normalized.includes('completed')) {
      return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    }
    if (normalized.includes('pending') || normalized.includes('upcoming')) {
      return 'bg-amber-100 text-amber-700 border-amber-200';
    }
    if (normalized.includes('leave') || normalized.includes('absent')) {
      return 'bg-blue-100 text-blue-700 border-blue-200';
    }
    if (normalized.includes('duty') || normalized.includes('assigned')) {
      return 'bg-purple-100 text-purple-700 border-purple-200';
    }
    if (normalized.includes('rejected') || normalized.includes('cancelled')) {
      return 'bg-red-100 text-red-700 border-red-200';
    }
    if (normalized.includes('deployed') || normalized.includes('mission')) {
      return 'bg-orange-100 text-orange-700 border-orange-200';
    }
    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  const sizeClasses = variant === 'large' ? 'px-3 py-1.5 text-sm' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center border rounded-md ${getStatusColor(
        status
      )} ${sizeClasses}`}
    >
      {status}
    </span>
  );
}
