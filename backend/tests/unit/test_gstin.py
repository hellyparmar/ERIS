import pytest

from app.core.gstin import generate_synthetic_gstin, is_valid_gstin


def test_synthetic_gstin_is_reproducible_and_checksum_valid():
    first = generate_synthetic_gstin("29", 42)
    second = generate_synthetic_gstin("29", 42)

    assert first == second
    assert first.startswith("29DEMOX")
    assert len(first) == 15
    assert is_valid_gstin(first)


@pytest.mark.parametrize("state_code", ["", "1", "XX", "00", "39"])
def test_synthetic_gstin_rejects_invalid_state_codes(state_code):
    with pytest.raises(ValueError):
        generate_synthetic_gstin(state_code, 1)
