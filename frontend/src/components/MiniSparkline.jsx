import React, { useId } from 'react';

/**
 * Lightweight, zero-layout-shift SVG MiniSparkline for 7-day price trajectory.
 */
export default function MiniSparkline({
  data = [],
  percentageChange = 0,
  width = 84,
  height = 34,
  className = '',
  showGradient = true,
}) {
  const gradientId = useId();

  // Color logic:
  // Spike (> +2%): Rose Red
  // Drop (< -2%): Emerald Green (consumer favorable / farmgate drop)
  // Stable: Slate Gray
  const strokeColor =
    percentageChange > 2.0
      ? '#F43F5E'
      : percentageChange < -2.0
      ? '#10B981'
      : '#94A3B8';

  const stopColor =
    percentageChange > 2.0
      ? '#F43F5E'
      : percentageChange < -2.0
      ? '#10B981'
      : '#94A3B8';

  if (!data || data.length < 2) {
    const cy = height / 2;
    return (
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className={`overflow-visible ${className}`}
      >
        <line
          x1={2}
          y1={cy}
          x2={width - 2}
          y2={cy}
          stroke={strokeColor}
          strokeWidth="1.5"
          strokeDasharray="3 3"
        />
      </svg>
    );
  }

  const paddingX = 4;
  const paddingTop = 4;
  const paddingBottom = 4;
  const effW = width - paddingX * 2;
  const effH = height - paddingTop - paddingBottom;

  const minVal = Math.min(...data);
  const maxVal = Math.max(...data);
  const range = maxVal - minVal || 1.0;

  const points = data.map((val, idx) => {
    const x = paddingX + (idx / (data.length - 1)) * effW;
    const norm = (val - minVal) / range;
    const y = paddingTop + (1.0 - norm) * effH;
    return { x, y };
  });

  // Generate smooth cubic bezier SVG path
  let pathD = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const midX = ((p0.x + p1.x) / 2).toFixed(1);
    pathD += ` C ${midX} ${p0.y.toFixed(1)}, ${midX} ${p1.y.toFixed(1)}, ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
  }

  const fillD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${height} L ${points[0].x.toFixed(1)} ${height} Z`;
  const lastPoint = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={`overflow-visible ${className}`}
      aria-label={`7-day trend sparkline: ${percentageChange > 0 ? '+' : ''}${percentageChange}%`}
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={stopColor} stopOpacity="0.30" />
          <stop offset="100%" stopColor={stopColor} stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {showGradient && (
        <path d={fillD} fill={`url(#${gradientId})`} />
      )}

      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* End point marker */}
      <circle
        cx={lastPoint.x}
        cy={lastPoint.y}
        r="2.5"
        fill={strokeColor}
      />
    </svg>
  );
}
