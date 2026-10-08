import json

import pytest

from src.phase0_bot import _load_progress, _save_progress


def test_progress_is_resumable(tmp_path):
    path = tmp_path / "progress.json"
    progress = {"completed_battle_ids": ["battle-1"], "completed_count": 1}
    _save_progress(path, progress)
    assert _load_progress(path) == progress


@pytest.mark.parametrize("battle_id", ["battle-1", "battle-2"])
def test_progress_file_is_json(tmp_path, battle_id):
    path = tmp_path / "progress.json"
    _save_progress(path, {"completed_battle_ids": [battle_id], "completed_count": 1})
    assert json.loads(path.read_text())["completed_battle_ids"] == [battle_id]

