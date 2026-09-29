// Hand-written mirror of backend/app/schemas.py. Kept in sync by hand (a
// small API surface like this one doesn't yet justify generating this file
// from the OpenAPI schema -- see docs/adr/ if this repo's API grows enough
// to make that worthwhile).

export interface Document {
  id: string;
  text: string;
  source: string;
  created_at: string;
}

export interface Task {
  id: string;
  document_id: string;
  status: "pending" | "in_review" | "golden" | "adjudication";
  created_at: string;
  document: Document;
}

export interface Annotation {
  id: string;
  task_id: string;
  annotator_id: string;
  labels: string[];
  note: string | null;
  created_at: string;
}

export interface GoldenExample {
  id: string;
  document_id: string;
  labels: string[];
  agreement_score: number;
  finalized_by: string;
  version: string;
}

export interface Taxonomy {
  labels: string[];
  descriptions: Record<string, string>;
}
