import json
import subprocess
from unittest.mock import patch

from src import review


def test_should_comment_when_header_has_implementation(tmp_path):
    header_file = tmp_path / "example.h"
    header_file.write_text(
        "class Example {\n"
        "public:\n"
        "    void implemented() {}\n"
        "};\n",
        encoding="utf-8",
    )

    ctags_output = json.dumps(
        {
            "_type": "tag",
            "name": "implemented",
            "path": str(header_file),
            "pattern": "/^    void implemented() {}$/",
            "line": 3,
            "kind": "function",
        }
    )

    config = {
        "path_source": str(tmp_path),
        "regexIgnore": [],
        "message": "${FILE_PATH} - ${METHODS}",
    }

    with patch.object(review.subprocess, "run") as run_mock:
        run_mock.return_value = subprocess.CompletedProcess(
            args="ctags",
            returncode=0,
            stdout=ctags_output + "\n",
            stderr="",
        )

        comments = review.review(config)

    assert len(comments) == 1
    assert comments[0]["position"]["path"] == "example.h"
    assert comments[0]["comment"] == "example.h - implemented"
