'use server';
/**
 * @fileOverview An AI agent that recommends optimal resources for traffic incidents.
 *
 * - intelligentResourceRecommendation - A function that handles the resource recommendation process.
 * - IntelligentResourceRecommendationInput - The input type for the intelligentResourceRecommendation function.
 * - IntelligentResourceRecommendationOutput - The return type for the intelligentResourceRecommendation function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const IntelligentResourceRecommendationInputSchema = z.object({
  incidentType: z
    .string()
    .describe('The type of traffic incident (e.g., "accident", "breakdown", "congestion").'),
  locationDescription: z.string().describe('A description of the incident location.'),
  severity: z
    .enum(['Low', 'Medium', 'High', 'Critical'])
    .describe('The severity level of the incident.'),
  currentTrafficImpact: z
    .enum(['Green', 'Yellow', 'Orange', 'Red'])
    .describe('The current traffic impact level, color-coded.'),
  affectedJunctions: z.array(z.string()).describe('A list of junctions or zones affected by the incident.'),
  estimatedDurationMinutes: z
    .number()
    .optional()
    .describe('An optional initial estimate of the incident duration in minutes.'),
});
export type IntelligentResourceRecommendationInput = z.infer<
  typeof IntelligentResourceRecommendationInputSchema
>;

const IntelligentResourceRecommendationOutputSchema = z.object({
  officersRequired: z.number().describe('The recommended number of traffic officers needed.'),
  barricadesRequired: z.number().describe('The recommended number of barricades needed.'),
  towVehiclesRequired: z.number().describe('The recommended number of tow vehicles needed.'),
  estimatedResolutionTimeMinutes: z
    .number()
    .describe('The estimated time to resolve the incident in minutes.'),
  recommendationConfidence: z
    .number()
    .min(0)
    .max(100)
    .describe('Confidence level of the recommendation (0-100).'),
  reasoning: z.string().describe('The reasoning behind the resource recommendations.'),
});
export type IntelligentResourceRecommendationOutput = z.infer<
  typeof IntelligentResourceRecommendationOutputSchema
>;

export async function intelligentResourceRecommendation(
  input: IntelligentResourceRecommendationInput
): Promise<IntelligentResourceRecommendationOutput> {
  return intelligentResourceRecommendationFlow(input);
}

const prompt = ai.definePrompt({
  name: 'intelligentResourceRecommendationPrompt',
  input: {schema: IntelligentResourceRecommendationInputSchema},
  output: {schema: IntelligentResourceRecommendationOutputSchema},
  prompt: `You are an expert traffic incident manager within the TRINETRA AI system. Your task is to recommend optimal resources and estimated resolution time for a given traffic incident.

Consider the following incident details:

Incident Type: {{{incidentType}}}
Location: {{{locationDescription}}}
Severity: {{{severity}}}
Current Traffic Impact: {{{currentTrafficImpact}}}
Affected Junctions: {{{affectedJunctions}}}
{{#if estimatedDurationMinutes}}Estimated Initial Duration: {{{estimatedDurationMinutes}}} minutes{{/if}}

Based on historical patterns, current traffic telemetry, and best practices for incident management, provide the following recommendations:

- The optimal number of officers required.
- The optimal number of barricades required.
- The optimal number of tow vehicles required.
- An estimated resolution time in minutes.
- A confidence score (0-100) for your recommendation.
- A brief reasoning for your recommendations.

Aim for efficient deployment while ensuring safety and quick resolution.`,
});

const intelligentResourceRecommendationFlow = ai.defineFlow(
  {
    name: 'intelligentResourceRecommendationFlow',
    inputSchema: IntelligentResourceRecommendationInputSchema,
    outputSchema: IntelligentResourceRecommendationOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    if (!output) {
      throw new Error('Failed to get a recommendation from the AI.');
    }
    return output;
  }
);
