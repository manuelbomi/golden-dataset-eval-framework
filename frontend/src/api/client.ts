import type { Annotation, GoldenExample, Task, Taxonomy } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${init?.method ?? "GET"} ${path} -> ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getTaxonomy: () => request<Taxonomy>("/taxonomy"),

  listTasks: (status?: string) =>
    request<Task[]>(`/tasks${status ? `?status=${status}` : ""}`),

  submitAnnotation: (
    taskId: string,
    body: { annotator_id: string; labels: string[]; note?: string }
  ) =>
    request<Annotation>(`/tasks/${taskId}/annotations`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listTaskAnnotations: (taskId: string) =>
    request<Annotation[]>(`/tasks/${taskId}/annotations`),

  listGolden: () => request<GoldenExample[]>("/golden"),
};
