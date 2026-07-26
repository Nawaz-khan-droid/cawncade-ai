import React from 'react';

export default function SectionCard({ title, icon: Icon, children, className = '' }) {
  return (
    <div className={`glass-card p-4 md:p-6 flex flex-col gap-3 rounded-2xl ${className}`}>
      {title && (
        <div className="flex items-center gap-2.5 pb-2.5 border-b border-white/5">
          {Icon && <Icon className="w-4 h-4 text-primary shrink-0" />}
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">{title}</h3>
        </div>
      )}
      {children}
    </div>
  );
}
