import React from 'react';

export const Logo: React.FC<{ size?: 'sm' | 'md' | 'lg'; className?: string }> = ({ size = 'md', className = '' }) => {
  const fontSizes = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-4xl',
  };

  return (
    <div className={`inline-flex items-center gap-1.5 select-none font-sans font-bold tracking-tight ${className}`}>
      <span className={`font-tamil text-sky-500 font-extrabold ${fontSizes[size]}`}>
        நீர்
      </span>
      <span className={`font-sans text-ink-900 dark:text-mist font-semibold ${fontSizes[size]}`}>
        Aran
      </span>
      <div className="w-1.5 h-1.5 rounded-full bg-aqua self-end mb-1"></div>
    </div>
  );
};
