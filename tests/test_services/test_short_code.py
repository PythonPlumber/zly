import pytest

from app.services.short_code import generate_short_code


def test_generate_short_code_length():
    code = generate_short_code()
    assert len(code) == 7


def test_generate_short_code_characters():
    code = generate_short_code()
    assert all(c in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in code)


def test_generate_short_code_uniqueness():
    codes = {generate_short_code() for _ in range(1000)}
    assert len(codes) == 1000


def test_generate_short_code_custom_length():
    code = generate_short_code(length=5)
    assert len(code) == 5
