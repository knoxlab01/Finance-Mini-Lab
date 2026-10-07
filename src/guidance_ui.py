"""Single-language presentation; guidance rules remain language-independent."""
import streamlit as st
from src.portfolio_guidance import generate_guidance
from src.i18n import tr, localize_message


def render_portfolio_guidance(historical, language="English"):
    t = lambda key, **values: tr(key, language, **values)
    message = lambda value: localize_message(value, language)
    st.subheader(t("Portfolio Guidance"))
    st.caption(t("guidance_disclaimer"))
    if not historical or historical.get("metrics") is None:
        st.info(t("run_history"))
        return
    demo = any(meta.get("provider") == "demo" for meta in historical.get("source_metadata", {}).values())
    if demo:
        st.caption(t("guidance_demo"))
    with st.form("guidance_profile"):
        st.markdown("**" + t("Your Profile") + "**")
        left, middle, right = st.columns(3)
        risk = left.selectbox(t("Risk Preference"), ["Conservative", "Balanced", "Aggressive"], index=1, format_func=t, key="pg_risk")
        horizon = middle.selectbox(t("Investment Horizon"), ["Short Term", "Medium Term", "Long Term"], index=2, format_func=t, key="pg_horizon")
        goal = right.selectbox(t("Primary Goal"), ["Capital Preservation", "Steady Growth", "Growth Priority"], index=1, format_func=t, key="pg_goal")
        run = st.form_submit_button(t("Generate Guidance"), key="pg_run")
    if run:
        historical["guidance_profile"] = dict(risk_preference=risk, investment_horizon=horizon, primary_goal=goal)
    profile = historical.get("guidance_profile")
    if profile is None:
        return
    result = generate_guidance(historical, profile)
    st.caption(t("Applied profile") + ": " + " · ".join(t(value) for value in profile.values()))
    left, right = st.columns(2)
    left.markdown("**" + t("Current Portfolio Assessment") + "**")
    left.write(message(result["assessment"]["label"]))
    right.markdown("**" + t("Fit with Your Profile") + "**")
    right.write(message(result["fit"]["label"]))
    st.caption(t("heuristic"))
    if not historical.get("future_outlook"):
        st.caption(t("run_future"))
    sim = (historical.get("future_outlook") or {}).get("simulation") or {}
    if sim.get("horizon"):
        st.caption(t("evidence_horizon", years=sim["horizon"]))
    if result["recommendations"]:
        st.markdown("**" + t("Key Guidance") + "**")
        for i, recommendation in enumerate(result["recommendations"], 1):
            st.markdown(f"**{i}. {t(recommendation['category'])}**")
            st.write(t("Recommendation") + ": " + message(recommendation["recommendation"]))
            st.caption(t("Why") + ": " + message(recommendation["reason"]))
        st.markdown("**" + t("Illustrative Allocation Direction") + "**")
        st.write(message(result["allocation"]))
    with st.expander(t("Why These Suggestions"), expanded=False):
        st.caption(t("Score") + ": " + str(result["assessment"]["score"]))
        for evidence in result["assessment"]["evidence"]:
            st.write(f"{message(evidence['reason'])} · +{evidence['points']}")
        for context in result["assessment"]["context"]:
            st.caption(message(context))
        if result["notices"]:
            st.caption(t("missing") + ": " + "; ".join(message(n) for n in result["notices"]))
        st.caption(t("rule_note"))
