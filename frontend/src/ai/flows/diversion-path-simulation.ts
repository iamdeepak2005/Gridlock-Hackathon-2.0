'use server';
/**
 * @fileOverview A Genkit flow for simulating traffic diversion paths due to road closures.
 *
 * - simulateDiversionPath - A function that handles the diversion path simulation process.
 * - DiversionPathSimulationInput - The input type for the simulateDiversionPath function.
 * - DiversionPathSimulationOutput - The return type for the simulateDiversionPath function.
 */

import { ai } from '@/ai/genkit';
import { z } from 'genkit';

const DiversionPathSimulationInputSchema = z.object({
  eventLocation: z
    .string()
    .describe(
      'A description or coordinates of the event location (e.g., "Near Main Street and Elm Avenue" or "34.0522,-118.2437").'
    ),
  roadClosureArea: z
    .string()
    .describe(
      'A description of the specific road segment or area that is closed (e.g., "Highway 101 between Exits 5 and 7" or "Intersection of Oak and Pine Street").'
    ),
  radius: z
    .number()
    .describe(
      'The radius in kilometers around the event location to consider for impact analysis.'
    ),
});
export type DiversionPathSimulationInput = z.infer<
  typeof DiversionPathSimulationInputSchema
>;

const DiversionPathSimulationOutputSchema = z.object({
  blockedRoads: z
    .array(z.string())
    .describe('A list of specific road names or segments that will be blocked.'),
  diversionPathsDescription: z
    .string()
    .describe('A descriptive summary of the primary diversion routes traffic will take.'),
  trafficRedistributionDescription: z
    .string()
    .describe(
      'A detailed description of how traffic will be redistributed across the road network.'
    ),
  extraTravelTimeMinutes: z
    .number()
    .describe('The estimated additional travel time in minutes for affected commuters.'),
  riskScore: z
    .enum(['Low', 'Medium', 'High', 'Critical'])
    .describe(
      'An assessment of the overall traffic impact risk (Low, Medium, High, Critical).'
    ),
  impactedJunctions: z
    .array(z.string())
    .describe('A list of key junctions that will be significantly impacted by the diversion.'),
});
export type DiversionPathSimulationOutput = z.infer<
  typeof DiversionPathSimulationOutputSchema
>;

export async function simulateDiversionPath(
  input: DiversionPathSimulationInput
): Promise<DiversionPathSimulationOutput> {
  return diversionPathSimulationFlow(input);
}

const prompt = ai.definePrompt({
  name: 'diversionPathSimulationPrompt',
  input: { schema: DiversionPathSimulationInputSchema },
  output: { schema: DiversionPathSimulationOutputSchema },
  prompt: `You are an expert traffic engineer and urban planner specializing in real-time traffic management and incident response. Your task is to simulate the impact of a road closure on traffic flow, calculate optimal diversion paths, and assess the overall risk to the urban network. Based on the provided event details, provide a structured analysis in JSON format.

Event Location: {{{eventLocation}}}
Road Closure Area: {{{roadClosureArea}}}
Radius of Impact: {{{radius}}} km

Based on this information, provide the following:
1.  **blockedRoads**: A list of specific road names or segments that will be rendered impassable due to the closure.
2.  **diversionPathsDescription**: A comprehensive description of the primary alternative routes that traffic will be redirected to. Explain how these paths manage the diverted volume.
3.  **trafficRedistributionDescription**: A detailed explanation of how traffic will be distributed across the wider road network, considering the primary and secondary diversion routes. Describe any expected bottlenecks or areas of increased congestion.
4.  **extraTravelTimeMinutes**: An estimated average additional travel time in minutes for commuters who would normally use the closed road, taking into account the diversion.
5.  **riskScore**: Assign a risk score (Low, Medium, High, Critical) to the overall traffic impact caused by this closure and diversion, based on severity, duration, and disruption.
6.  **impactedJunctions**: A list of key intersections or junctions that are expected to experience significant increases in traffic volume or congestion due to the diversion paths.`,
});

const diversionPathSimulationFlow = ai.defineFlow(
  {
    name: 'diversionPathSimulationFlow',
    inputSchema: DiversionPathSimulationInputSchema,
    outputSchema: DiversionPathSimulationOutputSchema,
  },
  async (input) => {
    const { output } = await prompt(input);
    return output!;
  }
);
