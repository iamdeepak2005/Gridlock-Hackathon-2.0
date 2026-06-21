
import { Shield, Truck, Construction, Clock, CheckCircle2, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard } from "@/context/DashboardContext";

export default function ResourcePanel() {
  const { resources, loading } = useDashboard();

  const recommendations = resources ? [
    { icon: Shield, label: "Traffic Officers", value: resources.officers_required, unit: "UNITS", status: "Available" },
    { icon: Construction, label: "Barricades", value: resources.barricades_required, unit: "BLOCKS", status: "In Transit" },
    { icon: Truck, label: "Tow Vehicles", value: resources.tow_vehicles_required, unit: "TRUCKS", status: "Deployed" },
    { icon: Clock, label: "Est. Resolution", value: Math.round(resources.estimated_resolution_time), unit: "MINS", status: "Predicted" },
    { icon: Shield, label: "Medical Teams", value: resources.officers_required > 3 ? 1 : 0, unit: "UNITS", status: "Standby" },
    { icon: Truck, label: "Technical Support", value: resources.tow_vehicles_required > 0 ? 1 : 0, unit: "CREW", status: "Ready" },
  ] : [
    { icon: Shield, label: "Traffic Officers", value: 0, unit: "UNITS", status: "Available" },
    { icon: Construction, label: "Barricades", value: 0, unit: "BLOCKS", status: "In Transit" },
    { icon: Truck, label: "Tow Vehicles", value: 0, unit: "TRUCKS", status: "Deployed" },
    { icon: Clock, label: "Est. Resolution", value: 0, unit: "MINS", status: "Predicted" },
    { icon: Shield, label: "Medical Teams", value: 0, unit: "UNITS", status: "Standby" },
    { icon: Truck, label: "Technical Support", value: 0, unit: "CREW", status: "Ready" },
  ];

  const confidenceText = resources ? `${Math.round(resources.confidence * 100)}%` : "0%";

  return (
    <div className="p-4 flex flex-col h-full bg-[#0d1117] overflow-hidden relative">
      {loading && (
        <div className="absolute inset-0 bg-black/75 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-2">
          <Loader2 className="animate-spin text-accent" size={24} />
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white">Running ML Inference...</span>
        </div>
      )}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-accent/20 flex items-center justify-center border border-accent/40 shadow-[0_0_15px_rgba(124,58,237,0.2)]">
            <Shield size={16} className="text-accent" />
          </div>
          <div>
            <h3 className="font-headline font-bold text-[10px] tracking-[0.2em] uppercase text-accent">Resource Deployment</h3>
            <span className="text-[7px] font-bold text-muted-foreground uppercase tracking-widest">Tactical_Provisioning</span>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-black/40 px-2 py-0.5 rounded-full border border-white/5">
           <span className="text-[8px] font-black text-muted-foreground uppercase tracking-widest">Conf.</span>
           <span className="text-[10px] font-mono font-bold text-emerald-500">{confidenceText}</span>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pb-4 pr-3">
          {recommendations.map((item, i) => (
            <div key={i} className="bg-white/[0.03] border border-white/10 rounded-lg p-3 flex flex-col hover:border-accent/60 hover:bg-white/[0.06] transition-all group">
              <div className="flex items-center justify-between mb-2">
                <div className="w-6 h-6 rounded bg-accent/10 flex items-center justify-center border border-accent/20">
                  <item.icon size={12} className="text-accent" />
                </div>
                <span className={`text-[7px] font-black uppercase tracking-widest ${
                  item.status === 'Deployed' ? 'text-blue-400' : 
                  item.status === 'Available' ? 'text-emerald-400' : 'text-orange-400'
                }`}>
                  {item.status}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[8px] uppercase font-black text-muted-foreground tracking-widest mb-0.5">{item.label}</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-xl font-headline font-bold text-white tracking-tighter">{item.value}</span>
                  <span className="text-[8px] text-muted-foreground font-black tracking-widest">{item.unit}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="mt-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-start gap-3 shrink-0">
        <CheckCircle2 size={14} className="text-emerald-500 shrink-0 mt-0.5" />
        <p className="text-[9px] text-emerald-100/90 leading-relaxed font-medium">
          Deployment vectors optimized for <span className="text-emerald-400 font-black tracking-widest">ZERO_GRIDLOCK</span>.
        </p>
      </div>
    </div>
  );
}
