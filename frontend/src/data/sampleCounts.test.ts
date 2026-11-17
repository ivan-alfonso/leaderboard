import { SAMPLE_COUNTS, getSampleCount } from "./sampleCounts";

describe("SAMPLE_COUNTS table", () => {
  it("has the correct overall total (629)", () => {
    expect(SAMPLE_COUNTS.All.Total).toBe(629);
  });

  it("has the correct A1 Total (104)", () => {
    expect(SAMPLE_COUNTS.A1.Total).toBe(104);
  });

  it("has the correct B2 Total (114)", () => {
    expect(SAMPLE_COUNTS.B2.Total).toBe(114);
  });

  it("has the correct B2 Grammar (34)", () => {
    expect(SAMPLE_COUNTS.B2.Grammar).toBe(34);
  });

  it("has the correct C2 Grammar (23)", () => {
    expect(SAMPLE_COUNTS.C2.Grammar).toBe(23);
  });

  it("has the correct All Vocab (158)", () => {
    expect(SAMPLE_COUNTS.All.Vocab).toBe(158);
  });

  it("has the correct All Grammar (161)", () => {
    expect(SAMPLE_COUNTS.All.Grammar).toBe(161);
  });

  it("has the correct All RC (155)", () => {
    expect(SAMPLE_COUNTS.All.RC).toBe(155);
  });

  it("has the correct All LC (155)", () => {
    expect(SAMPLE_COUNTS.All.LC).toBe(155);
  });

  it("row totals equal the sum of category columns", () => {
    const levels = ["A1", "A2", "B1", "B2", "C1", "C2", "All"] as const;
    for (const level of levels) {
      const row = SAMPLE_COUNTS[level];
      expect(row.Total).toBe(row.Vocab + row.Grammar + row.RC + row.LC);
    }
  });

  it("All column totals equal sum across CEFR levels", () => {
    const levels = ["A1", "A2", "B1", "B2", "C1", "C2"] as const;
    const cats = ["Vocab", "Grammar", "RC", "LC", "Total"] as const;
    for (const cat of cats) {
      const summed = levels.reduce((acc, lv) => acc + SAMPLE_COUNTS[lv][cat], 0);
      expect(SAMPLE_COUNTS.All[cat]).toBe(summed);
    }
  });
});

describe("getSampleCount", () => {
  it("returns 629 for All+All", () => {
    expect(getSampleCount("All", "All")).toBe(629);
  });

  it("returns 629 for All+Total (Total alias)", () => {
    expect(getSampleCount("All", "Total")).toBe(629);
  });

  it("returns correct count for A1+All (104)", () => {
    expect(getSampleCount("A1", "All")).toBe(104);
  });

  it("returns correct count for All+Grammar (161)", () => {
    expect(getSampleCount("All", "Grammar")).toBe(161);
  });

  it("returns correct count for B2+Grammar (34)", () => {
    expect(getSampleCount("B2", "Grammar")).toBe(34);
  });

  it("returns correct count for C2+Vocab (26)", () => {
    expect(getSampleCount("C2", "Vocab")).toBe(26);
  });

  it("falls back to 629 for unknown level", () => {
    expect(getSampleCount("X9", "Grammar")).toBe(629);
  });

  it("treats empty cefrLevel as All", () => {
    expect(getSampleCount("", "Grammar")).toBe(161);
  });
});
