import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function OrbitalConfidenceRing({ accuracy = 94.0, errorMargin = 2.4 }) {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(media.matches);
    const listener = (e) => setReducedMotion(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, []);

  // Tick count decreases as error margin increases (representing uncertainty)
  const baseTickCount = 60;
  const tickCount = Math.max(12, Math.round(baseTickCount - errorMargin * 6));
  
  // Calculate spacing & variance
  const radius = 70;
  const ticks = Array.from({ length: tickCount });

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'var(--surface-raised, #21262E)',
      border: '1px solid var(--border-strong, rgba(154,184,196,0.24))',
      borderRadius: 'var(--r-lg, 14px)',
      width: '240px',
      height: '240px',
      position: 'relative'
    }}>
      <svg width="180" height="180" viewBox="0 0 180 180" style={{ overflow: 'visible' }}>
        {/* Background circular track */}
        <circle
          cx="90"
          cy="90"
          r={radius}
          fill="none"
          stroke="var(--border, rgba(154,184,196,0.08))"
          strokeWidth="1.5"
        />

        {/* Orbiting ticks */}
        <motion.g
          animate={reducedMotion ? {} : { rotate: 360 }}
          transition={{
            repeat: Infinity,
            duration: 15 + errorMargin * 3, // speed depends on error margin
            ease: "linear"
          }}
          style={{ originX: "90px", originY: "90px" }}
        >
          {ticks.map((_, i) => {
            const angle = (i * 360) / tickCount;
            // Introduce slight jitter/offset in ticks based on errorMargin to visually indicate variance
            const variance = (Math.sin(i) * errorMargin * 0.4);
            const finalAngle = angle + variance;
            
            const rad = ((finalAngle - 90) * Math.PI) / 180;
            const x1 = 90 + radius * Math.cos(rad);
            const y1 = 90 + radius * Math.sin(rad);
            
            // Length of tick is longer for higher accuracy
            const tickLength = Math.max(4, 12 - errorMargin * 1.2);
            const x2 = 90 + (radius - tickLength) * Math.cos(rad);
            const y2 = 90 + (radius - tickLength) * Math.sin(rad);

            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={accuracy >= 95 ? "var(--signal-cyan, #2DD4BF)" : "var(--signal-amber, #E8A33D)"}
                strokeWidth="2.5"
                strokeLinecap="round"
                opacity={0.3 + (i / tickCount) * 0.7}
              />
            );
          })}
        </motion.g>

        {/* Inner glow circle */}
        <circle
          cx="90"
          cy="90"
          r={radius - 16}
          fill="none"
          stroke="var(--signal-cyan-dim, rgba(45,212,191,0.08))"
          strokeWidth="3"
          style={{ filter: 'drop-shadow(0 0 4px var(--signal-cyan))' }}
        />
      </svg>

      {/* Central percentage stats */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        width: '120px',
        height: '120px'
      }}>
        <div style={{
          fontFamily: 'var(--font-display, "Space Grotesk")',
          fontSize: '36px',
          fontWeight: 600,
          color: 'var(--text-primary, #E7ECEF)',
          lineHeight: 1
        }}>
          {accuracy}%
        </div>
        <div style={{
          fontFamily: 'var(--font-body, sans-serif)',
          fontSize: '11px',
          color: 'var(--text-secondary, #9AA8B2)',
          fontWeight: 500,
          marginTop: '4px',
          letterSpacing: '0.05em',
          textTransform: 'uppercase'
        }}>
          Accuracy
        </div>
        <div style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: '10px',
          color: 'var(--text-tertiary, #67737D)',
          marginTop: '2px'
        }}>
          ±{errorMargin}% MAPE
        </div>
      </div>
    </div>
  );
}
