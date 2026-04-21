import React from "react";
import { TableBlock } from "../components/runtime/TableBlock";
import { ModelMetricsBarChart } from "../components/charts/ModelMetricsBarChart";

const Home: React.FC = () => {
  return (
    <div id="5WFQu3cZBn89Z4xa" style={{"width": "auto", "height": "100vh", "padding": "0", "margin": "0", "position": "static", "textAlign": "left", "zIndex": 0, "backgroundColor": "#f8fafc", "color": "#1e293b", "--chart-color-palette": "default"}}>
    <section id="ic1xf" className="assistant-hero" style={{"padding": "64px 48px", "background": "linear-gradient(135deg, #3b4f68 0%, #7c93b6 100%)", "color": "#ffffff", "borderRadius": "16px", "margin": "24px", "textAlign": "center", "--chart-color-palette": "default"}}>
      {/* Logos at the top */}
      <div style={{"display": "flex", "justifyContent": "center", "alignItems": "center", "gap": "40px", "marginBottom": "32px", "flexWrap": "wrap"}}>
        <img 
          src="/img/list.png" 
          alt="LIST Logo" 
          style={{"height": "60px", "objectFit": "contain"}}
        />
        <img 
          src="/img/inl.png" 
          alt="INL Logo" 
          style={{"height": "60px", "objectFit": "contain"}}
        />
      </div>
      
      <h1 id="inicg" style={{"margin": "0", "fontSize": "2.25rem", "fontWeight": "800", "letterSpacing": "-0.02em", "lineHeight": "1.2", "--chart-color-palette": "default"}}>{"HOW WELL DO LLMS UNDERSTAND LUXEMBOURGISH?"}</h1>
    </section>
    
    <main id="ixzli" className="assistant-main" style={{"maxWidth": "1400px", "margin": "0 auto", "padding": "24px", "--chart-color-palette": "default"}}>
      {/* Introduction Section */}
      <section style={{"backgroundColor": "#ffffff", "borderRadius": "12px", "padding": "32px", "margin": "0 0 24px 0", "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"}}>
        <p style={{"fontSize": "1.05rem", "lineHeight": "1.8", "color": "#374151", "marginBottom": "20px"}}>
          {"Large Language Models (LLMs) have reshaped the AI landscape in recent years. They are becoming omnipresent, being used by private users and companies alike. However, LLMs are developed mainly for widespread languages such as English, Spanish, or German, leaving languages such as Luxembourgish on the sidelines."}
        </p>
        <p style={{"fontSize": "1.05rem", "lineHeight": "1.8", "color": "#374151", "marginBottom": "0"}}>
          {"In this project, we aimed to test the linguistic capabilities of LLMs in Luxembourgish. In collaboration with the Institut National des Langues Luxembourg, we used language proficiency exams to evaluate the performance of 45 current-day LLMs."}
        </p>
      </section>

      {/* How Does It Work Section */}
      <section style={{"backgroundColor": "#ffffff", "borderRadius": "12px", "padding": "32px", "margin": "0 0 24px 0", "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"}}>
        <h2 style={{"fontSize": "1.75rem", "fontWeight": "700", "color": "#1f2937", "marginBottom": "16px", "borderBottom": "3px solid #2563eb", "paddingBottom": "12px"}}>
          {"HOW DOES IT WORK?"}
        </h2>
        <p style={{"fontSize": "1rem", "lineHeight": "1.7", "color": "#4b5563", "marginBottom": "0"}}>
          {"Using official language exams crafted by experts at INLL, we systematically test LLMs by letting them solve each question and grade their overall performance. There are 630 multiple-choice questions in total, each belonging to one out of four broad categories (Vocabulary, Grammar, Reading Comprehension, Listening Comprehension) and a CEFR level (A1, A2, B1, B2, C1, C2). The performance of the LLMs for each category and CEFR level is expressed as a percentage of correctly answered questions."}
        </p>
      </section>

      {/* How to Use Section */}
      <section style={{"backgroundColor": "#ffffff", "borderRadius": "12px", "padding": "32px", "margin": "0 0 24px 0", "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"}}>
        <h2 style={{"fontSize": "1.75rem", "fontWeight": "700", "color": "#1f2937", "marginBottom": "16px", "borderBottom": "3px solid #2563eb", "paddingBottom": "12px"}}>
          {"HOW TO USE THIS LEADERBOARD?"}
        </h2>
        <p style={{"fontSize": "1rem", "lineHeight": "1.7", "color": "#4b5563", "marginBottom": "0"}}>
          {"Below, you find the control panel for filtering the leaderboard. You can select a desired CEFR level and category to filter the table accordingly. In addition, you can choose to display only open-source/closed-source models, select a specific language models family (e.g. only Llama models), select a specific size range of LLM parameters, or display models that correctly answered a given percentage of questions. To help with readability, the highest performing models are highlighted in green."}
        </p>
        <p style={{"fontSize": "1rem", "lineHeight": "1.7", "color": "#4b5563", "marginTop": "16px", "marginBottom": "0"}}>
          {"Underneath the table, you find a bar chart showing the performance of the LLMs for each category and CEFR level to help compare the performance of the LLMs."}
        </p>
      </section>

      <TableBlock id="i23pz" styles={{"width": "100%", "minHeight": "300px", "margin": "0 0 24px 0", "borderRadius": "12px", "--chart-color-palette": "default"}} title="Model Leaderboard" options={{"showHeader": true, "stripedRows": true, "showPagination": true, "rowsPerPage": 10, "actionButtons": false, "columns": [{"label": "LLM", "column_type": "field", "field": "name", "type": "str", "required": true}, {"label": "Size", "column_type": "field", "field": "data", "type": "str", "required": false}, {"label": "Family", "column_type": "field", "field": "source", "type": "str", "required": false}, {"label": "Closed_Open", "column_type": "field", "field": "licensing", "type": "str", "required": false}, {"label": "A1_total", "column_type": "field", "field": "a1_total", "type": "number", "required": false}, {"label": "A2_total", "column_type": "field", "field": "a2_total", "type": "number", "required": false}, {"label": "B1_total", "column_type": "field", "field": "b1_total", "type": "number", "required": false}, {"label": "B2_total", "column_type": "field", "field": "b2_total", "type": "number", "required": false}, {"label": "C1_total", "column_type": "field", "field": "c1_total", "type": "number", "required": false}, {"label": "C2_total", "column_type": "field", "field": "c2_total", "type": "number", "required": false}]}} dataBinding={{"entity": "Model", "endpoint": "/model/leaderboard"}} />
      <ModelMetricsBarChart id="metrics-chart" title="Model Performance Comparison" styles={{"margin": "0"}} maxModels={15} />
    </main>
    <footer id="iraev" className="assistant-footer" style={{"padding": "32px 48px", "backgroundColor": "#0f172a", "color": "#94a3b8", "display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginTop": "24px", "fontFamily": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif", "flexWrap": "wrap", "gap": "20px", "--chart-color-palette": "default"}}>
      <div id="Component">
        <div id="iogbp" style={{"fontWeight": "700", "fontSize": "1.1rem", "color": "#ffffff", "marginBottom": "4px", "--chart-color-palette": "default"}} />
        <div id="i231x" style={{"fontSize": "0.8rem", "--chart-color-palette": "default"}} />
      </div>
      
      <div style={{"display": "flex", "alignItems": "center", "gap": "32px", "flexWrap": "wrap"}}>
        <div id="i7al5" style={{"display": "flex", "gap": "20px", "--chart-color-palette": "default"}}>
          <a id="i9qf7" style={{"color": "#94a3b8", "textDecoration": "none", "fontSize": "0.85rem", "transition": "color 0.2s", "--chart-color-palette": "default"}} href="/">{"Privacy"}</a>
          <a id="i4ues" style={{"color": "#94a3b8", "textDecoration": "none", "fontSize": "0.85rem", "transition": "color 0.2s", "--chart-color-palette": "default"}} href="/">{"Terms"}</a>
          <a id="i9s8m" style={{"color": "#94a3b8", "textDecoration": "none", "fontSize": "0.85rem", "transition": "color 0.2s", "--chart-color-palette": "default"}} href="/">{"Contact"}</a>
        </div>
        
        {/* BESSER Credit */}
        <div style={{"display": "flex", "alignItems": "center", "gap": "10px", "paddingLeft": "32px", "borderLeft": "1px solid #334155"}}>
          <p style={{"fontSize": "0.85rem", "color": "#94a3b8", "margin": "0"}}>
            {"Designed with"}
          </p>
          <a 
            href="https://editor.besser-pearl.org/" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{"display": "inline-block", "transition": "transform 0.2s, opacity 0.2s", "cursor": "pointer", "lineHeight": "0"}}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "scale(1.05)";
              e.currentTarget.style.opacity = "0.8";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.opacity = "1";
            }}
          >
            <img 
              src="/img/besser.png" 
              alt="BESSER Low-Code Platform" 
              style={{"height": "28px", "display": "block", "filter": "brightness(0) invert(1) opacity(0.8)"}}
            />
          </a>
        </div>
      </div>
    </footer>    </div>
  );
};

export default Home;
