import pytest


def test_test1():
    pass


def test_failure1():
    assert False


def test_test2():
    pass


def test_skipped1():
    pytest.skip("")


def test_test3():
    pass


def test_skipped2():
    pytest.skip("")


def test_test4():
    pass


def test_failure2():
    assert False


def test_failure3():
    assert False
