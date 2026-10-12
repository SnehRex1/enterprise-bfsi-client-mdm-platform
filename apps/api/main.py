"""
FastAPI application for the BFSI MDM serving layer.

The API reads mastered data from Azure SQL.

It does NOT perform:
    - entity resolution
    - fuzzy matching
    - survivorship
    - clustering
    - Golden Record creation

Those operations already happened in Databricks.
"""

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from apps.api.db import engine
from apps.api.schemas import (
    HealthResponse,
    MatchDecisionRequest,
)


app = FastAPI(
    title="BFSI Client MDM API",
    description="Serving API for governed enterprise client master data.",
    version="1.0.0",
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "healthy"}

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {exc}",
        )


@app.get("/clients/search")
def search_clients(
    q: str = Query(
        min_length=1,
        description=(
            "Master ID, email, phone, "
            "or beginning of client name."
        ),
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=50,
    ),
):
    pattern = f"{q}%"

    sql = text(
        """
        SELECT
            master_client_id,
            name,
            dob,
            phone,
            email,
            segment,
            kyc_status
        FROM mdm.master_client
        WHERE
            master_client_id = :q
            OR email = :q
            OR phone = :q
            OR name LIKE :pattern
        ORDER BY master_client_id
        OFFSET 0 ROWS
        FETCH NEXT :limit ROWS ONLY;
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {
                "q": q,
                "pattern": pattern,
                "limit": limit,
            },
        )

        return [
            dict(row._mapping)
            for row in rows
        ]


@app.get("/clients/{master_client_id}")
def get_client(
    master_client_id: str,
):
    sql = text(
        """
        SELECT
            master_client_id,
            name,
            dob,
            phone,
            email,
            address,
            tax_id,
            lei,
            segment,
            kyc_status,
            verification_date,
            aum,
            risk_profile,
            relationship_manager
        FROM mdm.master_client
        WHERE master_client_id = :master_client_id;
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            sql,
            {
                "master_client_id": master_client_id
            },
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Master client not found",
        )

    return dict(row)


@app.get("/clients/{master_client_id}/sources")
def get_client_sources(
    master_client_id: str,
):
    sql = text(
        """
        SELECT
            r.*
        FROM mdm.client_record r
        INNER JOIN mdm.client_source_map m
            ON r.source_system = m.source_system
            AND r.source_id = m.source_id
        WHERE m.master_client_id = :master_client_id
        ORDER BY r.source_system;
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {
                "master_client_id": master_client_id
            },
        )

        return [
            dict(row._mapping)
            for row in rows
        ]


@app.get("/matches/pending")
def pending_matches(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    sql = text(
        """
        SELECT
            case_id,
            record_key_a,
            record_key_b,
            name_score,
            address_score,
            phone_score,
            email_score,
            dob_score,
            match_score,
            matching_rule,
            match_reason
        FROM mdm.v_pending_match_review
        ORDER BY match_score DESC
        OFFSET 0 ROWS
        FETCH NEXT :limit ROWS ONLY;
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {
                "limit": limit
            },
        )

        return [
            dict(row._mapping)
            for row in rows
        ]


@app.get("/matches/{case_id}")
def get_match(
    case_id: str,
):
    review_sql = text(
        """
        SELECT *
        FROM mdm.match_review
        WHERE case_id = :case_id;
        """
    )

    case_sql = text(
        """
        SELECT *
        FROM mdm.stewardship_case
        WHERE case_id = :case_id;
        """
    )

    with engine.connect() as connection:
        review = connection.execute(
            review_sql,
            {"case_id": case_id},
        ).mappings().first()

        case = connection.execute(
            case_sql,
            {"case_id": case_id},
        ).mappings().first()

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Review case not found",
        )

    record_a = get_source_record(
        review["record_key_a"]
    )

    record_b = get_source_record(
        review["record_key_b"]
    )

    return {
        "review": dict(review),
        "stewardship_case": (
            dict(case)
            if case else None
        ),
        "record_a": record_a,
        "record_b": record_b,
    }


def get_source_record(
    record_key: str,
):
    sql = text(
        """
        SELECT *
        FROM mdm.client_record
        WHERE record_key = :record_key;
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            sql,
            {
                "record_key": record_key
            },
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


@app.post("/matches/{case_id}/approve")
def approve_match(
    case_id: str,
    request: MatchDecisionRequest,
):
    return resolve_match(
        case_id=case_id,
        decision="APPROVE_MATCH",
        request=request,
    )


@app.post("/matches/{case_id}/reject")
def reject_match(
    case_id: str,
    request: MatchDecisionRequest,
):
    return resolve_match(
        case_id=case_id,
        decision="REJECT_MATCH",
        request=request,
    )


def resolve_match(
    case_id: str,
    decision: str,
    request: MatchDecisionRequest,
):
    with engine.begin() as connection:

        # Prevent a second decision for an already
        # resolved stewardship case.
        existing = connection.execute(
            text(
                """
                SELECT decision
                FROM mdm.stewardship_case
                WHERE case_id = :case_id;
                """
            ),
            {
                "case_id": case_id,
            },
        ).scalar()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Case already resolved as {existing}"
                ),
            )

        # FIX: Save the decision and transition the case
        # to RESOLVED within the same transaction.
        updated = connection.execute(
            text(
                """
                UPDATE mdm.stewardship_case
                SET
                    status = 'RESOLVED',
                    decision = :decision,
                    decision_reason = :reason,
                    steward_id = :steward_id,
                    decision_timestamp = SYSUTCDATETIME()
                WHERE case_id = :case_id;
                """
            ),
            {
                "case_id": case_id,
                "decision": decision,
                "reason": request.decision_reason,
                "steward_id": request.steward_id,
            },
        )

        if updated.rowcount != 1:
            raise HTTPException(
                status_code=404,
                detail="Stewardship case not found",
            )

        # Preserve an auditable decision history.
        connection.execute(
            text(
                """
                INSERT INTO mdm.stewardship_decision
                (
                    case_id,
                    decision,
                    decision_reason,
                    steward_id,
                    decision_timestamp
                )
                VALUES
                (
                    :case_id,
                    :decision,
                    :reason,
                    :steward_id,
                    SYSUTCDATETIME()
                );
                """
            ),
            {
                "case_id": case_id,
                "decision": decision,
                "reason": request.decision_reason,
                "steward_id": request.steward_id,
            },
        )

    return {
        "case_id": case_id,
        "decision": decision,
        "status": "persisted",
    }