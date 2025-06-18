import React from 'react';

export const ForecastRow: React.FC<{ forecast }> = ({ forecast }) => {
  const { time, rating, wave_height_m, wave_period_s, wind_speed_kmh, wind_type } = forecast;
  const colorClass = {
    Poor: 'text-rating-poor',
    Fair: 'text-rating-fair',
    Good: 'text-rating-good',
    Excellent: 'text-rating-excellent',
  }[rating] || 'text-gray-400';

  return (
    <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow">
      <span className={`font-semibold ${colorClass}`}>{rating}</span>
      <span className="flex-1 text-center">{wave_height_m.toFixed(2)} m</span>
      <span className="flex-1 text-center">{(wave_period_s||0).toFixed(1)} s</span>
      <span className="flex-1 text-center">{(wind_speed_kmh||0).toFixed(0)} km/h</span>
      <span className="flex-1 text-center capitalize">{wind_type}</span>
      <span className="ml-4 text-sm text-gray-500">{time.slice(11,16)}</span>
    </div>
  );
};
