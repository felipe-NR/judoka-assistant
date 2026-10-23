from collections import deque

from judo_chat.question_rate_limit import (
    DAY_S,
    QuestionRateLimiter,
    seconds_until_free_slot,
    wait_text,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _limiter(clock: FakeClock, **limits: int) -> QuestionRateLimiter:
    defaults = {"per_ip_per_minute": 2, "per_ip_per_day": 5, "global_per_day": 100, "max_tracked_ips": 100}
    return QuestionRateLimiter(**{**defaults, **limits}, clock=clock)


def test_free_slot_counts_only_the_window() -> None:
    accepted = deque([0.0, 50.0, 100.0, 110.0])
    assert seconds_until_free_slot(accepted, now=120.0, window_s=60.0, limit=3) is None
    assert seconds_until_free_slot(accepted, now=120.0, window_s=60.0, limit=2) == 40.0


def test_zero_limit_always_waits_the_whole_window() -> None:
    assert seconds_until_free_slot(deque(), now=0.0, window_s=60.0, limit=0) == 60.0


def test_minute_limit_blocks_then_frees() -> None:
    clock = FakeClock()
    limiter = _limiter(clock)
    assert limiter.check_and_record("1.1.1.1").allowed
    clock.now += 10
    assert limiter.check_and_record("1.1.1.1").allowed
    blocked = limiter.check_and_record("1.1.1.1")
    assert (blocked.allowed, blocked.limit, blocked.retry_after_s) == (False, "ip_por_minuto", 50)
    clock.now += 50
    assert limiter.check_and_record("1.1.1.1").allowed


def test_blocked_question_does_not_count() -> None:
    clock = FakeClock()
    limiter = _limiter(clock, per_ip_per_minute=1)
    limiter.check_and_record("1.1.1.1")
    for _ in range(5):
        assert not limiter.check_and_record("1.1.1.1").allowed
    clock.now += 60
    assert limiter.check_and_record("1.1.1.1").allowed


def test_day_limit_is_per_ip() -> None:
    clock = FakeClock()
    limiter = _limiter(clock)
    for _ in range(5):
        assert limiter.check_and_record("1.1.1.1").allowed
        clock.now += 60
    blocked = limiter.check_and_record("1.1.1.1")
    assert (blocked.allowed, blocked.limit) == (False, "ip_por_dia")
    assert blocked.retry_after_s == DAY_S - 5 * 60
    assert limiter.check_and_record("2.2.2.2").allowed


def test_global_limit_spans_ips() -> None:
    clock = FakeClock()
    limiter = _limiter(clock, global_per_day=3)
    for ip in ("1.1.1.1", "2.2.2.2", "3.3.3.3"):
        assert limiter.check_and_record(ip).allowed
    blocked = limiter.check_and_record("4.4.4.4")
    assert (blocked.allowed, blocked.limit) == (False, "global_por_dia")
    clock.now += DAY_S
    assert limiter.check_and_record("4.4.4.4").allowed


def test_least_recent_ip_is_forgotten_past_the_cap() -> None:
    clock = FakeClock()
    limiter = _limiter(clock, per_ip_per_minute=1, max_tracked_ips=2)
    limiter.check_and_record("1.1.1.1")
    limiter.check_and_record("2.2.2.2")
    limiter.check_and_record("3.3.3.3")
    assert limiter.check_and_record("1.1.1.1").allowed
    assert not limiter.check_and_record("3.3.3.3").allowed


def test_wait_text() -> None:
    assert wait_text(1) == "1 segundo"
    assert wait_text(50) == "50 segundos"
    assert wait_text(61) == "2 minutos"
    assert wait_text(3600) == "1 hora"
    assert wait_text(86_000) == "24 horas"
