import React from 'react';

interface Props {
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
}

export const PrimaryButton: React.FC<Props> = ({ onClick, children, className = '' }) => (
  <button
    onClick={onClick}
    className={`
      inline-block 
      font-medium 
      text-white 
      bg-accent-teal/80 
      hover:bg-accent-teal/90 
      ${className}
    `}
  >
    {children}
  </button>
);
