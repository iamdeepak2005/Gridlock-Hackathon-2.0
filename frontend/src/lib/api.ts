/**
 * API Client for TRINETRA AI Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function apiRequest(path: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API error (${response.status}): ${errorBody || response.statusText}`);
  }

  return response.json();
}

export interface TrafficEvent {
  id: string;
  event_type: string;
  latitude: number;
  longitude: number;
  event_cause: string;
  requires_road_closure: boolean;
  status: string;
  priority: string;
  description: string;
  zone?: string;
  junction?: string;
  corridor?: string;
  veh_type?: string;
  resolution_minutes?: number;
  impact_score?: number;
  start_datetime?: string;
}

export interface ImpactPrediction {
  impact_score: number;
  impact_level: string;
  confidence: number;
  top_contributing_factors: Array<{ feature: string; importance: number }>;
}

export interface ResourceRecommendation {
  officers_required: number;
  barricades_required: number;
  tow_vehicles_required: number;
  estimated_resolution_time: number;
  confidence: number;
}

export interface SimilarEvent {
  id: string;
  event_cause: string;
  zone?: string;
  junction?: string;
  resolution_minutes?: number;
  similarity_score: number;
  description?: string;
}

export interface SimilarEventsResponse {
  similar_events: SimilarEvent[];
  average_resolution_time?: number;
  historical_success_patterns: string[];
  recommended_action: string;
}

export interface ResolutionPrediction {
  estimated_resolution_minutes: number;
  confidence: number;
  risk_level: string;
}

export interface BlockedRoad {
  name: string;
  from_node: number;
  to_node: number;
  length_m?: number;
  coords?: number[][];
}

export interface NormalRoad {
  name: string;
  coords: number[][];
  speed_kph: number;
  flow_level: string;
}

export interface DiversionResponse {
  blocked_roads: BlockedRoad[];
  alternative_routes: Array<{ route_coords: number[][]; distance_m: number; estimated_time_min: number }>;
  normal_roads?: NormalRoad[];
  estimated_extra_travel_time: number;
  congestion_risk_score: number;
  affected_junctions: string[];
}

export interface ModelPerformance {
  models: Array<{
    model_name: string;
    feature_name: string;
    model_type: string;
    mae?: number;
    rmse?: number;
    r2?: number;
    accuracy?: number;
    drift_score?: number;
    last_trained?: string;
    prediction_count: number;
    is_active: boolean;
  }>;
  total_predictions: number;
  feedback_count: number;
}

export const trinetraApi = {
  // Fetch real events from DB
  getEvents: (limit: number = 100, offset: number = 0): Promise<TrafficEvent[]> => 
    apiRequest(`/api/v1/events?limit=${limit}&offset=${offset}`),

  // Predict Impact
  predictImpact: (payload: any): Promise<ImpactPrediction> => 
    apiRequest('/api/v1/predict-impact', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Recommend Resources
  recommendResources: (payload: any): Promise<ResourceRecommendation> => 
    apiRequest('/api/v1/recommend-resources', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Find Similar Incidents
  findSimilarEvents: (payload: any): Promise<SimilarEventsResponse> => 
    apiRequest('/api/v1/similar-events', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Predict Resolution Time
  predictResolution: (payload: any): Promise<ResolutionPrediction> => 
    apiRequest('/api/v1/predict-resolution', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Simulate Traffic Diversion
  simulateDiversion: (payload: any): Promise<DiversionResponse> => 
    apiRequest('/api/v1/simulate-diversion', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Get Model Performance
  getModelPerformance: (): Promise<ModelPerformance> => 
    apiRequest('/api/v1/model-performance'),

  // Submit Feedback
  submitFeedback: (payload: { prediction_id: string; actual_outcome?: any; feedback_text?: string }) => 
    apiRequest('/api/v1/feedback', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Query Backend Copilot (Gemini)
  copilotQuery: (payload: { query: string }): Promise<{ response: string }> =>
    apiRequest('/api/v1/copilot', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
