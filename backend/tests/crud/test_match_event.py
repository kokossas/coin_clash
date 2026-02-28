from app.crud.match_event import crud_match_event
from app.models.models import Match, MatchEvent


def _make_match(db_session, **overrides):
    defaults = dict(
        entry_fee=1.0,
        kill_award_rate=0.1,
        start_method="cap",
        start_threshold=10,
        status="completed",
    )
    defaults.update(overrides)
    m = Match(**defaults)
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


def _make_event(db_session, match_id, round_number=1):
    e = MatchEvent(
        match_id=match_id,
        round_number=round_number,
        event_type="direct_kill",
        scenario_source="test",
        scenario_text="something happened",
    )
    db_session.add(e)
    db_session.commit()
    db_session.refresh(e)
    return e


def test_get_by_match_id_returns_events_for_match(db_session):
    match_a = _make_match(db_session)
    match_b = _make_match(db_session)
    _make_event(db_session, match_a.id, round_number=1)
    _make_event(db_session, match_a.id, round_number=2)
    _make_event(db_session, match_b.id, round_number=1)

    result = crud_match_event.get_by_match_id(db_session, match_a.id)
    assert len(result) == 2
    assert all(e.match_id == match_a.id for e in result)


def test_get_by_match_id_cursor_filters_by_after_event_id(db_session):
    match = _make_match(db_session)
    e1 = _make_event(db_session, match.id, round_number=1)
    e2 = _make_event(db_session, match.id, round_number=2)
    e3 = _make_event(db_session, match.id, round_number=3)

    result = crud_match_event.get_by_match_id(db_session, match.id, after_event_id=e1.id)
    ids = [e.id for e in result]
    assert ids == [e2.id, e3.id]


def test_get_by_match_id_respects_limit(db_session):
    match = _make_match(db_session)
    for i in range(5):
        _make_event(db_session, match.id, round_number=i + 1)

    result = crud_match_event.get_by_match_id(db_session, match.id, limit=2)
    assert len(result) == 2


def test_get_by_match_id_returns_ordered_by_id(db_session):
    match = _make_match(db_session)
    _ = [_make_event(db_session, match.id, round_number=i) for i in range(4)]

    result = crud_match_event.get_by_match_id(db_session, match.id)
    ids = [e.id for e in result]
    assert ids == sorted(ids)
