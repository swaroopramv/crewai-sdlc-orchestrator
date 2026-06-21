"""Unit tests for retry policy."""

import pytest
from app.orchestration.retry_policy import RetryPolicy


class FakeRetryableError(Exception):
    pass


class FakePermanentError(Exception):
    pass


class TestRetryPolicy:
    def test_succeeds_on_first_try(self):
        policy = RetryPolicy(max_retries=3, base_delay_seconds=0)
        result = policy.execute(lambda: "ok", "stage_test")
        assert result == "ok"

    def test_retries_and_succeeds(self):
        calls = {"count": 0}

        def flaky():
            calls["count"] += 1
            if calls["count"] < 3:
                raise FakeRetryableError("rate limit")
            return "success"

        policy = RetryPolicy(max_retries=3, base_delay_seconds=0, retryable_error_types=("FakeRetryableError",))
        result = policy.execute(flaky, "stage_test")
        assert result == "success"
        assert calls["count"] == 3

    def test_raises_after_max_retries(self):
        policy = RetryPolicy(max_retries=2, base_delay_seconds=0, retryable_error_types=("FakeRetryableError",))
        with pytest.raises(FakeRetryableError):
            policy.execute(lambda: (_ for _ in ()).throw(FakeRetryableError("fail")), "stage_test")

    def test_non_retryable_error_raises_immediately(self):
        calls = {"count": 0}

        def failing():
            calls["count"] += 1
            raise FakePermanentError("fatal")

        policy = RetryPolicy(max_retries=3, base_delay_seconds=0, retryable_error_types=("FakeRetryableError",))
        with pytest.raises(FakePermanentError):
            policy.execute(failing, "stage_test")
        assert calls["count"] == 1

    def test_on_retry_callback_invoked(self):
        retries = []

        def failing():
            raise FakeRetryableError("x")

        def on_retry(attempt, exc):
            retries.append(attempt)

        policy = RetryPolicy(max_retries=2, base_delay_seconds=0, retryable_error_types=("FakeRetryableError",))
        with pytest.raises(FakeRetryableError):
            policy.execute(failing, "stage_test", on_retry=on_retry)

        assert retries == [1, 2]

    def test_delay_backoff(self):
        policy = RetryPolicy(max_retries=3, base_delay_seconds=10, backoff_multiplier=2.0)
        assert policy.delay_for(0) == 10.0
        assert policy.delay_for(1) == 20.0
        assert policy.delay_for(2) == 40.0
