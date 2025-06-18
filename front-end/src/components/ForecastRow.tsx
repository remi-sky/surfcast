// src/components/ForecastRow.tsx
import React from 'react';
import type { SurfForecast } from '../types';

interface Props {
  forecast: SurfForecast;
}

export const ForecastRow: React.FC<Props> = ({ forecast }) => {
  // Parse ISO timestamp to date/time
  const dt = new Date(forecast.time);
  const dateLabel = dt.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
  const timeLabel = dt.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });

  // Rating classes
  const ratingClasses: Record<NonNullable<SurfForecast['rating']>, string> = {
    Poor: 'text-rating-poor',
    Fair: 'text-rating-fair',
    Good: 'text-rating-good',
    Excellent: 'text-rating-excellent',
  };

  const colorClass =
    forecast.rating && ratingClasses[forecast.rating]
      ? ratingClasses[forecast.rating]
      : 'text-gray-400';

  return (
    <div className="p-4 bg-white/30 backdrop-blur-lg rounded-2xl shadow-lg mb-4">
      <div className="mb-2">
        <span className={`font-semibold ${colorClass}`}>{forecast.rating}</span>
        <span className="ml-2 text-sm text-white/80">{dateLabel} @ {timeLabel}</span>
      </div>
      <div className="text-sm text-white/90">{forecast.explanation}</div>
    </div>
  );
};
