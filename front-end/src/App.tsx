// src/App.tsx
import React, { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from './components/PageHeader';
import { PrimaryButton } from './components/PrimaryButton';

// Summarized forecast for display
interface SummaryForecast {
  date: string;
  time: string;
  rating: string;
  explanation: string;
}

// Spot metadata + forecasts
interface Spot {
  id: string;
  name: string;
  region: string;
  lat: number;
  lon: number;
  forecasts: SummaryForecast[];
}

// Geocoded location
interface Location {
  lat: number;
  lon: number;
  name: string;
}

// Default fallbacks by IANA timezone
const defaultLocations: Record<string, Location> = {
  'Europe/London':       { lat: 51.5072, lon: -0.1276, name: 'London, UK' },
  'America/New_York':    { lat: 40.7128, lon: -74.0060, name: 'New York, US' },
  'America/Los_Angeles': { lat: 34.0522, lon: -118.2437, name: 'Los Angeles, US' },
  'Europe/Paris':        { lat: 48.8566, lon: 2.3522,   name: 'Paris, FR' },
  'Asia/Tokyo':          { lat: 35.6895, lon: 139.6917, name: 'Tokyo, JP' },
};

/**
 * Geocode a free-text location via OSM Nominatim
 */
async function geocodeOSM(query: string): Promise<Location> {
  const url = `https://nominatim.openstreetmap.org/search` +
              `?q=${encodeURIComponent(query)}` +
              `&format=json&limit=1&addressdetails=1`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Geocoding error: ${res.statusText}`);
  const data = await res.json();
  if (!data.length) throw new Error('Location not found');
  const addr = data[0].address || {};
  const locality    = addr.city || addr.town || addr.village || addr.county;
  const region      = addr.state || addr.region;
  const countryCode = addr.country_code?.toUpperCase();
  const parts: string[] = [];
  if (locality)    parts.push(locality);
  if (region)      parts.push(region);
  if (countryCode) parts.push(countryCode);
  const name = parts.join(', ') || data[0].display_name.split(',').slice(0,3).join(', ');
  return { lat: +data[0].lat, lon: +data[0].lon, name };
}

/**
 * A simple card showing one forecast
 */
const SummaryRow: React.FC<{ forecast: SummaryForecast }> = ({ forecast }) => (
  <div className="p-4 bg-white border border-gray-light rounded-lg mb-2 hover:shadow-md transition-shadow">
    <div className="flex flex-col md:flex-row md:justify-between">
      <div className="mb-2 md:mb-0">
        <span className="font-semibold">{forecast.rating}</span>{' '}
        <span className="text-gray-500 text-sm">
          {forecast.date} @ {forecast.time}
        </span>
      </div>
      <p className="text-gray-700 text-sm">{forecast.explanation}</p>
    </div>
  </div>
);

const App: React.FC = () => {
  const navigate = useNavigate();
  const [spots, setSpots]         = useState<Spot[]>([]);
  const [location, setLocation]   = useState<Location | null>(null);
  const [query, setQuery]         = useState<string>('');
  const [loading, setLoading]     = useState<boolean>(false);
  const [error, setError]         = useState<string | null>(null);

  // 1) Initialize default based on browser timezone
  useEffect(() => {
    if (location) return;
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const def = defaultLocations[tz];
    if (def) {
      setLocation(def);
    } else {
      const city = tz.split('/')[1]?.replace(/_/g, ' ') || tz;
      geocodeOSM(city)
        .then(loc => setLocation(loc))
        .catch(() => setLocation({ lat: 0, lon: 0, name: city }));
    }
  }, [location]);

  // 2) Fetch spots when location is set
  useEffect(() => {
    if (!location) return;
    setLoading(true);
    setError(null);

    fetch(
      `/api/spots/forecasted?lat=${location.lat}&lon=${location.lon}&max_distance_km=500`
    )
      .then(res => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json() as Promise<Spot[]>;
      })
      .then(data => setSpots(data))
      .catch(err => setError(err.message || 'Failed fetching spots'))
      .finally(() => setLoading(false));
  }, [location]);

  // 3) Handle manual search override
  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setError(null);
    try {
      const loc = await geocodeOSM(query);
      setLocation(loc);
    } catch (err: unknown) {
      // Narrow unknown to derive a message
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
    }
  };

  return (
    <div className="min-h-screen bg-white text-gray-700">
      <PageHeader title="Surf Forecast Near You 🏄‍♂️" />

      <div className="px-4">
        {location ? (
          <p className="mb-2">
            Using <strong>{location.name}</strong>
          </p>
        ) : (
          <p className="italic mb-2">Detecting location via timezone…</p>
        )}

        <form onSubmit={handleSearch} className="mb-4 flex">
          <input
            type="text"
            placeholder="Or enter city, town or postcode"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 border border-gray-light rounded-l-lg p-2 focus:outline-none"
          />
          <button
            type="submit"
            className="bg-ocean text-white px-4 rounded-r-lg font-medium"
          >
            Search
          </button>
        </form>

        {loading && <p className="py-4">Loading forecasts…</p>}
        {error   && <p className="text-red-600 py-4">Error: {error}</p>}

        {!loading && !error && spots.map(spot => (
          <div key={spot.id} className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-xl font-semibold">{spot.name}</h2>
              <PrimaryButton onClick={() => navigate(`/spots/${spot.id}/forecast`)}>
                View 10-day forecast
              </PrimaryButton>
            </div>
            {spot.forecasts[0] && (
              <SummaryRow forecast={spot.forecasts[0]} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
