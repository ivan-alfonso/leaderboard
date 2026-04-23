import React, { CSSProperties } from "react";
import { useTheme } from "../../contexts/ThemeContext";

export interface ModelFilters {
  cefrLevel: string;
  testCategory: string;
  licensingType: string;
  sizeRange: [number, number];
  minPerformance: number;
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

  const handleFilterChange = (key: keyof ModelFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const panelStyle: CSSProperties = {
    backgroundColor: colors.surface,
    borderRadius: "16px",
    padding: "32px",
    boxShadow: colors.shadow,
    marginBottom: "24px",
    border: `1px solid ${colors.border}`,
    transition: "background-color 0.3s ease, border-color 0.3s ease",
    ...styles,
  };

  const filterGroupStyle: CSSProperties = {
    marginBottom: "0",
  };

  const labelStyle: CSSProperties = {
    display: "block",
    fontSize: "12px",
    fontWeight: 700,
    color: colors.textSecondary,
    marginBottom: "10px",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  };

  const selectStyle: CSSProperties = {
    width: "100%",
    padding: "10px 14px",
    fontSize: "14px",
    border: `1px solid ${colors.border}`,
    borderRadius: "8px",
    backgroundColor: colors.inputBg,
    color: colors.textPrimary,
    cursor: "pointer",
    outline: "none",
    transition: "all 0.15s ease",
    fontWeight: 500,
  };

  const sliderContainerStyle: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  };

  const sliderStyle: CSSProperties = {
    width: "100%",
    height: "6px",
    borderRadius: "3px",
    background: colors.border,
    outline: "none",
    WebkitAppearance: "none",
    cursor: "pointer",
  };

  const rangeDisplayStyle: CSSProperties = {
    fontSize: "13px",
    color: colors.textMuted,
    textAlign: "center",
    fontWeight: 500,
  };

  return (
    <div style={panelStyle}>
      <h3 style={{
        fontSize: "1.1rem",
        fontWeight: 700,
        color: colors.textPrimary,
        marginTop: 0,
        marginBottom: "24px",
        paddingBottom: "12px",
        borderBottom: `2px solid ${colors.accent}`,
        letterSpacing: "0.02em",
        textTransform: "uppercase",
      }}>
        Filter Models
      </h3>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px" }}>
        <div style={filterGroupStyle}>
          <label style={labelStyle}>CEFR Level</label>
          <select
            style={selectStyle}
            value={filters.cefrLevel}
            onChange={(e) => handleFilterChange("cefrLevel", e.target.value)}
            onFocus={(e) => e.currentTarget.style.borderColor = colors.accent}
            onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
          >
            <option value="All">All</option>
            <option value="A1">A1</option>
            <option value="A2">A2</option>
            <option value="B1">B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
            <option value="C2">C2</option>
          </select>
        </div>

        <div style={filterGroupStyle}>
          <label style={labelStyle}>Test Category</label>
          <select
            style={selectStyle}
            value={filters.testCategory}
            onChange={(e) => handleFilterChange("testCategory", e.target.value)}
            onFocus={(e) => e.currentTarget.style.borderColor = colors.accent}
            onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
          >
            <option value="All">All</option>
            <option value="Vocab">Vocabulary</option>
            <option value="Grammar">Grammar</option>
            <option value="RC">Reading Comprehension</option>
            <option value="LC">Listening Comprehension</option>
            <option value="Total">Total</option>
          </select>
        </div>

        <div style={filterGroupStyle}>
          <label style={labelStyle}>Model Type</label>
          <select
            style={selectStyle}
            value={filters.licensingType}
            onChange={(e) => handleFilterChange("licensingType", e.target.value)}
            onFocus={(e) => e.currentTarget.style.borderColor = colors.accent}
            onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
          >
            <option value="All">All</option>
            <option value="Open_Source">Open Source</option>
            <option value="Proprietary">Proprietary (Closed)</option>
          </select>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px", marginTop: "24px" }}>
        <div style={filterGroupStyle}>
          <label style={labelStyle}>LLM Size Range (Billion Parameters)</label>
          <div style={sliderContainerStyle}>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <input
                type="number"
                min="0"
                max="1000"
                step="0.5"
                value={filters.sizeRange[0]}
                onChange={(e) =>
                  handleFilterChange("sizeRange", [parseFloat(e.target.value), filters.sizeRange[1]])
                }
                onFocus={(e) => e.currentTarget.style.borderColor = colors.accent}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
                style={{ ...selectStyle, width: "90px" }}
              />
              <span style={{ color: colors.textMuted, fontWeight: 600 }}>to</span>
              <input
                type="number"
                min="0"
                max="1000"
                step="0.5"
                value={filters.sizeRange[1]}
                onChange={(e) =>
                  handleFilterChange("sizeRange", [filters.sizeRange[0], parseFloat(e.target.value)])
                }
                onFocus={(e) => e.currentTarget.style.borderColor = colors.accent}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
                style={{ ...selectStyle, width: "90px" }}
              />
              <span style={{ color: colors.textMuted, fontWeight: 600 }}>B</span>
            </div>
            <input
              type="range"
              min="0"
              max="1000"
              step="0.5"
              value={filters.sizeRange[0]}
              onChange={(e) =>
                handleFilterChange("sizeRange", [parseFloat(e.target.value), filters.sizeRange[1]])
              }
              style={sliderStyle}
            />
            <input
              type="range"
              min="0"
              max="1000"
              step="0.5"
              value={filters.sizeRange[1]}
              onChange={(e) =>
                handleFilterChange("sizeRange", [filters.sizeRange[0], parseFloat(e.target.value)])
              }
              style={sliderStyle}
            />
          </div>
        </div>

        <div style={filterGroupStyle}>
          <label style={labelStyle}>
            Minimum Performance: {filters.minPerformance}%
          </label>
          <div style={sliderContainerStyle}>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={filters.minPerformance}
              onChange={(e) => handleFilterChange("minPerformance", parseFloat(e.target.value))}
              style={{
                ...sliderStyle,
                background: `linear-gradient(to right, ${colors.accent} 0%, ${colors.accent} ${filters.minPerformance}%, ${colors.border} ${filters.minPerformance}%, ${colors.border} 100%)`,
              }}
            />
            <div style={rangeDisplayStyle}>
              Show LLMs with minimum {filters.minPerformance}% performance
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: "28px", textAlign: "right" }}>
        <button
          onClick={() => onFiltersChange({
            cefrLevel: "All",
            testCategory: "All",
            licensingType: "All",
            sizeRange: [0, 1000],
            minPerformance: 0,
          })}
          style={{
            padding: "9px 20px",
            fontSize: "13px",
            fontWeight: 600,
            color: colors.textPrimary,
            backgroundColor: "transparent",
            border: `1px solid ${colors.borderStrong}`,
            borderRadius: "8px",
            cursor: "pointer",
            transition: "all 0.15s ease",
            letterSpacing: "0.02em",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = colors.hoverBg;
            e.currentTarget.style.borderColor = colors.accent;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
            e.currentTarget.style.borderColor = colors.borderStrong;
          }}
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
};
