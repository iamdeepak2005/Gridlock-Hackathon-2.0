
import { Activity, Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard } from "@/context/DashboardContext";

export default function ImpactDashboard() {
  const { impact, loading } = useDashboard();

  const impactData = impact ? {
    score: Math.round(impact.impact_score),
    severity: (impact.impact_level || 'Low') as 'Low' | 'Medium' | 'High' | 'Critical',
    confidence: Math.round(impact.confidence * 100),
    factors: (impact.top_contributing_factors || []).map(f => ({
      name: f.feature.replace(/_/g, ' '),
      weight: Math.round(f.importance * 100)
    }))
  } : {
    score: 0,
    severity: 'Low' as const,
    confidence: 100,
    factors: []
  };

  return (
    <div className="p-4 flex flex-col h-full bg-[#0a0d14] overflow-hidden relative">
      {loading && (
        <div className="absolute inset-0 bg-black/75 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-2">
          <Loader2 className="animate-spin text-primary" size={24} />
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white">Running ML Inference...</span>
        </div>
      )}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-destructive/20 flex items-center justify-center border border-destructive/40 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
            <Activity size={16} className="text-destructive" />
          </div>
          <div>
            <h3 className="font-headline font-bold text-[10px] tracking-[0.2em] uppercase text-white">Predictive Impact</h3>
            <span className="text-[7px] font-bold text-muted-foreground uppercase tracking-widest">Neural_Analyzer_v4</span>
          </div>
        </div>
        <Badge variant="outline" className="text-[8px] border-primary/40 bg-primary/10 text-primary uppercase font-black px-1.5 py-0.5">AI_SYNC_ACTIVE</Badge>
      </div>

      <ScrollArea className="flex-1">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start pb-4 pr-3">
          <div className="flex flex-col items-center justify-center bg-black/40 border border-white/5 rounded-xl py-8 relative overflow-hidden group shadow-2xl">
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,rgba(239,68,68,0.3),transparent)] group-hover:opacity-20 transition-opacity" />
            <span className="text-5xl font-headline font-bold text-white mb-1 drop-shadow-[0_0_30px_rgba(0,145,255,0.4)]">{impactData.score}</span>
            <span className="text-[9px] uppercase font-bold text-muted-foreground tracking-widest">Risk Score</span>
            <Badge className={`mt-4 text-white border-none uppercase text-[8px] font-black px-4 py-1 animate-pulse ${
              impactData.severity === 'Critical' ? 'bg-red-500' :
              impactData.severity === 'High' ? 'bg-orange-500' :
              impactData.severity === 'Medium' ? 'bg-yellow-500' : 'bg-emerald-500'
            }`}>{impactData.severity}</Badge>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-[10px] uppercase font-black text-white tracking-widest">
                <span className="text-muted-foreground">Confidence</span>
                <span className="text-primary">{impactData.confidence}%</span>
              </div>
              <Progress value={impactData.confidence} className="h-1.5 bg-white/5 border border-white/5" />
            </div>
            
            <div className="space-y-3">
              <span className="text-[9px] uppercase font-black text-muted-foreground tracking-[0.15em] block">Risk Profile</span>
              <div className="grid gap-3">
                {impactData.factors.map(f => (
                  <div key={f.name} className="flex flex-col gap-1.5">
                     <div className="flex justify-between items-center text-[10px] font-bold text-white/90">
                        <span>{f.name}</span>
                        <span className="text-primary font-mono">{f.weight}%</span>
                     </div>
                     <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-primary transition-all duration-1000" style={{ width: `${f.weight}%` }} />
                     </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
