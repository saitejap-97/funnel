"""Repository: round-trip, corrupt-JSON recovery, upsert semantics."""
from funnel.models.profile import CandidateProfile
from funnel.repository.json_store import JsonFileCandidateStore


def _p(cid="c1"):
    return CandidateProfile(id=cid, name="Ann", skills=["python"],
                            source_file="a.pdf", file_hash="h")


def test_round_trip_and_upsert(tmp_path):
    store = JsonFileCandidateStore(tmp_path / "s.json")
    store.upsert(_p())
    store.upsert(_p())  # duplicate id → single row
    assert len(store.list()) == 1
    assert store.get("c1").name == "Ann"


def test_corrupt_json_recovers(tmp_path):
    f = tmp_path / "s.json"
    f.write_text("{not json")
    store = JsonFileCandidateStore(f)
    assert store.list() == []
    store.upsert(_p())
    assert len(store.list()) == 1


def test_job_store_round_trip(tmp_path):
    from funnel.models.job import JobDescription
    from funnel.repository.job_store import JsonFileJobStore

    store = JsonFileJobStore(tmp_path / "j.json")
    store.upsert(JobDescription(id="j1", title="Backend Engineer",
                                source_file="a.pdf", file_hash="h",
                                full_text="python"))
    store.upsert(JobDescription(id="j1", title="Backend Engineer",
                                source_file="a.pdf", file_hash="h",
                                full_text="python"))
    assert len(store.list()) == 1
    assert store.get("j1").title == "Backend Engineer"
    assert store.get("nope") is None
