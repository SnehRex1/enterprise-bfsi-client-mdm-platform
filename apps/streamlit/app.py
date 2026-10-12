"""

BFSI Client MDM — Streamlit Stewardship Console

Purpose:

    Provide a browser-based interface over the existing

    FastAPI endpoints.

Architecture:

    Streamlit -> FastAPI -> Azure SQL

This application does not connect to Azure SQL directly.

It does not perform entity resolution or create Gold records.

"""

import os

from urllib.parse import quote

import requests

import streamlit as st

# ============================================================

# 1. CONFIGURATION

# ============================================================

# Use the environment variable when provided.

# Otherwise, default to the local FastAPI development server.

API_URL = os.getenv(

    "MDM_API_URL",

    "http://127.0.0.1:8000",

).rstrip("/")

# Configure the browser page before displaying other elements.

st.set_page_config(

    page_title="BFSI Client MDM",

    page_icon="🏦",

    layout="wide",

)

# Show the previous decision result after the UI refreshes.

# This lets the review queue reload without losing the message.

if st.session_state.get("phase11_flash"):

    st.success(st.session_state.pop("phase11_flash"))

# ============================================================

# 2. HTTP HELPERS

# ============================================================

def api_get(path: str, params: dict | None = None):

    """

    Send a GET request to FastAPI and return the JSON response.

    Example:

        api_get("/health")

        api_get("/clients/search", {"q": "David", "limit": 20})

    """

    response = requests.get(

        f"{API_URL}{path}",

        params=params,

        timeout=30,

    )

    # Convert HTTP errors (such as 404 or 409) into exceptions

    # so the UI can display an appropriate message.

    response.raise_for_status()

    return response.json()

def api_post(path: str, payload: dict):

    """

    Send a POST request to FastAPI.

    Used for stewardship approval/rejection only.

    """

    response = requests.post(

        f"{API_URL}{path}",

        json=payload,

        timeout=30,

    )

    response.raise_for_status()

    return response.json()

def api_error_message(exc: requests.RequestException) -> str:

    """

    Produce a readable message for a failed API request.

    """

    response = getattr(exc, "response", None)

    if response is not None:

        try:

            body = response.json()

            detail = (

                body.get("detail", body)

                if isinstance(body, dict)

                else body

            )

        except ValueError:

            detail = response.text

        return f"HTTP {response.status_code}: {detail}"

    return str(exc)

def show_value(value) -> str:

    """Display missing values consistently in the UI."""

    if value is None or value == "":

        return "Not available"

    return str(value)

def submit_stewardship_decision(

    case_id: str,

    action: str,

    steward_id: str,

    decision_reason: str,

):

    """

    Submit a decision using the existing FastAPI endpoint.

    This function does not write to SQL itself.

    FastAPI handles the SQL transaction and audit insert.

    """

    if not steward_id.strip():

        st.warning("Enter a Steward ID before submitting.")

        return

    if not decision_reason.strip():

        st.warning("Enter a decision reason before submitting.")

        return

    endpoint = f"/matches/{quote(case_id, safe='')}/{action}"

    payload = {

        "steward_id": steward_id.strip(),

        "decision_reason": decision_reason.strip(),

    }

    try:

        result = api_post(endpoint, payload)

        st.session_state["phase11_flash"] = (
            f"Case {result['case_id']} saved successfully: "
            f"{result['decision']}."
        )

        # After saving a manually loaded case, return to the pending queue.
        if st.session_state.get("phase11_manual_case_override") == case_id:
            st.session_state.pop("phase11_manual_case_override", None)

        # Reload the pending list. A resolved case should disappear
        # because the existing API reads the pending-review view.
        st.rerun()

    except requests.RequestException as exc:

        st.error(

            "The stewardship decision was not confirmed by the API. "

            "Check the response before retrying. "

            + api_error_message(exc)

        )

# ============================================================

# 3. SIDEBAR NAVIGATION

# ============================================================

st.sidebar.title("BFSI MDM")

st.sidebar.caption(

    "Enterprise Client Master Data Management"

)

st.sidebar.caption(f"FastAPI: {API_URL}")

page = st.sidebar.radio(

    "Navigate",

    [

        "Client Search",

        "Golden Record",

        "Match Review",

    ],

)

# ============================================================

# PAGE 1 — CLIENT SEARCH

# ============================================================

if page == "Client Search":

    st.title("Client Search")

    st.write(

        "Search the published Golden Records by master ID, "

        "name prefix, email or phone."

    )

    with st.form("client_search_form"):

        query = st.text_input(

            "Master ID, name, email or phone",

            placeholder="Example: MC000550 or David",

        )

        limit = st.selectbox(

            "Maximum results",

            options=[10, 20, 30, 50],

            index=1,

        )

        search_clicked = st.form_submit_button(

            "Search",

            use_container_width=True,

        )

    if search_clicked:

        if not query.strip():

            st.session_state.pop(

                "phase11_search_results",

                None,

            )

            st.warning("Enter a search value.")

        else:

            try:

                results = api_get(

                    "/clients/search",

                    params={

                        "q": query.strip(),

                        "limit": limit,

                    },

                )

                st.session_state["phase11_search_results"] = results

                st.session_state["phase11_search_query"] = query.strip()

            except requests.RequestException as exc:

                st.session_state.pop(

                    "phase11_search_results",

                    None,

                )

                st.error(

                    "Client search failed. "

                    + api_error_message(exc)

                )

    # Display the last successful search until another search replaces it.

    if "phase11_search_results" in st.session_state:

        results = st.session_state["phase11_search_results"]

        searched_for = st.session_state.get(

            "phase11_search_query",

            "",

        )

        st.divider()

        st.subheader("Search Results")

        st.caption(f"Search query: {searched_for}")

        if results:

            st.success(f"Found {len(results)} returned record(s).")

            st.dataframe(

                results,

                use_container_width=True,

                hide_index=True,

            )

            st.info(

                "Use the Golden Record page to inspect a client's "

                "complete profile and contributing source records."

            )

        else:

            st.info("No clients matched the search.")

# ============================================================

# PAGE 2 — GOLDEN RECORD

# ============================================================

elif page == "Golden Record":

    st.title("Golden Record")

    st.write(

        "Inspect the published master record and the trusted source "

        "records associated with its MASTER_CLIENT_ID."

    )

    with st.form("golden_record_form"):

        master_id = st.text_input(

            "MASTER_CLIENT_ID",

            placeholder="Example: MC000550",

        )

        load_clicked = st.form_submit_button(

            "Load Golden Record",

            use_container_width=True,

        )

    if load_clicked:

        # Clear the previous result so an unsuccessful lookup

        # cannot leave a different client's data on screen.

        st.session_state.pop(

            "phase11_golden_client",

            None,

        )

        st.session_state.pop(

            "phase11_golden_sources",

            None,

        )

        if not master_id.strip():

            st.warning("Enter a MASTER_CLIENT_ID.")

        else:

            encoded_master_id = quote(

                master_id.strip(),

                safe="",

            )

            try:

                # Fetch the Golden Record through FastAPI.

                client = api_get(

                    f"/clients/{encoded_master_id}"

                )

                # Fetch the associated source-system records

                # through the existing source endpoint.

                sources = api_get(

                    f"/clients/{encoded_master_id}/sources"

                )

                st.session_state["phase11_golden_client"] = client

                st.session_state["phase11_golden_sources"] = sources

            except requests.RequestException as exc:

                st.error(

                    "Golden Record lookup failed. "

                    + api_error_message(exc)

                )

    # Keep results visible while the user remains on this page.

    if "phase11_golden_client" in st.session_state:

        client = st.session_state["phase11_golden_client"]

        sources = st.session_state["phase11_golden_sources"]

        st.divider()

        st.subheader(

            show_value(client.get("name"))

        )

        # Summary cards.

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(

                "Master ID",

                show_value(client.get("master_client_id")),

            )

        with col2:

            st.metric(

                "KYC Status",

                show_value(client.get("kyc_status")),

            )

        with col3:

            st.metric(

                "Segment",

                show_value(client.get("segment")),

            )

        # The full JSON view exposes every returned Golden Record

        # attribute, including optional/nullable values.

        with st.expander("View complete Golden Record"):

            st.json(client)

        st.subheader("Trusted Source Records")

        if sources:

            st.caption(

                f"{len(sources)} source record(s) mapped to this master."

            )

            st.dataframe(

                sources,

                use_container_width=True,

                hide_index=True,

            )

            with st.expander("View source records as JSON"):

                st.json(sources)

        else:

            st.info(

                "No source records were returned for this master ID."

            )

# ============================================================
# PAGE 3 — MATCH REVIEW
# ============================================================

else:
    st.title("Stewardship Match Review")
    st.write(
        "Review potential identity matches, compare source evidence, "
        "and submit a decision through FastAPI."
    )

    # Fetch only a small page from the existing pending-review endpoint.
    # The direct case-ID field below can load a case outside this first page.
    pending = []
    try:
        pending = api_get(
            "/matches/pending",
            params={"limit": 100},
        )
    except requests.RequestException as exc:
        st.error(
            "Could not load the pending review queue. "
            + api_error_message(exc)
        )

    case_ids = [
        item["case_id"]
        for item in pending
        if item.get("case_id")
    ]

    if case_ids:
        st.caption(
            f"Displaying up to {len(case_ids)} pending case(s) "
            "returned by the API."
        )
        queue_selected_case = st.selectbox(
            "Select a review case",
            options=case_ids,
            format_func=lambda value: value[:16] + "...",
            key="phase11_queue_selected_case",
        )
    else:
        queue_selected_case = None
        st.info(
            "No pending cases were returned in the current queue. "
            "You can still load a specific case ID below."
        )

    # A manual lookup lets a steward inspect cases outside the API's first
    # 100 returned pending cases. Details are still fetched through FastAPI.
    with st.form("load_case_by_id_form"):
        manual_case_id = st.text_input(
            "Or load a specific case ID from SQL",
            placeholder="Paste the full case_id here",
        )
        load_case_clicked = st.form_submit_button("Load specific case")

    if load_case_clicked:
        if manual_case_id.strip():
            st.session_state["phase11_manual_case_override"] = (
                manual_case_id.strip()
            )
            st.rerun()
        else:
            st.warning("Enter a full case ID.")

    manual_override = st.session_state.get("phase11_manual_case_override")
    if manual_override:
        selected_case = manual_override
        st.caption(f"Reviewing manually selected case: {selected_case}")
        if st.button("Return to pending queue selection"):
            st.session_state.pop("phase11_manual_case_override", None)
            st.rerun()
    else:
        selected_case = queue_selected_case

    if selected_case:
        try:
            details = api_get(
                f"/matches/{quote(selected_case, safe='')}"
            )

            review = details["review"]
            stewardship_case = details.get("stewardship_case")
            record_a = details.get("record_a")
            record_b = details.get("record_b")

            st.divider()
            st.subheader("Match Evidence")

            score_col, rule_col, status_col = st.columns(3)
            with score_col:
                st.metric("Match Score", show_value(review.get("match_score")))
            with rule_col:
                st.metric("Matching Rule", show_value(review.get("matching_rule")))
            with status_col:
                current_status = (
                    stewardship_case.get("status")
                    if stewardship_case
                    else "Not available"
                )
                st.metric("Case Status", show_value(current_status))

            st.markdown("**Explanation**")
            st.write(show_value(review.get("match_reason")))

            with st.expander("Inspect individual similarity scores"):
                score_fields = [
                    "name_score",
                    "address_score",
                    "phone_score",
                    "email_score",
                    "dob_score",
                ]
                score_values = {
                    field: review.get(field)
                    for field in score_fields
                }
                st.json(score_values)

            left, right = st.columns(2)
            with left:
                st.subheader("Record A")
                st.caption(show_value(review.get("record_key_a")))
                if record_a is not None:
                    st.json(record_a)
                else:
                    st.warning("Record A could not be retrieved.")

            with right:
                st.subheader("Record B")
                st.caption(show_value(review.get("record_key_b")))
                if record_b is not None:
                    st.json(record_b)
                else:
                    st.warning("Record B could not be retrieved.")

            st.divider()
            st.subheader("Submit Stewardship Decision")
            st.warning(
                "Submitting a decision updates Azure SQL. "
                "A decision cannot be overwritten by submitting the "
                "opposite decision for the same case."
            )

            with st.form(f"decision_form_{selected_case}"):
                steward_id = st.text_input(
                    "Steward ID",
                    placeholder="Example: demo_steward",
                )
                decision_reason = st.text_area(
                    "Decision reason",
                    placeholder=(
                        "Explain the identity evidence supporting "
                        "approval or rejection."
                    ),
                )
                approve_col, reject_col = st.columns(2)
                with approve_col:
                    approve_clicked = st.form_submit_button(
                        "Approve Match",
                        use_container_width=True,
                    )
                with reject_col:
                    reject_clicked = st.form_submit_button(
                        "Reject Match",
                        use_container_width=True,
                    )

            if approve_clicked:
                submit_stewardship_decision(
                    case_id=selected_case,
                    action="approve",
                    steward_id=steward_id,
                    decision_reason=decision_reason,
                )
            elif reject_clicked:
                submit_stewardship_decision(
                    case_id=selected_case,
                    action="reject",
                    steward_id=steward_id,
                    decision_reason=decision_reason,
                )

        except requests.RequestException as exc:
            st.error(
                "Could not retrieve the selected match details. "
                + api_error_message(exc)
            )
    else:
        st.info("Select a pending case or enter a case ID above to inspect it.")
