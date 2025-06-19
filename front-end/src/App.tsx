// src/App.tsx
import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from './components/PageHeader';
import { PrimaryButton } from './components/PrimaryButton';
import { API_BASE } from './config';

// Types
interface SummaryForecast {
  date: string;
  time: string;
  rating: string;
  explanation: string;
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
  const [qualityFilter,setQualityFilter]=useState<string[]>(['Fair','Good','Excellent']);

  // init location
  useEffect(()=>{
    if(location) return;
    const tz=Intl.DateTimeFormat().resolvedOptions().timeZone;
    const def=defaultLocations[tz];
    if(def) setLocation(def);
    else{const city=tz.split('/')[1]?.replace(/_/g,' ')||tz;
      geocodeOSM(city).then(setLocation).catch(()=>setLocation({lat:0,lon:0,name:city}));
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
    e.preventDefault();if(!query) return;setError(null);
    try{const loc=await geocodeOSM(query);setLocation(loc);}catch(err:unknown){setError(err instanceof Error ? err.message : String(err));}
  };

  const toggleQuality=(q:string)=>{
    setQualityFilter(qv=>qv.includes(q)?qv.filter(x=>x!==q):[...qv,q]);
  };

  return(
    <div className="min-h-screen bg-gradient-to-r from-gradient-start to-gradient-end p-4">
      <PageHeader title="Surf Opportunities 🏄‍♂️" />
      <div className="px-4 text-white">
        {location? <p className="mb-2">Closest to <strong>{location.name}</strong></p>:
          <p className="italic mb-2">Detecting location…</p>}

        {/* Search */}
        <form onSubmit={handleSearch} className="flex mb-4">
          <input
            className="flex-1 px-3 py-2 rounded-l-lg border border-white text-black"
            placeholder="City, town or postcode"
            value={query} onChange={e=>setQuery(e.target.value)}
          />
          <PrimaryButton
            className="bg-accent-teal text-white px-4 py-2 rounded-r-lg"
          >
            Search
          </PrimaryButton>
        </form>

        {/* Quality toggles */}
        <div className="flex space-x-2 mb-6">
          {['Fair','Good','Excellent'].map(q=>(
            <button
              key={q}
              onClick={()=>toggleQuality(q)}
              className={
                `px-3 py-1 rounded-full text-sm font-medium transition `+
                (qualityFilter.includes(q)
                  ? 'bg-accent-teal text-white'
                  : 'bg-white/30 text-white/70')
              }
            >{q}</button>
          ))}
        </div>

        {loading && <p className="py-4">Loading forecasts…</p>}
        {error && <p className="text-red-400">Error: {error}</p>}

        {/* Spot cards */}
        <div className="space-y-8">
          {spots.map(spot=>{
            const filtered=spot.forecasts.filter(f=>qualityFilter.includes(f.rating));
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
                {Object.entries(groups).map(([date,items])=>(
                  <div key={date} className="mb-4">
                    <h3 className="font-semibold text-white">
                      {new Date(date).toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'})}
                    </h3>
                    <ul className="pl-4">
                      {items.map(f=>(
                        <li key={f.time} className="text-sm text-white/90 mb-1">
                          <span className="font-medium capitalize">{f.rating}</span> — {f.explanation}
                        </li>
                      ))}
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
