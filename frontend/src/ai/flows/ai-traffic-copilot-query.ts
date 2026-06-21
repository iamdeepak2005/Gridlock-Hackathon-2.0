'use server';
/**
 * @fileOverview This flow implements the AI Traffic Copilot, providing natural language responses
 * to queries about traffic incidents, trends, and resource deployment recommendations.
 *
 * - aiTrafficCopilotQuery - A function that handles natural language queries for the AI Copilot.
 * - AiTrafficCopilotQueryInput - The input type for the aiTrafficCopilotQuery function.
 * - AiTrafficCopilotQueryOutput - The return type for the aiTrafficCopilotQuery function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AiTrafficCopilotQueryInputSchema = z.object({
  query: z.string().describe('The natural language query from the traffic operator.'),
});
export type AiTrafficCopilotQueryInput = z.infer<typeof AiTrafficCopilotQueryInputSchema>;

const AiTrafficCopilotQueryOutputSchema = z.string().describe('The AI Copilot\u0027s natural language response.');
export type AiTrafficCopilotQueryOutput = z.infer<typeof AiTrafficCopilotQueryOutputSchema>;

export async function aiTrafficCopilotQuery(
  input: AiTrafficCopilotQueryInput
): Promise<AiTrafficCopilotQueryOutput> {
  return aiTrafficCopilotQueryFlow(input);
}

const prompt = ai.definePrompt({
  name: 'aiTrafficCopilotPrompt',
  input: {schema: AiTrafficCopilotQueryInputSchema},
  prompt: `You are Trinetra AI, an advanced Traffic Copilot designed for city traffic police operations in Bengaluru. Your goal is to provide quick, accurate, and actionable insights to operators.

If the operator is describing or reporting a new traffic incident (e.g. "Report a vehicle breakdown on Hebbal Flyover", "There is a major accident near Silk Board", "Protest blocking Richmond Road"), you must perform two actions:
1. Provide a professional, tactical response confirming receipt and initial assessment.
2. Underneath your response, on a single line, output [EVENT_JSON] followed by a JSON object containing the extracted details:
{
  "event_type": "unplanned" or "planned",
  "event_cause": "accident", "vehicle_breakdown", "tree_fall", "water_logging", "protest", or "other",
  "description": "<short description>",
  "zone": "<Bengaluru zone, e.g., North Zone 1, South Zone 1, Central Zone 1, East Zone 1, West Zone 1>",
  "junction": "<junction name, e.g., HebbalFlyoverJunc, SilkBoardJunc, RichmondRoadJunc>",
  "corridor": "<corridor name or Non-corridor>",
  "priority": "High" or "Low",
  "requires_road_closure": true or false,
  "latitude": <realistic float latitude in Bengaluru, e.g. Hebbal is ~13.03, Silk Board is ~12.91, Central is ~12.97>,
  "longitude": <realistic float longitude in Bengaluru, e.g. ~77.59>
}

Example output when reporting:
"Tactical report received. Logged a vehicle breakdown at Hebbal Flyover. Initializing prediction engines and routing simulations."
[EVENT_JSON] {"event_type": "unplanned", "event_cause": "vehicle_breakdown", "description": "BMTC breakdown on Hebbal flyover", "zone": "North Zone 1", "junction": "HebbalFlyoverJunc", "corridor": "Bellary Road", "priority": "High", "requires_road_closure": false, "latitude": 13.0350, "longitude": 77.5980}

If they are just asking general questions, do not output the [EVENT_JSON] line.

Operator's Query: {{{query}}}`,
});

const aiTrafficCopilotQueryFlow = ai.defineFlow(
  {
    name: 'aiTrafficCopilotQueryFlow',
    inputSchema: AiTrafficCopilotQueryInputSchema,
    outputSchema: AiTrafficCopilotQueryOutputSchema,
  },
  async input => {
    const response = await prompt(input);
    if (!response.text) {
      throw new Error('AI Copilot did not return a response.');
    }
    return response.text;
  }
);
