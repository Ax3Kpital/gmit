'use client';

interface GprPoint {
  period: string;
  gpr_value: number | null;
  gpr_threat: number | null;
  gpr_act: number | null;
}

interface Props {
  series: GprPoint[];
}

export function GprChart({ series }: Props) {
  const valid = series.filter(p => p.gpr_value !== null) as (GprPoint & { gpr_value: number })[];
  if (valid.length < 2) {
    return (
      <div className="flex items-center justify-center h-32 text-xs mono" style={{ color: 'var(--muted)' }}>
        UNAVAILABLE — GPR data not yet loaded
      </div>
    );
  }

  const W = 800;
  const H = 120;
  const PAD = { top: 8, right: 8, bottom: 20, left: 44 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;

  const vals = valid.map(p => p.gpr_value);
  const minV = Math.min(...vals);
  const maxV = Math.max(...vals);
  const range = maxV - minV || 1;

  const x = (i: number) => PAD.left + (i / (valid.length - 1)) * chartW;
  const y = (v: number) => PAD.top + chartH - ((v - minV) / range) * chartH;

  // Main GPR line
  const gprPts = valid.map((p, i) => `${x(i).toFixed(1)},${y(p.gpr_value).toFixed(1)}`).join(' ');

  // Threat line
  const threatValid = valid.filter(p => p.gpr_threat !== null);
  const threatPts = valid
    .map((p, i) => (p.gpr_threat !== null ? `${x(i).toFixed(1)},${y(p.gpr_threat!).toFixed(1)}` : null))
    .filter(Boolean)
    .join(' ');

  // Area fill under GPR line
  const firstX = x(0).toFixed(1);
  const lastX = x(valid.length - 1).toFixed(1);
  const bottomY = (PAD.top + chartH).toFixed(1);
  const areaPath = `M${firstX},${bottomY} ` +
    valid.map((p, i) => `L${x(i).toFixed(1)},${y(p.gpr_value).toFixed(1)}`).join(' ') +
    ` L${lastX},${bottomY} Z`;

  // Y-axis ticks (3 ticks)
  const tickCount = 3;
  const yTicks = Array.from({ length: tickCount }, (_, i) => {
    const v = minV + (range / (tickCount - 1)) * i;
    return { v: Math.round(v), yPos: y(v) };
  });

  // X-axis labels (every ~12 months)
  const xLabels: { label: string; xPos: number }[] = [];
  valid.forEach((p, i) => {
    const d = new Date(p.period);
    if (d.getMonth() === 0 || i === 0 || i === valid.length - 1) {
      xLabels.push({ label: d.getFullYear().toString(), xPos: x(i) });
    }
  });

  // Current value
  const latest = valid[valid.length - 1];
  const latestY = y(latest.gpr_value);

  return (
    <div className="w-full overflow-hidden">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ height: 120 }}
        preserveAspectRatio="xMidYMid meet"
        aria-label="GPR Index historical chart"
      >
        {/* Y grid lines */}
        {yTicks.map(tick => (
          <line
            key={tick.v}
            x1={PAD.left}
            y1={tick.yPos}
            x2={W - PAD.right}
            y2={tick.yPos}
            stroke="var(--line)"
            strokeWidth="0.5"
          />
        ))}

        {/* Area fill */}
        <path d={areaPath} fill="var(--accent)" opacity="0.06" />

        {/* Threat component line (subtle) */}
        {threatPts && (
          <polyline
            points={threatPts}
            fill="none"
            stroke="var(--warn)"
            strokeWidth="1"
            opacity="0.4"
            strokeDasharray="3,3"
          />
        )}

        {/* Main GPR line */}
        <polyline
          points={gprPts}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Latest value dot */}
        <circle cx={x(valid.length - 1)} cy={latestY} r="3" fill="var(--accent)" />

        {/* Y-axis labels */}
        {yTicks.map(tick => (
          <text
            key={tick.v}
            x={PAD.left - 4}
            y={tick.yPos + 3}
            textAnchor="end"
            fontSize="8"
            fill="var(--muted)"
            fontFamily="IBM Plex Mono, monospace"
          >
            {tick.v}
          </text>
        ))}

        {/* X-axis labels */}
        {xLabels.map(l => (
          <text
            key={l.label + l.xPos}
            x={l.xPos}
            y={H - 4}
            textAnchor="middle"
            fontSize="8"
            fill="var(--muted)"
            fontFamily="IBM Plex Mono, monospace"
          >
            {l.label}
          </text>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-1">
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-0.5 rounded" style={{ background: 'var(--accent)' }} />
          <span className="text-xs mono" style={{ color: 'var(--muted)' }}>GPR Overall</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-0.5 rounded" style={{ background: 'var(--warn)', opacity: 0.5 }} />
          <span className="text-xs mono" style={{ color: 'var(--muted)' }}>Threat Component</span>
        </div>
        <span className="text-xs mono ml-auto" style={{ color: 'var(--muted)' }}>
          latest: <span style={{ color: 'var(--text)' }}>{latest.gpr_value.toFixed(0)}</span>
        </span>
      </div>
    </div>
  );
}
