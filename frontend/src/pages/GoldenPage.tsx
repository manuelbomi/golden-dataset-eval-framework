import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { GoldenExample } from "../types";

export function GoldenPage() {
  const [examples, setExamples] = useState<GoldenExample[]>([]);

  useEffect(() => {
    api.listGolden().then(setExamples);
  }, []);

  return (
    <div className="golden-page">
      <h2>Golden set ({examples.length} examples)</h2>
      <table>
        <thead>
          <tr>
            <th>Labels</th>
            <th>Agreement</th>
            <th>Finalized by</th>
            <th>Version</th>
          </tr>
        </thead>
        <tbody>
          {examples.map((ex) => (
            <tr key={ex.id}>
              <td>{ex.labels.join(", ")}</td>
              <td>{ex.agreement_score.toFixed(2)}</td>
              <td>{ex.finalized_by}</td>
              <td>{ex.version}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
