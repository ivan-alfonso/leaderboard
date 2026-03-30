import React from "react";
import { ChartBlock } from "../components/runtime/ChartBlock";
import { TableBlock } from "../components/runtime/TableBlock";
import { MetricCardBlock } from "../components/runtime/MetricCardBlock";

const Home: React.FC = () => {
  return (
    <div id="5WFQu3cZBn89Z4xa" style={{"width": "auto", "height": "100vh", "padding": "0", "margin": "0", "position": "static", "textAlign": "left", "zIndex": 0, "backgroundColor": "#f8fafc", "color": "#1e293b", "--chart-color-palette": "default"}}>
    <section id="ic1xf" className="assistant-hero" style={{"padding": "64px 48px", "background": "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)", "color": "#ffffff", "borderRadius": "16px", "margin": "24px", "textAlign": "center", "--chart-color-palette": "default"}}>
      <h1 id="inicg" style={{"margin": "0 0 16px 0", "fontSize": "2.25rem", "fontWeight": "800", "letterSpacing": "-0.02em", "lineHeight": "1.2", "--chart-color-palette": "default"}}>{"Welcome to Metric Manager"}</h1>
    </section>
    <main id="ixzli" className="assistant-main" style={{"maxWidth": "1200px", "margin": "0 auto", "padding": "24px 16px", "--chart-color-palette": "default"}}>
      <section id="i0ehg" className="assistant-stats-grid" style={{"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "16px", "margin": "12px 24px", "--chart-color-palette": "default"}}>
        <h2 id="if6qh" style={{"gridColumn": "1 / -1", "fontSize": "1.25rem", "fontWeight": "700", "color": "#0f172a", "margin": "0 0 4px 0", "--chart-color-palette": "default"}}>{"Overview"}</h2>
        <MetricCardBlock id="izfwl" styles={{"width": "100%", "minHeight": "140px", "--chart-color-palette": "default"}} metric={{"metricTitle": "Active Projects", "format": "number", "valueColor": "#2c3e50", "valueSize": 32, "showTrend": true, "positiveColor": "#27ae60", "negativeColor": "#e74c3c", "value": 0, "trend": 12}} dataBinding={{"entity": "Measure", "endpoint": "/measure/", "data_field": "uncertainty"}} />
        <MetricCardBlock id="ibud9" styles={{"width": "100%", "minHeight": "140px", "--chart-color-palette": "default"}} metric={{"metricTitle": "Total Metrics", "format": "number", "valueColor": "#2c3e50", "valueSize": 32, "showTrend": true, "positiveColor": "#27ae60", "negativeColor": "#e74c3c", "value": 0, "trend": 12}} dataBinding={{"entity": "Measure", "endpoint": "/measure/", "data_field": "uncertainty"}} />
        <MetricCardBlock id="i34mih" styles={{"width": "100%", "minHeight": "140px", "--chart-color-palette": "default"}} metric={{"metricTitle": "Total Metrics", "format": "number", "valueColor": "#2c3e50", "valueSize": 32, "showTrend": true, "positiveColor": "#27ae60", "negativeColor": "#e74c3c", "value": 0, "trend": 12}} dataBinding={{"entity": "Measure", "endpoint": "/measure/", "data_field": "uncertainty"}} />
        <MetricCardBlock id="izgtz" styles={{"width": "100%", "minHeight": "140px", "--chart-color-palette": "default"}} metric={{"metricTitle": "Evaluations Completed", "format": "number", "valueColor": "#2c3e50", "valueSize": 32, "showTrend": true, "positiveColor": "#27ae60", "negativeColor": "#e74c3c", "value": 0, "trend": 12}} dataBinding={{"entity": "Measure", "endpoint": "/measure/", "data_field": "uncertainty"}} />
      </section>
      <section id="iux5j" className="assistant-two-column" style={{"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "margin": "12px 24px", "--chart-color-palette": "default"}}>
        <h2 id="i2ppg" style={{"gridColumn": "1 / -1", "fontSize": "1.35rem", "fontWeight": "700", "color": "#0f172a", "margin": "0 0 8px 0", "--chart-color-palette": "default"}}>{"Recent Evaluations & Projects"}</h2>
      </section>
      <TableBlock id="i23pz" styles={{"width": "100%", "minHeight": "300px", "margin": "12px 0", "borderRadius": "12px", "--chart-color-palette": "default"}} title="Recent Evaluations" options={{"showHeader": true, "stripedRows": false, "showPagination": true, "rowsPerPage": 5, "actionButtons": true, "columns": [{"label": "Name", "column_type": "field", "field": "name", "type": "str", "required": true}, {"label": "Description", "column_type": "field", "field": "description", "type": "str", "required": true}, {"label": "Category", "column_type": "lookup", "path": "category", "entity": "MetricCategory", "field": "name", "type": "list", "required": false}, {"label": "Measures", "column_type": "lookup", "path": "measures", "entity": "Measure", "field": "value", "type": "list", "required": false}, {"label": "DerivedBy", "column_type": "lookup", "path": "derivedBy", "entity": "Derived", "field": "expression", "type": "list", "required": false}], "formColumns": [{"column_type": "field", "field": "name", "label": "name", "type": "str", "required": true, "defaultValue": null}, {"column_type": "field", "field": "description", "label": "description", "type": "str", "required": true, "defaultValue": null}, {"column_type": "lookup", "path": "category", "field": "category", "lookup_field": "name", "entity": "MetricCategory", "type": "list", "required": false}, {"column_type": "lookup", "path": "measures", "field": "measures", "lookup_field": "value", "entity": "Measure", "type": "list", "required": false}, {"column_type": "lookup", "path": "derivedBy", "field": "derivedBy", "lookup_field": "name", "entity": "Derived", "type": "list", "required": false}]}} dataBinding={{"entity": "Metric", "endpoint": "/metric/"}} />
      <ChartBlock id="ira693" styles={{"width": "100%", "minHeight": "400px", "--chart-color-palette": "default"}} chartType="bar-chart" title="Bar Chart Title" color="#3498db" chart={{"barWidth": 30, "orientation": "vertical", "showGrid": true, "showLegend": true, "showTooltip": true, "stacked": false, "animate": true, "legendPosition": "top", "gridColor": "#e0e0e0", "barGap": 4}} series={[{"name": "Series_1", "label": "Series 1", "color": "#3498db"}]} />
    </main>
    <footer id="iraev" className="assistant-footer" style={{"padding": "32px 48px", "backgroundColor": "#0f172a", "color": "#94a3b8", "display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginTop": "24px", "fontFamily": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif", "--chart-color-palette": "default"}}>
      <div id="Component">
        <div id="iogbp" style={{"fontWeight": "700", "fontSize": "1.1rem", "color": "#ffffff", "marginBottom": "4px", "--chart-color-palette": "default"}} />
        <div id="i231x" style={{"fontSize": "0.8rem", "--chart-color-palette": "default"}} />
      </div>
      <div id="i7al5" style={{"display": "flex", "gap": "20px", "--chart-color-palette": "default"}}>
        <a id="i9qf7" style={{"color": "#94a3b8", "textDecoration": "none", "fontSize": "0.85rem", "transition": "color 0.2s", "--chart-color-palette": "default"}} href="/">{"Privacy"}</a>
        <a id="i4ues" style={{"color": "#94a3b8", "textDecoration": "none", "fontSize": "0.85rem", "transition": "color 0.2s", "--chart-color-palette": "default"}} href="/">{"Terms"}</a>
        <a id="i9s8m" style={{"color": "#94a3b8", "textDecoration": "none", "fontSize": "0.85rem", "transition": "color 0.2s", "--chart-color-palette": "default"}} href="/">{"Contact"}</a>
      </div>
    </footer>    </div>
  );
};

export default Home;
