"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import { Layers, AlertTriangle, ZoomIn, ZoomOut, Navigation, Compass } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TrafficEvent, DiversionResponse } from "@/lib/api";

interface LeafletMapProps {
  events: TrafficEvent[];
  selectedEvent: TrafficEvent | null;
  diversion: DiversionResponse | null;
  selectEvent: (event: TrafficEvent) => Promise<void>;
  mapLoading: boolean;
}

export default function LeafletMap({ events, selectedEvent, diversion, selectEvent, mapLoading }: LeafletMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const routesLayerRef = useRef<L.LayerGroup | null>(null);

  // Initialize Leaflet Map instance
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Centered on Bengaluru city center
    const map = L.map(mapContainerRef.current, {
      center: [12.9716, 77.5946],
      zoom: 13,
      zoomControl: false,
      attributionControl: false
    });

    // Dark themed tactical tiles from CartoDB (Dark Matter)
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 20
    }).addTo(map);

    mapInstanceRef.current = map;
    markersLayerRef.current = L.layerGroup().addTo(map);
    routesLayerRef.current = L.layerGroup().addTo(map);

    // Add a custom attribution control in the corner manually
    L.control.attribution({ prefix: false }).addAttribution('&copy; CartoDB & OpenStreetMap').addTo(map);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update map features when events, selectedEvent or diversion changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    const routesLayer = routesLayerRef.current;

    if (!map || !markersLayer || !routesLayer) return;

    // Clean old layers
    markersLayer.clearLayers();
    routesLayer.clearLayers();

    // 1. Draw Normal Flow Corridors (from API response)
    if (diversion && diversion.normal_roads && diversion.normal_roads.length > 0) {
      diversion.normal_roads.forEach((road) => {
        if (road.coords && road.coords.length > 0) {
          const polyline = L.polyline(road.coords as L.LatLngExpression[], {
            color: road.flow_level === "congested" ? "#f59e0b" : "#10b981", // Orange if slow, emerald for normal flow
            weight: 3,
            opacity: 0.5,
            className: "normal-flow-line"
          });
          polyline.addTo(routesLayer);
        }
      });
    }

    // 2. Draw Blocked Roads (solid glowing red lines)
    if (diversion && diversion.blocked_roads && diversion.blocked_roads.length > 0) {
      diversion.blocked_roads.forEach((road) => {
        if (road.coords && road.coords.length > 0) {
          const polyline = L.polyline(road.coords as L.LatLngExpression[], {
            color: "#ef4444",
            weight: 7,
            opacity: 0.9,
            className: "blocked-road-line"
          });
          polyline.addTo(routesLayer);

          // Tooltip showing blocked road name
          polyline.bindTooltip(`CLOSED: ${road.name}`, {
            permanent: true,
            direction: "center",
            className: "bg-red-950/90 border border-red-500/30 text-red-300 font-bold px-2 py-0.5 rounded text-[8px] uppercase tracking-wider shadow-2xl"
          });
        }
      });
    }

    // 3. Draw Alternative Detour Routes (neon blue flowing paths)
    if (diversion && diversion.alternative_routes && diversion.alternative_routes.length > 0) {
      diversion.alternative_routes.forEach((route) => {
        if (route.route_coords && route.route_coords.length > 0) {
          const polyline = L.polyline(route.route_coords as L.LatLngExpression[], {
            color: "#0091ff",
            weight: 5,
            opacity: 0.95,
            className: "detour-flow-line"
          });
          polyline.addTo(routesLayer);

          // Add arrows or tooltip for detour route
          polyline.bindTooltip(`DETOUR: ${(route.distance_m / 1000).toFixed(2)} km`, {
            sticky: true,
            className: "bg-blue-950/90 border border-blue-500/30 text-blue-300 font-bold px-2 py-0.5 rounded text-[8px] uppercase tracking-wider"
          });
        }
      });
    }

    // 4. Render Incident Markers on Map
    events.slice(0, 30).forEach((event) => {
      const isSelected = selectedEvent?.id === event.id;
      const score = event.impact_score || (event.priority === "High" ? 65 : 25);
      const severity = score >= 75 ? "Critical" :
                       score >= 50 ? "High" :
                       score >= 25 ? "Medium" : "Low";

      // Dynamic color classes based on severity
      let colorClass = "bg-emerald-500 border-emerald-300 shadow-emerald-500/50";
      if (severity === "Critical") colorClass = "bg-red-500 border-red-400 shadow-red-500/50 animate-pulse";
      else if (severity === "High") colorClass = "bg-orange-500 border-orange-400 shadow-orange-500/50 animate-pulse";
      else if (severity === "Medium") colorClass = "bg-yellow-500 border-yellow-300 shadow-yellow-500/50";

      // Glow indicators for selected incident
      const ringGlow = isSelected 
        ? "ring-4 ring-primary ring-offset-2 ring-offset-black scale-125 border-white animate-pulse" 
        : "";

      // Custom marker icon HTML matching overall theme
      const icon = L.divIcon({
        className: "custom-leaflet-marker",
        html: `
          <div class="relative flex items-center justify-center w-10 h-10">
            <!-- Pulsing outer ring -->
            <div class="absolute w-8 h-8 rounded-full opacity-20 blur-xs ${isSelected ? 'bg-primary animate-ping' : 'bg-transparent'}"></div>
            <!-- Glow background -->
            <div class="absolute w-5 h-5 rounded-full opacity-35 blur-xs ${severity === 'Critical' ? 'bg-red-500' : severity === 'High' ? 'bg-orange-500' : 'bg-emerald-500'}"></div>
            <!-- Core Dot -->
            <div class="w-3.5 h-3.5 rounded-full border-2 shadow-2xl transition-all duration-300 ${colorClass} ${ringGlow}"></div>
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
      });

      const marker = L.marker([event.latitude, event.longitude], { icon });
      
      // Select event on click
      marker.on("click", () => {
        selectEvent(event);
      });

      // Dark theme tactical tooltip
      const titleName = event.junction && event.junction !== "unknown" 
        ? event.junction 
        : `${event.event_cause.replace(/_/g, ' ').toUpperCase()}`;

      marker.bindTooltip(`
        <div class="bg-[#05070a] border border-white/15 text-white p-2 rounded shadow-2xl text-[9px] font-bold uppercase tracking-wider min-w-[140px]">
          <div class="text-primary flex items-center justify-between gap-2 border-b border-white/5 pb-1 mb-1">
            <span>${titleName.substring(0, 20)}</span>
            <span class="text-[7px] font-mono text-muted-foreground">${event.id}</span>
          </div>
          <div class="flex items-center gap-1.5 text-white/70 text-[8px] font-normal">
            <span class="w-1.5 h-1.5 rounded-full ${severity === 'Critical' ? 'bg-red-500' : severity === 'High' ? 'bg-orange-500' : 'bg-emerald-500'}"></span>
            ${event.event_cause.replace(/_/g, ' ')} (${severity})
          </div>
          <div class="text-[7px] font-mono text-muted-foreground mt-1 lowercase">${event.status} | priority: ${event.priority}</div>
        </div>
      `, {
        direction: "top",
        offset: [0, -12],
        className: "custom-leaflet-tooltip",
        opacity: 0.95
      });

      marker.addTo(markersLayer);
    });

    // 5. Fit bounds to show incident + detour when selected
    if (selectedEvent) {
      if (diversion && diversion.alternative_routes && diversion.alternative_routes.length > 0) {
        const points: L.LatLngExpression[] = [
          [selectedEvent.latitude, selectedEvent.longitude]
        ];

        diversion.alternative_routes.forEach((route) => {
          route.route_coords.forEach(([lat, lng]) => {
            points.push([lat, lng]);
          });
        });

        if (diversion.blocked_roads) {
          diversion.blocked_roads.forEach((road) => {
            if (road.coords) {
              road.coords.forEach(([lat, lng]) => {
                points.push([lat, lng]);
              });
            }
          });
        }

        const bounds = L.latLngBounds(points);
        map.fitBounds(bounds, {
          padding: [60, 60],
          maxZoom: 16,
          animate: true,
          duration: 1.2
        });
      } else {
        map.setView([selectedEvent.latitude, selectedEvent.longitude], 15, {
          animate: true,
          duration: 1.0
        });
      }
    }
  }, [events, selectedEvent, diversion, selectEvent]);

  // HUD controller actions
  const handleZoomIn = () => {
    mapInstanceRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    mapInstanceRef.current?.zoomOut();
  };

  const handleRecenter = () => {
    if (!mapInstanceRef.current) return;
    if (selectedEvent) {
      mapInstanceRef.current.setView([selectedEvent.latitude, selectedEvent.longitude], 15, { animate: true });
    } else {
      mapInstanceRef.current.setView([12.9716, 77.5946], 13, { animate: true });
    }
  };

  // Counting unresolved critical/high incidents
  const unresolvedAlertCount = events.filter(
    (e) => (e.priority === "High" || e.impact_score && e.impact_score >= 75) && e.status === "active"
  ).length;

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#05070a] border border-white/5 rounded-lg shadow-inner">
      {/* Map Container DOM Element */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Map loading state spinner overlay */}
      {mapLoading && (
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-[1000] flex flex-col items-center justify-center gap-2">
          <div className="w-8 h-8 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
          <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white">Re-routing Spatial Grid...</span>
        </div>
      )}

      {/* Visual Map Gradient Overlay (Edges fade out) */}
      <div className="absolute inset-0 pointer-events-none map-gradient z-10" />

      {/* Tactical HUD (Controls Overlay) */}
      <div className="absolute top-6 left-6 flex flex-col gap-3 z-20">
        <div className="bg-black/85 backdrop-blur-xl border border-white/10 p-1.5 rounded-lg flex flex-col gap-1.5 shadow-2xl">
          <button 
            className="p-2 hover:bg-white/10 text-muted-foreground hover:text-white rounded transition-all"
            title="Toggle Map Layers"
          >
            <Layers size={16} />
          </button>
          <button 
            className="p-2 hover:bg-white/10 text-muted-foreground hover:text-white rounded transition-all"
            onClick={handleRecenter}
            title="Recenter Map"
          >
            <Navigation size={16} />
          </button>
          <div className="h-px bg-white/10 mx-1 my-0.5" />
          <button 
            className="p-2 hover:bg-white/10 text-muted-foreground hover:text-white rounded transition-all" 
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button 
            className="p-2 hover:bg-white/10 text-muted-foreground hover:text-white rounded transition-all" 
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
        </div>
      </div>

      {/* Compass Overlay HUD */}
      <div className="absolute top-6 right-6 flex items-center gap-2 z-20 pointer-events-none opacity-40">
        <div className="bg-black/60 backdrop-blur-md p-2 rounded-full border border-white/10">
          <Compass size={20} className="text-white animate-pulse" />
        </div>
      </div>

      {/* Center Coordinate Display Overlay */}
      <div className="absolute bottom-6 left-6 flex items-center gap-2 z-20">
        <div className="bg-black/85 backdrop-blur-md px-3.5 py-2 rounded border border-white/10 flex flex-col shadow-2xl">
          <span className="text-[7px] uppercase tracking-widest text-muted-foreground font-black">Operator Focus Zone</span>
          <span className="text-[9px] font-mono font-bold text-white uppercase mt-0.5">
            {selectedEvent 
              ? `${selectedEvent.latitude.toFixed(4)}° N / ${selectedEvent.longitude.toFixed(4)}° E` 
              : "12.9716° N / 77.5946° E (BENGALURU)"}
          </span>
        </div>
      </div>

      {/* Incidents Alert Hud Overlay */}
      <div className="absolute bottom-6 right-6 flex gap-2 z-20">
        <Badge className="bg-red-500/15 border-red-500/25 text-red-400 text-[9px] py-1.5 px-3 gap-2 backdrop-blur-md font-bold uppercase tracking-wider shadow-2xl">
          <AlertTriangle size={11} className="animate-bounce" /> 
          SYSTEM_ALERT: {unresolvedAlertCount} CRITICAL EVENTS UNRESOLVED
        </Badge>
      </div>

      {/* Custom Styles overrides for Leaflet elements inside this component */}
      <style jsx global>{`
        .leaflet-tooltip-pane {
          z-index: 650;
        }
        .custom-leaflet-tooltip {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          padding: 0 !important;
        }
        .custom-leaflet-tooltip::before {
          display: none !important;
        }
        .leaflet-tooltip-dark {
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
        }
        .leaflet-bar {
          border: none !important;
          box-shadow: none !important;
        }
      `}</style>
    </div>
  );
}
