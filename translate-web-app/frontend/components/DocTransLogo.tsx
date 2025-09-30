export default function DocTransLogo({ className = "", size = "md" }: { className?: string; size?: "sm" | "md" | "lg" }) {
  const sizes = {
    sm: { width: 120, height: 40, fontSize: 16, iconSize: 20 },
    md: { width: 200, height: 60, fontSize: 24, iconSize: 30 },
    lg: { width: 300, height: 90, fontSize: 36, iconSize: 45 }
  };

  const { width, height, fontSize, iconSize } = sizes[size];

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className}>
      <defs>
        <linearGradient id="docTransGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style={{ stopColor: '#fbbf24', stopOpacity: 1 }} />
          <stop offset="100%" style={{ stopColor: '#f97316', stopOpacity: 1 }} />
        </linearGradient>
        <mask id="cutout">
          <rect width="100%" height="100%" fill="white"/>
          <circle cx={iconSize * 1.5} cy={height / 2} r={iconSize * 0.4} fill="black"/>
        </mask>
      </defs>

      {/* Logo Icon */}
      <g transform={`translate(${iconSize * 0.3}, ${height / 2 - iconSize / 2})`}>
        {/* Rotating Square */}
        <rect
          x="0"
          y="0"
          width={iconSize}
          height={iconSize}
          fill="url(#docTransGradient)"
          mask="url(#cutout)"
          transform={`rotate(45 ${iconSize / 2} ${iconSize / 2})`}
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from={`45 ${iconSize / 2} ${iconSize / 2}`}
            to={`405 ${iconSize / 2} ${iconSize / 2}`}
            dur="30s"
            repeatCount="indefinite"
          />
        </rect>

        {/* Circle */}
        <circle
          cx={iconSize * 1.2}
          cy={iconSize / 2}
          r={iconSize * 0.4}
          fill="none"
          stroke="url(#docTransGradient)"
          strokeWidth="2"
        />

        {/* Connection Lines */}
        <line
          x1={iconSize * 0.5}
          y1={iconSize * 0.5}
          x2={iconSize * 0.8}
          y2={iconSize * 0.5}
          stroke="currentColor"
          strokeWidth="1"
          opacity="0.3"
        />
      </g>

      {/* Text */}
      <text
        x={iconSize * 2}
        y={height / 2 + fontSize * 0.35}
        fontFamily="'Inter', sans-serif"
        fontSize={fontSize}
        fontWeight="100"
        fill="currentColor"
      >
        doc
        <tspan fontWeight="900" fill="url(#docTransGradient)">Trans</tspan>
      </text>
    </svg>
  );
}