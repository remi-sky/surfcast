import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { PrimaryButton } from '../components/PrimaryButton';
import { API_BASE } from '../config';

// Types
interface Location {
  lat: number;
  lon: number;
  name: string;
  region?: string;
  country?: string;
}

interface SurfAlertForm {
  email: string;
  location: Location | null;
  locationQuery: string;
  radiusMiles: number;
  qualityLevels: string[];
}

// Default fallback locations
const defaultLocations: Record<string, Location> = {
  'Europe/London':       { lat: 51.5072, lon: -0.1276, name: 'London, UK', region: 'England', country: 'GB' },
  'America/New_York':    { lat: 40.7128, lon: -74.0060, name: 'New York, US', region: 'New York', country: 'US' },
  'America/Los_Angeles': { lat: 34.0522, lon: -118.2437, name: 'Los Angeles, US', region: 'California', country: 'US' },
  'Europe/Paris':        { lat: 48.8566, lon:   2.3522, name: 'Paris, FR', region: 'Île-de-France', country: 'FR' },
  'Asia/Tokyo':          { lat: 35.6895, lon: 139.6917, name: 'Tokyo, JP', region: 'Tokyo', country: 'JP' },
};

/** OSM geocode helper */
async function geocodeOSM(query: string): Promise<Location> {
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&addressdetails=1`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Geocoding error: ${res.statusText}`);
  const data = await res.json();
  if (!data.length) throw new Error('Location not found');
  const addr = data[0].address || {};
  const locality = addr.city || addr.town || addr.village || addr.county;
  const region = addr.state || addr.region;
  const country = addr.country_code?.toUpperCase();
  const parts = [locality, region, country].filter((x): x is string => Boolean(x));
  const name = parts.join(', ') || data[0].display_name.split(',').slice(0, 3).join(', ');
  
  console.log('Geocoding result for:', query, { locality, region, country, name, addr });
  
  return { lat: +data[0].lat, lon: +data[0].lon, name, region, country };
}

/** Set cookie helper */
function setCookie(name: string, value: string, days: number = 365) {
  const expires = new Date();
  expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

export default function SurfAlertPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<SurfAlertForm>({
    email: '',
    location: null,
    locationQuery: '',
    radiusMiles: 150,
    qualityLevels: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [hasEditedLocation, setHasEditedLocation] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Initialize location only once
  useEffect(() => {
    if (hasInitialized) return;
    setHasInitialized(true);
    
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const def = defaultLocations[tz];
    if (def) {
      setForm(prev => ({ ...prev, location: def, locationQuery: def.name }));
    } else {
      const city = tz.split('/')[1]?.replace(/_/g, ' ') || tz;
      geocodeOSM(city).then(loc => {
        setForm(prev => ({ ...prev, location: loc, locationQuery: loc.name }));
      }).catch(() => {
        const fallback = { lat: 0, lon: 0, name: city, region: '', country: '' };
        setForm(prev => ({ ...prev, location: fallback, locationQuery: city }));
      });
    }
  }, [hasInitialized]);

  const handleLocationSearch = async () => {
    if (!form.locationQuery) return;
    setError(null);
    setLoading(true);
    try {
      const loc = await geocodeOSM(form.locationQuery);
      setForm(prev => ({ ...prev, location: loc, locationQuery: loc.name }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleQuality = (q: string) => {
    setForm(prev => ({
      ...prev,
      qualityLevels: prev.qualityLevels.includes(q)
        ? prev.qualityLevels.filter(x => x !== q)
        : [...prev.qualityLevels, q]
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.location || !form.email || form.qualityLevels.length === 0) {
      setError('Please fill in all required fields and select at least one quality level');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Extract town name from the location data
      const addr = form.location.name.split(', ');
      const town = addr[0]; // First part is the town
      
      const requestData = {
        email: form.email,
        town: town,
        lat: form.location.lat,
        lon: form.location.lon,
        radius_km: form.radiusMiles * 1.60934, // Convert miles to km
        quality_levels: form.qualityLevels,
        region: form.location.region || '',
        country: form.location.country || ''
      };
      
      console.log('Submitting surf alert with data:', requestData);
      
      const response = await fetch(`${API_BASE}/api/alerts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create alert');
      }

      const result = await response.json();
      
      // Store alert_uuid in cookie
      setCookie('alert_uuid', result.alert_uuid);
      
      setSuccess(true);
      
      // Redirect to main page after a short delay
      setTimeout(() => {
        navigate('/');
      }, 2000);
      
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-r from-gradient-start via-gradient-middle to-gradient-end p-4 timeLabel">
        <div className="max-w-3xl mx-auto text-white">
          <PageHeader title="Surf Alert Created!" />
          <div className="bg-white/30 backdrop-blur-lg rounded-2xl shadow-lg p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-semibold mb-4">Your surf alert has been set up successfully!</h2>
            <p className="text-white/80 mb-6">
              We'll notify you when great surf conditions are detected near {form.location?.name.split(', ')[0]}.
            </p>
            <PrimaryButton 
              onClick={() => navigate('/')}
              className="bg-accent-teal text-white px-6 py-3 rounded-lg hover:opacity-90 transition"
            >
              Back to Surf Forecast
            </PrimaryButton>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-gradient-start via-gradient-middle to-gradient-end p-4 timeLabel">
      <div className="max-w-3xl mx-auto text-white">
        <PageHeader title="Set Up Surf Alert" />
        
        <div className="bg-white/30 backdrop-blur-lg rounded-2xl shadow-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-white mb-2">
                Email Address *
              </label>
              <input
                id="email"
                type="email"
                required
                className="w-full px-3 py-2 rounded-lg border border-white text-black"
                placeholder="your@email.com"
                value={form.email}
                onChange={e => setForm(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>

            {/* Location Search */}
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Location *
              </label>
              <div className="flex">
                <input
                  className="flex-1 px-3 py-2 rounded-l-lg border border-white text-black"
                  placeholder="City, town or postcode"
                  value={form.locationQuery}
                  onChange={e => {
                    setForm(prev => ({ ...prev, locationQuery: e.target.value }));
                    setHasEditedLocation(true);
                  }}
                  onFocus={() => {
                    if (!hasEditedLocation) setForm(prev => ({ ...prev, locationQuery: '' }));
                  }}
                  onKeyPress={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleLocationSearch();
                    }
                  }}
                />
                <button 
                  type="button"
                  onClick={handleLocationSearch}
                  className="bg-accent-teal text-white px-4 py-2 rounded-r-lg hover:opacity-90 transition disabled:opacity-50"
                  disabled={loading}
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
              {form.location && (
                <p className="text-sm text-white/80 mt-2">
                  Selected: <strong>{form.location.name.split(', ')[0]}</strong>
                  {form.location.region && `, ${form.location.region}`}
                  {form.location.country && `, ${form.location.country}`}
                </p>
              )}
            </div>

            {/* Search Radius */}
            <div>
              <label htmlFor="radius" className="block text-sm font-medium text-white mb-2">
                Search Radius: {form.radiusMiles} miles
              </label>
              <input
                id="radius"
                type="range"
                min="25"
                max="300"
                step="25"
                className="w-full h-2 bg-white/30 rounded-lg appearance-none cursor-pointer"
                value={form.radiusMiles}
                onChange={e => setForm(prev => ({ ...prev, radiusMiles: parseInt(e.target.value) }))}
              />
              <div className="flex justify-between text-xs text-white/60 mt-1">
                <span>25 mi</span>
                <span>150 mi</span>
                <span>300 mi</span>
              </div>
            </div>

            {/* Quality Levels */}
            <div>
              <label className="block text-sm font-medium text-white mb-3">
                Surf Quality Levels *
              </label>
              <div className="flex items-center flex-wrap gap-3">
                {['Playable', 'Solid', 'Firing'].map(q => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => toggleQuality(q)}
                    className={
                      `px-4 py-2 rounded-full font-medium transition ` +
                      (form.qualityLevels.includes(q)
                        ? 'bg-accent-teal text-white'
                        : 'bg-white/30 text-white/70 hover:bg-white/40')
                    }
                  >
                    {q}
                  </button>
                ))}
              </div>
              <p className="text-xs text-white/60 mt-2">
                Select at least one quality level to receive alerts for
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 text-red-200 p-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                className="flex-1 bg-accent-teal text-white px-6 py-3 rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading || !form.location || !form.email || form.qualityLevels.length === 0}
              >
                {loading ? 'Creating Alert...' : 'Create Surf Alert'}
              </button>
              <PrimaryButton
                onClick={() => navigate('/')}
                className="px-6 py-3 bg-white/30 text-white rounded-lg hover:bg-white/40 transition"
              >
                Cancel
              </PrimaryButton>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
