export default function AgpLogo({ width = 120, height = 48, textColor = "#D4EFF3", arcColor = "#8FC5CF", className, style }) {
  return (
    <svg
      viewBox="0 0 220 88"
      width={width}
      height={height}
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
      aria-label="AGP"
      role="img"
    >
      <path
        d="M 12,58 C 52,-10 168,-10 208,58"
        fill="none"
        stroke={arcColor}
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <text
        x="110"
        y="82"
        textAnchor="middle"
        fontFamily="'Franklin Gothic Heavy','Arial Black',Impact,'Helvetica Neue Condensed Bold',sans-serif"
        fontWeight="900"
        fontSize="42"
        fill={textColor}
        letterSpacing="8"
      >
        AGP
      </text>
    </svg>
  );
}
