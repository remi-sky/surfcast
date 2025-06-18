import React from 'react';

export const PageHeader: React.FC<{ title: string }> = ({ title }) => (
  <header className="py-6 px-4 border-b border-gray-light mb-6">
    <h1 className="text-ocean text-2xl font-semibold">{title}</h1>
  </header>
);
