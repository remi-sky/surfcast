// src/App.tsx
import React, { useState, useEffect, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import './index.css';
import { PageHeader } from './components/PageHeader';
import { SummaryRow } from './components/SummaryRow';
import { PrimaryButton } from './components/PrimaryButton';

interface SummaryForecast {
  date: string;
  time: string;
  rating: string;
  explanation: string;
}

interface Spot {
  id: string;
  name: string;
  region: string;
  lat: number;
  lon: number;
  forecasts: SummaryForecast[];
}

interface Location {
  lat: number;
  lon: number;
  name: string;
}

// Haversine formula to compute miles
function getDistanceMiles(
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const R = 6371; // km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat/2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon/2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const km = R * c;
  return km * 0.621371;
}

const defaultLocations: Record<string, Location> = {
  'Europe/London':       { lat: 51.5072, lon: -0.1276, name: 'London, UK' },
  'America/New_York':    { lat: 40.7128, lon: -74.0060, name: 'New York, US' },
  'America/Los_Angeles': { lat: 34.0522, lon: -118.2437, name: 'Los Angeles, US' },
  'Europe/Paris':        { lat: 48.8566, lon: 2.3522,   name: 'Paris, FR' },
  'Asia/Tokyo':          { lat: 35.6895, lon: 139.6917, name: 'Tokyo, JP' },
};

async function geocodeOSM(query: string): Promise<Location> {
  const res = await fetch(
    `https://nominatim.openstreetmap.org/search` +
    `?q=${encodeURIComponent(query)}` +
    `&format=json&limit=1&addressdetails=1`
  );
  if (!res.ok) throw new Error(res.statusText);
  const data = await res.json();
  if (!data.length) throw new Error('Location not found');
  const addr = data[0].address || {};
  const locality = addr.city || addr.town || addr.village || addr.county;
  const region   = addr.state || addr.region;
  const cc       = addr.country_code?.toUpperCase();
  const parts    = [locality, region, cc].filter(Boolean);
  return { lat: +data[0].lat, lon: +data[0].lon, name: parts.join(', ') };
}

export default function App() {
  const navigate = useNavigate();
  const [spots, setSpots]       = useState<Spot[]>([]);
  const [location, setLocation] = useState<Location | null>(null);
  const [query, setQuery]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  // 1) Default location via timezone
  useEffect(() => {
    if (location) return;
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const def = defaultLocations[tz];
    if (def) {
      setLocation(def);
    } else {
      const city = tz.split('/')[1]?.replace(/_/g,' ') || tz;
      geocodeOSM(city)
        .then(setLocation)
        .catch(() => setLocation({ lat: 0, lon: 0, name: city }));
    }
  }, [location]);

  // 2) Fetch & sort spots by distance
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
      .then(data => {
        // sort closest first
        data.sort((a, b) => {
          const da = getDistanceMiles(location.lat, location.lon, a.lat, a.lon);
          const db = getDistanceMiles(location.lat, location.lon, b.lat, b.lon);
          return da - db;
        });
        setSpots(data);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [location]);

  // 3) Manual search
  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setError(null);
    try {
      const loc = await geocodeOSM(query);
      setLocation(loc);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-r from-gradient-start to-gradient-end p-4">
      <PageHeader title="Surf Forecast Near You 🏄‍♂️" />

      <div className="px-2 md:px-6">
        {location ? (
          <p className="mb-2 text-white/90">
            Using <strong>{location.name}</strong>
          </p>
        ) : (
          <p className="italic mb-2 text-white/80">Detecting location…</p>
        )}

        <form onSubmit={handleSearch} className="mb-6 flex">
          <input
            type="text"
            placeholder="Enter city, town or postcode"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="
              flex-1 p-2 rounded-l-lg border border-white/40 
              bg-white/20 text-white placeholder-white/70
              focus:outline-none
            "
          />
          <button
            type="submit"
            className="
              px-4 py-2 rounded-r-lg 
              bg-white/40 text-white font-semibold 
              hover:bg-white/50 transition
            "
          >
            Search
          </button>
        </form>

        {loading && <p className="text-white/90">Loading forecasts…</p>}
        {error   && <p className="text-red-400 mb-4">{error}</p>}

        {!loading && !error && spots.map(spot => {
          const miles = getDistanceMiles(location!.lat, location!.lon, spot.lat, spot.lon);
          return (
            <div key={spot.id} className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-semibold text-white drop-shadow-lg">
                    {spot.name}
                  </h2>
                  <span className="text-sm text-white/80 ml-1">
                    ({miles.toFixed(1)} mi)
                  </span>
                </div>
                <PrimaryButton
                  onClick={() => navigate(`/spots/${spot.id}/forecast`)}
                  className="
                    text-sm px-3 py-1 
                    bg-accent-teal/80 text-white font-semibold 
                    hover:bg-accent-teal/90 transition
                  "
                >
                  View 10-day
                </PrimaryButton>
              </div>
              {spot.forecasts[0] && (
                <SummaryRow forecast={spot.forecasts[0]} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
