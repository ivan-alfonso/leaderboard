import React from "react";
import { TableBlock } from "../components/runtime/TableBlock";
import { ModelMetricsBarChart } from "../components/charts/ModelMetricsBarChart";
import { useTheme } from "../contexts/ThemeContext";

const Home: React.FC = () => {
  const { theme, colors, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  const pageStyle: React.CSSProperties = {
    width: "auto",
    minHeight: "100vh",
    padding: 0,
    margin: 0,
    backgroundColor: colors.pageBg,
    color: colors.textPrimary,
    fontFamily: "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
    transition: "background-color 0.3s ease, color 0.3s ease",
  };

  const heroStyle: React.CSSProperties = {
    padding: "28px 48px 32px",
    backgroundColor: colors.pageBg,
    color: colors.textPrimary,
    margin: 0,
    textAlign: "center",
    transition: "background-color 0.3s ease, color 0.3s ease",
  };

  const sectionStyle: React.CSSProperties = {
    backgroundColor: colors.surface,
    borderRadius: "16px",
    padding: "32px",
    margin: "0 0 20px 0",
    border: `1px solid ${colors.border}`,
    boxShadow: colors.shadow,
    transition: "background-color 0.3s ease, border-color 0.3s ease",
  };

  const sectionHeadingStyle: React.CSSProperties = {
    fontSize: "1.35rem",
    fontWeight: 700,
    color: colors.textPrimary,
    marginTop: 0,
    marginBottom: "16px",
    paddingBottom: "12px",
    borderBottom: `2px solid ${colors.accent}`,
    letterSpacing: "-0.01em",
    textTransform: "uppercase",
  };

  const bodyTextStyle: React.CSSProperties = {
    fontSize: "1rem",
    lineHeight: 1.75,
    color: colors.textSecondary,
    margin: 0,
  };

  return (
    <div id="5WFQu3cZBn89Z4xa" style={pageStyle}>
      <section id="ic1xf" className="assistant-hero" style={heroStyle}>
        {/* Top row: logos on the left, theme toggle on the right */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "24px", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "40px", flexWrap: "wrap" }}>
            <img
              src="/img/list.png"
              alt="LIST Logo"
              style={{ height: "56px", objectFit: "contain", filter: isDark ? "brightness(0) invert(1)" : "none" }}
            />
            <img
              src="/img/inl.png"
              alt="INL Logo"
              style={{ height: "56px", objectFit: "contain", filter: isDark ? "brightness(0) invert(1)" : "none" }}
            />
          </div>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 14px",
              borderRadius: "999px",
              border: `1px solid ${colors.border}`,
              backgroundColor: colors.surface,
              color: colors.textPrimary,
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: 600,
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = colors.hoverBg;
              e.currentTarget.style.borderColor = colors.borderStrong;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = colors.surface;
              e.currentTarget.style.borderColor = colors.border;
            }}
          >
            {isDark ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
                <span>Light</span>
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
                <span>Dark</span>
              </>
            )}
          </button>
        </div>

        <hr style={{ border: "none", borderTop: `1px solid ${colors.border}`, margin: "20px 0 36px 0" }} />

        <h1
          id="inicg"
          style={{
            margin: 0,
            fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
            fontWeight: 800,
            letterSpacing: "-0.02em",
            lineHeight: 1.15,
            color: colors.textPrimary,
          }}
        >
          HOW WELL DO LLMS UNDERSTAND LUXEMBOURGISH?
        </h1>
      </section>

      <main id="ixzli" className="assistant-main" style={{ maxWidth: "1400px", margin: "0 auto", padding: "8px 24px 24px" }}>
        {/* Introduction Section */}
        <section style={sectionStyle}>
          <p style={{ ...bodyTextStyle, marginBottom: "16px" }}>
            Large Language Models (LLMs) have reshaped the AI landscape in recent years. They are becoming omnipresent, being used by private users and companies alike. However, LLMs are developed mainly for widespread languages such as English, Spanish, or German, leaving languages such as Luxembourgish on the sidelines.
          </p>
          <p style={bodyTextStyle}>
            In this project, we aimed to test the linguistic capabilities of LLMs in Luxembourgish. In collaboration with the Institut National des Langues Luxembourg, we used language proficiency exams to evaluate the performance of 45 current-day LLMs.
          </p>
        </section>

        {/* How Does It Work Section */}
        <section style={sectionStyle}>
          <h2 style={sectionHeadingStyle}>How Does It Work?</h2>
          <p style={bodyTextStyle}>
            Using official language exams crafted by experts at INLL, we systematically test LLMs by letting them solve each question and grade their overall performance. There are 630 multiple-choice questions in total, each belonging to one out of four broad categories (Vocabulary, Grammar, Reading Comprehension, Listening Comprehension) and a CEFR level (A1, A2, B1, B2, C1, C2). The performance of the LLMs for each category and CEFR level is expressed as a percentage of correctly answered questions.
          </p>
        </section>

        {/* How to Use Section */}
        <section style={sectionStyle}>
          <h2 style={sectionHeadingStyle}>How To Use This Leaderboard?</h2>
          <p style={{ ...bodyTextStyle, marginBottom: "14px" }}>
            Below, you find the control panel for filtering the leaderboard. You can select a desired CEFR level and category to filter the table accordingly. In addition, you can choose to display only open-source/closed-source models, select a specific language models family (e.g. only Llama models), select a specific size range of LLM parameters, or display models that correctly answered a given percentage of questions. To help with readability, the highest performing models are highlighted in green.
          </p>
          <p style={bodyTextStyle}>
            Underneath the table, you find a bar chart showing the performance of the LLMs for each category and CEFR level to help compare the performance of the LLMs.
          </p>
        </section>

        <TableBlock
          id="i23pz"
          styles={{ width: "100%", minHeight: "300px", margin: "0 0 20px 0" }}
          title="Model Leaderboard"
          options={{
            showHeader: true,
            stripedRows: true,
            showPagination: true,
            rowsPerPage: 10,
            actionButtons: false,
            columns: [
              { label: "LLM", column_type: "field", field: "name", type: "str", required: true },
              { label: "Size", column_type: "field", field: "data", type: "str", required: false },
              { label: "Family", column_type: "field", field: "source", type: "str", required: false },
              { label: "Closed_Open", column_type: "field", field: "licensing", type: "str", required: false },
              { label: "A1_total", column_type: "field", field: "a1_total", type: "number", required: false },
              { label: "A2_total", column_type: "field", field: "a2_total", type: "number", required: false },
              { label: "B1_total", column_type: "field", field: "b1_total", type: "number", required: false },
              { label: "B2_total", column_type: "field", field: "b2_total", type: "number", required: false },
              { label: "C1_total", column_type: "field", field: "c1_total", type: "number", required: false },
              { label: "C2_total", column_type: "field", field: "c2_total", type: "number", required: false },
            ],
          }}
          dataBinding={{ entity: "Model", endpoint: "/model/leaderboard" }}
        />
        <ModelMetricsBarChart id="metrics-chart" title="Model Performance Comparison" styles={{ margin: 0 }} maxModels={54} />
      </main>

      <footer
        id="iraev"
        className="assistant-footer"
        style={{
          padding: "32px 48px",
          backgroundColor: colors.footerBg,
          color: colors.footerText,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "40px",
          fontFamily: "inherit",
          flexWrap: "wrap",
          gap: "20px",
          transition: "background-color 0.3s ease",
        }}
      >
        <div id="Component">
          <div id="iogbp" style={{ fontWeight: 700, fontSize: "1.1rem", color: "#ffffff", marginBottom: "4px" }} />
          <div id="i231x" style={{ fontSize: "0.8rem" }} />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "32px", flexWrap: "wrap" }}>
          <div id="i7al5" style={{ display: "flex", gap: "20px" }}>
            <a id="i9qf7" style={{ color: colors.footerText, textDecoration: "none", fontSize: "0.85rem", transition: "color 0.2s" }} href="/">Privacy</a>
            <a id="i4ues" style={{ color: colors.footerText, textDecoration: "none", fontSize: "0.85rem", transition: "color 0.2s" }} href="/">Terms</a>
            <a id="i9s8m" style={{ color: colors.footerText, textDecoration: "none", fontSize: "0.85rem", transition: "color 0.2s" }} href="/">Contact</a>
          </div>

          {/* BESSER Credit */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", paddingLeft: "32px", borderLeft: `1px solid ${colors.footerDivider}` }}>
            <p style={{ fontSize: "0.85rem", color: colors.footerText, margin: 0 }}>Designed with</p>
            <a
              href="https://editor.besser-pearl.org/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: "inline-block", transition: "transform 0.2s, opacity 0.2s", cursor: "pointer", lineHeight: 0 }}
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
                style={{ height: "28px", display: "block", filter: "brightness(0) invert(1) opacity(0.8)" }}
              />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
