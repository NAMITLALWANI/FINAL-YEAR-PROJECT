"""T015: tests of the evaluation freeze manifest. Synthetic only (a temporary directory and a fake git runner)."""
import hashlib
import json

import pytest

from hammer_pilot import freeze as fz


def fake_git(dirty=True):
    def run(repo, *args):
        if args[:1] == ("status",):
            return " M a.py\n" if dirty else ""
        if args[:2] == ("rev-parse", "--abbrev-ref"):
            return "main\n"
        return "abc123\n"
    return run


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 2\n")
    return tmp_path


def build(repo, **kw):
    args = dict(repo=repo, freeze_id="F1", files=["a.py", "b.py"], effective_config={"t": 0.75}, params={"beta": 0.05}, env={}, git=fake_git())
    args.update(kw)
    return fz.build_freeze(**args)


def test_seed_rule_is_the_documented_one():
    want = int(hashlib.sha256(b"HAMMER|pilot|F1").hexdigest()[:8], 16)
    assert fz.derive_seed("pilot", "F1") == want
    assert fz.derive_seed("pilot", "F1") != fz.derive_seed("main", "F1")
    assert fz.derive_seed("pilot", "F1") != fz.derive_seed("pilot", "F2")


def test_bad_seed_inputs_refused():
    with pytest.raises(fz.FreezeError):
        fz.derive_seed("other", "F1")
    with pytest.raises(fz.FreezeError):
        fz.derive_seed("pilot", "a|b")
    with pytest.raises(fz.FreezeError):
        fz.derive_seed("pilot", "")


def test_manifest_records_hashes_seeds_and_state(repo):
    m = build(repo)
    assert m["frozen_file_sha256"]["a.py"] == hashlib.sha256(b"x = 1\n").hexdigest()
    assert m["seeds"] == {r: fz.derive_seed(r, "F1") for r in fz.SEED_ROLES}
    assert m["working_tree_dirty"] is True and m["git_head"] == "abc123"
    assert fz.verify_freeze(m, repo) == []


def test_clean_tree_recorded(repo):
    assert build(repo, git=fake_git(dirty=False))["working_tree_dirty"] is False


def test_environment_override_refused(repo):
    with pytest.raises(fz.FreezeError):
        build(repo, env={"AUTHOR_AUTO_SCORE_THRESHOLD": "0.5"})
    with pytest.raises(fz.FreezeError):
        build(repo, env={"DEDUP_LOG_THRESHOLD": "0.1"})
    build(repo, env={"PATH": "/bin"})  # unrelated variables are fine


def test_missing_or_empty_file_set_refused(repo):
    with pytest.raises(fz.FreezeError):
        build(repo, files=["nope.py"])
    with pytest.raises(fz.FreezeError):
        build(repo, files=[])


def test_verify_detects_changed_missing_and_tampered(repo):
    m = build(repo)
    (repo / "a.py").write_text("x = 99\n")
    assert fz.verify_freeze(m, repo) == ["changed: a.py"]
    (repo / "b.py").unlink()
    assert "missing: b.py" in fz.verify_freeze(m, repo)
    m2 = json.loads(json.dumps(build(repo.parent if False else repo, files=["a.py"])))
    m2["seeds"]["pilot"] += 1
    probs = fz.verify_freeze(m2, repo)
    assert any("own hash" in p for p in probs) and any("seed pilot" in p for p in probs)


def test_parameter_change_changes_manifest_hash(repo):
    assert build(repo)["manifest_sha256"] != build(repo, params={"beta": 0.10})["manifest_sha256"]
    assert build(repo)["manifest_sha256"] == build(repo)["manifest_sha256"]
