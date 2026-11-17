/**
 * Sample counts per CEFR level × test category, derived from INLL_full_test.tsv.
 * Rows: A1–C2 individual levels, plus All (sum across all levels).
 * Columns: Vocab, Grammar, RC, LC per-category counts, plus Total (sum across categories).
 * Verified against expected values: overall total = 629.
 */

export type CefrRow = "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | "All";
export type CategoryCol = "Vocab" | "Grammar" | "RC" | "LC" | "Total";

export const SAMPLE_COUNTS: Record<CefrRow, Record<CategoryCol, number>> = {
  A1:  { Vocab: 26,  Grammar: 26,  RC: 26,  LC: 26,  Total: 104 },
  A2:  { Vocab: 26,  Grammar: 26,  RC: 26,  LC: 26,  Total: 104 },
  B1:  { Vocab: 26,  Grammar: 25,  RC: 25,  LC: 26,  Total: 102 },
  B2:  { Vocab: 28,  Grammar: 34,  RC: 26,  LC: 26,  Total: 114 },
  C1:  { Vocab: 26,  Grammar: 27,  RC: 26,  LC: 25,  Total: 104 },
  C2:  { Vocab: 26,  Grammar: 23,  RC: 26,  LC: 26,  Total: 101 },
  All: { Vocab: 158, Grammar: 161, RC: 155, LC: 155, Total: 629 },
};

/**
 * Return the sample count for a given CEFR level + test category filter combination.
 *
 * - cefrLevel "All" + testCategory "All"  → 629 (full evaluation set)
 * - cefrLevel "All" + testCategory "Grammar" → 161 (all Grammar questions)
 * - cefrLevel "B2"  + testCategory "All"  → 114 (all B2 questions)
 * - cefrLevel "B2"  + testCategory "Grammar" → 34
 *
 * The filter UI uses "Total" as an alias for "All categories" in the category
 * dropdown, so "Total" maps to the row-level Total column.
 */
export function getSampleCount(cefrLevel: string, testCategory: string): number {
  const levelKey = (cefrLevel === "All" || !cefrLevel ? "All" : cefrLevel) as CefrRow;
  let catKey: CategoryCol;

  switch (testCategory) {
    case "Vocab":    catKey = "Vocab";   break;
    case "Grammar":  catKey = "Grammar"; break;
    case "RC":       catKey = "RC";      break;
    case "LC":       catKey = "LC";      break;
    case "Total":
    case "All":
    default:         catKey = "Total";   break;
  }

  return SAMPLE_COUNTS[levelKey]?.[catKey] ?? 629;
}
