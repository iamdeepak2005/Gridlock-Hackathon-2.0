export type Severity = 'Low' | 'Medium' | 'High' | 'Critical';
export type TrafficImpact = 'Green' | 'Yellow' | 'Orange' | 'Red';

export interface TrafficIncident {
  id: string;
  type: 'accident' | 'breakdown' | 'congestion' | 'road_closure' | 'protest';
  location: {
    lat: number;
    lng: number;
    description: string;
  };
  severity: Severity;
  impactLevel: TrafficImpact;
  timestamp: Date;
  affectedJunctions: string[];
}

export interface DeploymentPlan {
  officers: number;
  barricades: number;
  towVehicles: number;
  resolutionTime: number;
  confidence: number;
  reasoning: string;
}