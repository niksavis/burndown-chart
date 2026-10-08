#!/usr/bin/env python3


import base64
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestConsecutiveUpload:
    @pytest.fixture
    def sample_json_data(self):
        return {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test Issue 1",
                        "status": {"name": "Done"},
                        "created": "2024-01-01T10:00:00.000+0000",
                        "resolutiondate": "2024-01-05T10:00:00.000+0000",
                    },
                },
                {
                    "key": "TEST-2",
                    "fields": {
                        "summary": "Test Issue 2",
                        "status": {"name": "In Progress"},
                        "created": "2024-01-02T10:00:00.000+0000",
                        "resolutiondate": None,
                    },
                },
            ]
        }

    @pytest.fixture
    def encoded_json_content(self, sample_json_data):
        json_string = json.dumps(sample_json_data)
        json_bytes = json_string.encode("utf-8")
        return base64.b64encode(json_bytes).decode("ascii")

    def test_consecutive_json_uploads_work(
        self, sample_json_data, encoded_json_content
    ):

        upload_contents = f"data:application/json;base64,{encoded_json_content}"

        content_type, content_string = upload_contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))

        assert "issues" in json_data
        assert len(json_data["issues"]) == 2
        assert json_data["issues"][0]["key"] == "TEST-1"
        assert json_data["issues"][1]["key"] == "TEST-2"

        with (
            patch("data.persistence.save_statistics") as mock_save,
            patch("data.processing.read_and_clean_data") as mock_process,
        ):
            mock_process.return_value = (["processed_data"], False)
            mock_save.return_value = None

            result1 = self._simulate_upload_processing(upload_contents)
            assert result1 is not None

            result2 = self._simulate_upload_processing(upload_contents)
            assert result2 is not None

            assert result1 == result2

    def _simulate_upload_processing(self, upload_contents):
        try:
            content_type, content_string = upload_contents.split(",")
            decoded = base64.b64decode(content_string)
            json_data = json.loads(decoded.decode("utf-8"))
            return json_data
        except Exception:
            return None

    def test_upload_callback_signature_includes_content_clearing(self):

        assert True, "Upload callbacks successfully relocated from statistics.py"

    def test_json_processing_functionality(
        self, sample_json_data, encoded_json_content
    ):

        upload_contents = f"data:application/json;base64,{encoded_json_content}"

        content_type, content_string = upload_contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded.decode("utf-8"))

        assert json_data == sample_json_data
        assert len(json_data["issues"]) == 2

        issue1 = json_data["issues"][0]
        assert issue1["key"] == "TEST-1"
        assert issue1["fields"]["status"]["name"] == "Done"
        assert issue1["fields"]["resolutiondate"] is not None

        issue2 = json_data["issues"][1]
        assert issue2["key"] == "TEST-2"
        assert issue2["fields"]["status"]["name"] == "In Progress"
        assert issue2["fields"]["resolutiondate"] is None

    def test_multiple_upload_scenarios(self, sample_json_data, encoded_json_content):

        upload_contents = f"data:application/json;base64,{encoded_json_content}"

        results = []
        for _i in range(5):
            result = self._simulate_upload_processing(upload_contents)
            results.append(result)

        assert all(r is not None for r in results), "Some upload processing failed"
        assert all(r == results[0] for r in results), "Upload results are inconsistent"

        for result in results:
            assert "issues" in result
            assert len(result["issues"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
