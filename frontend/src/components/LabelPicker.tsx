import { useState } from "react";
import type { Taxonomy } from "../types";

interface Props {
  taxonomy: Taxonomy;
  onSubmit: (labels: string[], note: string) => void;
  disabled?: boolean;
}

/**
 * Multi-select label picker. Selection ORDER matters: the backend treats
 * the first-picked label as the annotator's "primary" label for agreement
 * scoring (see backend/app/api/annotations.py::_primary_label), so we keep
 * `selected` as an ordered array (push on select, filter on deselect)
 * rather than a Set, and show the pick order as a small badge.
 */
export function LabelPicker({ taxonomy, onSubmit, disabled }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [note, setNote] = useState("");

  function toggle(label: string) {
    setSelected((prev) =>
      prev.includes(label) ? prev.filter((l) => l !== label) : [...prev, label]
    );
  }

  return (
    <div className="label-picker">
      <div className="label-grid">
        {taxonomy.labels.map((label) => {
          const order = selected.indexOf(label);
          return (
            <button
              key={label}
              type="button"
              className={`label-chip ${order >= 0 ? "selected" : ""}`}
              title={taxonomy.descriptions[label]}
              onClick={() => toggle(label)}
              disabled={disabled}
            >
              {label}
              {order >= 0 && <span className="order-badge">{order + 1}</span>}
            </button>
          );
        })}
      </div>
      <textarea
        placeholder="Optional note / free-text override"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        disabled={disabled}
      />
      <button
        type="button"
        className="submit-button"
        disabled={disabled || selected.length === 0}
        onClick={() => {
          onSubmit(selected, note);
          setSelected([]);
          setNote("");
        }}
      >
        Submit annotation
      </button>
    </div>
  );
}
