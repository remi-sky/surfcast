import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface SurfForecast {
  time: string;
  wave_height_m: number;
  wave_direction_s?: number;
  wind_speed_kmh?: number;
  wind_type?: string;
  rating?: string;
  explanation?: string;
}

// Group forecasts by date (YYYY-MM-DD)
const groupByDate = (forecasts: SurfForecast[]) => {
  return forecasts.reduce<Record<string, SurfForecast[]>>((acc, f) => {
    const date = f.time.split('T')[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(f);
    return acc;
  }, {});
};

const SpotForecastPage: React.FC = () => {
  const { spotId } = useParams<{ spotId: string }>();
  const navigate = useNavigate();
  const [forecasts, setForecasts] = useState<SurfForecast[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch 10 days of forecasts
  useEffect(() => {
    if (!spotId) return;
    setLoading(true);
    fetch(`/api/spots/${spotId}/forecasts?days=10`)
      .then(res => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json() as Promise<SurfForecast[]>;
      })
      .then(data => setForecasts(data))
      .catch(err => setError(err.message || 'Failed to load forecasts'))
      .finally(() => setLoading(false));
  }, [spotId]);

  const grouped = groupByDate(forecasts);

  // Format date header as 'Tuesday, 5 June 2025'
  const formatDateHeader = (dateStr: string) => {
    const dt = new Date(dateStr);
    return dt.toLocaleDateString(undefined, {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-blue-500 underline"
      >
        ← Back
      </button>
      <h1 className="text-2xl font-bold mb-4">10-Day Forecast</h1>

      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">Error: {error}</p>}

      {!loading && !error && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([date, dayForecasts]) => (
            <div key={date}>
              <h2 className="text-xl font-semibold mb-2">
                {formatDateHeader(date)}
              </h2>
              <div className="space-y-2">
                {dayForecasts.map(f => {
                  const timeLabel = f.time.split('T')[1].slice(0,5);
                  return (
                    <div
                      key={f.time}
                      className="flex justify-between items-center border-b py-2"
                    >
                      <span className="w-1/6">{timeLabel}</span>
                      <span className="w-1/6 capitalize">{f.rating ?? 'N/A'}</span>
                      <span className="w-1/6">{f.wave_height_m.toFixed(2)}m</span>
                      <span className="w-1/6">{(f.wave_period_s ?? 0).toFixed(1)}s</span>
                      <span className="w-1/6">{(f.wind_speed_kmh ?? 0).toFixed(0)}km/h</span>
                      <span className="w-1/6 capitalize">{f.wind_type ?? 'N/A'}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SpotForecastPage;
