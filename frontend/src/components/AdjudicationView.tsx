import type { Annotation, Task } from "../types";

interface Props {
  task: Task;
  annotations: Annotation[];
}

/**
 * Shows disagreeing annotations for a task side-by-side so a senior
 * annotator (or SME) can see exactly where and why raters diverged, rather
 * than re-annotating blind. This is the human step the eval-gate CI job
 * can never replace -- see docs/adr/0003-gate-in-ci.md for why the gate
 * augments, rather than removes, this review step.
 */
export function AdjudicationView({ task, annotations }: Props) {
  return (
    <div className="adjudication-view">
      <p className="snippet-text">&ldquo;{task.document.text}&rdquo;</p>
      <div className="rater-columns">
        {annotations.map((a) => (
          <div key={a.id} className="rater-column">
            <h4>{a.annotator_id}</h4>
            <ul>
              {a.labels.map((label) => (
                <li key={label}>{label}</li>
              ))}
            </ul>
            {a.note && <p className="rater-note">{a.note}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
