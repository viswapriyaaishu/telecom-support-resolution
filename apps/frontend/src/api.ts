import axios from "axios";

export const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ComplaintIntelligence {
  intent: string;
  sub_intent: string;
  product: string;
  severity: string;
  sentiment: string;
  entities: Record<string, string>;
  confidence: number;
  model_version: string;
}

export interface ResolutionCitation {
  source_id: string;
  section: string | null;
}

export interface ResolutionResponse {
  summary: string;
  diagnosis: string;
  recommended_steps: string[];
  escalation_required: boolean;
  confidence: number;
  citations: ResolutionCitation[];
}

export interface ResolveResponse {
  complaint: string;
  intelligence: ComplaintIntelligence;
  resolution: ResolutionResponse;
  grounding: {
    is_grounded: boolean;
    unsupported_steps: string[];
    authoritative_evidence_count: number;
  };
}

export async function resolveComplaint(
  complaint: string,
): Promise<ResolveResponse> {
  const response = await api.post<ResolveResponse>(
    "/resolve",
    { complaint },
  );

  return response.data;
}