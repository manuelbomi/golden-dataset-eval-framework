import { useEffect, useState } from "react";
import { api } from "../api/client";
import { AdjudicationView } from "../components/AdjudicationView";
import type { Annotation, Task } from "../types";

export function AdjudicationPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [annotationsByTask, setAnnotationsByTask] = useState<Record<string, Annotation[]>>({});

  useEffect(() => {
    api.listTasks("adjudication").then(async (taskList) => {
      setTasks(taskList);
      const entries = await Promise.all(
        taskList.map(async (t) => [t.id, await api.listTaskAnnotations(t.id)] as const)
      );
      setAnnotationsByTask(Object.fromEntries(entries));
    });
  }, []);

  if (tasks.length === 0) {
    return <p className="empty-state">No tasks currently need adjudication.</p>;
  }

  return (
    <div className="adjudication-page">
      <h2>Needs adjudication ({tasks.length})</h2>
      {tasks.map((task) => (
        <AdjudicationView key={task.id} task={task} annotations={annotationsByTask[task.id] ?? []} />
      ))}
    </div>
  );
}
