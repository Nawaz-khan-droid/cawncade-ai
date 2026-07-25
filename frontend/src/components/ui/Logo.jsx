import React from 'react';

export default function Logo({ size = 32, className = '' }) {
  return (
    <img 
      src="/logo.png" 
      alt="CAWNCADE AI Logo" 
      width={size} 
      height={size} 
      className={`rounded-xl shadow-lg shadow-blue-500/20 object-contain ${className}`}
      style={{ width: size, height: size }}
    />
  );
}
