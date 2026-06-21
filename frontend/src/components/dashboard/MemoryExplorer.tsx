
import { History, Search, ExternalLink, Download, Loader2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDashboard } from "@/context/DashboardContext";

export default function MemoryExplorer() {
  const { similar, loading, selectEvent, events } = useDashboard();

  const pastEvents = similar?.similar_events ? similar.similar_events.map(e => {
    // Try to find the full event from our cache
    const matchedEvent = events.find(evt => evt.id === e.id);
    return {
      id: e.id,
      date: matchedEvent?.start_datetime ? new Date(matchedEvent.start_datetime).toLocaleDateString() : "Historical",
      type: e.event_cause,
      location: e.junction && e.junction !== 'unknown' ? `${e.junction} (${e.zone || 'unknown'})` : (e.zone || 'unknown'),
      resolution: e.resolution_minutes ? `${Math.round(e.resolution_minutes)} min` : "unknown",
      success: Math.round(e.similarity_score * 100),
      rawEvent: matchedEvent || {
        id: e.id,
        event_type: "unplanned",
        event_cause: e.event_cause,
        zone: e.zone || "unknown",
        junction: e.junction || "unknown",
        requires_road_closure: false,
        description: e.description || "",
        latitude: 12.9716,
        longitude: 77.5946,
      }
    };
  }) : [];

  return (
    <div className="flex flex-col h-full bg-[#05070a] relative">
      {loading && (
        <div className="absolute inset-0 bg-black/75 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-2">
          <Loader2 className="animate-spin text-primary" size={24} />
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white">Retrieving Similarity Matrix...</span>
        </div>
      )}
      {/* Search & Actions */}
      <div className="p-4 border-b border-white/5 bg-black/20 space-y-3">
        <div className="flex items-center gap-2 mb-1">
          <History size={14} className="text-primary" />
          <span className="text-[10px] font-black uppercase tracking-widest text-white/80">Historical Uplink</span>
        </div>
        <div className="relative">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Search tactical archives..." 
            className="w-full bg-white/5 border border-white/10 rounded-md pl-9 pr-3 py-2 text-[10px] font-mono focus:ring-1 focus:ring-primary outline-none text-white"
          />
        </div>
        <button className="w-full flex items-center justify-center gap-2 py-2 text-[9px] font-black uppercase tracking-widest text-muted-foreground hover:text-white transition-colors bg-white/5 rounded border border-white/10">
          <Download size={12} /> Export Event Logs
        </button>
      </div>

      {/* Table Area */}
      <ScrollArea className="flex-1">
        <div className="p-0">
          {pastEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-muted-foreground text-[10px] uppercase font-bold tracking-widest">
              No historical matches found
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-[#05070a] sticky top-0 z-10 shadow-lg">
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="text-[9px] uppercase font-black tracking-widest text-white/40 pl-4 h-10">Event Details</TableHead>
                  <TableHead className="text-[9px] uppercase font-black tracking-widest text-white/40 h-10">Similarity</TableHead>
                  <TableHead className="text-[9px] uppercase font-black tracking-widest text-white/40 text-right pr-4 h-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pastEvents.map((event, i) => (
                  <TableRow key={i} className="border-white/5 hover:bg-primary/5 group">
                    <TableCell className="pl-4 py-4">
                      <div className="flex flex-col gap-1.5">
                        <div className="flex items-center gap-2">
                           <Badge variant="outline" className="text-[7px] uppercase font-black bg-black/40 border-white/10 text-primary">
                             {event.type.replace(/_/g, ' ')}
                           </Badge>
                           <span className="text-[9px] font-mono text-white/40">{event.date}</span>
                        </div>
                        <span className="text-[11px] font-bold text-white leading-tight">{event.location}</span>
                        <span className="text-[8px] font-mono text-muted-foreground uppercase tracking-wider">Resolution: {event.resolution}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-4">
                      <div className="flex flex-col gap-1.5 items-start">
                        <span className="text-[11px] font-mono font-bold text-primary">{event.success}%</span>
                        <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: `${event.success}%` }} />
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right pr-4 py-4">
                      <button 
                        onClick={() => selectEvent(event.rawEvent as any)}
                        className="text-white/20 hover:text-primary transition-colors p-2"
                        title="Load Incident"
                      >
                        <ExternalLink size={14} />
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
