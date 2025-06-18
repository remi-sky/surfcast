// src/pages/SpotForecastPage.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { SurfForecast } from '../types';  // your shared type
import { PageHeader } from '../components/PageHeader';
import { PrimaryButton } from '../components/PrimaryButton';

type Params = { spotId: string };

const groupByDate = (forecasts: SurfForecast[]) =>
  forecasts.reduce<Record<string, SurfForecast[]>>((acc, f) => {
    const date = f.time.split('T')[0];
    (acc[date] ||= []).push(f);
    return acc;
  }, {});

export default function SpotForecastPage() {
  const { spotId } = useParams<Params>();
  const navigate = useNavigate();

  const [forecasts, setForecasts] = useState<SurfForecast[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  useEffect(() => {
    if (!spotId) return;

    setLoading(true);
    setError(null);

    fetch(`/api/spots/${spotId}/forecasts?days=10`)
      .then(res => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json() as Promise<SurfForecast[]>;
      })
      .then(setForecasts)
      .catch(err => setError(err.message || 'Failed to load'))
      .finally(() => setLoading(false));
  }, [spotId]);

  const grouped = groupByDate(forecasts);

  const formatDateHeader = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString(undefined, {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });

  return (
    <div className="max-w-3xl mx-auto p-4">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-blue-500 underline"
      >
        ← Back
      </button>

      <PageHeader title="10-Day Forecast" />

      {loading && <p>Loading…</p>}
      {error   && <p className="text-red-600">Error: {error}</p>}

      {!loading && !error && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([date, dayForecasts]) => (
            <section key={date}>
              <h2 className="text-xl font-semibold mb-2">
                {formatDateHeader(date)}
              </h2>
              <div className="space-y-2">
                {dayForecasts.map(f => {
                  const [_, timePart] = f.time.split('T');
                  const timeLabel = timePart.slice(0,5);
                  return (
                    <div
                      key={f.time}
                      className="flex justify-between items-center border-b py-2"
                    >
                      <span className="w-1/6 text-sm">{timeLabel}</span>
                      <span className="w-1/6 text-sm capitalize">
                        {f.rating ?? 'N/A'}
                      </span>
                      <span className="w-1/6 text-sm">
                        {f.wave_height_m.toFixed(2)} m
                      </span>
                      <span className="w-1/6 text-sm">
                        {(f.wave_period_s ?? 0).toFixed(1)} s
                      </span>
                      <span className="w-1/6 text-sm">
                        {(f.wind_speed_kmh ?? 0).toFixed(0)} km/h
                      </span>
                      <span className="w-1/6 text-sm capitalize">
                        {f.wind_type ?? 'N/A'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
