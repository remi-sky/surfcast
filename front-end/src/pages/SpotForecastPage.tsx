// src/pages/SpotForecastPage.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { SurfForecast } from '../types';
import { API_BASE } from '../config';
import { PageHeader } from '../components/PageHeader';
import { SwellArrow } from '../components/SwellArrow';

interface SurfSpot {
  id: string;
  name: string;
  lat: number | null;
  lon: number | null;
  facing_direction: number | null;
  swell_min_m: number | null;
  swell_dir_min: number | null;
  swell_dir_max: number | null;
  preferred_wind_wave_max_m: number | null;
  best_swell_dir_label: string | null;
  best_wind_dir_label: string | null;
  post_code: string | null;
  town: string | null;
  region: string | null;
  surf_benchmark_url: string | null;
  image_url: string | null;
  image_credit: string | null;
  image_credit_url: string | null;
  image_source_url: string | null;
  timezone: string | null;
}

type Params = { spotId: string };

const groupByDate = (forecasts: SurfForecast[]) =>
  forecasts.reduce<Record<string, SurfForecast[]>>((acc, f) => {
    const date = f.time.split('T')[0];
    (acc[date] ||= []).push(f);
    return acc;
  }, {});

const ratingColors: Record<string, string> = {
  'Lake Mode': 'bg-white text-gray-700',
  Sketchy: 'bg-yellow-500 text-white',
  Playable: 'bg-blue-400 text-white',
  Solid: 'bg-purple-600 text-white',
  Firing: 'bg-red-600 text-white',
};

export default function SpotForecastPage() {
  const { spotId } = useParams<Params>();
  const navigate = useNavigate();

  const [forecasts, setForecasts] = useState<SurfForecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [spotDetails, setSpotDetails] = useState<any>(null);


  useEffect(() => {
    if (!spotId) return;
    setLoading(true);
    setError(null);
    // Fetch the 10-day forecast for the spot
    fetch(`${API_BASE}/api/spots/${spotId}/forecasts?days=10`)
      .then(res => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json() as Promise<SurfForecast[]>;
      })
      .then(setForecasts)
      .catch(err => setError(err.message || 'Failed to load'))
      .finally(() => setLoading(false));

    // Fetch the spot details
    fetch(`${API_BASE}/api/spots/${spotId}`)
      .then(res => res.ok ? res.json() as Promise<SurfSpot> : Promise.reject(res.statusText))
      .then(setSpotDetails)
      .catch(err => console.error('Error fetching spot info:', err));
  }, [spotId]);

  const grouped = groupByDate(forecasts);

  const formatDateHeader = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString(undefined, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    });

  const [selectedRatings, setSelectedRatings] = useState<string[]>([]);

  const toggleRating = (rating: string) => {
  setSelectedRatings(prev =>
    prev.includes(rating)
      ? prev.filter(r => r !== rating)
      : [...prev, rating]
    );
  };


  return (
  <div className="min-h-screen bg-gradient-to-r from-gradient-start via-gradient-middle to-gradient-end p-4">
    <div className="max-w-3xl mx-auto p-4">
      <div className="mb-2">
        <button onClick={() => navigate(-1)} className="text-sm text-white underline">
          ← Back
        </button>
      </div>


      {spotDetails && (
        
         <>
              <PageHeader title={`${spotDetails.name} – Forecast`} />

         </>
    )}

      <div className="mb-4">
            <p className="text-white/80 text-sm mb-1">Filter by Surf Potential</p>
            <div className="flex gap-2">
              {['Playable', 'Solid', 'Firing'].map(label => (
                <button
                  key={label}
                  onClick={() => toggleRating(label)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                    selectedRatings.includes(label)
                      ? 'bg-accent-teal text-white'
                      : 'bg-white/20 text-white hover:bg-white/30'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
     </div>


      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">Error: {error}</p>}

      {!loading && !error && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([date, dayForecasts]) => {
            const filteredForecasts = selectedRatings.length
              ? dayForecasts.filter(f => selectedRatings.includes(f.rating))
              : dayForecasts;
            return (
            <section key={date} className="bg-white/10 rounded-xl p-4">
              <h2 className="text-lg font-semibold text-white mb-3 border-b border-white/30 pb-1">
                {formatDateHeader(date)}
              </h2>

            <div className="space-y-4">
              {filteredForecasts.map(f => {
                const [, timePart] = f.time.split('T');
                const hour = parseInt(timePart.slice(0, 2));
                const minutes = timePart.slice(3, 5);
                const ampmHour = ((hour + 11) % 12 + 1); // converts 0–23 to 1–12
                const period = hour < 12 ? 'am' : 'pm';
                const timeLabel = `${ampmHour}:${minutes} ${period}`;

                const swell = `${f.swell_wave_height.toFixed(2)}m @ ${f.swell_wave_peak_period?.toFixed(1) ?? '?'}s`;
                const wind = `${f.wind_speed_kmh?.toFixed(0) ?? '?'} km/h ${f.wind_type}${f.wind_type !== 'glassy' && f.wind_severity ? `, ${f.wind_severity}` : ''}`;

                return (
                  <div key={f.time} className="p-3 rounded-lg bg-white/10 text-white/90 space-y-1">
  <div className="flex justify-between items-center">
    <div className="text-sm font-semibold">{timeLabel}</div>
    <div className="text-xs px-2 py-0.5 rounded-full bg-white/20 text-white">
      {f.rating}
    </div>
  </div>
  <div className="flex items-center gap-2 text-sm">
    <span>🌊</span>
    <span>
      {f.swell_wave_height.toFixed(2)}m @ {f.swell_wave_peak_period?.toFixed(1) ?? '?'}s
    </span>
    <SwellArrow direction={f.swell_wave_direction ?? 0} />
  </div>
  <div className="flex items-center gap-2 text-sm">
    <span>💨</span>
    <span>
      {f.wind_speed_kmh?.toFixed(0) ?? '?'} km/h {f.wind_type}
      {f.wind_type !== 'glassy' && f.wind_severity ? `, ${f.wind_severity}` : ''}
    </span>
  </div>
</div>

                );
              })}
            </div>
          </section>


            );
          })}
        </div>
      )}
    </div>
  </div>
);
}
