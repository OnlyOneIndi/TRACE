
import json
from datetime import datetime

import streamlit as st

from engine import run_research, ResearchVerificationError
from storage import list_saved_reports, load_report
from provenance import build_provenance


# ─────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────

st.set_page_config(
    page_title="TRACE — Research Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────
# DESIGN
# ─────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(
            ellipse at 50% 15%,
            #303033 0%,
            #202123 40%,
            #18191B 80%
        );
    color: #F1F0EE;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1050px;
    padding-top: 3rem;
    padding-bottom: 5rem;
}

#MainMenu, footer {
    visibility: hidden;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    letter-spacing: -0.035em;
}

.trace-kicker {
    text-align: center;
    font-size: 10px;
    letter-spacing: 0.42em;
    color: #B4B4B7;
    font-weight: 600;
}

.trace-hero {
    text-align: center;
    font-family: 'Manrope', sans-serif;
    font-size: clamp(74px, 14vw, 165px);
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -0.09em;
    color: #F0EFED;
    margin: 38px 0 12px;
}

.trace-subtitle {
    text-align: center;
    color: #AAA9AB;
    letter-spacing: 0.28em;
    font-size: 10px;
    margin-bottom: 65px;
}

.trace-section-label {
    font-size: 11px;
    letter-spacing: 0.25em;
    font-weight: 600;
    color: #AAA9AB;
    margin-bottom: 18px;
}

.trace-caption {
    font-size: 12px;
    color: #99999D;
    letter-spacing: 0.04em;
}

.trace-footer {
    text-align: center;
    font-size: 10px;
    letter-spacing: 0.24em;
    color: #77777B;
    padding-top: 35px;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #202124;
    border-right: 1px solid #38393B;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.4rem;
}

/* Sidebar navigation buttons */

[data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start;
    text-align: left;
    border: none;
    background: transparent;
    color: #E5E5E7;
    font-size: 13px;
    font-weight: 400;
    border-radius: 7px;
    min-height: 37px;
    padding: 8px 12px;
    transition: background 0.15s ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #313235;
    color: #FFFFFF;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #37383C;
    color: #FFFFFF;
    border: none;
}

[data-testid="stSidebar"] .stTextInput input {
    background: #292A2D;
    border: 1px solid #3D3E42;
    border-radius: 7px;
}

/* RESEARCH INPUT */

[data-testid="stChatInput"] {
    background: #242528 !important;
    border: 1px solid #454548 !important;
    border-radius: 7px !important;
}

[data-testid="stChatInput"] textarea {
    color: #F1F0EE !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
}

/* REPORT CARDS */

[data-testid="stExpander"] {
    background: rgba(39, 40, 43, 0.85);
    border: 1px solid #3E3F42;
    border-radius: 4px;
    margin-bottom: 12px;
}

[data-testid="stMetric"] {
    background: #242528;
    padding: 22px;
    border: 1px solid #36373A;
    border-radius: 4px;
}

[data-testid="stMetricLabel"] {
    color: #AAA9AC;
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

hr {
    border-color: #3C3C40 !important;
    opacity: 0.6;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────

if "report" not in st.session_state:
    st.session_state.report = None

if "saved_path" not in st.session_state:
    st.session_state.saved_path = None

if "report_origin" not in st.session_state:
    st.session_state.report_origin = None


# ─────────────────────────────────────────
# HISTORY HELPER FUNCTIONS
# ─────────────────────────────────────────

def get_report_title(filepath):
    """
    Read the research title directly from the JSON file.

    Supports older reports whose key_findings format
    may not match the current Pydantic schema.
    """

    try:
        with filepath.open("r", encoding="utf-8") as file:
            data = json.load(file)

        title = data.get("topic", "")

        if isinstance(title, str) and title.strip():
            return " ".join(title.split())

    except (OSError, ValueError, TypeError, AttributeError):
        pass

    return "Untitled Research"


def get_history_group(filepath):
    """Group reports by the date they were last modified."""

    modified = datetime.fromtimestamp(
        filepath.stat().st_mtime
    ).date()

    today = datetime.now().date()

    age = (today - modified).days

    if age <= 0:
        return "Today"

    if age == 1:
        return "Yesterday"

    if age <= 7:
        return "Previous 7 Days"

    if age <= 30:
        return "Previous 30 Days"

    return "Older"


def open_saved_research(filepath):
    """Load a saved report into the main workspace."""

    report = load_report(filepath)

    st.session_state.report = report
    st.session_state.saved_path = filepath
    st.session_state.report_origin = "archive"


def clear_research():
    """Clear the current report without deleting saved files."""

    st.session_state.report = None
    st.session_state.saved_path = None
    st.session_state.report_origin = None


# ─────────────────────────────────────────
# CHATGPT-STYLE RESEARCH SIDEBAR
# ─────────────────────────────────────────

with st.sidebar:

    st.markdown("## ◈ TRACE")
    st.caption("RESEARCH INTELLIGENCE")

    st.write("")

    if st.button(
        "✎  New Research",
        use_container_width=True,
        key="new_research_button",
    ):
        clear_research()
        st.rerun()

    st.divider()

    history_search = st.text_input(
        "Search research history",
        placeholder="Search investigations...",
        key="history_search",
    )

    st.write("")

    saved_reports = list_saved_reports()

    st.caption(
        f"RESEARCH HISTORY · {len(saved_reports)} SAVED"
    )

    # Read each report's title from its saved JSON.
    history_items = []

    for filepath in saved_reports:
        title = get_report_title(filepath)

        history_items.append({
            "path": filepath,
            "title": title,
            "group": get_history_group(filepath),
        })

    # Filter by the full research title.
    if history_search.strip():

        search_term = history_search.strip().casefold()

        history_items = [
            item
            for item in history_items
            if search_term in item["title"].casefold()
        ]

    # Display the groups in order.
    group_order = [
        "Today",
        "Yesterday",
        "Previous 7 Days",
        "Previous 30 Days",
        "Older",
    ]

    if not history_items:

        st.caption(
            "No matching research reports."
        )

    else:

        for group_name in group_order:

            group_items = [
                item
                for item in history_items
                if item["group"] == group_name
            ]

            if not group_items:
                continue

            st.caption(group_name.upper())

            for item in group_items:

                filepath = item["path"]
                full_title = item["title"]

                # Keep long titles readable in the sidebar.
                display_title = (
                    full_title[:43] + "…"
                    if len(full_title) > 44
                    else full_title
                )

                is_active = (
                    st.session_state.saved_path is not None
                    and str(st.session_state.saved_path)
                    == str(filepath)
                )

                if st.button(
                    display_title,
                    key=f"history_{filepath.stem}",
                    use_container_width=True,
                    type=(
                        "primary"
                        if is_active
                        else "secondary"
                    ),
                    help=full_title,
                ):
                    try:
                        open_saved_research(filepath)
                        st.rerun()

                    except Exception as error:
                        st.error(
                            "This report could not be opened."
                        )

                        with st.expander("Technical details"):
                            st.code(str(error))

            st.write("")

    st.divider()
    st.caption("TRACE / LOCAL WORKSPACE")


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.markdown(
    '<div class="trace-kicker">'
    'INDEPENDENT RESEARCH SYSTEM'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="trace-hero">TRACE</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="trace-subtitle">'
    'EXPLORE IDEAS. TRACE THE EVIDENCE.'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────
# RESEARCH WORKSPACE
# ─────────────────────────────────────────

st.markdown(
    '<div class="trace-section-label">'
    '01 / NEW INVESTIGATION'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────
# RESEARCH CONFIGURATION
# ─────────────────────────────────────────

with st.expander(
    "RESEARCH SETTINGS",
    expanded=False,
):

    max_papers = st.slider(
        "Maximum number of papers",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        key="trace_max_papers",
    )

    restrict_year = st.checkbox(
        "Restrict publication years",
        value=False,
        key="trace_restrict_year",
    )

    earliest_year = None

    if restrict_year:

        current_year = datetime.now().year

        earliest_year = st.number_input(
            "Earliest publication year",
            min_value=1900,
            max_value=current_year,
            value=min(2023, current_year),
            step=1,
            key="trace_earliest_year",
        )

        earliest_year = int(earliest_year)


# ─────────────────────────────────────────
# CHAT-STYLE RESEARCH INPUT
# ─────────────────────────────────────────

question = st.chat_input(
    "Ask Trace to investigate something...",
    key="trace_research_input",
)

st.markdown(
    '<div class="trace-caption">'
    'ENTER TO RESEARCH / SHIFT + ENTER FOR NEW LINE'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────
# RUN RESEARCH
# ─────────────────────────────────────────

if question:

    clear_research()

    try:

        with st.spinner(
            "Searching literature and checking evidence..."
        ):

            report, saved_path = run_research(
                question=question,
                max_papers=max_papers,
                from_year=earliest_year,
            )

        st.session_state.report = report
        st.session_state.saved_path = saved_path
        st.session_state.report_origin = "new"

        st.success(
            "Research completed!. "

        )

    except ResearchVerificationError as error:

        st.error(
            "Research did not pass verification."
        )

        with st.expander("Verification details"):
            st.code(str(error))

    except Exception as error:

        st.error(
            f"Research failed: {type(error).__name__}"
        )

        with st.expander("Technical details"):
            st.code(str(error))


# ─────────────────────────────────────────
# DISPLAY REPORT
# ─────────────────────────────────────────

report = st.session_state.report

if report is not None:

    st.divider()

    st.markdown(
        '<div class="trace-section-label">'
        '02 / RESEARCH OUTPUT'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.report_origin == "archive":
        st.caption("OPENED FROM RESEARCH HISTORY")

    else:
        st.caption("NEW RESEARCH / CHECKS PASSED")

    st.header(report.topic)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "PAPERS",
        len(report.papers),
    )

    col2.metric(
        "FINDINGS",
        len(report.key_findings),
    )

    col3.metric(
        "STATUS",
        "SAVED",
    )

    # OVERVIEW

    st.subheader("Overview")
    st.write(report.overall_summary)

    st.divider()

    # PAPERS

    st.markdown(
        '<div class="trace-section-label">'
        '03 / SOURCE LIBRARY'
        '</div>',
        unsafe_allow_html=True,
    )

    for index, paper in enumerate(
        report.papers,
        start=1,
    ):

        with st.expander(
            f"{index:02d} / {paper.title}",
            expanded=index == 1,
        ):

            col_year, col_citations = st.columns(2)

            col_year.caption("PUBLICATION YEAR")
            col_year.write(
                paper.year
                if paper.year is not None
                else "Unknown"
            )

            col_citations.caption(
                "CITATIONS AT RETRIEVAL"
            )
            col_citations.write(paper.citations)

            st.write(paper.summary)

            st.link_button(
                "VIEW ORIGINAL SOURCE",
                paper.url,
            )

    st.divider()

    # FINDINGS

    # ─────────────────────────────────────
    # FINDINGS WITH SOURCE PROVENANCE
    # ─────────────────────────────────────

    st.markdown(
        '<div class="trace-section-label">'
        '04 / EVIDENCE & SOURCE PROVENANCE'
        '</div>',
        unsafe_allow_html=True,
    )

    provenance_records = build_provenance(report)

    for record in provenance_records:

        with st.container(border=True):

            st.caption(
                f"FINDING {record['finding_number']:02d}"
            )

            st.markdown(
                f"#### {record['claim']}"
            )

            if record["source_linked"]:
                st.caption(
                    "SOURCE LINKED TO REPORT"
                )
            else:
                st.warning(
                    "No matching paper found in this report."
                )

            st.markdown("**Supporting evidence**")
            st.info(record["evidence"])

            with st.expander(
                "VIEW SOURCE PROVENANCE"
            ):

                if record["source_linked"]:

                    st.markdown(
                        f"**Paper:** {record['source_title']}"
                    )

                    st.write(
                        "Publication year:",
                        record["source_year"]
                    )

                    st.write(
                        "Citations at retrieval:",
                        record["source_citations"]
                    )

                st.markdown(
                    f"[OPEN ORIGINAL SOURCE]"
                    f"({record['source_url']})"
                )

                st.divider()

                st.markdown(
                    "**How this information was produced**"
                )

                st.write(
                    "**OpenAlex:** Research paper metadata "
                    "and abstract retrieval."
                )

                st.write(
                    "**Gemini:** Generated the claim, "
                    "summary, and selected evidence passage."
                )

                st.write(
                    "**Trace:** Checks source metadata, "
                    "evidence quotations, and certain "
                    "numerical inconsistencies before "
                    "saving a new report."
                )

                st.caption(
                    "Source linkage is not proof that "
                    "the claim follows from the evidence. "
                    "Opening an archived report does not "
                    "repeat its original verification."
                )


    # DOWNLOAD

    st.markdown(
        '<div class="trace-section-label">'
        '05 / EXPORT'
        '</div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        label="DOWNLOAD RESEARCH REPORT / JSON",
        data=report.model_dump_json(indent=2),
        file_name="trace_report.json",
        mime="application/json",
        use_container_width=True,
    )

    st.caption(
        "Trace verifies retrieved paper metadata, "
        "quoted evidence, and selected numerical "
        "consistency checks. These checks do not "
        "guarantee scientific accuracy."
    )


# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────

st.markdown(
    '<div class="trace-footer">'
    'TRACE © 2026 · RESEARCH INTELLIGENCE SYSTEM'
    '</div>',
    unsafe_allow_html=True,
)
