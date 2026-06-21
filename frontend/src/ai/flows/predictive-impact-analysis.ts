'use server';
/**
 * @fileOverview This file implements a Genkit flow for performing predictive impact analysis of traffic incidents.
 *
 * - predictiveImpactAnalysis - A function that analyzes a traffic incident and provides predicted impact, severity, and contributing factors.
 * - PredictiveImpactAnalysisInput - The input type for the predictiveImpactAnalysis function.
 * - PredictiveImpactAnalysisOutput - The return type for the predictiveImpactAnalysis function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

// Input Schema
const PredictiveImpactAnalysisInputSchema = z.object({
  incidentDescription: z.string().describe('A detailed description of the traffic incident.'),
  incidentType: z.enum(['accident', 'breakdown', 'road_closure', 'protest', 'event', 'other']).describe('The type of traffic incident.'),
  locationDescription: z.string().describe('A clear description of the incident location (e.g., "near Silk Board junction", "on Highway 101 North at Exit 23").'),
  currentTrafficLevel: z.enum(['light', 'moderate', 'heavy', 'gridlock']).describe('The current traffic density in the vicinity of the incident.'),
  timeOfDay: z.enum(['morning_rush', 'midday', 'evening_rush', 'night']).describe('The time of day when the incident occurred or was reported.'),
  weatherConditions: z.string().optional().describe('Current weather conditions (e.g., "clear", "rainy", "foggy").')
});
export type PredictiveImpactAnalysisInput = z.infer<typeof PredictiveImpactAnalysisInputSchema>;

// Output Schema
const PredictiveImpactAnalysisOutputSchema = z.object({
  impactScore: z.number().int().min(0).max(100).describe('A numerical score (0-100) indicating the overall predicted impact of the incident, where 100 is maximum impact.'),
  severityLevel: z.enum(['Low', 'Medium', 'High', 'Critical']).describe('A categorized severity level for the incident.'),
  confidenceScore: z.number().int().min(0).max(100).describe('A numerical score (0-100) indicating the model\'s confidence in its prediction.'),
  contributingFactors: z.array(z.string()).describe('A list of key factors contributing to the predicted impact and severity.')
});
export type PredictiveImpactAnalysisOutput = z.infer<typeof PredictiveImpactAnalysisOutputSchema>;

// Prompt definition
const predictiveImpactPrompt = ai.definePrompt({
  name: 'predictiveImpactPrompt',
  input: {schema: PredictiveImpactAnalysisInputSchema},
  output: {schema: PredictiveImpactAnalysisOutputSchema},
  prompt: `You are an expert Traffic Intelligence System. Your task is to analyze a given traffic incident and provide a predicted impact score, severity level, confidence score, and a list of key contributing factors.\n\nConsider the following details for the incident:\n\nIncident Description: {{{incidentDescription}}}\nIncident Type: {{{incidentType}}}\nLocation: {{{locationDescription}}}\nCurrent Traffic Level: {{{currentTrafficLevel}}}\nTime of Day: {{{timeOfDay}}}\n{{#if weatherConditions}}\nWeather Conditions: {{{weatherConditions}}}\n{{/if}}\n\nBased on the provided information, assess the potential disruption to traffic flow, public safety, and required resources. Assign an impact score from 0 (no impact) to 100 (catastrophic impact), categorize the severity, and explain the main reasons for your assessment as contributing factors. The confidence score should reflect how certain you are about the prediction given the input.\n`
});

// Flow definition
const predictiveImpactAnalysisFlow = ai.defineFlow(
  {
    name: 'predictiveImpactAnalysisFlow',
    inputSchema: PredictiveImpactAnalysisInputSchema,
    outputSchema: PredictiveImpactAnalysisOutputSchema
  },
  async (input) => {
    const { output } = await predictiveImpactPrompt(input);
    if (!output) {
      throw new Error('Failed to get output from predictive impact prompt.');
    }
    return output;
  }
);

// Wrapper function
export async function predictiveImpactAnalysis(input: PredictiveImpactAnalysisInput): Promise<PredictiveImpactAnalysisOutput> {
  return predictiveImpactAnalysisFlow(input);
}
