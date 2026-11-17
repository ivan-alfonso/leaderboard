import React from "react";
import { useTranslation } from "react-i18next";
import { TableBlock } from "../components/runtime/TableBlock";
import { ModelMetricsBarChart } from "../components/charts/ModelMetricsBarChart";
import { AgentComponent } from "../components/AgentComponent";
import { useTheme } from "../contexts/ThemeContext";
import { LanguageSwitcher } from "../i18n/LanguageSwitcher";

const Home: React.FC = () => {
  const { theme, colors, toggleTheme } = useTheme();
  const { t } = useTranslation(["common", "leaderboard"]);
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
        {/* Top row: logos on the left, controls on the right */}
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

          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <LanguageSwitcher />

            <button
              type="button"
              onClick={toggleTheme}
              aria-label={isDark ? t("common:theme.switchToLight") : t("common:theme.switchToDark")}
              title={isDark ? t("common:theme.switchToLight") : t("common:theme.switchToDark")}
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
                  <span>{t("common:theme.light")}</span>
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                  </svg>
                  <span>{t("common:theme.dark")}</span>
                </>
              )}
            </button>
          </div>
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
          {t("leaderboard:hero.title")}
        </h1>
      </section>

      <main id="ixzli" className="assistant-main" style={{ maxWidth: "1400px", margin: "0 auto", padding: "8px 24px 24px" }}>
        {/* Introduction Section */}
        <section style={sectionStyle}>
          <p style={{ ...bodyTextStyle, marginBottom: "16px" }}>
            {t("leaderboard:intro.paragraph1")}
          </p>
          <p style={bodyTextStyle}>
            {t("leaderboard:intro.paragraph2")}
          </p>
        </section>

        {/* How Does It Work Section */}
        <section style={sectionStyle}>
          <h2 style={sectionHeadingStyle}>{t("leaderboard:howItWorks.title")}</h2>
          <p style={bodyTextStyle}>
            {t("leaderboard:howItWorks.body")}
          </p>
          <p style={{ ...bodyTextStyle, marginTop: "12px" }}>
            {t("leaderboard:howItWorks.paperSentence")}{" "}
            <a
              href="https://aclanthology.org/2026.findings-eacl.128/"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: colors.accent, textDecoration: "underline" }}
            >
              {t("leaderboard:howItWorks.paperLinkText")}
            </a>
            .
          </p>
        </section>

        {/* How to Use Section */}
        <section style={sectionStyle}>
          <h2 style={sectionHeadingStyle}>{t("leaderboard:howToUse.title")}</h2>
          <p style={{ ...bodyTextStyle, marginBottom: "14px" }}>
            {t("leaderboard:howToUse.paragraph1")}
          </p>
          <p style={bodyTextStyle}>
            {t("leaderboard:howToUse.paragraph2")}
          </p>
        </section>

        <TableBlock
          id="i23pz"
          styles={{ width: "100%", minHeight: "300px", margin: "0 0 20px 0" }}
          title={t("leaderboard:table.title")}
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
            defaultSort: { field: "c2_total", direction: "desc" },
          }}
          dataBinding={{ entity: "Model", endpoint: "/model/leaderboard" }}
        />
        <ModelMetricsBarChart id="metrics-chart" styles={{ margin: 0 }} maxModels={20} />
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
            <a id="i9qf7" style={{ color: colors.footerText, textDecoration: "none", fontSize: "0.85rem", transition: "color 0.2s" }} href="/">{t("common:footer.privacy")}</a>
            <a id="i4ues" style={{ color: colors.footerText, textDecoration: "none", fontSize: "0.85rem", transition: "color 0.2s" }} href="/">{t("common:footer.terms")}</a>
            <a id="i9s8m" style={{ color: colors.footerText, textDecoration: "none", fontSize: "0.85rem", transition: "color 0.2s" }} href="/">{t("common:footer.contact")}</a>
          </div>

          {/* BESSER Credit */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", paddingLeft: "32px", borderLeft: `1px solid ${colors.footerDivider}` }}>
            <p style={{ fontSize: "0.85rem", color: colors.footerText, margin: 0 }}>{t("common:footer.designedWith")}</p>
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
      <AgentComponent />
    </div>
  );
};

export default Home;
