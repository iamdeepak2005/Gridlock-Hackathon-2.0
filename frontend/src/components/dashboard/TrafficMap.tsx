"use client";

import dynamic from "next/dynamic";
import { useDashboard } from "@/context/DashboardContext";

// Dynamically import the client-only LeafletMap component to bypass Next.js SSR issues
const LeafletMap = dynamic(
  () => import("./LeafletMap"),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full bg-[#05070a] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
        <span className="text-[9px] font-black uppercase tracking-[0.25em] text-white/50">Initializing Tactical Map...</span>
      </div>
    )
  }
);

export default function TrafficMap() {
  const { events, selectedEvent, diversion, selectEvent, mapLoading } = useDashboard();

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#05070a]">
      <LeafletMap 
        events={events}
        selectedEvent={selectedEvent}
        diversion={diversion}
        selectEvent={selectEvent}
        mapLoading={mapLoading}
      />
    </div>
  );
}
