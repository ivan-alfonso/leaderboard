import React, { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from "../../contexts/ThemeContext";

export interface ModelFilters {
  cefrLevel: string;
  testCategory: string;
  licensingType: string;
  sizeRange: [number, number];
  minPerformance: number;
  maxModels: number;
}

interface Props {
  filters: ModelFilters;
  onFiltersChange: (filters: ModelFilters) => void;
  styles?: CSSProperties;
}

export const ModelFilterPanel: React.FC<Props> = ({
  filters,
  onFiltersChange,
  styles,
}) => {
  const { colors } = useTheme();
  const { t } = useTranslation("leaderboard");

  const handleFilterChange = (key: keyof ModelFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  // Chip = label prefix + select/input fused into one bordered unit
  const chipOuter: CSSProperties = {
    display: "inline-flex",
    alignItems: "stretch",
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    overflow: "hidden",
    backgroundColor: colors.surface,
    flexShrink: 0,
    height: "32px",
  };

  const chipLabel: CSSProperties = {
    display: "flex",
    alignItems: "center",
    padding: "0 9px",
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: colors.textMuted,
    backgroundColor: colors.tableHeaderBg,
    borderRight: `1px solid ${colors.border}`,
    whiteSpace: "nowrap",
    userSelect: "none",
    lineHeight: 1,
  };

  const chipSelect: CSSProperties = {
    padding: "0 8px",
    height: "100%",
    fontSize: "13px",
    fontWeight: 500,
    border: "none",
    backgroundColor: "transparent",
    color: colors.textPrimary,
    cursor: "pointer",
    outline: "none",
    minWidth: "68px",
  };

  const numInput: CSSProperties = {
    width: "64px",
    height: "32px",
    padding: "0 8px",
    fontSize: "13px",
    fontWeight: 500,
    border: `1px solid ${colors.border}`,
    borderRadius: "6px",
    backgroundColor: colors.inputBg,
    color: colors.textPrimary,
    outline: "none",
    textAlign: "center",
    boxSizing: "border-box",
    flexShrink: 0,
  };

  const sliderRow: CSSProperties = {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "20px",
    marginTop: "14px",
  };

  const sliderGroup: CSSProperties = { display: "flex", flexDirection: "column", gap: "6px" };

  const sliderMeta: CSSProperties = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "baseline",
  };

  const sliderLbl: CSSProperties = {
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: colors.textMuted,
    lineHeight: 1,
  };

  const sliderVal: CSSProperties = {
    fontSize: "13px",
    fontWeight: 600,
    color: colors.textPrimary,
    fontVariantNumeric: "tabular-nums",
    lineHeight: 1,
  };

  const sliderBase: CSSProperties = {
    width: "100%",
    height: "4px",
    borderRadius: "2px",
    outline: "none",
    WebkitAppearance: "none",
    cursor: "pointer",
    display: "block",
  };

  const accentSlider = (pct: number): CSSProperties => ({
    ...sliderBase,
    background: `linear-gradient(to right, ${colors.accent} 0%, ${colors.accent} ${pct}%, ${colors.border} ${pct}%, ${colors.border} 100%)`,
  });

  const divider: CSSProperties = {
    alignSelf: "stretch",
    width: "1px",
    backgroundColor: colors.border,
    flexShrink: 0,
  };

  return (
    <div style={styles}>
      {/* ── Row 1: dropdown chips + size range + reset ── */}
      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>

        {/* CEFR Level */}
        <div style={chipOuter}>
          <span style={chipLabel}>{t("filters.cefrLevel")}</span>
          <select
            style={chipSelect}
            value={filters.cefrLevel}
            onChange={(e) => handleFilterChange("cefrLevel", e.target.value)}
          >
            <option value="All">{t("filters.all")}</option>
            <option value="A1">A1</option>
            <option value="A2">A2</option>
            <option value="B1">B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
            <option value="C2">C2</option>
          </select>
        </div>

        {/* Test Category */}
        <div style={chipOuter}>
          <span style={chipLabel}>{t("filters.testCategory")}</span>
          <select
            style={chipSelect}
            value={filters.testCategory}
            onChange={(e) => handleFilterChange("testCategory", e.target.value)}
          >
            <option value="All">{t("filters.all")}</option>
            <option value="Vocab">{t("filters.vocabulary")}</option>
            <option value="Grammar">{t("filters.grammar")}</option>
            <option value="RC">{t("filters.readingComprehension")}</option>
            <option value="LC">{t("filters.listeningComprehension")}</option>
            <option value="Total">{t("filters.total")}</option>
          </select>
        </div>

        {/* Model Type */}
        <div style={chipOuter}>
          <span style={chipLabel}>{t("filters.modelType")}</span>
          <select
            style={chipSelect}
            value={filters.licensingType}
            onChange={(e) => handleFilterChange("licensingType", e.target.value)}
          >
            <option value="All">{t("filters.all")}</option>
            <option value="Open_Source">{t("filters.openSource")}</option>
            <option value="Proprietary">{t("filters.proprietary")}</option>
          </select>
        </div>

        <div style={divider} />

        {/* Size range — number inputs only */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", flexShrink: 0 }}>
          <span style={{ ...sliderLbl, whiteSpace: "nowrap" }}>{t("filters.billion")}</span>
          <input
            type="number"
            min="0"
            max="1000"
            step="0.5"
            value={filters.sizeRange[0]}
            onChange={(e) =>
              handleFilterChange("sizeRange", [parseFloat(e.target.value), filters.sizeRange[1]])
            }
            onFocus={(e) => (e.currentTarget.style.borderColor = colors.accent)}
            onBlur={(e) => (e.currentTarget.style.borderColor = colors.border)}
            style={numInput}
          />
          <span style={{ color: colors.textMuted, fontSize: "12px", fontWeight: 500 }}>–</span>
          <input
            type="number"
            min="0"
            max="1000"
            step="0.5"
            value={filters.sizeRange[1]}
            onChange={(e) =>
              handleFilterChange("sizeRange", [filters.sizeRange[0], parseFloat(e.target.value)])
            }
            onFocus={(e) => (e.currentTarget.style.borderColor = colors.accent)}
            onBlur={(e) => (e.currentTarget.style.borderColor = colors.border)}
            style={numInput}
          />
          <span style={{ ...sliderLbl, whiteSpace: "nowrap" }}>{t("filters.billion")}</span>
        </div>

        {/* Spacer */}
        <div style={{ flex: 1, minWidth: "8px" }} />

        {/* Reset */}
        <button
          onClick={() =>
            onFiltersChange({
              cefrLevel: "All",
              testCategory: "All",
              licensingType: "All",
              sizeRange: [0, 1000],
              minPerformance: 40,
              maxModels: 20,
            })
          }
          style={{
            height: "32px",
            padding: "0 14px",
            fontSize: "12px",
            fontWeight: 600,
            color: colors.textMuted,
            backgroundColor: "transparent",
            border: `1px solid ${colors.border}`,
            borderRadius: "6px",
            cursor: "pointer",
            letterSpacing: "0.03em",
            transition: "color 0.15s, background-color 0.15s, border-color 0.15s",
            flexShrink: 0,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = colors.hoverBg;
            e.currentTarget.style.borderColor = colors.borderStrong;
            e.currentTarget.style.color = colors.textPrimary;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.borderColor = colors.border;
            e.currentTarget.style.color = colors.textMuted;
          }}
        >
          {t("filters.resetFilters")}
        </button>
      </div>

      {/* ── Row 2: sliders for max models + min performance ── */}
      <div style={sliderRow}>
        {/* Max models */}
        <div style={sliderGroup}>
          <div style={sliderMeta}>
            <span style={sliderLbl}>{t("filters.modelsShown", { value: "" }).replace(/[:\s]+$/, "")}</span>
            <input
              type="number"
              min="1"
              max="100"
              step="1"
              value={filters.maxModels}
              onChange={(e) =>
                handleFilterChange("maxModels", Math.max(1, Math.min(100, parseInt(e.target.value) || 1)))
              }
              style={{
                width: "48px",
                height: "20px",
                padding: "0 4px",
                fontSize: "13px",
                fontWeight: 600,
                border: `1px solid ${colors.border}`,
                borderRadius: "4px",
                backgroundColor: "transparent",
                color: colors.textPrimary,
                outline: "none",
                textAlign: "center",
                fontVariantNumeric: "tabular-nums",
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = colors.accent)}
              onBlur={(e) => (e.currentTarget.style.borderColor = colors.border)}
            />
          </div>
          <input
            type="range"
            min="1"
            max="100"
            step="1"
            value={filters.maxModels}
            onChange={(e) => handleFilterChange("maxModels", parseInt(e.target.value))}
            style={accentSlider(filters.maxModels)}
          />
        </div>

        {/* Min performance */}
        <div style={sliderGroup}>
          <div style={sliderMeta}>
            <span style={sliderLbl}>
              {t("filters.minPerformance", { value: "" }).replace(/[:\s]+$/, "")}
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: "3px" }}>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={filters.minPerformance}
                onChange={(e) =>
                  handleFilterChange("minPerformance", Math.max(0, Math.min(100, parseFloat(e.target.value) || 0)))
                }
                style={{
                  width: "48px",
                  height: "20px",
                  padding: "0 4px",
                  fontSize: "13px",
                  fontWeight: 600,
                  border: `1px solid ${colors.border}`,
                  borderRadius: "4px",
                  backgroundColor: "transparent",
                  color: colors.textPrimary,
                  outline: "none",
                  textAlign: "center",
                  fontVariantNumeric: "tabular-nums",
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = colors.accent)}
                onBlur={(e) => (e.currentTarget.style.borderColor = colors.border)}
              />
              <span style={{ ...sliderVal, fontSize: "12px" }}>%</span>
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={filters.minPerformance}
            onChange={(e) => handleFilterChange("minPerformance", parseFloat(e.target.value))}
            style={accentSlider(filters.minPerformance)}
          />
        </div>
      </div>
    </div>
  );
};
