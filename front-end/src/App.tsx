import React, { useState, useEffect, FormEvent } from 'react';
import { Link } from 'react-router-dom';

interface Forecast {
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
  forecasts: Forecast[];
}

interface Location {
  lat: number;
  lon: number;
  name: string;
}

// Mapping from IANA time zones to default locations
const defaultLocations: Record<string, Location> = {
  'Europe/London': { lat: 51.5072, lon: -0.1276, name: 'London, UK' },
  'America/New_York': { lat: 40.7128, lon: -74.0060, name: 'New York, US' },
  'America/Los_Angeles': { lat: 34.0522, lon: -118.2437, name: 'Los Angeles, US' },
  'Europe/Paris': { lat: 48.8566, lon: 2.3522, name: 'Paris, FR' },
  'Asia/Tokyo': { lat: 35.6895, lon: 139.6917, name: 'Tokyo, JP' },
};

// Geocode user query to lat/lon + structured display name via OSM Nominatim
const geocodeOSM = async (query: string): Promise<Location> => {
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&addressdetails=1`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Geocoding error: ${res.statusText}`);
  const data = await res.json();
  if (!data.length) throw new Error('Location not found');
  const addr = data[0].address || {};
  // Choose city-like field
  const locality = addr.city || addr.town || addr.village || addr.hamlet || addr.county;
  const region = addr.state || addr.region || addr.province;
  const countryCode = addr.country_code ? addr.country_code.toUpperCase() : undefined;
  const parts = [] as string[];
  if (locality) parts.push(locality);
  if (region) parts.push(region);
  if (countryCode) parts.push(countryCode);
  const name = parts.join(', ') || data[0].display_name.split(',').slice(0,3).join(', ');
  return {
    lat: parseFloat(data[0].lat),
    lon: parseFloat(data[0].lon),
    name,
  };
};

// Compute distance in miles between two coords
const haversineMiles = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const toRad = (x: number) => (x * Math.PI) / 180;
  const R = 6371; // Earth's radius in km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distanceKm = R * c;
  return distanceKm * 0.621371; // convert to miles
};

// Format date+time as "Tuesday, 5 June 2025 @ 19:00"
const formatDateTime = (dateStr: string, timeStr: string): string => {
  const dt = new Date(`${dateStr}T${timeStr}`);
  const dateOpts: Intl.DateTimeFormatOptions = {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  };
  const formattedDate = dt.toLocaleDateString(undefined, dateOpts);
  const formattedTime = dt.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  return `${formattedDate} @ ${formattedTime}`;
};

const App: React.FC = () => {
  const [spots, setSpots] = useState<(Spot & { distanceMiles: number })[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<string>('');
  const [location, setLocation] = useState<Location | null>(null);

  // Initialize default location based on browser time zone
  useEffect(() => {
    if (location) return;
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const defaultLoc = defaultLocations[tz];
    if (defaultLoc) {
      setLocation(defaultLoc);
    } else {
      const city = tz.split('/')[1]?.replace(/_/g, ' ') || tz;
      geocodeOSM(city)
        .then(loc => setLocation(loc))
        .catch(() => setLocation({ lat: 0, lon: 0, name: city }));
    }
  }, [location]);

  // Fetch surf spots whenever location changes
  useEffect(() => {
    if (!location) return;
    const fetchSpots = async () => {
      setLoading(true);
      setError(null);
      try {
        const { lat, lon } = location;
        const res = await fetch(
          `/api/spots/forecasted?lat=${lat}&lon=${lon}&max_distance_km=500`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: Spot[] = await res.json();
        const enriched = data.map(spot => ({
          ...spot,
          distanceMiles: haversineMiles(lat, lon, spot.lat, spot.lon),
        }));
        enriched.sort((a, b) => a.distanceMiles - b.distanceMiles);
        setSpots(enriched);
      } catch (err: any) {
        console.error(err);
        setError(err.message || 'Failed fetching forecasts');
      } finally {
        setLoading(false);
      }
    };
    fetchSpots();
  }, [location]);

  // Handle manual override geocoding
  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setError(null);
    try {
      const loc = await geocodeOSM(query);
      setLocation(loc);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Geocoding failed');
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Surf Forecast 🏄‍♂️</h1>

      {location ? (
        <p className="mb-2">
          Closest to <strong>{location.name}</strong>
        </p>
      ) : (
        <p className="italic">Detecting location from timezone…</p>
      )}

      <form onSubmit={handleSearch} className="mb-4">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Or enter city, town or postcode"
          className="border p-2 rounded w-full mb-2"
        />
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Search
        </button>
      </form>

      {loading && <div className="p-4">Loading forecasts...</div>}
      {error && <div className="text-red-600 mb-4">Error: {error}</div>}

      {location && !loading && !error && (
        <div>
          {spots.length === 0 ? (
            <p>No spots found within range.</p>
          ) : (
            spots.map(spot => (
              <div key={spot.id} className="border rounded-lg p-4 mb-4 shadow-sm">
                <div className="flex justify-between items-center mb-1">
                  <h2 className="text-xl font-semibold">
                    {spot.name} <span className="text-gray-500">({spot.region})</span>
                  </h2>
                  <Link
                    to={`/spots/${spot.id}/forecast`}
                    className="text-blue-500 underline text-sm"
                  >
                    View 10-day forecast
                  </Link>
                </div>
                <p className="text-gray-500 mb-2">
                  {spot.distanceMiles.toFixed(1)} mi away
                </p>
                <ul className="list-disc list-inside">
                  {spot.forecasts.map(f => (
                    <li key={`${spot.id}-${f.date}-${f.time}`} className="mb-1">
                      <span className="font-medium">
                        {formatDateTime(f.date, f.time)}
                      </span> — <span className="capitalize">{f.rating}</span>: {f.explanation}
                    </li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default App;
