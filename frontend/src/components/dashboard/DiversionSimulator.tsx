
import { MapPin, Route, Info, AlertCircle, TrendingUp, Users, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard } from "@/context/DashboardContext";
import { useState, useEffect } from "react";

export default function DiversionSimulator() {
  const { selectedEvent, diversion, simulateRoadClosure, mapLoading } = useDashboard();
  const [radius, setRadius] = useState(500); // meters

  const handleSimulate = async () => {
    if (!selectedEvent) return;
    await simulateRoadClosure(selectedEvent.latitude, selectedEvent.longitude, radius);
  };

  // Sync radius with selected event changes or default
  useEffect(() => {
    if (diversion && diversion.alternative_routes.length > 0) {
      // Use existing diversion if present
    }
  }, [selectedEvent]);

  const riskScore = diversion ? diversion.congestion_risk_score : 0;
  const riskLevel = riskScore >= 75 ? "CRITICAL_THREAT" : 
                    riskScore >= 50 ? "HIGH_THREAT" : 
                    riskScore >= 25 ? "MODERATE_THREAT" : "LOW_THREAT";

  const delayText = diversion ? `+${Math.round(diversion.estimated_extra_travel_time)}` : "0";
  
  // Calculate simulated commuters based on risk score and blocked roads
  const blockedLength = diversion?.blocked_roads.reduce((sum, r) => sum + (r.length_m || 300), 0) || 0;
  const commuters = diversion ? Math.round(blockedLength * (riskScore / 50) + 120) : 0;
  const commutersFormatted = commuters >= 1000 ? `${(commuters / 1000).toFixed(1)}k` : `${commuters}`;

  return (
    <div className="flex flex-col h-full bg-[#05070a] relative">
      {mapLoading && (
        <div className="absolute inset-0 bg-black/75 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-2">
          <Loader2 className="animate-spin text-primary" size={24} />
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white">Simulating Detour Paths...</span>
        </div>
      )}
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-primary">
              <Route size={16} />
              <h3 className="font-headline font-bold text-xs tracking-widest uppercase text-white">Simulation Engine</h3>
            </div>
            
            <div className="space-y-3">
              <label className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Active Closure Point</label>
              <div className="relative">
                <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-primary" />
                <input 
                  type="text" 
                  value={selectedEvent ? `${selectedEvent.junction || selectedEvent.event_cause} @ ${selectedEvent.latitude.toFixed(4)}, ${selectedEvent.longitude.toFixed(4)}` : "No incident selected"}
                  disabled
                  className="w-full bg-white/5 border border-white/10 rounded-md pl-10 pr-4 py-2.5 text-[10px] font-mono text-white/50 cursor-not-allowed"
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Propagation Radius</label>
                <span className="text-[11px] font-mono font-bold text-primary">{radius} M</span>
              </div>
              <input 
                type="range" 
                className="w-full accent-primary h-1.5" 
                min="100" 
                max="2000" 
                step="100"
                value={radius} 
                onChange={(e) => setRadius(Number(e.target.value))}
              />
            </div>

            <Button 
              onClick={handleSimulate}
              disabled={!selectedEvent}
              className="w-full bg-primary/20 border border-primary/40 text-primary hover:bg-primary hover:text-white transition-all font-black text-[10px] uppercase tracking-[0.2em] h-10 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Initialize Scenario
            </Button>
          </div>

          <div className="border-t border-white/5 pt-6 space-y-5">
            <div className="flex items-center justify-between">
               <span className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Predicted Impact Level</span>
               <Badge className={`border text-[9px] uppercase font-black px-3 py-1 ${
                 riskLevel.includes("CRITICAL") ? "bg-red-500/20 text-red-400 border-red-500/40" :
                 riskLevel.includes("HIGH") ? "bg-orange-500/20 text-orange-400 border-orange-500/40" :
                 riskLevel.includes("MODERATE") ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/40" :
                 "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
               }`}>{riskLevel}</Badge>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/40 p-4 rounded-xl border border-white/5 flex flex-col items-center gap-1 shadow-inner">
                <TrendingUp size={14} className="text-red-400 mb-1" />
                <span className="text-2xl font-headline font-bold text-white">{delayText}</span>
                <span className="text-[9px] uppercase font-black text-muted-foreground text-center tracking-tighter">Delay Escalation (Min)</span>
              </div>
              <div className="bg-black/40 p-4 rounded-xl border border-white/5 flex flex-col items-center gap-1 shadow-inner">
                <Users size={14} className="text-primary mb-1" />
                <span className="text-2xl font-headline font-bold text-white">{commutersFormatted}</span>
                <span className="text-[9px] uppercase font-black text-muted-foreground text-center tracking-tighter">Affected Commuters</span>
              </div>
            </div>

            <div className="space-y-3">
               <span className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Strategic Diversions</span>
               <div className="bg-white/[0.03] p-4 rounded-xl text-[11px] leading-relaxed text-white/90 border border-white/10 shadow-xl">
                  {diversion && diversion.alternative_routes.length > 0 ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-primary font-black uppercase tracking-widest text-[9px]">
                        <AlertCircle size={14} /> Detours Computed
                      </div>
                      <p>
                        OSM graph analyzed. Blocked segments: <span className="text-orange-400 font-bold">{diversion.blocked_roads.map(r => r.name || 'Unnamed segment').slice(0, 2).join(', ') || 'Primary link'}</span>.
                      </p>
                      <p className="mt-1">
                        Detour route found: <span className="text-primary font-bold">{(diversion.alternative_routes[0].distance_m / 1000).toFixed(2)} km</span> via secondary link. Est. detour travel time: <span className="text-primary font-bold">{diversion.alternative_routes[0].estimated_time_min.toFixed(1)} mins</span>.
                      </p>
                    </div>
                  ) : (
                    <div>
                      <div className="flex items-center gap-2 mb-2 text-muted-foreground font-black uppercase tracking-widest text-[9px]">
                        <Info size={14} /> Standby Mode
                      </div>
                      No road closure simulated. Enable closure or click "Initialize Scenario" to compute shortest path detours on the Bengaluru spatial network.
                    </div>
                  )}
               </div>
            </div>
            
            <div className="space-y-3">
               <span className="text-[10px] uppercase font-black text-muted-foreground tracking-widest">Affected Junctions</span>
               <div className="grid grid-cols-1 gap-2">
                  {diversion && diversion.affected_junctions.length > 0 ? (
                    diversion.affected_junctions.slice(0, 4).map((j, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 bg-white/5 rounded-md border border-white/5">
                        <span className="text-[10px] font-mono text-white/70">{j}</span>
                        <span className="text-[8px] font-black uppercase px-2 py-0.5 rounded bg-orange-500/20 text-orange-400">HIGH_FLOW</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-4 text-white/30 text-[9px] uppercase font-bold tracking-widest bg-white/[0.02] border border-dashed border-white/10 rounded-lg">
                      No affected junctions logged
                    </div>
                  )}
               </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
