// src/components/ForecastRow.tsx
import React from 'react';
import type { SurfForecast } from '../types';

interface Props {
  forecast: SurfForecast;
}

export const ForecastRow: React.FC<Props> = ({ forecast }) => {
  // Map only the four known ratings
  const ratingClasses: Record<NonNullable<SurfForecast['rating']>, string> = {
    Poor:      'text-rating-poor',
    Fair:      'text-rating-fair',
    Good:      'text-rating-good',
    Excellent: 'text-rating-excellent',
  };

  const colorClass = forecast.rating
    ? ratingClasses[forecast.rating]
    : 'text-gray-400';

  return (
    <div className="p-6 bg-white/30 backdrop-blur-lg rounded-2xl shadow-lg hover:shadow-2xl transform hover:-translate-y-1 transition-all">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center">
        <div className="mb-3 md:mb-0">
          <span className={`font-semibold ${colorClass}`}>
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
};
