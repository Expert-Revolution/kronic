import os
import sys
import pytest

from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import config

config.TEST = True

import kron
import objects


@pytest.fixture
def cronjob_list():
    return objects.create_cronjob_list()


# Define a fixture to create a timestamp in the past
@pytest.fixture
def past_timestamp():
    return (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()


# Define a fixture to create a timestamp in the future
@pytest.fixture
def future_timestamp():
    return (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()


def test_get_human_readable_time_difference_past(past_timestamp):
    result = kron._get_time_since(past_timestamp)
    assert "d" in result  # Check if the result contains 'd' for days


def test_get_human_readable_time_difference_future(future_timestamp):
    result = kron._get_time_since(future_timestamp)
    assert result == "In the future"  # Check if the result is "In the future"


def test_get_human_readable_time_difference_now():
    result = kron._get_time_since(datetime.now(timezone.utc).isoformat())
    assert result == "0s"  # Check if the result is "0s" for the current time


def test_get_human_readable_time_difference_invalid_format():
    with pytest.raises(ValueError):
        kron._get_time_since("invalid_timestamp")


def test_filter_dict_fields():
    cron_dict_list = [
        {"metadata": {"name": "first", "namespace": "test"}},
        {"metadata": {"name": "second", "namespace": "test"}},
    ]

    assert kron._filter_dict_fields(cron_dict_list) == [
        {"name": "first"},
        {"name": "second"},
    ]

    assert kron._filter_dict_fields(cron_dict_list) == [
        {"name": "first"},
        {"name": "second"},
    ]


def test_clean_api_object(cronjob_list):
    for job in cronjob_list.items:
        assert job.metadata.name == kron._clean_api_object(job)["metadata"]["name"]
        assert (
            job.metadata.namespace
            == kron._clean_api_object(job)["metadata"]["namespace"]
        )
        assert "managedFields" not in kron._clean_api_object(job)["metadata"]


def test_has_label(cronjob_list):
    cronjob = kron._clean_api_object(cronjob_list.items[0])
    assert kron._has_label(cronjob, "app", "test") == True
    assert kron._has_label(cronjob, "app", "badlabel") == False


def test_namespace_filter_denies_access(namespace: str = "test"):
    config.ALLOW_NAMESPACES = "qa"

    @kron.namespace_filter
    def to_be_decorated(namespace, **kwargs):
        # Filter will override this return if behaving properly
        return True

    result = to_be_decorated(namespace)
    assert result is False


def test_namespace_filter_allows_access(namespace: str = "test"):
    config.ALLOW_NAMESPACES = "qa,test"

    @kron.namespace_filter
    def to_be_decorated(namespace, **kwargs):
        # Filter will keep return status if behaving properly
        return True

    result = to_be_decorated(namespace)
    assert result is True


def test_interpret_cron_schedule_every_minute():
    result = kron._interpret_cron_schedule("* * * * *")
    assert result == "Every minute"


def test_interpret_cron_schedule_every_10_minutes():
    result = kron._interpret_cron_schedule("*/10 * * * *")
    assert result == "Every 10 minutes"


def test_interpret_cron_schedule_every_hour():
    result = kron._interpret_cron_schedule("0 */1 * * *")
    assert result == "Every hour"


def test_interpret_cron_schedule_every_2_hours():
    result = kron._interpret_cron_schedule("0 */2 * * *")
    assert result == "Every 2 hours"


def test_interpret_cron_schedule_daily_midnight():
    result = kron._interpret_cron_schedule("0 0 * * *")
    assert result == "Daily at midnight"


def test_interpret_cron_schedule_daily_specific_time():
    result = kron._interpret_cron_schedule("30 14 * * *")
    assert result == "Daily at 14:30"


def test_interpret_cron_schedule_weekly():
    result = kron._interpret_cron_schedule("0 0 * * 0")
    assert result == "Weekly on Sunday at midnight"


def test_interpret_cron_schedule_weekly_specific_time():
    result = kron._interpret_cron_schedule("15 9 * * 1")
    assert result == "Weekly on Monday at 09:15"


def test_interpret_cron_schedule_monthly():
    result = kron._interpret_cron_schedule("0 0 1 * *")
    assert result == "Monthly on the 1st at midnight"


def test_interpret_cron_schedule_monthly_specific():
    result = kron._interpret_cron_schedule("30 12 15 * *")
    assert result == "Monthly on the 15 at 12:30"


def test_interpret_cron_schedule_invalid_format():
    result = kron._interpret_cron_schedule("invalid")
    assert result == "Invalid cron format"


def test_interpret_cron_schedule_empty():
    result = kron._interpret_cron_schedule("")
    assert result == "Invalid schedule"


def test_interpret_cron_schedule_none():
    result = kron._interpret_cron_schedule(None)
    assert result == "Invalid schedule"


def test_interpret_cron_schedule_complex():
    result = kron._interpret_cron_schedule("15,45 */6 * * 1-5")
    assert result == "Custom schedule: 15,45 */6 * * 1-5"

def test_clean_api_object_preserves_timezone():
    """Test that timezone field is properly preserved when cleaning API objects"""
    from kubernetes import client
    from tests.objects import create_job

    # Create a CronJob with timezone
    job_template = create_job()
    cronjob_spec = client.V1CronJobSpec(
        schedule="0 9 * * *", job_template=job_template, time_zone="America/New_York"
    )
    cronjob = client.V1CronJob(
        api_version="batch/v1",
        kind="CronJob",
        metadata=client.V1ObjectMeta(name="test-tz", namespace="test"),
        spec=cronjob_spec,
    )

    # Clean the API object
    cleaned = kron._clean_api_object(cronjob)

    # Verify timezone is preserved and correctly named
    assert "timeZone" in cleaned["spec"]
    assert cleaned["spec"]["timeZone"] == "America/New_York"


def test_clean_api_object_handles_missing_timezone():
    """Test that missing timezone field doesn't cause issues"""
    from kubernetes import client
    from tests.objects import create_job

    # Create a CronJob without timezone (default behavior)
    job_template = create_job()
    cronjob_spec = client.V1CronJobSpec(
        schedule="0 9 * * *",
        job_template=job_template,
        # No time_zone specified
    )
    cronjob = client.V1CronJob(
        api_version="batch/v1",
        kind="CronJob",
        metadata=client.V1ObjectMeta(name="test-no-tz", namespace="test"),
        spec=cronjob_spec,
    )

    # Clean the API object
    cleaned = kron._clean_api_object(cronjob)

    # Verify timezone field is either None or not present
    timezone_value = cleaned["spec"].get("timeZone")
    assert timezone_value is None or "timeZone" not in cleaned["spec"]

