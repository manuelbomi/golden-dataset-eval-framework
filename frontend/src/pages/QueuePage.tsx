import { useEffect, useState } from "react";
import { api } from "../api/client";
import { LabelPicker } from "../components/LabelPicker";
import { TaskQueue } from "../components/TaskQueue";
import type { Task, Taxonomy } from "../types";

const ANNOTATOR_ID = "demo-annotator"; // swap for real auth in a multi-annotator deployment

export function QueuePage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [selected, setSelected] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const [taskList, tax] = await Promise.all([
        api.listTasks("pending"),
        api.getTaxonomy(),
      ]);
      setTasks(taskList);
      setTaxonomy(tax);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleSubmit(labels: string[], note: string) {
    if (!selected) return;
    await api.submitAnnotation(selected.id, {
      annotator_id: ANNOTATOR_ID,
      labels,
      note: note || undefined,
    });
    setSelected(null);
    refresh();
  }

  if (error) {
    return (
      <div className="error-banner">
        Could not reach the backend ({error}). Is it running on :8000?
      </div>
    );
  }

  return (
    <div className="queue-page">
      <aside>
        <h2>Pending tasks ({tasks.length})</h2>
        <TaskQueue tasks={tasks} selectedTaskId={selected?.id ?? null} onSelect={setSelected} />
      </aside>
      <main>
        {selected && taxonomy ? (
          <>
            <p className="snippet-text">&ldquo;{selected.document.text}&rdquo;</p>
            <LabelPicker taxonomy={taxonomy} onSubmit={handleSubmit} />
          </>
        ) : (
          <p className="empty-state">Select a task from the queue to annotate it.</p>
        )}
      </main>
    </div>
  );
}
