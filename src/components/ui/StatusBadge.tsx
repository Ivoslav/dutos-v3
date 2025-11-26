import React from 'react';

type StatusType = 'active' | 'pending' | 'inactive' | 'alert' | 'completed' | 'approved' | 'rejected' | 'on-duty' | 'on-leave';

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'active':
      case 'completed':
      case 'approved':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'pending':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'inactive':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'alert':
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'on-duty':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'on-leave':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const displayLabel = label || status.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md border text-xs tracking-wide uppercase ${getStatusStyles()}`}>
      {displayLabel}
    </span>
  );
}
