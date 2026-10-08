
import json
import time
from typing import Any

import pandas as pd
import requests
import streamlit as st


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="ContractIQ | Contract Intelligence",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Custom CSS
# ============================================================

st.markdown(
    """
    <style>
    /* ---------- Global ---------- */
    .stApp {
        background: #f6f8fb;
    }

    .block-container {
        
        max-width: 1450px;
        padding-top: 4.5rem !important;
        padding-bottom: 3rem;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: #101828;
        border-right: 1px solid #1d2939;
    }

    section[data-testid="stSidebar"] * {
        color: #f2f4f7;
    }

    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #344054;
        background: #182230;
        color: #f2f4f7;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        border-color: #84adff;
        background: #1d2939;
    }

    /* ---------- Header ---------- */
    .app-brand {
        
        
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 0.5rem;
        margin-bottom: 12px;
    }

    .brand-icon {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #1d4ed8;
        color: white;
        font-size: 22px;
        font-weight: 700;
        box-shadow: 0 8px 20px rgba(29, 78, 216, 0.20);
    }

    .brand-title {
        font-size: 26px;
        line-height: 1.2;
        font-weight: 750;
        color: #101828;
        margin: 0;
    }

    .brand-subtitle {
        color: #667085;
        font-size: 13px;
        line-height: 1.4;
        margin: 5px 0 0 0;
    }

    .page-kicker {
        color: #475467;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 22px;
        margin-bottom: 4px;
    }

    .page-title {
        color: #101828;
        font-size: 30px;
        font-weight: 750;
        margin: 0;
    }

    .page-description {
        color: #667085;
        font-size: 14px;
        margin-top: 6px;
        margin-bottom: 18px;
    }

    /* ---------- Cards ---------- */
    .info-card {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
        margin-bottom: 12px;
    }

    .info-card h4 {
        margin: 0 0 7px 0;
        color: #101828;
        font-size: 15px;
    }

    .info-card p {
        margin: 0;
        color: #667085;
        font-size: 13px;
        line-height: 1.55;
    }

    .status-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 700;
        background: #ecfdf3;
        color: #027a48;
        border: 1px solid #abefc6;
    }

    .status-pill.warning {
        background: #fffaeb;
        color: #b54708;
        border-color: #fedf89;
    }

    .status-pill.danger {
        background: #fef3f2;
        color: #b42318;
        border-color: #fecdca;
    }

    /* ---------- Metrics ---------- */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #667085;
    }

    div[data-testid="stMetricValue"] {
        color: #101828;
    }

    /* ---------- Buttons ---------- */
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 9px;
        min-height: 40px;
        font-weight: 650;
    }

    /* ---------- Inputs ---------- */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        border-radius: 9px;
    }

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {
        font-weight: 650;
        color: #667085;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #1d4ed8;
    }

    /* ---------- Risk rows ---------- */
    .risk-high {
        border-left: 4px solid #d92d20;
    }

    .risk-medium {
        border-left: 4px solid #f79009;
    }

    .risk-low {
        border-left: 4px solid #12b76a;
    }

    .evidence {
        background: #f8fafc;
        border: 1px solid #eaecf0;
        border-radius: 8px;
        padding: 10px 12px;
        color: #475467;
        font-size: 13px;
        line-height: 1.55;
    }

    /* ---------- Upload area ---------- */
    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1px dashed #98a2b3;
        border-radius: 12px;
        padding: 6px;
    }

    /* ---------- Footer ---------- */
    .footer {
        margin-top: 40px;
        padding-top: 18px;
        border-top: 1px solid #e4e7ec;
        color: #98a2b3;
        font-size: 12px;
        text-align: center;
    }

    /* ---------- Hide Streamlit chrome ---------- */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Session state
# ============================================================

DEFAULT_API = "http://127.0.0.1:8000"

if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = DEFAULT_API

if "document_version_id" not in st.session_state:
    st.session_state.document_version_id = ""

if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

if "summary" not in st.session_state:
    st.session_state.summary = None

if "extraction" not in st.session_state:
    st.session_state.extraction = None

if "qa_result" not in st.session_state:
    st.session_state.qa_result = None


# ============================================================
# API helpers
# ============================================================

def api_url(path: str) -> str:
    base = st.session_state.api_base_url.rstrip("/")
    return f"{base}{path}"


def api_get(path: str, **kwargs):
    timeout = kwargs.pop("timeout", 30)
    return requests.get(api_url(path), timeout=timeout, **kwargs)


def api_post(path: str, **kwargs):
    timeout = kwargs.pop("timeout", 120)
    return requests.post(api_url(path), timeout=timeout, **kwargs)


def extract_version_id(payload: dict[str, Any]) -> str:
    return (
        payload.get("version_id")
        or payload.get("document_version_id")
        or ""
    )


def safe_value(obj: Any, default: str = "Not identified") -> str:
    if isinstance(obj, dict):
        value = obj.get("value")
        return value if value else default

    if obj is None:
        return default

    return str(obj)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="app-brand">
            <div class="brand-icon">C</div>
            <div>
                <div style="font-size:18px;font-weight:750;">ContractIQ</div>
                <div style="font-size:11px;color:#98A2B3;">
                    Contract Intelligence
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("**Backend**")

    api_url_input = st.text_input(
        "FastAPI URL",
        value=st.session_state.api_base_url,
        label_visibility="collapsed",
    )

    st.session_state.api_base_url = api_url_input.rstrip("/")

    if st.button("Test Backend Connection"):
        try:
            response = api_get("/docs", timeout=10)

            if response.ok:
                st.success("Backend is reachable.")
            else:
                st.warning(
                    f"Backend responded with {response.status_code}."
                )

        except requests.RequestException as exc:
            st.error(f"Connection failed: {exc}")

    st.divider()

    st.markdown("**Current Contract**")

    version_input = st.text_input(
        "Document Version ID",
        value=st.session_state.document_version_id,
        placeholder="Paste document version UUID",
        label_visibility="collapsed",
    )

    if version_input:
        st.session_state.document_version_id = version_input.strip()

    if st.session_state.document_version_id:
        st.caption(
            f"Version: {st.session_state.document_version_id}"
        )

        if st.button("Load Existing Contract"):
            try:
                response = api_get(
                    f"/analysis/summary/{st.session_state.document_version_id}",
                    timeout=30,
                )

                if response.ok:
                    st.session_state.summary = response.json()
                    st.success("Contract loaded.")
                else:
                    st.error(
                        "Summary not available yet. "
                        "The document may still be processing or has not been analyzed."
                    )
                    st.code(response.text)

            except requests.RequestException as exc:
                st.error(f"Could not load contract: {exc}")

    st.divider()

    st.caption("Development UI")
    st.caption("FastAPI + Temporal + PostgreSQL")


# ============================================================
# Main header
# ============================================================

st.markdown(
    """
    <div class="app-brand">
        <div class="brand-icon">C</div>
        <div>
            <div class="brand-title">Contract Intelligence</div>
            <div class="brand-subtitle">
                AI-powered contract analysis, extraction and risk intelligence
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Navigation
# ============================================================

page = st.radio(
    "Navigation",
    [
        "Overview",
        "Upload & Analyze",
        "Contract Details",
        "Risk Analysis",
        "Ask Contract",
    ],
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# Overview
# ============================================================

if page == "Overview":

    st.markdown('<div class="page-kicker">Workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">Contract Overview</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-description">'
        'Review contract intelligence from one dashboard.'
        '</div>',
        unsafe_allow_html=True,
    )

    summary = st.session_state.summary

    if not summary:
        st.info(
            "Upload a contract or enter a processed document version "
            "from the sidebar to load its analysis."
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(
                """
                <div class="info-card">
                    <h4>01 · Ingest</h4>
                    <p>Upload a PDF through the FastAPI document pipeline.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """
                <div class="info-card">
                    <h4>02 · Understand</h4>
                    <p>Extract contract terms and ground answers in source evidence.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                """
                <div class="info-card">
                    <h4>03 · Assess</h4>
                    <p>Apply deterministic risk rules and surface review priorities.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        contract = summary.get("contract", {})
        risk_summary = summary.get("risk_summary", {})
        document = summary.get("document", {})

        title = safe_value(contract.get("title"), "Contract")

        st.markdown(
            f"""
            <div class="info-card">
                <h4>{title}</h4>
                <p>
                    Version {document.get("version_number", "-")}
                    &nbsp;·&nbsp;
                    Processing status: {document.get("processing_status", "-")}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.metric(
                "Total Risks",
                risk_summary.get("total", 0),
            )

        with m2:
            st.metric(
                "High",
                risk_summary.get("high", 0),
            )

        with m3:
            st.metric(
                "Medium",
                risk_summary.get("medium", 0),
            )

        with m4:
            st.metric(
                "Low",
                risk_summary.get("low", 0),
            )

        st.markdown("### Contract Snapshot")

        left, right = st.columns([1.4, 1])

        with left:
            parties = contract.get("parties", [])

            party_values = [
                safe_value(party)
                for party in parties
            ]

            st.markdown("#### Parties")

            if party_values:
                for party in party_values:
                    st.markdown(f"- {party}")
            else:
                st.caption("No parties identified.")

        with right:
            st.markdown("#### Key Dates")

            st.write(
                "**Effective date:** "
                + safe_value(contract.get("effective_date"))
            )

            st.write(
                "**Expiry date:** "
                + safe_value(contract.get("expiry_date"))
            )

            st.write(
                "**Duration:** "
                + safe_value(contract.get("duration"))
            )

        st.markdown("#### Priority Risks")

        risks = summary.get("risks", [])

        for risk in risks[:5]:
            severity = risk.get("severity", "LOW")
            css_class = f"risk-{severity.lower()}"

            with st.container(border=True):
                st.markdown(
                    f'<div class="{css_class}">'
                    f'<strong>{risk.get("title", "Risk")}</strong>'
                    f' &nbsp; '
                    f'<span>{severity}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    risk.get("description", "")
                )

                pages = risk.get("source_pages") or []

                if pages:
                    st.caption(
                        "Source pages: "
                        + ", ".join(map(str, pages))
                    )


# ============================================================
# Upload & Analyze
# ============================================================

elif page == "Upload & Analyze":

    st.markdown('<div class="page-kicker">Ingestion</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">Upload & Analyze</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-description">'
        'Upload a contract, wait for Temporal document processing, then run extraction and risk analysis.'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload contract PDF",
        type=["pdf"],
        help="PDF contracts only.",
    )

    if uploaded_file:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(
                f"""
                <div class="info-card">
                    <h4>{uploaded_file.name}</h4>
                    <p>
                        {uploaded_file.size / 1024:.1f} KB
                        &nbsp;·&nbsp; PDF
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button(
                "Upload Contract",
                type="primary",
                use_container_width=True,
            ):
                try:
                    with st.spinner("Uploading contract..."):
                        response = api_post(
                            "/documents",
                            files={
                                "file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    "application/pdf",
                                )
                            },
                            timeout=60,
                        )

                    if response.ok:
                        payload = response.json()

                        st.session_state.upload_response = payload

                        version_id = extract_version_id(payload)

                        if version_id:
                            st.session_state.document_version_id = version_id

                        st.success(
                            "Contract uploaded and Temporal processing started."
                        )

                        st.json(payload)

                    else:
                        st.error(
                            f"Upload failed ({response.status_code})"
                        )
                        st.code(response.text)

                except requests.RequestException as exc:
                    st.error(f"Upload request failed: {exc}")

    if st.session_state.upload_response:
        st.markdown("### Processing")

        upload = st.session_state.upload_response

        status = (
            upload.get("status")
            or upload.get("processing_status")
            or "UPLOADED"
        )

        st.info(
            "The upload starts the Temporal document-processing workflow. "
            "Once PDF extraction/OCR and indexing have completed, run analysis below."
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Status", status)

        with c2:
            st.metric(
                "Version",
                st.session_state.document_version_id[:8]
                if st.session_state.document_version_id
                else "-",
            )

        with c3:
            workflow_id = upload.get("workflow_id", "-")
            st.metric(
                "Workflow",
                str(workflow_id)[:16],
            )

        st.markdown("### Run Contract Analysis")

        st.caption(
            "Run this after the Temporal document-processing workflow "
            "has completed successfully."
        )

        if st.button(
            "Extract Terms & Analyze Risks",
            type="primary",
            use_container_width=True,
        ):
            version_id = st.session_state.document_version_id

            if not version_id:
                st.error("No document version ID is available.")
                st.stop()

            progress = st.progress(0)
            status_box = st.empty()

            try:
                # 1. Structured extraction
                status_box.info("Step 1/2 · Extracting contract terms...")

                extraction_response = api_post(
                    "/analysis/extract",
                    json={
                        "document_version_id": version_id
                    },
                    timeout=180,
                )

                if not extraction_response.ok:
                    st.error(
                        "Extraction failed. The document may still be "
                        "processing. Wait for Temporal to complete and retry."
                    )
                    st.code(extraction_response.text)
                    st.stop()

                extraction_payload = extraction_response.json()
                st.session_state.extraction = extraction_payload
                progress.progress(50)

                # 2. Risk analysis
                status_box.info("Step 2/2 · Running deterministic risk analysis...")

                risk_response = api_post(
                    "/analysis/risks",
                    params={
                        "document_version_id": version_id
                    },
                    timeout=60,
                )

                if not risk_response.ok:
                    st.error("Risk analysis failed.")
                    st.code(risk_response.text)
                    st.stop()

                progress.progress(90)

                # 3. Load dashboard summary
                summary_response = api_get(
                    f"/analysis/summary/{version_id}",
                    timeout=60,
                )

                if summary_response.ok:
                    st.session_state.summary = summary_response.json()

                progress.progress(100)
                status_box.success("Contract analysis completed.")

            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")

    if st.session_state.document_version_id:
        st.markdown("### Current Version")

        st.code(
            st.session_state.document_version_id,
            language="text",
        )

        st.caption(
            "This UUID identifies the immutable processed document version."
        )


# ============================================================
# Contract Details
# ============================================================

elif page == "Contract Details":

    st.markdown('<div class="page-kicker">Structured Data</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">Contract Details</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-description">'
        'Explore the structured terms extracted from the contract.'
        '</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.summary:
        st.warning("Load a contract summary first.")
    else:
        summary = st.session_state.summary
        contract = summary.get("contract", {})
        commercial = summary.get("commercial", {})
        legal = summary.get("legal", {})

        tabs = st.tabs(
            [
                "Overview",
                "Commercial",
                "Legal",
                "Obligations",
                "Important Dates",
            ]
        )

        with tabs[0]:
            st.subheader("Contract")

            st.write(
                "**Title:** "
                + safe_value(contract.get("title"))
            )

            st.write(
                "**Effective date:** "
                + safe_value(contract.get("effective_date"))
            )

            st.write(
                "**Expiry date:** "
                + safe_value(contract.get("expiry_date"))
            )

            st.write(
                "**Duration:** "
                + safe_value(contract.get("duration"))
            )

            st.subheader("Parties")

            parties = contract.get("parties", [])

            for party in parties:
                with st.expander(
                    safe_value(party, "Party")
                ):
                    st.write(
                        "**Evidence:** "
                        + safe_value(
                            party.get("evidence")
                            if isinstance(party, dict)
                            else None
                        )
                    )

                    pages = (
                        party.get("source_pages", [])
                        if isinstance(party, dict)
                        else []
                    )

                    if pages:
                        st.caption(
                            "Source pages: "
                            + ", ".join(map(str, pages))
                        )

        with tabs[1]:
            st.subheader("Scope of Work")

            scope = commercial.get("scope_of_work", {})

            st.write(safe_value(scope))

            if isinstance(scope, dict) and scope.get("source_pages"):
                st.caption(
                    "Source pages: "
                    + ", ".join(
                        map(str, scope["source_pages"])
                    )
                )

            st.subheader("Payment Terms")

            payment = commercial.get("payment_terms", {})

            st.write(safe_value(payment))

            if isinstance(payment, dict) and payment.get("source_pages"):
                st.caption(
                    "Source pages: "
                    + ", ".join(
                        map(str, payment["source_pages"])
                    )
                )

            st.subheader("Penalties")

            penalties = commercial.get("penalties", [])

            if penalties:
                for penalty in penalties:
                    with st.expander(
                        safe_value(penalty, "Penalty")
                    ):
                        if isinstance(penalty, dict):
                            st.write(
                                penalty.get(
                                    "evidence",
                                    "No evidence available.",
                                )
                            )

                            pages = penalty.get(
                                "source_pages",
                                [],
                            )

                            if pages:
                                st.caption(
                                    "Source pages: "
                                    + ", ".join(
                                        map(str, pages)
                                    )
                                )
            else:
                st.caption("No penalties identified.")

        with tabs[2]:
            st.subheader("Termination")

            termination = legal.get(
                "termination_clauses",
                [],
            )

            for clause in termination:
                with st.expander(
                    safe_value(clause, "Termination clause")
                ):
                    if isinstance(clause, dict):
                        st.write(
                            clause.get(
                                "evidence",
                                "No evidence available.",
                            )
                        )

                        pages = clause.get(
                            "source_pages",
                            [],
                        )

                        if pages:
                            st.caption(
                                "Source pages: "
                                + ", ".join(
                                    map(str, pages)
                                )
                            )

            st.subheader("Dispute Resolution")
            st.write(
                safe_value(
                    legal.get("dispute_resolution")
                )
            )

            st.subheader("Force Majeure")
            st.write(
                safe_value(
                    legal.get("force_majeure")
                )
            )

            st.subheader("Governing Law")
            st.write(
                safe_value(
                    legal.get("governing_law")
                )
            )

        with tabs[3]:
            obligations = summary.get(
                "obligations",
                [],
            )

            if obligations:
                for index, obligation in enumerate(
                    obligations,
                    start=1,
                ):
                    with st.expander(
                        f"Obligation {index}"
                    ):
                        st.write(
                            safe_value(obligation)
                        )

                        if isinstance(obligation, dict):
                            pages = obligation.get(
                                "source_pages",
                                [],
                            )

                            if pages:
                                st.caption(
                                    "Source pages: "
                                    + ", ".join(
                                        map(str, pages)
                                    )
                                )
            else:
                st.caption("No obligations identified.")

        with tabs[4]:
            dates = summary.get(
                "important_dates",
                [],
            )

            if dates:
                rows = []

                for date_item in dates:
                    rows.append(
                        {
                            "Date / Event": safe_value(
                                date_item
                            ),
                            "Source Pages": ", ".join(
                                map(
                                    str,
                                    date_item.get(
                                        "source_pages",
                                        [],
                                    ),
                                )
                            )
                            if isinstance(
                                date_item,
                                dict,
                            )
                            else "",
                        }
                    )

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No important dates identified.")


# ============================================================
# Risk Analysis
# ============================================================

elif page == "Risk Analysis":

    st.markdown('<div class="page-kicker">Compliance</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">Risk Analysis</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-description">'
        'Deterministic contract risks with evidence and source pages.'
        '</div>',
        unsafe_allow_html=True,
    )

    summary = st.session_state.summary

    if not summary:
        st.warning("Load a contract summary first.")
    else:
        risk_summary = summary.get(
            "risk_summary",
            {},
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Total",
                risk_summary.get("total", 0),
            )

        with c2:
            st.metric(
                "High",
                risk_summary.get("high", 0),
            )

        with c3:
            st.metric(
                "Medium",
                risk_summary.get("medium", 0),
            )

        with c4:
            st.metric(
                "Low",
                risk_summary.get("low", 0),
            )

        st.markdown("### Risk Register")

        risks = summary.get("risks", [])

        severity_filter = st.selectbox(
            "Filter by severity",
            ["All", "HIGH", "MEDIUM", "LOW"],
        )

        filtered_risks = [
            risk
            for risk in risks
            if severity_filter == "All"
            or risk.get("severity") == severity_filter
        ]

        for risk in filtered_risks:
            severity = risk.get(
                "severity",
                "LOW",
            )

            css_class = f"risk-{severity.lower()}"

            with st.container(border=True):
                st.markdown(
                    f'<div class="{css_class}">'
                    f'<strong>{risk.get("title", "Risk")}</strong>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                r1, r2 = st.columns([3, 1])

                with r1:
                    st.caption(
                        risk.get(
                            "risk_type",
                            "Risk",
                        )
                    )

                    st.write(
                        risk.get(
                            "description",
                            "",
                        )
                    )

                with r2:
                    st.metric(
                        "Severity",
                        severity,
                    )

                    pages = risk.get(
                        "source_pages",
                        [],
                    )

                    if pages:
                        st.caption(
                            "Page "
                            + ", ".join(
                                map(str, pages)
                            )
                        )

                evidence = risk.get("evidence")

                if evidence:
                    st.markdown(
                        f"""
                        <div class="evidence">
                            <strong>Evidence</strong><br>
                            {evidence}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.caption(
                    "Rule: "
                    + risk.get(
                        "rule_code",
                        "N/A",
                    )
                )


# ============================================================
# Ask Contract
# ============================================================

elif page == "Ask Contract":

    st.markdown('<div class="page-kicker">AI Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-title">Ask Contract</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-description">'
        'Ask questions and receive grounded answers with retrieved source chunks.'
        '</div>',
        unsafe_allow_html=True,
    )

    version_id = st.session_state.document_version_id

    if not version_id:
        st.warning(
            "Upload a contract or enter a document version ID first."
        )
    else:
        question = st.text_area(
            "Your question",
            placeholder=(
                "Example: What are the payment terms "
                "and when are the installments payable?"
            ),
            height=110,
        )

        top_k = st.slider(
            "Retrieved sources",
            min_value=1,
            max_value=8,
            value=3,
        )

        if st.button(
            "Ask Contract",
            type="primary",
            disabled=not question.strip(),
        ):
            try:
                with st.spinner("Searching contract evidence..."):
                    response = api_post(
                        "/qa/ask",
                        json={
                            "document_version_id": version_id,
                            "question": question.strip(),
                            "top_k": top_k,
                        },
                        timeout=180,
                    )

                if response.ok:
                    result = response.json()
                    st.session_state.qa_result = result
                else:
                    st.error(
                        f"Q&A failed ({response.status_code})"
                    )
                    st.code(response.text)

            except requests.RequestException as exc:
                st.error(
                    f"Q&A request failed: {exc}"
                )

        if st.session_state.qa_result:
            result = st.session_state.qa_result

            st.markdown("### Answer")

            st.markdown(
                f"""
                <div class="info-card">
                    <p style="font-size:15px;color:#101828;">
                        {result.get("answer", "No answer returned.")}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            sources = result.get(
                "sources",
                [],
            )

            st.markdown("### Sources")

            if sources:
                for index, source in enumerate(
                    sources,
                    start=1,
                ):
                    start_page = source.get(
                        "start_page",
                        "?",
                    )

                    end_page = source.get(
                        "end_page",
                        start_page,
                    )

                    label = (
                        f"Source {index} · "
                        f"Page {start_page}"
                    )

                    if end_page != start_page:
                        label += f"–{end_page}"

                    with st.expander(label):
                        st.write(
                            source.get(
                                "text",
                                source.get(
                                    "chunk_text",
                                    "Source text not returned.",
                                ),
                            )
                        )

                        if source.get(
                            "similarity_score"
                        ) is not None:
                            st.caption(
                                "Similarity: "
                                + str(
                                    source[
                                        "similarity_score"
                                    ]
                                )
                            )
            else:
                st.caption(
                    "No source chunks returned."
                )


# ============================================================
# Footer
# ============================================================

st.markdown(
    """
    <div class="footer">
        ContractIQ · Contract Intelligence Dashboard ·
        FastAPI + Temporal + PostgreSQL + RAG
    </div>
    """,
    unsafe_allow_html=True,
)
