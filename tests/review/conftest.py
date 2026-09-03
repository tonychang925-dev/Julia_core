from __future__ import annotations

import pytest

from tests.review import _testonly
from julia_core.review.admission import (
    _reset_candidate_admission_composition_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_review_admission_composition():
    _testonly._TEST_ADMISSION_SOURCE = None
    _reset_candidate_admission_composition_for_tests()
    yield
    _testonly._TEST_ADMISSION_SOURCE = None
    _reset_candidate_admission_composition_for_tests()
