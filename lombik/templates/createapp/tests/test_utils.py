from datetime import datetime, timezone

from application import utils


def test_utc_now_is_timezone_aware():
    assert utils.utc_now().tzinfo is not None


def test_ensure_tz_aware():
    naive = datetime(2024, 1, 1, 12, 0, 0)
    aware = utils.ensure_tz_aware(naive)
    assert aware.tzinfo is not None
    assert aware.replace(tzinfo=None) == naive


def test_ensure_tz_aware_passes_aware_through():
    aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert utils.ensure_tz_aware(aware) is aware


def test_month_helpers_actually_shift_months():
    now = utils.utc_now()
    # relativedelta(months=1) must advance a full month, not set month=1.
    assert (utils.utc_next_month() - now).days >= 28
    assert (now - utils.utc_last_month()).days >= 28


def test_to_utc_midnight():
    result = utils.to_utc_midnight("2024-06-15")
    assert result.hour == 0
    assert result.minute == 0
    assert result.tzinfo is not None


def test_generate_token_length():
    assert len(utils.generate_token()) == 43  # 32 random bytes base64url-encoded
    assert len(utils.generate_token(16)) == 22


def test_generate_uuid_unique():
    assert utils.generate_uuid() != utils.generate_uuid()
