import React from 'react';

/**
 * Handcrafted Bespoke Vector Illustrations for PricePulse BD
 * Covers all staple categories and individual commodity signatures.
 */

// ── 1. Vegetables (শাকসবজি - Onion / Brinjal / Fresh produce) ───────────────
export function VegetableIcon({ className = "w-6 h-6", color = "#10B981" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="24" cy="24" r="22" fill={color} fillOpacity="0.12" stroke={color} strokeWidth="1.5" strokeOpacity="0.3" />
      {/* Onion / Aubergine Bulb */}
      <path d="M24 12 C18 16 14 23 15 31 C16 37 20 40 24 40 C28 40 32 37 33 31 C34 23 30 16 24 12 Z" 
            fill={color} fillOpacity="0.25" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      {/* Root fibers */}
      <path d="M24 40 V43 M21 39 L19 42 M27 39 L29 42" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      {/* Sprout & Leaves */}
      <path d="M24 12 C24 7 21 6 18 6 C18 9 21 11 24 12 Z" fill="#34D399" />
      <path d="M24 12 C25 6 28 6 31 7 C30 10 27 11 24 12 Z" fill="#34D399" />
      <path d="M24 18 V34 M20 22 C19 26 19 30 20 34 M28 22 C29 26 29 30 28 34" 
            stroke={color} strokeWidth="1.2" strokeOpacity="0.6" strokeLinecap="round" />
    </svg>
  );
}

// ── 2. Grains & Pulses (চাল, আটা ও ডাল - Golden Wheat & Stalk) ──────────────
export function GrainIcon({ className = "w-6 h-6", color = "#F59E0B" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="24" cy="24" r="22" fill={color} fillOpacity="0.12" stroke={color} strokeWidth="1.5" strokeOpacity="0.3" />
      {/* Central stalk */}
      <path d="M24 40 V10" stroke={color} strokeWidth="2" strokeLinecap="round" />
      {/* Grain ears */}
      <path d="M24 10 C21 8 20 12 24 14 Z" fill={color} />
      <path d="M24 14 C19 13 18 18 24 19 Z" fill={color} fillOpacity="0.85" />
      <path d="M24 14 C29 13 30 18 24 19 Z" fill={color} fillOpacity="0.85" />
      <path d="M24 20 C18 19 17 24 24 25 Z" fill={color} fillOpacity="0.85" />
      <path d="M24 20 C30 19 31 24 24 25 Z" fill={color} fillOpacity="0.85" />
      <path d="M24 26 C18 25 17 30 24 31 Z" fill={color} fillOpacity="0.85" />
      <path d="M24 26 C30 25 31 30 24 31 Z" fill={color} fillOpacity="0.85" />
      {/* Awn tips */}
      <path d="M19 13 L14 8 M29 13 L34 8 M18 19 L12 15 M30 19 L36 15" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

// ── 3. Meat & Fish (মাছ ও মাংস - Hilsa/Rui Silhouette & Livestock) ───────────
export function MeatFishIcon({ className = "w-6 h-6", color = "#F43F5E" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="24" cy="24" r="22" fill={color} fillOpacity="0.12" stroke={color} strokeWidth="1.5" strokeOpacity="0.3" />
      {/* Swimming River Fish Body */}
      <path d="M10 24 C14 17 25 17 33 22 L40 17 V31 L33 26 C25 31 14 31 10 24 Z" 
            fill={color} fillOpacity="0.25" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      {/* Eye & Gill */}
      <circle cx="15" cy="23" r="1.5" fill={color} />
      <path d="M19 20 C20 23 20 25 19 28" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      {/* Fin */}
      <path d="M23 21 C26 21 27 24 25 26" stroke={color} strokeWidth="1.5" strokeLinecap="round" fill={color} fillOpacity="0.3" />
    </svg>
  );
}

// ── 4. Dairy & Eggs (দুধ ও ডিম - Fresh Jug & Egg Emblem) ────────────────────
export function DairyEggIcon({ className = "w-6 h-6", color = "#EAB308" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="24" cy="24" r="22" fill={color} fillOpacity="0.12" stroke={color} strokeWidth="1.5" strokeOpacity="0.3" />
      {/* Milk Jug Outline */}
      <path d="M15 17 H25 L27 22 V36 H13 V22 L15 17 Z" 
            fill={color} fillOpacity="0.25" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      <path d="M17 14 H23 V17 H17 Z" fill={color} fillOpacity="0.4" stroke={color} strokeWidth="1.5" />
      {/* Egg Profile */}
      <path d="M31 23 C27 23 25 28 25 32 C25 36 28 38 31 38 C34 38 37 36 37 32 C37 28 35 23 31 23 Z" 
            fill="#FEF08A" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  );
}

// ── 5. Oils & Spices (তেল ও মসলা - Golden Drop & Spice Seed) ────────────────
export function OilSpiceIcon({ className = "w-6 h-6", color = "#F97316" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="24" cy="24" r="22" fill={color} fillOpacity="0.12" stroke={color} strokeWidth="1.5" strokeOpacity="0.3" />
      {/* Oil Droplet */}
      <path d="M24 10 C24 10 14 24 14 30 C14 35.5 18.5 40 24 40 C29.5 40 34 35.5 34 30 C34 24 24 10 24 10 Z" 
            fill={color} fillOpacity="0.25" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      {/* Gloss Reflection inside drop */}
      <path d="M20 24 C18 27 18 31 20 34" stroke="#FED7AA" strokeWidth="1.8" strokeLinecap="round" />
      {/* Spice Star / Flame Sparkle */}
      <circle cx="27" cy="28" r="2.5" fill="#FBBF24" />
    </svg>
  );
}

// ── 6. Generic Staple / All Items ──────────────────────────────────────────
export function AllStaplesIcon({ className = "w-6 h-6", color = "#10B981" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <circle cx="24" cy="24" r="22" fill={color} fillOpacity="0.12" stroke={color} strokeWidth="1.5" strokeOpacity="0.3" />
      <rect x="14" y="14" width="8" height="8" rx="2" fill={color} />
      <rect x="26" y="14" width="8" height="8" rx="2" fill={color} fillOpacity="0.6" />
      <rect x="14" y="26" width="8" height="8" rx="2" fill={color} fillOpacity="0.6" />
      <rect x="26" y="26" width="8" height="8" rx="2" fill={color} />
    </svg>
  );
}

import { getCommodityCanonicalCategory } from '../../utils/taxonomy';

/**
 * Smart Dispatcher: Returns the optimal bespoke vector icon
 * strictly matching the canonical commodity taxonomy category.
 */
export default function CommodityIcon({
  category = "",
  name = "",
  className = "w-6 h-6",
  color = null,
}) {
  const canonicalCategory = getCommodityCanonicalCategory({
    category,
    canonical_name: name,
  });

  switch (canonicalCategory) {
    case 'vegetables':
      return <VegetableIcon className={className} color={color || "#10B981"} />;
    case 'grains_pulses':
      return <GrainIcon className={className} color={color || "#F59E0B"} />;
    case 'meat_fish':
      return <MeatFishIcon className={className} color={color || "#F43F5E"} />;
    case 'eggs_dairy':
      return <DairyEggIcon className={className} color={color || "#EAB308"} />;
    case 'oils_spices':
      return <OilSpiceIcon className={className} color={color || "#F97316"} />;
    default:
      return <AllStaplesIcon className={className} color={color || "#10B981"} />;
  }
}
