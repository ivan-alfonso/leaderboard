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

const metricColors = {
  a1_total: "#10b981", // Emerald
  a2_total: "#14b8a6", // Teal
  b1_total: "#3b82f6", // Blue
  b2_total: "#6366f1", // Indigo
  c1_total: "#8b5cf6", // Violet
  c2_total: "#ec4899", // Pink
};

const metricLabels = {
  a1_total: "A1 Total",
  a2_total: "A2 Total",
  b1_total: "B1 Total",
  b2_total: "B2 Total",
  c1_total: "C1 Total",
  c2_total: "C2 Total",
};

export const ModelMetricsBarChart: React.FC<Props> = ({
  id,
  title = "Model Performance Metrics",
  styles,
  maxModels = 15,
}) => {
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

    // Filter by licensing type
    if (filters.licensingType !== "All") {
      filtered = filtered.filter(
        (model) => model.licensing === filters.licensingType
      );
    }

    // Filter by size range (extract number from data field)
    filtered = filtered.filter((model) => {
      const sizeMatch = model.data?.match(/(\d+\.?\d*)/);
      if (!sizeMatch) return true; // Keep if no size info
      const size = parseFloat(sizeMatch[1]);
      return size >= filters.sizeRange[0] && size <= filters.sizeRange[1];
    });

    const categorySuffix =
    filters.testCategory === "All" || filters.testCategory === "Total"
      ? "total"
      : filters.testCategory.toLowerCase();

    // Filter by CEFR level and test category
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

    // Filter by minimum performance
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

    // Limit the number of models
    filtered = filtered.slice(0, maxModels);

    setFilteredData(filtered);
  }, [allData, filters, maxModels]);

  const containerStyle: CSSProperties = {
    width: "100%",
    backgroundColor: "#ffffff",
    borderRadius: "16px",
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    border: "1px solid #e5e7eb",
    padding: "28px",
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
          <p style={{ color: "#6b7280" }}>Loading metrics...</p>
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

  // Get visible metrics based on CEFR filter
  const visibleMetrics = [];
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
          borderBottom: "2px solid #e5e7eb",
          paddingBottom: "24px"
        }}
      />
      
      <div style={chartContainerStyle}>
        {title && (
          <h3 style={{ 
            textAlign: "center", 
            marginBottom: "10px",
            fontSize: "1.25rem",
            fontWeight: "600",
            color: "#1f2937"
          }}>
            {title}
            <span style={{ 
              fontSize: "0.875rem", 
              fontWeight: "400", 
              color: "#6b7280",
              marginLeft: "10px"
            }}>
              ({filteredData.length} models)
            </span>
          </h3>
        )}
        
        {filteredData.length === 0 ? (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "80%" }}>
            <p style={{ color: "#6b7280" }}>No models match the selected filters</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="90%">
            <BarChart
              data={filteredData}
              margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="name" 
                angle={-90}
                textAnchor="end"
                height={100}
                interval={0}
                tick={{ fontSize: 11, fill: "#374151" }}
              />
              <YAxis 
                label={{ value: "Score", angle: -90, position: "insideLeft", style: { fill: "#374151" } }}
                tick={{ fill: "#374151" }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: "#ffffff", 
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
                }}
                labelStyle={{ fontWeight: "600", marginBottom: "8px" }}
              />
              <Legend 
                wrapperStyle={{ paddingTop: "20px" }}
                iconType="square"
              />
              
              {/* Render only visible metric bars */}
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
