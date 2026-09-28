import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, Tooltip as LeafletTooltip, Polyline } from 'react-leaflet';
import { MapPin, Navigation, Tag, ArrowRight, Truck, TrendingUp, Layers, X, Clock, ShieldCheck, AlertTriangle } from 'lucide-react';
import { getSpatialArbitrage } from '../api/endpoints';

// Helper component to smoothly re-center map when points change
function ChangeView({ center, zoom }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

// Compute distance from Dhaka in km
function calculateDistanceDhaka(lat, lon) {
  if (!lat || !lon) return 0;
  const dhakaLat = 23.8103;
  const dhakaLon = 90.4125;
  const R = 6371; // km
  const dLat = (lat - dhakaLat) * (Math.PI / 180);
  const dLon = (lon - dhakaLon) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(dhakaLat * (Math.PI / 180)) * Math.cos(lat * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 1.25); // road circuity factor
}

export default function BangladeshPriceMap({ spatialData, commodityName = 'Onion (Local)', unit = 'kg' }) {
  const [arbitrageData, setArbitrageData] = useState(null);
  const [showCorridors, setShowCorridors] = useState(true);
  const [activeCorridor, setActiveCorridor] = useState(null);

  const defaultCenter = [23.8103, 90.4125]; // Dhaka center

  // Fetch arbitrage freight opportunities
  useEffect(() => {
    if (spatialData?.commodity_id) {
      getSpatialArbitrage(spatialData.commodity_id)
        .then((data) => setArbitrageData(data))
        .catch((err) => console.error('Arbitrage fetch error:', err));
    }
  }, [spatialData?.commodity_id]);

  if (!spatialData) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium text-slate-300">জেলাভিত্তিক বাজার তথ্য লোড হচ্ছে...</p>
        <p className="text-xs text-slate-500 mt-1">Loading 64-district spatial market telemetry...</p>
      </div>
    );
  }

  const districts = spatialData?.districts || [];
  const markets = spatialData?.markets || [];
  const spreadSummary = spatialData?.spread_summary || {};
  const geojsonFeatures = spatialData?.geojson_feature_collection?.features || [];

  const minPrice = spreadSummary.cheapest_price || 0;
  const maxPrice = spreadSummary.highest_price || 0;

  const getMarkerColor = (price, minP, maxP) => {
    if (!price || minP === maxP) return '#3b82f6';
    const ratio = (price - minP) / (maxP - minP || 1);
    if (ratio < 0.33) return '#10b981'; // Green (Low / Surplus)
    if (ratio < 0.66) return '#f59e0b'; // Amber (Normal)
    return '#ef4444'; // Red (High / Deficit)
  };

  const getCorridorColor = (feasibility) => {
    if (feasibility === 'Highly Feasible') return '#10b981'; // Emerald
    if (feasibility === 'Marginal') return '#f59e0b'; // Amber
    return '#f43f5e'; // Rose / Red
  };

  return (
    <div className="space-y-4 mb-6">
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-white font-outfit flex items-center gap-2">
              <MapPin className="w-5 h-5 text-emerald-400" />
              64-District National Geospatial Price Map
            </h3>
            <p className="text-xs text-slate-400">
              Administrative spatial coverage across 8 Divisions and 64 Districts for <strong className="text-slate-200">{commodityName}</strong>.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Show Transit Corridors Toggle Switch */}
            <button
              type="button"
              id="toggle-transit-corridors-btn"
              onClick={() => setShowCorridors(!showCorridors)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                showCorridors
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm'
                  : 'bg-slate-900/90 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              <Truck className={`w-3.5 h-3.5 ${showCorridors ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>Show Transit Corridors (পরিবহন করিডোর)</span>
              <span className={`w-2 h-2 rounded-full ${showCorridors ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
            </button>

            {/* Spatial Price Dispersion Index D(t) Pill */}
            {spreadSummary.spatial_dispersion_index !== undefined && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-xs">
                <span className="text-indigo-300">Dispersion Index D(t):</span>
                <span className="font-bold text-indigo-200 font-mono">
                  {spreadSummary.spatial_dispersion_index.toFixed(4)}
                </span>
                <span className="text-[10px] text-indigo-400">
                  (CV: {((spreadSummary.spatial_dispersion_index || 0) * 100).toFixed(1)}%)
                </span>
              </div>
            )}

            {spreadSummary.absolute_spread_bdt !== undefined && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs">
                <span className="text-slate-400">Spread:</span>
                <span className="font-bold text-white font-outfit">BDT {spreadSummary.absolute_spread_bdt.toFixed(2)}</span>
                <span className="text-amber-400 font-semibold">({spreadSummary.percentage_spread}%)</span>
              </div>
            )}
          </div>
        </div>

        {/* Cheapest vs Highest Market Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">Cheapest Node (Surplus)</span>
              <span className="text-sm font-bold text-white">{spreadSummary.cheapest_market || 'Karwan Bazar (Dhaka)'}</span>
            </div>
            <div className="text-base font-bold text-emerald-400 font-outfit">
              BDT {spreadSummary.cheapest_price ? spreadSummary.cheapest_price.toFixed(2) : 'N/A'}/{unit}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">Highest Node (Deficit)</span>
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
            className="z-0 h-full w-full"
          >
            <ChangeView center={defaultCenter} zoom={7} />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Interactive Highway Transit Corridors Polylines */}
            {showCorridors && arbitrageData?.routes?.map((route, rIdx) => {
              if (!route.waypoints || route.waypoints.length < 2) return null;
              const isSelected = activeCorridor?.corridor_name === route.corridor_name ||
                (activeCorridor?.source_district === (route.source_district || route.origin_district) &&
                 activeCorridor?.destination_district === route.destination_district);
              const color = getCorridorColor(route.economic_feasibility);
              const weight = isSelected ? 6 : (route.economic_feasibility === 'Highly Feasible' ? 4 : 3);
              const opacity = isSelected ? 1.0 : (route.economic_feasibility === 'Highly Feasible' ? 0.85 : 0.7);
              const dashArray = route.economic_feasibility === 'Infeasible (Transport Barrier)' ? '5, 8' : (route.economic_feasibility === 'Marginal' ? '6, 6' : undefined);

              return (
                <Polyline
                  key={`corridor-${rIdx}-${route.source_district || route.origin_district}`}
                  positions={route.waypoints}
                  pathOptions={{
                    color,
                    weight,
                    opacity,
                    dashArray,
                  }}
                  eventHandlers={{
                    click: () => setActiveCorridor(route),
                  }}
                >
                  <LeafletTooltip sticky>
                    <div className="p-1 font-sans text-xs">
                      <div className="font-bold text-slate-900">{route.corridor_name || `${route.source_district || route.origin_district} ➔ ${route.destination_district}`}</div>
                      <div className="text-[11px] text-slate-600 mt-0.5">
                        দূরত্ব: {route.distance_km} km • সময়: ~{route.transit_hours_estimated || (route.distance_km / 45 + 1).toFixed(1)}h
                      </div>
                      <div className="mt-1 flex items-center justify-between gap-3 font-semibold">
                        <span className="text-slate-700">নিট মার্জিন:</span>
                        <span className={route.net_arbitrage_margin_bdt > 0 ? 'text-emerald-700 font-bold' : 'text-rose-700'}>
                          {route.net_arbitrage_margin_bdt > 0 ? `+৳${route.net_arbitrage_margin_bdt.toFixed(2)}` : `৳${route.net_arbitrage_margin_bdt.toFixed(2)}`}/{unit}
                        </span>
                      </div>
                    </div>
                  </LeafletTooltip>
                </Polyline>
              );
            })}

            {/* 64-District Choropleth Markers from GeoJSON or Aggregates */}
            {geojsonFeatures.map((f, idx) => {
              const props = f.properties || {};
              const coords = f.geometry?.coordinates || [90.4, 23.8];
              const lat = coords[1];
              const lon = coords[0];
              const avgP = props.avg_price || minPrice;
              const color = getMarkerColor(avgP, minPrice, maxPrice);
              const distFromDhaka = calculateDistanceDhaka(lat, lon);

              return (
                <CircleMarker
                  key={`dist-${props.name || idx}`}
                  center={[lat, lon]}
                  radius={props.has_data ? 9 : 6}
                  fillColor={color}
                  color="#ffffff"
                  weight={1.5}
                  opacity={0.9}
                  fillOpacity={0.8}
                >
                  <Popup>
                    <div className="p-1 text-slate-100 text-xs">
                      <div className="flex items-center justify-between gap-2 border-b border-slate-700 pb-1 mb-1">
                        <span className="font-bold text-sm text-white">{props.name} ({props.bn_name})</span>
                        <span className="text-[10px] text-slate-400">{props.division}</span>
                      </div>
                      <p className="text-slate-300 text-[11px] mb-1">
                        Primary Market: <strong className="text-white">{props.primary_market}</strong>
                      </p>
                      <p className="text-slate-400 text-[10px] mb-1.5 flex items-center gap-1">
                        <Navigation className="w-3 h-3 text-emerald-400" />
                        Distance from Dhaka: <strong className="text-slate-200">{distFromDhaka} km</strong>
                      </p>
                      <div className="pt-1 border-t border-slate-700 flex justify-between gap-3 font-mono">
                        <span className="text-slate-400">District Avg:</span>
                        <strong className="text-emerald-400">
                          {props.avg_price ? `BDT ${props.avg_price.toFixed(2)}/${unit}` : 'Baseline Tier'}
                        </strong>
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

            {/* Detailed Market Pinpoints */}
            {markets.map((m) => {
              if (!m.latitude || !m.longitude) return null;
              const color = getMarkerColor(m.avg_price, minPrice, maxPrice);
              const distFromDhaka = calculateDistanceDhaka(m.latitude, m.longitude);

              return (
                <CircleMarker
                  key={`mkt-${m.market_id}`}
                  center={[m.latitude, m.longitude]}
                  radius={11}
                  fillColor={color}
                  color="#fbbf24"
                  weight={2}
                  opacity={1}
                  fillOpacity={0.9}
                >
                  <Popup>
                    <div className="p-1 text-slate-100 text-xs">
                      <p className="font-bold text-sm text-white mb-0.5">{m.market_name}</p>
                      <p className="text-slate-300 mb-1">
                        {m.district}, {m.division} • <span className="capitalize">{m.market_type}</span>
                      </p>
                      <p className="text-slate-400 text-[10px] mb-1 flex items-center gap-1">
                        <Navigation className="w-3 h-3 text-amber-400" />
                        Distance from Capital: {distFromDhaka} km
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

          {/* Active Corridor Detail Glassmorphic Sidebar / Drawer */}
          {activeCorridor && (
            <div className="absolute top-3 left-3 z-[1000] max-w-sm w-[92%] sm:w-80 bg-slate-900/95 backdrop-blur-md border border-slate-700/90 rounded-xl p-3.5 shadow-2xl text-xs transition-all animate-in fade-in slide-in-from-left-2">
              <div className="flex items-start justify-between gap-2 border-b border-slate-700/80 pb-2 mb-2.5">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                    <Truck className="w-3.5 h-3.5" />
                    ট্রানজিট করিডোর বিবরণ
                  </span>
                  <h5 className="font-bold text-sm text-white mt-0.5 font-outfit">
                    {activeCorridor.corridor_name || `${activeCorridor.source_district || activeCorridor.origin_district} ➔ ${activeCorridor.destination_district}`}
                  </h5>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveCorridor(null)}
                  className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                {/* Distance & Transit Hours */}
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                  <div className="flex items-center gap-1.5 text-slate-300">
                    <Navigation className="w-3.5 h-3.5 text-indigo-400" />
                    <span>হাইওয়ে দূরত্ব:</span>
                  </div>
                  <span className="font-bold text-white font-mono">{activeCorridor.distance_km} km</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/80 border border-slate-700/60">
                  <div className="flex items-center gap-1.5 text-slate-300">
                    <Clock className="w-3.5 h-3.5 text-amber-400" />
                    <span>আনুমানিক ট্রানজিট সময়:</span>
                  </div>
                  <span className="font-bold text-amber-300 font-mono">
                    ~{activeCorridor.transit_hours_estimated || (activeCorridor.distance_km / 45 + 1).toFixed(1)} ঘণ্টা
                  </span>
                </div>

                {/* Price Gap Overview */}
                <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60 space-y-1">
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>উৎস ({activeCorridor.source_district || activeCorridor.origin_district}):</span>
                    <span className="font-mono text-white">৳{(activeCorridor.source_price ?? activeCorridor.origin_price ?? 0).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 text-[11px]">
                    <span>গন্তব্য ({activeCorridor.destination_district}):</span>
                    <span className="font-mono text-white">৳{activeCorridor.destination_price.toFixed(2)}</span>
                  </div>
                  <div className="pt-1 border-t border-slate-700/80 flex justify-between font-semibold">
                    <span className="text-slate-300">গ্রস মূল্য ব্যবধান:</span>
                    <span className="text-emerald-400 font-mono">+৳{activeCorridor.gross_spread_bdt.toFixed(2)}/{unit}</span>
                  </div>
                </div>

                {/* Freight & Toll Breakdown */}
                <div className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/60 space-y-1 text-[11px]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                    পরিবহন ও টোল ব্রেকডাউন (Freight & Toll)
                  </span>
                  <div className="flex justify-between text-slate-400">
                    <span>মূল ট্রাক ভাড়া (Base Freight):</span>
                    <span className="font-mono text-slate-200">
                      ৳{(activeCorridor.freight_breakdown?.base_freight || (activeCorridor.estimated_freight_cost_bdt - (activeCorridor.toll_and_buffer_cost_bdt || 0))).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>ব্রিজ টোল ও কনজেশন বাফার:</span>
                    <span className="font-mono text-amber-300">
                      +৳{(activeCorridor.toll_and_buffer_cost_bdt || 0.50).toFixed(2)}/কেজি
                    </span>
                  </div>
                  <div className="pt-1 border-t border-slate-700 flex justify-between font-bold text-slate-200">
                    <span>মোট পরিবহন খরচ:</span>
                    <span className="font-mono text-rose-300">
                      -৳{activeCorridor.estimated_freight_cost_bdt.toFixed(2)}/{unit}
                    </span>
                  </div>
                </div>

                {/* Net Margin & Feasibility Badge */}
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">নিট আরবিট্রেজ মার্জিন</span>
                    <span className={`text-base font-extrabold font-mono ${
                      activeCorridor.net_arbitrage_margin_bdt > 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {activeCorridor.net_arbitrage_margin_bdt > 0 ? `+৳${activeCorridor.net_arbitrage_margin_bdt.toFixed(2)}` : `৳${activeCorridor.net_arbitrage_margin_bdt.toFixed(2)}`}/{unit}
                    </span>
                    <span className="text-[10px] text-slate-400 ml-1.5">(ROI: {activeCorridor.roi_percentage}%)</span>
                  </div>
                  <span className={`px-2 py-1 rounded text-[10px] font-bold ${
                    activeCorridor.economic_feasibility === 'Highly Feasible'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : activeCorridor.economic_feasibility === 'Marginal'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  }`}>
                    {activeCorridor.economic_feasibility}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Map Legend Overlay */}
          <div className="absolute bottom-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-lg p-2.5 text-[11px] shadow-lg">
            <span className="font-bold text-white block mb-1">Price Intensity Legend</span>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>
                <span className="text-slate-300">Surplus / Low Price</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
                <span className="text-slate-300">Normal Band</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-rose-500 inline-block"></span>
                <span className="text-slate-300">Deficit / High Price</span>
              </div>
              {showCorridors && (
                <div className="pt-1.5 mt-1.5 border-t border-slate-700/80 space-y-1">
                  <span className="font-semibold text-slate-400 block text-[10px]">Transit Corridors</span>
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-0.5 bg-emerald-400 inline-block"></span>
                    <span className="text-slate-300 text-[10px]">Feasible (≥৳৬/kg)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-0.5 bg-amber-400 inline-block border-b border-dashed border-amber-400"></span>
                    <span className="text-slate-300 text-[10px]">Marginal (৳২-৳৬)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-0.5 bg-rose-400 inline-block border-b border-dotted border-rose-400"></span>
                    <span className="text-slate-300 text-[10px]">Infeasible (&lt;৳২)</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Inter-District Freight & Spatial Arbitrage Matrix */}
      {arbitrageData?.routes?.length > 0 && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-sm font-bold text-white font-outfit uppercase tracking-wider flex items-center gap-2">
                <Truck className="w-4 h-4 text-emerald-400" />
                Inter-District Freight & Transport Arbitrage Spread Model
              </h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates transport overhead vs spatial margin between northern production hubs and urban consumption centers.
              </p>
            </div>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
              {arbitrageData.routes.length} Active Corridors
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/80 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Origin (Production Hub)</th>
                  <th className="py-2.5 px-3 font-semibold">Destination (Consumption Hub)</th>
                  <th className="py-2.5 px-3 font-semibold">Distance & Transit</th>
                  <th className="py-2.5 px-3 font-semibold">Gross Spread</th>
                  <th className="py-2.5 px-3 font-semibold">Freight & Toll Buffer</th>
                  <th className="py-2.5 px-3 font-semibold">Net Arbitrage Margin</th>
                  <th className="py-2.5 px-3 font-semibold">Economic Feasibility</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {arbitrageData.routes.slice(0, 8).map((route, i) => {
                  const srcDist = route.source_district || route.origin_district;
                  const srcPrice = route.source_price ?? route.origin_price ?? 0;
                  const isSelected = activeCorridor?.corridor_name === route.corridor_name ||
                    (activeCorridor?.source_district === srcDist && activeCorridor?.destination_district === route.destination_district);

                  return (
                    <tr
                      key={i}
                      onClick={() => {
                        setActiveCorridor(route);
                        setShowCorridors(true);
                      }}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-emerald-500/15 border-l-2 border-emerald-400' : 'hover:bg-slate-800/40'
                      }`}
                    >
                      <td className="py-2.5 px-3 font-sans font-medium text-white">
                        {srcDist}
                        <span className="block text-[10px] text-slate-500 font-mono">BDT {srcPrice.toFixed(2)}</span>
                      </td>
                      <td className="py-2.5 px-3 font-sans font-medium text-white">
                        {route.destination_district}
                        <span className="block text-[10px] text-slate-500 font-mono">BDT {route.destination_price.toFixed(2)}</span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span>{route.distance_km} km</span>
                        <span className="block text-[10px] text-amber-400/90 font-mono">
                          ~{route.transit_hours_estimated || (route.distance_km / 45 + 1).toFixed(1)}h
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">+{route.gross_spread_bdt.toFixed(2)} BDT</td>
                      <td className="py-2.5 px-3 text-slate-400">
                        <span>-{route.estimated_freight_cost_bdt.toFixed(2)} BDT</span>
                        {route.toll_and_buffer_cost_bdt > 0 && (
                          <span className="block text-[9px] text-amber-500/90">
                            (incl. ৳{route.toll_and_buffer_cost_bdt.toFixed(2)} toll)
                          </span>
                        )}
                      </td>
                      <td className={`py-2.5 px-3 font-bold ${route.net_arbitrage_margin_bdt > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {route.net_arbitrage_margin_bdt > 0 ? `+${route.net_arbitrage_margin_bdt.toFixed(2)}` : route.net_arbitrage_margin_bdt.toFixed(2)} BDT
                      </td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          route.economic_feasibility === 'Highly Feasible'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                            : route.economic_feasibility === 'Marginal'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        }`}>
                          {route.economic_feasibility}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
