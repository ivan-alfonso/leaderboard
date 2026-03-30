import React, { CSSProperties } from "react";

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
  const handleFilterChange = (key: keyof ModelFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const panelStyle: CSSProperties = {
    backgroundColor: "#ffffff",
    borderRadius: "16px",
    padding: "32px",
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    marginBottom: "24px",
    border: "1px solid #e5e7eb",
    ...styles,
  };

  const filterGroupStyle: CSSProperties = {
    marginBottom: "0",
  };

  const labelStyle: CSSProperties = {
    display: "block",
    fontSize: "13px",
    fontWeight: "700",
    color: "#374151",
    marginBottom: "10px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  };

  const selectStyle: CSSProperties = {
    width: "100%",
    padding: "10px 14px",
    fontSize: "14px",
    border: "2px solid #e5e7eb",
    borderRadius: "8px",
    backgroundColor: "#f9fafb",
    color: "#1f2937",
    cursor: "pointer",
    outline: "none",
    transition: "all 0.2s ease",
    fontWeight: "500",
  };

  const sliderContainerStyle: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  };

  const sliderStyle: CSSProperties = {
    width: "100%",
    height: "8px",
    borderRadius: "4px",
    background: "#e5e7eb",
    outline: "none",
    WebkitAppearance: "none",
    cursor: "pointer",
  };

  const rangeDisplayStyle: CSSProperties = {
    fontSize: "13px",
    color: "#6b7280",
    textAlign: "center",
    fontWeight: "500",
  };

  return (
    <div style={panelStyle}>
      <h3 style={{ 
        fontSize: "1.25rem", 
        fontWeight: "800", 
        color: "#1f2937", 
        marginBottom: "24px",
        borderBottom: "3px solid #2563eb",
        paddingBottom: "12px",
        letterSpacing: "-0.01em"
      }}>
        FILTER MODELS
      </h3>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "24px" }}>
        {/* CEFR Level Filter */}
        <div style={filterGroupStyle}>
          <label style={labelStyle}>CEFR Level</label>
          <select
            style={selectStyle}
            value={filters.cefrLevel}
            onChange={(e) => handleFilterChange("cefrLevel", e.target.value)}
            onFocus={(e) => e.currentTarget.style.borderColor = "#2563eb"}
            onBlur={(e) => e.currentTarget.style.borderColor = "#e5e7eb"}
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

        {/* Test Category Filter */}
        <div style={filterGroupStyle}>
          <label style={labelStyle}>Test Category</label>
          <select
            style={selectStyle}
            value={filters.testCategory}
            onChange={(e) => handleFilterChange("testCategory", e.target.value)}
            onFocus={(e) => e.currentTarget.style.borderColor = "#2563eb"}
            onBlur={(e) => e.currentTarget.style.borderColor = "#e5e7eb"}
          >
            <option value="All">All</option>
            <option value="Vocab">Vocabulary</option>
            <option value="Grammar">Grammar</option>
            <option value="RC">Reading Comprehension</option>
            <option value="LC">Listening Comprehension</option>
            <option value="Total">Total</option>
          </select>
        </div>

        {/* Licensing Type Filter */}
        <div style={filterGroupStyle}>
          <label style={labelStyle}>Model Type</label>
          <select
            style={selectStyle}
            value={filters.licensingType}
            onChange={(e) => handleFilterChange("licensingType", e.target.value)}
            onFocus={(e) => e.currentTarget.style.borderColor = "#2563eb"}
            onBlur={(e) => e.currentTarget.style.borderColor = "#e5e7eb"}
          >
            <option value="All">All</option>
            <option value="Open_Source">Open Source</option>
            <option value="Proprietary">Proprietary (Closed)</option>
          </select>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginTop: "24px" }}>
        {/* LLM Size Range Slider */}
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
                onFocus={(e) => e.currentTarget.style.borderColor = "#2563eb"}
                onBlur={(e) => e.currentTarget.style.borderColor = "#e5e7eb"}
                style={{
                  ...selectStyle,
                  width: "90px",
                }}
              />
              <span style={{ color: "#6b7280", fontWeight: "600" }}>to</span>
              <input
                type="number"
                min="0"
                max="1000"
                step="0.5"
                value={filters.sizeRange[1]}
                onChange={(e) => 
                  handleFilterChange("sizeRange", [filters.sizeRange[0], parseFloat(e.target.value)])
                }
                onFocus={(e) => e.currentTarget.style.borderColor = "#2563eb"}
                onBlur={(e) => e.currentTarget.style.borderColor = "#e5e7eb"}
                style={{
                  ...selectStyle,
                  width: "90px",
                }}
              />
              <span style={{ color: "#6b7280", fontWeight: "600" }}>B</span>
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

        {/* Minimum Performance Slider */}
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
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${filters.minPerformance}%, #e5e7eb ${filters.minPerformance}%, #e5e7eb 100%)`,
              }}
            />
            <div style={rangeDisplayStyle}>
              Show LLMs with minimum {filters.minPerformance}% performance
            </div>
          </div>
        </div>
      </div>

      {/* Reset Filters Button */}
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
            padding: "10px 20px",
            fontSize: "14px",
            fontWeight: "700",
            color: "#ffffff",
            backgroundColor: "#6b7280",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            transition: "all 0.2s",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#4b5563";
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow = "0 4px 6px rgba(0,0,0,0.1)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "#6b7280";
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
};
