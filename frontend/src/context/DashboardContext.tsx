"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  trinetraApi, 
  TrafficEvent, 
  ImpactPrediction, 
  ResourceRecommendation, 
  SimilarEventsResponse, 
  ResolutionPrediction, 
  DiversionResponse,
  ModelPerformance 
} from '@/lib/api';

interface DashboardContextType {
  events: TrafficEvent[];
  selectedEvent: TrafficEvent | null;
  impact: ImpactPrediction | null;
  resources: ResourceRecommendation | null;
  similar: SimilarEventsResponse | null;
  resolution: ResolutionPrediction | null;
  diversion: DiversionResponse | null;
  performance: ModelPerformance | null;
  loading: boolean;
  mapLoading: boolean;
  refreshEvents: () => Promise<void>;
  selectEvent: (event: TrafficEvent) => Promise<void>;
  simulateRoadClosure: (lat: number, lng: number, radiusM: number) => Promise<void>;
  submitNewIncident: (incident: Omit<TrafficEvent, 'id' | 'status'> & { id?: string }) => Promise<void>;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [events, setEvents] = useState<TrafficEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<TrafficEvent | null>(null);
  const [impact, setImpact] = useState<ImpactPrediction | null>(null);
  const [resources, setResources] = useState<ResourceRecommendation | null>(null);
  const [similar, setSimilar] = useState<SimilarEventsResponse | null>(null);
  const [resolution, setResolution] = useState<ResolutionPrediction | null>(null);
  const [diversion, setDiversion] = useState<DiversionResponse | null>(null);
  const [performance, setPerformance] = useState<ModelPerformance | null>(null);
  const [loading, setLoading] = useState(false);
  const [mapLoading, setMapLoading] = useState(false);

  const refreshEvents = async () => {
    try {
      const data = await trinetraApi.getEvents(50);
      setEvents(data);
      if (data.length > 0 && !selectedEvent) {
        // Run analysis on the first event by default
        await selectEvent(data[0]);
      }
    } catch (error) {
      console.error("Failed to load events", error);
    }
  };

  const selectEvent = async (event: TrafficEvent) => {
    setSelectedEvent(event);
    setLoading(true);
    try {
      const payload = {
        event_type: event.event_type || "unplanned",
        event_cause: event.event_cause || "other",
        zone: event.zone || "unknown",
        junction: event.junction || "unknown",
        corridor: event.corridor || "Non-corridor",
        priority: event.priority || "Low",
        veh_type: event.veh_type || "unknown",
        requires_road_closure: event.requires_road_closure ?? false,
        start_datetime: event.start_datetime || new Date().toISOString(),
        description: event.description || "",
        latitude: event.latitude || 12.9716,
        longitude: event.longitude || 77.5946
      };

      // Call endpoints in parallel
      const [impactRes, resourcesRes, similarRes, resolutionRes] = await Promise.all([
        trinetraApi.predictImpact(payload),
        trinetraApi.recommendResources(payload),
        trinetraApi.findSimilarEvents(payload),
        trinetraApi.predictResolution(payload)
      ]);

      setImpact(impactRes);
      setResources(resourcesRes);
      setSimilar(similarRes);
      setResolution(resolutionRes);
      
      // Instantly unblock dashboard UI
      setLoading(false);

      // Trigger diversion simulation in background
      setMapLoading(true);
      try {
        const diversionRes = await trinetraApi.simulateDiversion({
          event_latitude: payload.latitude,
          event_longitude: payload.longitude,
          road_closure: payload.requires_road_closure,
          impact_radius_meters: 500
        });
        setDiversion(diversionRes);
      } catch (e) {
        console.error("Diversion simulation failed", e);
        setDiversion(null);
      } finally {
        setMapLoading(false);
      }
    } catch (error) {
      console.error("Error running event analysis", error);
      setLoading(false);
    }
  };

  const simulateRoadClosure = async (lat: number, lng: number, radiusM: number) => {
    setMapLoading(true);
    try {
      const diversionRes = await trinetraApi.simulateDiversion({
        event_latitude: lat,
        event_longitude: lng,
        road_closure: true,
        impact_radius_meters: radiusM
      });
      setDiversion(diversionRes);
    } catch (error) {
      console.error("Diversion simulation failed", error);
      setDiversion(null);
    } finally {
      setMapLoading(false);
    }
  };

  const submitNewIncident = async (incident: Omit<TrafficEvent, 'id' | 'status'> & { id?: string }) => {
    setLoading(true);
    try {
      const fullIncident: TrafficEvent = {
        id: incident.id || `FKID${Math.floor(100000 + Math.random() * 900000)}`,
        status: "active",
        ...incident
      };

      // Set as the current selected event
      setSelectedEvent(fullIncident);
      setEvents(prev => [fullIncident, ...prev]);

      // Analyze immediately
      await selectEvent(fullIncident);
    } catch (error) {
      console.error("Failed to submit incident", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshEvents();
    // Load performance metrics
    trinetraApi.getModelPerformance()
      .then(setPerformance)
      .catch(err => console.error("Failed to load metrics", err));
  }, []);

  return (
    <DashboardContext.Provider value={{
      events,
      selectedEvent,
      impact,
      resources,
      similar,
      resolution,
      diversion,
      performance,
      loading,
      mapLoading,
      refreshEvents,
      selectEvent,
      simulateRoadClosure,
      submitNewIncident
    }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
}
