import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { MapPin, Navigation, Tag, ArrowRight } from 'lucide-react';

// Helper component to smoothly re-center map when points change
function ChangeView({ center, zoom }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

export default function BangladeshPriceMap({ spatialData, commodityName = 'Onion (Local)', unit = 'kg' }) {
  const [activeDistrict, setActiveDistrict] = useState(null);

  const defaultCenter = [23.8103, 90.4125]; // Dhaka center
  const districts = spatialData?.districts || [];
  const markets = spatialData?.markets || [];
  const spreadSummary = spatialData?.spread_summary || {};

  const getMarkerColor = (price, minP, maxP) => {
    if (!price || minP === maxP) return '#3b82f6';
    if (price === minP) return '#10b981'; // Green (Cheapest)
    if (price === maxP) return '#ef4444'; // Red (Highest)
    return '#f59e0b'; // Amber (Mid)
  };

  const minPrice = spreadSummary.cheapest_price || 0;
  const maxPrice = spreadSummary.highest_price || 0;

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-bold text-white font-outfit flex items-center gap-2">
            <MapPin className="w-5 h-5 text-emerald-400" />
            Inter-District Spatial Dispersion & Geo-Spread
          </h3>
          <p className="text-xs text-slate-400">
            OpenStreetMap geospatial distribution for <strong className="text-slate-200">{commodityName}</strong> across reporting market nodes.
          </p>
        </div>

        {/* Spread KPI Pill */}
        {spreadSummary.absolute_spread_bdt && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs">
            <span className="text-slate-400">Spatial Spread:</span>
            <span className="font-bold text-white font-outfit">BDT {spreadSummary.absolute_spread_bdt.toFixed(2)}</span>
            <span className="text-amber-400 font-semibold">({spreadSummary.percentage_spread}%)</span>
          </div>
        )}
      </div>

      {/* Cheapest vs Highest Market Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">Cheapest Market Node</span>
            <span className="text-sm font-bold text-white">{spreadSummary.cheapest_market || 'Karwan Bazar (Dhaka)'}</span>
          </div>
          <div className="text-base font-bold text-emerald-400 font-outfit">
            BDT {spreadSummary.cheapest_price ? spreadSummary.cheapest_price.toFixed(2) : 'N/A'}/{unit}
          </div>
        </div>

        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">Highest Market Node</span>
            <span className="text-sm font-bold text-white">{spreadSummary.highest_market || 'Chaldal Online Hub (Dhaka)'}</span>
          </div>
          <div className="text-base font-bold text-rose-400 font-outfit">
            BDT {spreadSummary.highest_price ? spreadSummary.highest_price.toFixed(2) : 'N/A'}/{unit}
          </div>
        </div>
      </div>

      {/* Leaflet Map Frame */}
      <div className="h-96 w-full rounded-xl overflow-hidden border border-slate-700/80 relative">
        <MapContainer
          center={defaultCenter}
          zoom={7}
          scrollWheelZoom={false}
          className="z-0"
        >
          <ChangeView center={defaultCenter} zoom={7} />
          {/* OpenStreetMap standard tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Render Markets as high-precision glowing circle markers */}
          {markets.map((m) => {
            if (!m.latitude || !m.longitude) return null;
            const color = getMarkerColor(m.avg_price, minPrice, maxPrice);

            return (
              <CircleMarker
                key={`mkt-${m.market_id}`}
                center={[m.latitude, m.longitude]}
                radius={10}
                fillColor={color}
                color="#ffffff"
                weight={2}
                opacity={1}
                fillOpacity={0.85}
              >
                <Popup>
                  <div className="p-1 text-slate-100 text-xs">
                    <p className="font-bold text-sm text-white mb-1">{m.market_name}</p>
                    <p className="text-slate-300 mb-1">
                      {m.district}, {m.division} ({m.market_type})
                    </p>
                    <div className="pt-1 border-t border-slate-700 flex justify-between gap-4 font-mono">
                      <span>Observed Price:</span>
                      <strong className="text-emerald-400">BDT {m.avg_price.toFixed(2)}/{unit}</strong>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
