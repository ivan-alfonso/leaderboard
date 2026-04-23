import React, { CSSProperties, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import axios from "axios";
import { ModelFilterPanel, ModelFilters } from "./ModelFilterPanel";
import { useTheme } from "../../contexts/ThemeContext";

interface ModelMetric {
  id: number;
  name: string;
  data: string;
  source: string;
  licensing: string;
  a1_total: number;
  a2_total: number;
  b1_total: number;
  b2_total: number;
  c1_total: number;
  c2_total: number;
  [key: string]: string | number;
}

interface Props {
  id: string;
  title?: string;
  styles?: CSSProperties;
  maxModels?: number; // Limit number of models shown
}

// Professional, color-blind-friendly palette (inspired by Okabe-Ito + Tailwind 500s).
// Distinct hues across the spectrum to maximize bar-to-bar contrast.
const metricColors: Record<string, string> = {
  a1_total: "#2563eb", // indigo blue
  a2_total: "#0ea5e9", // sky
  b1_total: "#10b981", // emerald
  b2_total: "#f59e0b", // amber
  c1_total: "#ef4444", // red
  c2_total: "#7c3aed", // violet
};

export const ModelMetricsBarChart: React.FC<Props> = ({
  id,
  title = "Model Performance Metrics",
  styles,
  maxModels = 15,
}) => {
  const { colors, theme } = useTheme();
  const isDark = theme === "dark";

  const [allData, setAllData] = useState<ModelMetric[]>([]);
  const [filteredData, setFilteredData] = useState<ModelMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ModelFilters>({
    cefrLevel: "All",
    testCategory: "All",
    licensingType: "All",
    sizeRange: [0, 1000],
    minPerformance: 0,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const backendBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await axios.get(`${backendBase}/model/leaderboard`);

        setAllData(response.data);
        setError(null);
      } catch (err) {
        console.error("Error fetching model metrics:", err);
        setError("Failed to load model metrics");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Apply filters whenever filters or data change
  useEffect(() => {
    if (!allData || allData.length === 0) {
      setFilteredData([]);
      return;
    }

    let filtered = [...allData];

    if (filters.licensingType !== "All") {
      filtered = filtered.filter(
        (model) => model.licensing === filters.licensingType
      );
    }

    filtered = filtered.filter((model) => {
      const sizeMatch = model.data?.match(/(\d+\.?\d*)/);
      if (!sizeMatch) return true;
      const size = parseFloat(sizeMatch[1]);
      return size >= filters.sizeRange[0] && size <= filters.sizeRange[1];
    });

    const categorySuffix =
    filters.testCategory === "All" || filters.testCategory === "Total"
      ? "total"
      : filters.testCategory.toLowerCase();

    if (filters.cefrLevel !== "All" || filters.testCategory !== "All") {
      filtered = filtered.map((model) => {
        const filteredModel = { ...model };

        filteredModel.a1_total =
          filters.cefrLevel === "All" || filters.cefrLevel === "A1"
            ? Number(model[`a1_${categorySuffix}`] ?? 0)
            : 0;

        filteredModel.a2_total =
          filters.cefrLevel === "All" || filters.cefrLevel === "A2"
            ? Number(model[`a2_${categorySuffix}`] ?? 0)
            : 0;

        filteredModel.b1_total =
          filters.cefrLevel === "All" || filters.cefrLevel === "B1"
            ? Number(model[`b1_${categorySuffix}`] ?? 0)
            : 0;

        filteredModel.b2_total =
          filters.cefrLevel === "All" || filters.cefrLevel === "B2"
            ? Number(model[`b2_${categorySuffix}`] ?? 0)
            : 0;

        filteredModel.c1_total =
          filters.cefrLevel === "All" || filters.cefrLevel === "C1"
            ? Number(model[`c1_${categorySuffix}`] ?? 0)
            : 0;

        filteredModel.c2_total =
          filters.cefrLevel === "All" || filters.cefrLevel === "C2"
            ? Number(model[`c2_${categorySuffix}`] ?? 0)
            : 0;

        return filteredModel;
      });
    }

    if (filters.minPerformance > 0) {
      filtered = filtered.filter((model) => {
        const maxScore = Math.max(
          model.a1_total,
          model.a2_total,
          model.b1_total,
          model.b2_total,
          model.c1_total,
          model.c2_total
        );
        return maxScore >= filters.minPerformance;
      });
    }

    filtered = filtered.slice(0, maxModels);
    setFilteredData(filtered);
  }, [allData, filters, maxModels]);

  const containerStyle: CSSProperties = {
    width: "100%",
    maxWidth: "100%",
    boxSizing: "border-box",
    backgroundColor: colors.surface,
    borderRadius: "16px",
    boxShadow: colors.shadow,
    border: `1px solid ${colors.border}`,
    padding: "24px",
    transition: "background-color 0.3s ease, border-color 0.3s ease",
    ...styles,
  };

  const chartContainerStyle: CSSProperties = {
    width: "100%",
    height: "500px",
    marginTop: "24px",
  };

  if (loading) {
    return (
      <div id={id} style={containerStyle}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "400px" }}>
          <p style={{ color: colors.textMuted }}>Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id={id} style={containerStyle}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "400px" }}>
          <p style={{ color: "#ef4444" }}>{error}</p>
        </div>
      </div>
    );
  }

  const visibleMetrics: string[] = [];
  if (filters.cefrLevel === "All" || filters.cefrLevel === "A1") visibleMetrics.push("a1_total");
  if (filters.cefrLevel === "All" || filters.cefrLevel === "A2") visibleMetrics.push("a2_total");
  if (filters.cefrLevel === "All" || filters.cefrLevel === "B1") visibleMetrics.push("b1_total");
  if (filters.cefrLevel === "All" || filters.cefrLevel === "B2") visibleMetrics.push("b2_total");
  if (filters.cefrLevel === "All" || filters.cefrLevel === "C1") visibleMetrics.push("c1_total");
  if (filters.cefrLevel === "All" || filters.cefrLevel === "C2") visibleMetrics.push("c2_total");

  const metricNameSuffix =
    filters.testCategory === "All" || filters.testCategory === "Total"
      ? "Total"
      : filters.testCategory === "Vocab"
        ? "Vocabulary"
        : filters.testCategory === "RC"
          ? "Reading Comprehension"
          : filters.testCategory === "LC"
            ? "Listening Comprehension"
            : "Grammar";

  const getMetricLabel = (level: string) => `${level} ${metricNameSuffix}`;

  return (
    <div id={id} style={containerStyle}>
      <ModelFilterPanel
        filters={filters}
        onFiltersChange={setFilters}
        styles={{
          backgroundColor: "transparent",
          boxShadow: "none",
          border: "none",
          padding: "0",
          marginBottom: "32px",
          borderBottom: `1px solid ${colors.border}`,
          paddingBottom: "24px"
        }}
      />

      <div style={chartContainerStyle}>
        {title && (
          <h3 style={{
            textAlign: "center",
            marginBottom: "10px",
            fontSize: "1.25rem",
            fontWeight: 600,
            color: colors.textPrimary,
            letterSpacing: "-0.01em",
          }}>
            {title}
            <span style={{
              fontSize: "0.875rem",
              fontWeight: 400,
              color: colors.textMuted,
              marginLeft: "10px"
            }}>
              ({filteredData.length} models)
            </span>
          </h3>
        )}

        {filteredData.length === 0 ? (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "80%" }}>
            <p style={{ color: colors.textMuted }}>No models match the selected filters</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="90%">
            <BarChart
              data={filteredData}
              margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={colors.chartGrid} />
              <XAxis
                dataKey="name"
                angle={-90}
                textAnchor="end"
                height={100}
                interval={0}
                tick={{ fontSize: 11, fill: colors.chartAxis }}
                stroke={colors.chartAxis}
              />
              <YAxis
                label={{ value: "Score", angle: -90, position: "insideLeft", style: { fill: colors.chartAxis } }}
                tick={{ fill: colors.chartAxis }}
                stroke={colors.chartAxis}
              />
              <Tooltip
                cursor={{ fill: isDark ? "rgba(148,163,184,0.1)" : "rgba(15,23,42,0.05)" }}
                contentStyle={{
                  backgroundColor: colors.surfaceElevated,
                  border: `1px solid ${colors.border}`,
                  borderRadius: "8px",
                  boxShadow: colors.shadow,
                  color: colors.textPrimary,
                }}
                labelStyle={{ fontWeight: 600, marginBottom: "8px", color: colors.textPrimary }}
                itemStyle={{ color: colors.textPrimary }}
              />
              <Legend
                wrapperStyle={{ paddingTop: "20px", color: colors.textPrimary }}
                iconType="square"
              />

              {visibleMetrics.includes("a1_total") && (
                <Bar
                  dataKey="a1_total"
                  name={getMetricLabel("A1")}
                  fill={metricColors.a1_total}
                  radius={[4, 4, 0, 0]}
                />
              )}
              {visibleMetrics.includes("a2_total") && (
                <Bar
                  dataKey="a2_total"
                  name={getMetricLabel("A2")}
                  fill={metricColors.a2_total}
                  radius={[4, 4, 0, 0]}
                />
              )}
              {visibleMetrics.includes("b1_total") && (
                <Bar
                  dataKey="b1_total"
                  name={getMetricLabel("B1")}
                  fill={metricColors.b1_total}
                  radius={[4, 4, 0, 0]}
                />
              )}
              {visibleMetrics.includes("b2_total") && (
                <Bar
                  dataKey="b2_total"
                  name={getMetricLabel("B2")}
                  fill={metricColors.b2_total}
                  radius={[4, 4, 0, 0]}
                />
              )}
              {visibleMetrics.includes("c1_total") && (
                <Bar
                  dataKey="c1_total"
                  name={getMetricLabel("C1")}
                  fill={metricColors.c1_total}
                  radius={[4, 4, 0, 0]}
                />
              )}
              {visibleMetrics.includes("c2_total") && (
                <Bar
                  dataKey="c2_total"
                  name={getMetricLabel("C2")}
                  fill={metricColors.c2_total}
                  radius={[4, 4, 0, 0]}
                />
              )}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
