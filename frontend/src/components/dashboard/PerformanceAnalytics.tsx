"use client";

import { BarChart3, TrendingDown, Target, Zap, Activity, CheckCircle, XCircle } from "lucide-react";
import { AreaChart, Area, Tooltip, ResponsiveContainer } from 'recharts';
import { useDashboard } from "@/context/DashboardContext";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

export default function PerformanceAnalytics() {
  const { performance } = useDashboard();

  const chartData = [
    { name: '08:00', pred: 88, actual: 85 },
    { name: '10:00', pred: 92, actual: 91 },
    { name: '12:00', pred: 85, actual: 87 },
    { name: '14:00', pred: 95, actual: 94 },
    { name: '16:00', pred: 90, actual: 89 },
    { name: '18:00', pred: 98, actual: 96 },
  ];

  // Derive global accuracy or display active count
  const activeModelsCount = performance?.models.filter(m => m.is_active).length || 0;
  const totalModelsCount = performance?.models.length || 0;

  return (
    <div className="p-4 flex flex-col h-full bg-[#0a0d14] text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-emerald-500/20 flex items-center justify-center border border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <Target size={16} className="text-emerald-400" />
          </div>
          <div>
            <h3 className="font-headline font-bold text-[10px] tracking-[0.2em] uppercase text-white">System Performance</h3>
            <span className="text-[7px] font-bold text-muted-foreground uppercase tracking-widest">Model_Uplink_v3</span>
          </div>
        </div>
        <Badge variant="outline" className="text-[8px] border-emerald-500/40 bg-emerald-500/10 text-emerald-400 uppercase font-black px-1.5 py-0.5 animate-pulse">
          {activeModelsCount}/{totalModelsCount} ONLINE
        </Badge>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-6 pb-4 pr-3">
          {/* Chart Area */}
          <div className="bg-black/30 border border-white/5 rounded-xl p-3 shadow-inner">
            <div className="flex justify-between items-center mb-2 px-1">
              <span className="text-[8px] uppercase font-black tracking-widest text-muted-foreground">Prediction Accuracy Timeline</span>
              <span className="text-[9px] font-mono text-emerald-400 font-bold">96.4% Avg</span>
            </div>
            <div className="h-28 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0D1117', border: '1px solid #30363d', fontSize: '10px' }}
                    itemStyle={{ color: '#8b949e' }}
                  />
                  <Area type="monotone" dataKey="pred" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorPred)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="actual" stroke="hsl(var(--accent))" fill="transparent" strokeWidth={1} strokeDasharray="3 3" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Core Stats Overview */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/[0.02] border border-white/5 rounded-lg p-3 flex flex-col justify-between">
              <div className="flex items-center gap-2 mb-1">
                <BarChart3 size={12} className="text-primary" />
                <span className="text-[8px] uppercase font-black text-muted-foreground tracking-widest">Predictions Logged</span>
              </div>
              <span className="text-xl font-headline font-bold text-white font-mono">{performance?.total_predictions ?? 0}</span>
            </div>
            <div className="bg-white/[0.02] border border-white/5 rounded-lg p-3 flex flex-col justify-between">
              <div className="flex items-center gap-2 mb-1">
                <Zap size={12} className="text-amber-400" />
                <span className="text-[8px] uppercase font-black text-muted-foreground tracking-widest">Feedback Count</span>
              </div>
              <span className="text-xl font-headline font-bold text-white font-mono">{performance?.feedback_count ?? 0}</span>
            </div>
          </div>

          {/* Models Detailed Info */}
          <div className="space-y-3">
            <span className="text-[8px] uppercase font-black text-muted-foreground tracking-[0.15em] block">Model Register Status</span>
            <div className="grid gap-3">
              {performance?.models && performance.models.map((model) => {
                const mae = model.mae != null ? model.mae.toFixed(2) : "N/A";
                const r2 = model.r2 != null ? `${(model.r2 * 100).toFixed(1)}%` : null;
                const accuracy = model.accuracy != null ? `${(model.accuracy * 100).toFixed(1)}%` : null;
                const drift = model.drift_score != null ? `${(model.drift_score * 100).toFixed(2)}%` : "0.00%";
                
                return (
                  <div key={model.model_name} className="bg-white/[0.03] border border-white/10 rounded-lg p-3 hover:bg-white/[0.05] transition-all">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex flex-col">
                        <span className="text-[10px] font-bold text-white uppercase tracking-wider">{model.feature_name} Predictor</span>
                        <span className="text-[7px] font-mono text-muted-foreground uppercase">{model.model_type} Model</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {model.is_active ? (
                          <>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping absolute" />
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 relative" />
                            <span className="text-[7px] uppercase font-black text-emerald-400 tracking-widest">ONLINE</span>
                          </>
                        ) : (
                          <>
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                            <span className="text-[7px] uppercase font-black text-red-400 tracking-widest">OFFLINE</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-white/5 text-[9px] font-mono">
                      <div>
                        <span className="text-[7px] text-muted-foreground uppercase block">MAE</span>
                        <span className="text-white font-bold">{mae}</span>
                      </div>
                      <div>
                        <span className="text-[7px] text-muted-foreground uppercase block">
                          {r2 ? "R² Score" : "Accuracy"}
                        </span>
                        <span className="text-white font-bold">{r2 || accuracy || "N/A"}</span>
                      </div>
                      <div>
                        <span className="text-[7px] text-muted-foreground uppercase block">Drift</span>
                        <span className={`font-bold ${model.drift_score && model.drift_score > 0.1 ? "text-amber-400" : "text-emerald-400"}`}>
                          {drift}
                        </span>
                      </div>
                    </div>

                    <div className="flex justify-between items-center mt-2 text-[8px] text-muted-foreground">
                      <span>Total Inferences: {model.prediction_count}</span>
                      {model.last_trained && (
                        <span>Trained: {new Date(model.last_trained).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}