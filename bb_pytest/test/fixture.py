import pytest


def test_test1():
    pass


@pytest.mark.failure
def test_failure1():
    assert False


def test_test2():
    pass


@pytest.mark.skipped
def test_skipped1():
    pytest.skip("")


def test_test3():
    pass


@pytest.mark.skipped
def test_skipped2():
    pytest.skip("")


def test_test4():
    pass


@pytest.mark.failure
def test_failure2():
    assert False


@pytest.mark.failure
def test_failure3():
    assert False

xfail = pytest.mark.xfail

@xfail(reason="bug")
def test_xpass():
    assert False


@pytest.mark.failure
@xfail(reason="bug fixed")
def test_xfail():
    pass


@pytest.mark.slowtest
def test_marked():
    pass
