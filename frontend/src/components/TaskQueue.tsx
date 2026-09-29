import type { Task } from "../types";

interface Props {
  tasks: Task[];
  selectedTaskId: string | null;
  onSelect: (task: Task) => void;
}

export function TaskQueue({ tasks, selectedTaskId, onSelect }: Props) {
  if (tasks.length === 0) {
    return <p className="empty-state">No pending tasks. Seed some documents to get started.</p>;
  }
  return (
    <ul className="task-queue">
      {tasks.map((task) => (
        <li key={task.id}>
          <button
            type="button"
            className={task.id === selectedTaskId ? "task-item selected" : "task-item"}
            onClick={() => onSelect(task)}
          >
            <span className={`status-dot status-${task.status}`} />
            <span className="task-text">{task.document.text}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
