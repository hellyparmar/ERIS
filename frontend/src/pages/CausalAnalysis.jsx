import React, { useState } from 'react';
import { useFetch } from '../hooks/useApi';
import { Bot, Calendar, TrendingUp, AlertTriangle, ArrowRight } from 'lucide-react';

export default function CausalAnalysis() {
  const [outletId, setOutletId] = useState('1'); // Default to outlet ID 1

  const { data: summary, isLoading, error } = useFetch(
    ['causalSummary', outletId],
    `/api/v1/causal/summary/${outletId}`
  );

  if (isLoading) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-6 text-[var(--color-navy-text)]">Causal Analysis</h1>
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-[var(--color-navy-muted)]/20 rounded-xl"></div>
          <div className="h-64 bg-[var(--color-navy-muted)]/20 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-6 text-[var(--color-navy-text)]">Causal Analysis</h1>
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl">
          Error loading causal analysis: {error.message}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#f4f2ed]">Causal Analysis</h1>
          <p className="text-[var(--color-navy-text)] mt-1">AI-driven insights into sales drivers and holiday impacts</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm text-[var(--color-navy-text)]">Outlet ID:</label>
          <input
            type="text"
            value={outletId}
            onChange={(e) => setOutletId(e.target.value)}
            className="bg-[var(--color-navy-dim)] border border-[rgba(255,255,255,0.1)] rounded-lg px-3 py-1.5 text-sm text-[#f4f2ed] focus:outline-none focus:border-[var(--color-amber)]"
          />
        </div>
      </div>

      {!summary ? (
        <div className="text-[var(--color-navy-text)]">No analysis available for this outlet.</div>
      ) : (
        <div className="space-y-6">
          {/* Actionable Insights */}
          <div className="bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.06)] rounded-xl p-6">
            <h2 className="text-lg font-semibold text-[#f4f2ed] mb-4 flex items-center gap-2">
              <Bot size={20} className="text-[var(--color-amber)]" />
              Actionable Insights
            </h2>
            <div className="space-y-3">
              {summary.actionable_insights?.map((insight, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-[var(--color-navy-dim)] rounded-lg border border-[rgba(255,255,255,0.04)]">
                  <ArrowRight size={16} className="text-[var(--color-amber)] mt-0.5 shrink-0" />
                  <p className="text-sm text-[#d4d0c8]">{insight}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Key Drivers */}
            <div className="bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.06)] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-[#f4f2ed] mb-4 flex items-center gap-2">
                <TrendingUp size={20} className="text-blue-400" />
                Key Drivers
              </h2>
              <div className="space-y-4">
                {summary.key_drivers?.map((driver, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-[#d4d0c8]">{driver.name}</span>
                      <span className="text-sm text-[var(--color-navy-text)]">{driver.impact > 0 ? '+' : ''}{driver.impact.toFixed(1)} impact</span>
                    </div>
                    <div className="w-full bg-[var(--color-navy-dim)] rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${driver.impact > 0 ? 'bg-emerald-400' : 'bg-red-400'}`}
                        style={{ width: `${Math.min(Math.abs(driver.impact_pct) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Holiday Analysis */}
            <div className="bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.06)] rounded-xl p-6">
              <h2 className="text-lg font-semibold text-[#f4f2ed] mb-4 flex items-center gap-2">
                <Calendar size={20} className="text-purple-400" />
                Holiday Impact ({summary.holiday_analysis?.year})
              </h2>
              <div className="mb-6">
                <div className="text-[var(--color-navy-text)] text-sm mb-1">Total Impact</div>
                <div className="text-2xl font-bold text-[#f4f2ed]">
                  {summary.holiday_analysis?.total_impact > 0 ? '+' : ''}
                  {summary.holiday_analysis?.total_impact.toFixed(1)}
                </div>
              </div>
              
              <h3 className="text-sm font-medium text-[#d4d0c8] mb-3">Strongest Holiday</h3>
              {summary.holiday_analysis?.strongest_holiday ? (
                <div className="p-4 bg-[var(--color-navy-dim)] rounded-lg border border-[rgba(255,255,255,0.04)]">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-[#f4f2ed]">{summary.holiday_analysis.strongest_holiday.name}</span>
                    <span className={`text-sm font-medium ${summary.holiday_analysis.strongest_holiday.impact > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {summary.holiday_analysis.strongest_holiday.impact > 0 ? '+' : ''}
                      {summary.holiday_analysis.strongest_holiday.impact.toFixed(1)}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--color-navy-text)]">
                    Confidence: {(summary.holiday_analysis.strongest_holiday.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              ) : (
                <div className="text-sm text-[var(--color-navy-text)]">No significant holidays detected.</div>
              )}
            </div>
            
            {/* Recent Anomalies */}
            {summary.recent_anomalies && summary.recent_anomalies.length > 0 && (
              <div className="bg-[var(--color-navy-deep)] border border-[rgba(255,255,255,0.06)] rounded-xl p-6 lg:col-span-2">
                <h2 className="text-lg font-semibold text-[#f4f2ed] mb-4 flex items-center gap-2">
                  <AlertTriangle size={20} className="text-amber-400" />
                  Recent Anomalies
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {summary.recent_anomalies.map((anomaly, idx) => (
                    <div key={idx} className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-start gap-3">
                      <AlertTriangle size={18} className="text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="font-medium text-amber-100 text-sm">{anomaly.type.replace('_', ' ').toUpperCase()}</div>
                        <div className="text-xs text-amber-200/70 mt-1">{anomaly.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
