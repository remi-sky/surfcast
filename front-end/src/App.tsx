// src/App.tsx
import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from './components/PageHeader';
import { PrimaryButton } from './components/PrimaryButton';
import { API_BASE } from './config';
import { SwellArrow } from './components/SwellArrow';

// Types
interface SummaryForecast {
  date: string;
  time: string;
  rating: 'Lake Mode' | 'Sketchy' | 'Playable' | 'Solid' | 'Firing';
  explanation: string;
  swell_wave_height: number;
  swell_wave_peak_period?: number;
  swell_wave_direction?: number;
  wind_speed_kmh?: number;
  wind_type?: string;
  wind_severity?: string;
}

interface Spot {
  id: string;
  name: string;
  lat: number;
  lon: number;
  forecasts: SummaryForecast[];
  distance: number;
}
interface Location {
  lat: number;
  lon: number;
  name: string;
}

// Default fallback locations
const defaultLocations: Record<string, Location> = {
  'Europe/London':       { lat: 51.5072, lon: -0.1276, name: 'London, UK' },
  'America/New_York':    { lat: 40.7128, lon: -74.0060, name: 'New York, US' },
  'America/Los_Angeles': { lat: 34.0522, lon: -118.2437, name: 'Los Angeles, US' },
  'Europe/Paris':        { lat: 48.8566, lon:   2.3522, name: 'Paris, FR' },
  'Asia/Tokyo':          { lat: 35.6895, lon: 139.6917, name: 'Tokyo, JP' },
};

/** Haversine for miles */
function getDistanceMiles(lat1:number,lon1:number,lat2:number,lon2:number):number{
  const toRad=(d:number)=>(d*Math.PI)/180;
  const R=6371;
  const dLat=toRad(lat2-lat1), dLon=toRad(lon2-lon1);
  const a=Math.sin(dLat/2)**2+Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLon/2)**2;
  const c=2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
  return R*c*0.621371;
}

/** OSM geocode helper */
async function geocodeOSM(query:string):Promise<Location>{
  const url=`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1&addressdetails=1`;
  const res=await fetch(url);
  if(!res.ok) throw new Error(`Geocoding error: ${res.statusText}`);
  const data=await res.json();
  if(!data.length) throw new Error('Location not found');
  const addr=data[0].address||{};
  const locality=addr.city||addr.town||addr.village||addr.county;
  const region=addr.state||addr.region;
  const country=addr.country_code?.toUpperCase();
  // Only keep the defined strings, no `any` needed
  const parts = [locality, region, country].filter((x): x is string => Boolean(x));
  const name=parts.join(', ')||data[0].display_name.split(',').slice(0,3).join(', ');
  return{lat:+data[0].lat,lon:+data[0].lon,name};
}

export default function App(){
  const navigate=useNavigate();
  const [spots,setSpots]=useState<Spot[]>([]);
  const [location,setLocation]=useState<Location|null>(null);
  const [query,setQuery]=useState('');
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [hasEditedQuery, setHasEditedQuery] = useState(false);
  const [qualityFilter, setQualityFilter] = useState<string[]>([]);

  // init location
  useEffect(()=>{
  if(location) return;
  const tz=Intl.DateTimeFormat().resolvedOptions().timeZone;
  const def=defaultLocations[tz];
  if(def) {
  setLocation(def);
  setQuery(def.name); // <-- add this line
  } else {
  const city=tz.split('/')[1]?.replace(/_/g,' ')||tz;
  geocodeOSM(city).then(loc => {
    setLocation(loc);
    setQuery(loc.name); // <-- add this line
  }).catch(() => {
    const fallback = {lat:0,lon:0,name:city};
    setLocation(fallback);
    setQuery(city); // <-- add this line
  });
}
  },[location]);

  // fetch and sort
  useEffect(()=>{
    if(!location) return;
    setLoading(true);setError(null);
    fetch(`${API_BASE}/api/spots/forecasted?lat=${location.lat}&lon=${location.lon}&max_distance_km=500`)
      .then(r=>r.ok?r.json() as Promise<Spot[]>:Promise.reject(r.statusText))
      .then(data=>{
        const aug=data.map(s=>({
          ...s,
          distance:getDistanceMiles(location.lat,location.lon,s.lat,s.lon),
        }));
        aug.sort((a,b)=>a.distance-b.distance);
        setSpots(aug);
      })
      .catch(e=>setError(String(e)))
      .finally(()=>setLoading(false));
  },[location]);


  const handleSearch=async(e:FormEvent)=>{
    e.preventDefault();
    if(!query) return;
    setError(null);
    try {
      const loc = await geocodeOSM(query);
      setLocation(loc);
      setQuery(loc.name); // <-- add this line
    } catch(err:unknown){
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const toggleQuality=(q:string)=>{
    setQualityFilter(qv=>qv.includes(q)?qv.filter(x=>x!==q):[...qv,q]);
  };
  

  return(
  <div className="min-h-screen bg-gradient-to-r from-gradient-start via-gradient-middle to-gradient-end p-4 text-white">
  <div className="max-w-3xl mx-auto">
    <PageHeader title="Surf more, with less planning" />

    {location ? (
      <p className="mb-2 px-4">Find surfable spots around you, up to 10 days ahead</p>
    ) : (
      <p className="italic mb-2 px-4">Detecting location…</p>
    )}

    {/* Search */}
    <form onSubmit={handleSearch} className="flex px-4 mb-4">
      <input
        className="flex-1 px-3 py-2 rounded-l-lg border border-white text-black"
        placeholder="City, town or postcode"
        value={query}
        onChange={e => {
          setQuery(e.target.value);
          setHasEditedQuery(true);
        }}
        onFocus={() => {
          if (!hasEditedQuery) setQuery('');
        }}
      />
      <PrimaryButton className="bg-accent-teal text-white px-4 py-2 rounded-r-lg">
        Search
      </PrimaryButton>
    </form>

    {/* Surf Quality Filter */}
    <div className="mb-6 px-4">
      <p className="text-white/80 text-sm mb-1">Show results by surf potential</p>
      <div className="flex space-x-2">
        {['Playable', 'Solid', 'Firing'].map(q => (
          <button
            key={q}
            onClick={() => toggleQuality(q)}
            className={
              `px-3 py-1 rounded-full text-sm font-medium transition ` +
              (qualityFilter.includes(q)
                ? 'bg-accent-teal text-white'
                : 'bg-white/30 text-white/70')
            }
          >
            {q}
          </button>
        ))}
      </div>
    </div>

    {/* Results */}
    <div className="space-y-8 px-4">
      {spots.filter(spot => {
        const forecasts = qualityFilter.length
          ? spot.forecasts.filter(f => qualityFilter.includes(f.rating))
          : spot.forecasts;
        return forecasts.length > 0;
      }).length === 0 && (
        <div className="bg-white/10 text-white/80 text-sm text-center p-4 rounded-xl">
          No sessions match your current filter.
        </div>
      )}          
      
            {spots.map(spot=>{
              const filtered = qualityFilter.length
                ? spot.forecasts.filter(f => qualityFilter.includes(f.rating))
                : spot.forecasts;

              if(!filtered.length) return null;

              // group by date
              const groups: Record<string,SummaryForecast[]> = {};
              filtered.forEach(f=>{(groups[f.date]||(groups[f.date]=[])).push(f);});

              return(
                <div key={spot.id} className="relative p-6 bg-white/30 backdrop-blur-lg rounded-2xl shadow-lg">
                  <div className="flex justify-between items-baseline mb-3">
                    <h2 className="text-xl font-semibold text-white drop-shadow">
                      {spot.name} <span className="text-sm font-normal">({spot.distance.toFixed(1)} mi)</span>
                    </h2>
                  </div>

                  {/* forecast groups */}
                  {Object.entries(groups).map(([date,items])=> (
                    <div key={date} className="mb-4">
                      <h3 className="font-semibold text-white mb-2 border-b border-white/20 pb-1">
                        {new Date(date).toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'})}
                      </h3>
                      <ul className="space-y-2">
                        {items.map(f=> {
                          const arrowDeg = f.swell_wave_direction ?? 0;
                          const datetimeStr = `${date}T${f.time}`;
                          const timeLabel = new Date(datetimeStr).toLocaleTimeString(undefined, {                            hour: 'numeric',
                            hour12: true,
                          });
                          return (
                            <li key={f.time} className="p-3 rounded-lg bg-white/10 text-white/90 space-y-1">
                            <div className="flex items-center gap-2">
                              <div className="text-sm text-white/90">
                                {timeLabel}
                              </div>
                              <div className="text-xs px-2 py-0.5 rounded-full bg-white/10 border border-white/20 text-white/90">
                                {f.rating}
                              </div>
                            </div>
                              <div className="flex items-center gap-2 text-sm">
                            <span>🌊</span>
                                <span>
                                  {f.swell_wave_height.toFixed(2)}m @ {f.swell_wave_peak_period?.toFixed(1) ?? '?'}s
                                </span>
                                <SwellArrow direction={arrowDeg} />
                              </div>
                              <div className="flex items-center gap-2 text-sm">
                                <span>💨</span>
                                <span>
                                  {f.wind_speed_kmh?.toFixed(0) ?? '?'} km/h {f.wind_type}
                                  {f.wind_type !== 'glassy' && f.wind_severity ? `, ${f.wind_severity}` : ''}
                                </span>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}

                  <div className="flex justify-end mt-4">
                    <PrimaryButton onClick={() => navigate(`/spots/${spot.id}/forecast`)} className="px-3 py-1 bg-accent-teal text-white rounded-full text-sm hover:opacity-90 transition">
                      View Forecast
                    </PrimaryButton>
                  </div>
                </div>
              );
            })}
          </div>

      </div>
      </div>
  );
};