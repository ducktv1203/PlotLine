"""Cases endpoints — create cases, list them, attach tracks."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.models.spatial import Case, TimelineTrack, case_tracks


router = APIRouter(prefix="/cases", tags=["cases"])


class CaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2048)
    track_ids: list[int] = Field(default_factory=list)


class CaseSummary(BaseModel):
    id: int
    name: str
    description: str | None
    track_count: int


class CaseDetail(BaseModel):
    id: int
    name: str
    description: str | None
    track_ids: list[int]


async def _attach_tracks(
    session: AsyncSession, case_id: int, track_ids: list[int]
) -> None:
    if not track_ids:
        return
    existing_ids = set(
        (
            await session.execute(
                select(TimelineTrack.id).where(TimelineTrack.id.in_(track_ids))
            )
        ).scalars().all()
    )
    missing = set(track_ids) - existing_ids
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"unknown track ids: {sorted(missing)}",
        )
    # Insert directly into the association table — avoids triggering a
    # lazy-load on case.tracks, which would deadlock under asyncpg.
    await session.execute(
        insert(case_tracks),
        [{"case_id": case_id, "track_id": tid} for tid in track_ids],
    )


@router.post("", response_model=CaseDetail)
async def create_case(
    payload: CaseCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CaseDetail:
    case = Case(name=payload.name, description=payload.description)
    session.add(case)
    await session.flush()
    await _attach_tracks(session, case.id, payload.track_ids)
    await session.commit()
    # Reading case.tracks after commit would trigger a lazy load outside the
    # async greenlet; we already know which ids we just attached.
    return CaseDetail(
        id=case.id,
        name=case.name,
        description=case.description,
        track_ids=list(payload.track_ids),
    )


@router.get("", response_model=list[CaseSummary])
async def list_cases(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CaseSummary]:
    from sqlalchemy import func

    cases = (
        await session.execute(select(Case).order_by(Case.id.desc()))
    ).scalars().all()

    # One round-trip for all the counts.
    counts = dict(
        (
            await session.execute(
                select(case_tracks.c.case_id, func.count(case_tracks.c.track_id))
                .group_by(case_tracks.c.case_id)
            )
        ).all()
    )

    return [
        CaseSummary(
            id=c.id,
            name=c.name,
            description=c.description,
            track_count=int(counts.get(c.id, 0)),
        )
        for c in cases
    ]


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CaseDetail:
    case = await session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"case {case_id} not found")
    track_ids = (
        await session.execute(
            select(case_tracks.c.track_id)
            .where(case_tracks.c.case_id == case_id)
            .order_by(case_tracks.c.track_id)
        )
    ).scalars().all()
    return CaseDetail(
        id=case.id,
        name=case.name,
        description=case.description,
        track_ids=list(track_ids),
    )


@router.delete("/{case_id}", status_code=204)
async def delete_case(
    case_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    case = await session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"case {case_id} not found")
    await session.delete(case)
    await session.commit()
