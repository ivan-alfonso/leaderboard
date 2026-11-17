import React, { CSSProperties, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { ModelFilterPanel, ModelFilters } from "./ModelFilterPanel";
import { getSampleCount } from "../../data/sampleCounts";
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
  macro_avg: number;
  [key: string]: string | number;
}

interface Props {
  id: string;
  title?: string;
  styles?: CSSProperties;
  maxModels?: number; // Limit number of models shown
}

const metricColors: Record<string, string> = {
  a1_total: "#2563eb",
  a2_total: "#0ea5e9",
  b1_total: "#10b981",
  b2_total: "#f59e0b",
  c1_total: "#ef4444",
  c2_total: "#7c3aed",
  macro_avg: "#2563eb",
};

const cefrBaselines: Record<string, number> = {
  A1: 37.7,
  A2: 37.4,
  B1: 33.6,
  B2: 32.8,
  C1: 32.3,
  C2: 33.7,
};

export const ModelMetricsBarChart: React.FC<Props> = ({
  id,
  title,
  styles,
  maxModels = 15,
}) => {
  const { colors, theme } = useTheme();
  const { t } = useTranslation("leaderboard");
  const isDark = theme === "dark";
  const resolvedTitle = title ?? t("chart.title");

  const [plotMode, setPlotMode] = useState<"simple" | "detailed">("simple");
  const [allData, setAllData] = useState<ModelMetric[]>([]);
  const [filteredData, setFilteredData] = useState<ModelMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ModelFilters>({
    cefrLevel: "All",
    testCategory: "All",
    licensingType: "All",
    sizeRange: [0, 1000],
    minPerformance: 40,
    maxModels: 20,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const backendBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await axios.get(`${backendBase}/model/leaderboard`);

        // Compute macro_avg from CEFR level totals for models that don't have it stored
        const enriched = (response.data as ModelMetric[]).map((m) => {
          if (m.macro_avg > 0) return m;
          const totals = [m.a1_total, m.a2_total, m.b1_total, m.b2_total, m.c1_total, m.c2_total].filter((v) => v > 0);
          if (totals.length === 0) return m;
          const computed = Math.round((totals.reduce((s, v) => s + v, 0) / totals.length) * 100) / 100;
          return { ...m, macro_avg: computed };
        });
        setAllData(enriched);
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

  // Listen for filter events dispatched by the agent chat
  useEffect(() => {
    const onApplyFilters = (e: Event) => {
      const incoming = (e as CustomEvent).detail as Partial<ModelFilters>;
      setFilters((prev) => ({ ...prev, ...incoming }));
    };
    const defaultFilters: ModelFilters = {
      cefrLevel: "All",
      testCategory: "All",
      licensingType: "All",
      sizeRange: [0, 1000],
      minPerformance: 40,
      maxModels: 20,
    };
    const onResetFilters = (e: Event) => {
      const detail = (e as CustomEvent).detail as { fields?: string[] } | undefined;
      if (detail?.fields?.length) {
        const partial: Partial<ModelFilters> = {};
        for (const f of detail.fields) {
          if (f in defaultFilters) {
            (partial as Record<string, unknown>)[f] =
              defaultFilters[f as keyof ModelFilters];
          }
        }
        setFilters((prev) => ({ ...prev, ...partial }));
      } else {
        setFilters(defaultFilters);
        setPlotMode("simple");
      }
    };
    window.addEventListener("letzeval:apply_filters", onApplyFilters);
    window.addEventListener("letzeval:reset_filters", onResetFilters);
    return () => {
      window.removeEventListener("letzeval:apply_filters", onApplyFilters);
      window.removeEventListener("letzeval:reset_filters", onResetFilters);
    };
  }, []);

  // Auto-switch plot mode when CEFR / category filters change.
  // Activating either filter → Detailed; resetting both → Simple.
  useEffect(() => {
    const hasFilter =
      filters.cefrLevel !== "All" || filters.testCategory !== "All";
    setPlotMode(hasFilter ? "detailed" : "simple");
  }, [filters.cefrLevel, filters.testCategory]);

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

    if (plotMode === "simple") {
      filtered = filtered.filter((model) => model.macro_avg >= filters.minPerformance);
      filtered.sort((a, b) => b.macro_avg - a.macro_avg);
    } else {
      const categorySuffix =
        filters.testCategory === "All" || filters.testCategory === "Total"
          ? "total"
          : filters.testCategory.toLowerCase();

      if (filters.cefrLevel !== "All" || filters.testCategory !== "All") {
        filtered = filtered.map((model) => {
          const filteredModel = { ...model };
          filteredModel.a1_total =
            filters.cefrLevel === "All" || filters.cefrLevel === "A1"
              ? Number(model[`a1_${categorySuffix}`] ?? 0) : 0;
          filteredModel.a2_total =
            filters.cefrLevel === "All" || filters.cefrLevel === "A2"
              ? Number(model[`a2_${categorySuffix}`] ?? 0) : 0;
          filteredModel.b1_total =
            filters.cefrLevel === "All" || filters.cefrLevel === "B1"
              ? Number(model[`b1_${categorySuffix}`] ?? 0) : 0;
          filteredModel.b2_total =
            filters.cefrLevel === "All" || filters.cefrLevel === "B2"
              ? Number(model[`b2_${categorySuffix}`] ?? 0) : 0;
          filteredModel.c1_total =
            filters.cefrLevel === "All" || filters.cefrLevel === "C1"
              ? Number(model[`c1_${categorySuffix}`] ?? 0) : 0;
          filteredModel.c2_total =
            filters.cefrLevel === "All" || filters.cefrLevel === "C2"
              ? Number(model[`c2_${categorySuffix}`] ?? 0) : 0;
          return filteredModel;
        });
      }

      if (filters.minPerformance > 0) {
        filtered = filtered.filter((model) => {
          const maxScore = Math.max(
            model.a1_total, model.a2_total, model.b1_total,
            model.b2_total, model.c1_total, model.c2_total
          );
          return maxScore >= filters.minPerformance;
        });
      }

      filtered.sort((a, b) => {
        const avg = (m: ModelMetric) =>
          (m.a1_total + m.a2_total + m.b1_total + m.b2_total + m.c1_total + m.c2_total) / 6;
        return avg(b) - avg(a);
      });
    }

    filtered = filtered.slice(0, filters.maxModels);
    setFilteredData(filtered);
  }, [allData, filters, maxModels, plotMode]);

  const subtitleSampleCount =
    plotMode === "simple"
      ? 629
      : getSampleCount(filters.cefrLevel, filters.testCategory);

  const containerStyle: CSSProperties = {
    width: "100%",
    maxWidth: "100%",
    boxSizing: "border-box",
    backgroundColor: colors.surface,
    borderRadius: "16px",
    boxShadow: colors.shadow,
    border: `1px solid ${colors.border}`,
    padding: "24px 28px 20px",
    transition: "background-color 0.3s ease, border-color 0.3s ease",
    ...styles,
  };

  if (loading) {
    return (
      <div id={id} style={containerStyle}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "400px" }}>
          <p style={{ color: colors.textMuted }}>{t("chart.loading")}</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div id={id} style={containerStyle}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "400px" }}>
          <p style={{ color: "#ef4444" }}>{t("chart.error")}</p>
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
      ? t("chart.metricNames.total")
      : filters.testCategory === "Vocab"
        ? t("chart.metricNames.vocabulary")
        : filters.testCategory === "RC"
          ? t("chart.metricNames.readingComprehension")
          : filters.testCategory === "LC"
            ? t("chart.metricNames.listeningComprehension")
            : t("chart.metricNames.grammar");

  const getMetricLabel = (level: string) => `${level} ${metricNameSuffix}`;

  const BaselineLabel = ({ viewBox, value }: any) => {
    if (!viewBox) return null;
    const { x, y, width } = viewBox;
    return (
      <text
        x={x + width - 4}
        y={y - 4}
        textAnchor="end"
        fontSize={10}
        fontWeight={600}
        stroke="#000000"
        strokeWidth={3}
        strokeLinejoin="round"
        paintOrder="stroke"
        fill="#ffffff"
      >
        {value}
      </text>
    );
  };

  return (
    <div id={id} style={containerStyle}>

      {/* ── Card header: title left, toggle right ── */}
      <div style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: "16px",
        marginBottom: "20px",
        flexWrap: "wrap",
      }}>
        <div>
          <h3 style={{
            margin: "0 0 4px",
            fontSize: "1.15rem",
            fontWeight: 700,
            color: colors.textPrimary,
            letterSpacing: "-0.02em",
            lineHeight: 1.3,
          }}>
            {resolvedTitle}
            {filteredData.length > 0 && (
              <span style={{
                fontSize: "0.8rem",
                fontWeight: 500,
                color: colors.textMuted,
                marginLeft: "10px",
                letterSpacing: "0",
              }}>
                {t("chart.modelsCount", { count: filteredData.length })}
              </span>
            )}
          </h3>
          <p style={{
            margin: 0,
            fontSize: "0.78rem",
            color: colors.textMuted,
            fontWeight: 500,
            letterSpacing: "0.01em",
          }}>
            {plotMode === "simple"
              ? t("chart.questionCount", { n: 629 })
              : `${filters.cefrLevel === "All" ? t("filters.all") : filters.cefrLevel} · ${metricNameSuffix} · ${t("chart.questionCount", { n: subtitleSampleCount })}`}
          </p>
        </div>

        {/* Simple / Detailed segmented toggle */}
        <div style={{
          display: "inline-flex",
          border: `1px solid ${colors.border}`,
          borderRadius: "8px",
          overflow: "hidden",
          backgroundColor: colors.tableHeaderBg,
          flexShrink: 0,
        }}>
          {(["simple", "detailed"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setPlotMode(mode)}
              style={{
                padding: "6px 18px",
                fontSize: "12px",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                backgroundColor: plotMode === mode ? colors.accent : "transparent",
                color: plotMode === mode ? "#ffffff" : colors.textMuted,
                transition: "background-color 0.15s, color 0.15s",
                letterSpacing: "0.03em",
                textTransform: "uppercase",
              }}
            >
              {t(`chart.plotMode.${mode}`)}
            </button>
          ))}
        </div>
      </div>

      {/* ── Compact filter bar ── */}
      <ModelFilterPanel
        filters={filters}
        onFiltersChange={setFilters}
        styles={{
          marginBottom: "20px",
          paddingBottom: "20px",
          borderBottom: `1px solid ${colors.border}`,
        }}
      />

      {/* ── Chart ── */}
      {filteredData.length === 0 ? (
        <div style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "320px",
        }}>
          <p style={{ color: colors.textMuted, fontSize: "0.9rem" }}>{t("chart.noModels")}</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={480}>
          <BarChart
            data={filteredData}
            margin={{ top: 12, right: 16, left: 8, bottom: 90 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={colors.chartGrid}
              vertical={false}
            />
            <XAxis
              dataKey="name"
              angle={-42}
              textAnchor="end"
              height={90}
              interval={0}
              tick={{ fontSize: 10, fill: colors.chartAxis }}
              tickFormatter={(name: string) =>
                name.length > 22 ? name.slice(0, 22) + "…" : name
              }
              stroke={colors.chartAxis}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
              tick={{ fontSize: 11, fill: colors.chartAxis }}
              stroke="none"
              tickLine={false}
              width={44}
              axisLine={false}
            />
            <Tooltip
              cursor={{ fill: isDark ? "rgba(148,163,184,0.07)" : "rgba(15,23,42,0.04)" }}
              contentStyle={{
                backgroundColor: colors.surfaceElevated,
                border: `1px solid ${colors.border}`,
                borderRadius: "8px",
                boxShadow: colors.shadow,
                color: colors.textPrimary,
                fontSize: "13px",
              }}
              formatter={(value: number) => [`${value.toFixed(1)}%`, undefined]}
              labelStyle={{ fontWeight: 600, marginBottom: "6px", color: colors.textPrimary }}
              itemStyle={{ color: colors.textPrimary, padding: "2px 0" }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: "16px",
                fontSize: "12px",
                color: colors.textPrimary,
                lineHeight: "20px",
              }}
              iconType="square"
              iconSize={10}
            />

            {/* Baseline reference line — black border + white fill for readability */}
            {plotMode === "simple" && (
              <>
                <ReferenceLine
                  y={34.6}
                  stroke="#000000"
                  strokeDasharray="6 3"
                  strokeWidth={4}
                />
                <ReferenceLine
                  y={34.6}
                  stroke="#ffffff"
                  strokeDasharray="6 3"
                  strokeWidth={2}
                  label={<BaselineLabel value="Baseline 34.6%" />}
                />
              </>
            )}
            {plotMode === "detailed" && filters.cefrLevel !== "All" && (
              <>
                <ReferenceLine
                  y={cefrBaselines[filters.cefrLevel]}
                  stroke="#000000"
                  strokeDasharray="6 3"
                  strokeWidth={4}
                />
                <ReferenceLine
                  y={cefrBaselines[filters.cefrLevel]}
                  stroke="#ffffff"
                  strokeDasharray="6 3"
                  strokeWidth={2}
                  label={<BaselineLabel value={`Baseline ${cefrBaselines[filters.cefrLevel]}%`} />}
                />
              </>
            )}

            {/* Bars */}
            {plotMode === "simple" ? (
              <Bar
                dataKey="macro_avg"
                name={`Macro Average (No. of Test Questions = 629)`}
                fill={metricColors.macro_avg}
                radius={[3, 3, 0, 0]}
                maxBarSize={48}
              />
            ) : (
              <>
                {visibleMetrics.includes("a1_total") && (
                  <Bar dataKey="a1_total" name={`${getMetricLabel("A1")} (No. of Test Questions = ${getSampleCount("A1", filters.testCategory)})`} fill={metricColors.a1_total} radius={[3, 3, 0, 0]} maxBarSize={32} />
                )}
                {visibleMetrics.includes("a2_total") && (
                  <Bar dataKey="a2_total" name={`${getMetricLabel("A2")} (No. of Test Questions = ${getSampleCount("A2", filters.testCategory)})`} fill={metricColors.a2_total} radius={[3, 3, 0, 0]} maxBarSize={32} />
                )}
                {visibleMetrics.includes("b1_total") && (
                  <Bar dataKey="b1_total" name={`${getMetricLabel("B1")} (No. of Test Questions = ${getSampleCount("B1", filters.testCategory)})`} fill={metricColors.b1_total} radius={[3, 3, 0, 0]} maxBarSize={32} />
                )}
                {visibleMetrics.includes("b2_total") && (
                  <Bar dataKey="b2_total" name={`${getMetricLabel("B2")} (No. of Test Questions = ${getSampleCount("B2", filters.testCategory)})`} fill={metricColors.b2_total} radius={[3, 3, 0, 0]} maxBarSize={32} />
                )}
                {visibleMetrics.includes("c1_total") && (
                  <Bar dataKey="c1_total" name={`${getMetricLabel("C1")} (No. of Test Questions = ${getSampleCount("C1", filters.testCategory)})`} fill={metricColors.c1_total} radius={[3, 3, 0, 0]} maxBarSize={32} />
                )}
                {visibleMetrics.includes("c2_total") && (
                  <Bar dataKey="c2_total" name={`${getMetricLabel("C2")} (No. of Test Questions = ${getSampleCount("C2", filters.testCategory)})`} fill={metricColors.c2_total} radius={[3, 3, 0, 0]} maxBarSize={32} />
                )}
              </>
            )}
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
