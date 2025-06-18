// src/components/SummaryRow.tsx
import React from 'react';

interface SummaryForecast {
  date: string;
  time: string;
  rating: string;
  explanation: string;
}

interface Props {
  forecast: SummaryForecast;
}

export const SummaryRow: React.FC<Props> = ({ forecast }) => (
  <div
    className="
      p-6 
      bg-white/30
      backdrop-blur-lg
      rounded-2xl
      shadow-lg 
      hover:shadow-2xl 
      transform hover:-translate-y-1 
      transition-all
    "
  >
    <div className="flex flex-col md:flex-row md:justify-between md:items-center">
      <div className="mb-3 md:mb-0">
        <span className="font-semibold text-white drop-shadow">
          {forecast.rating}
        </span>{' '}
        <span className="text-white/80 text-sm">
          {forecast.date} @ {forecast.time}
        </span>
      </div>
      <p className="text-white/90 text-sm">{forecast.explanation}</p>
    </div>
  </div>
);
