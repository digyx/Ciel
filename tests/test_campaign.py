from datetime import timedelta
from random import randint

import pytest

from campaign import Campaign


@pytest.fixture
def test_campaign(request: pytest.FixtureRequest) -> Campaign:
    metadata = [
        "Monday",
        "8:00",
        "1",
        "1",
    ]

    return Campaign.new(request.node.name, randint(0, 100000000), metadata)


def test_campaign_new(test_campaign: Campaign):
    assert test_campaign.name == "test_campaign_new"
    assert test_campaign.weekday == "Monday"


def test_save(test_campaign: Campaign):
    test_campaign.chan_id = 2
    test_campaign.off_weeks = 4
    test_campaign.save()

    t = Campaign("test_save")
    assert t.chan_id != 2
    assert t.off_weeks == 4


def test_cancel(test_campaign: Campaign):
    test_campaign.cancel()
    assert test_campaign.cancelled == 1

    t = Campaign(test_campaign.name)
    assert t.cancelled == 1


def test_reset_off_weeks(test_campaign: Campaign):
    test_campaign.on_count = 2
    test_campaign.off_count = 4
    test_campaign.save()

    test_campaign.reset_off_weeks()
    assert test_campaign.on_count == 0
    assert test_campaign.off_count == 0


def test_is_on_week(test_campaign: Campaign):
    # Toggle
    assert test_campaign.is_on_week()
    assert not test_campaign.is_on_week()

    # Double Check
    assert test_campaign.is_on_week()
    assert not test_campaign.is_on_week()

    # Test Cancelling On Week
    test_campaign.cancel()
    assert not test_campaign.is_on_week()
    assert not test_campaign.is_on_week()
    assert test_campaign.is_on_week()

    # Test Cancelling Off Week
    test_campaign.cancel()
    assert not test_campaign.is_on_week()
    assert test_campaign.is_on_week()


def test_next_sesion(test_campaign: Campaign):
    base = test_campaign.next_session()
    week_delta = timedelta(days=7)

    test_campaign.on_count = 1  # Toggle off
    test_campaign.save()
    assert (base + week_delta) == test_campaign.next_session()

    # Test Cancellation
    test_campaign.cancel()
    assert (base + 2 * week_delta) == test_campaign.next_session()
