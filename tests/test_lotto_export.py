import pytest
import json
from unittest.mock import Mock, patch
from datetime import date, datetime
from lottery_base import DrawResult, LotteryExporter
from lotto_6aus49_export import (
    get_available_years,
    get_year_timestamps,
    fetch_lotto_results,
)


@pytest.fixture
def mock_exporter():
    """Cool exporter that never sleeps and caches everything"""
    return LotteryExporter("test.json", enable_wait=False, cache_dir=".test_cache")


@pytest.fixture
def jackpot_response():
    """The response that makes dreams come true (or crushes them)"""
    return {
        "drawDate": 1640995200000,  # 2022-01-01
        "drawNumbersCollection": [
            {"drawNumber": 7},
            {"drawNumber": 14},
            {"drawNumber": 21},
            {"drawNumber": 28},
            {"drawNumber": 35},
            {"drawNumber": 42},
        ],
        "superNumber": 9,
        "oddsCollection": [
            {
                "winningClassDescription": {"winningClassShortName": "I"},
                "odds": 50000000,
            },
            {
                "winningClassDescription": {"winningClassShortName": "II"},
                "odds": 5000000,
            },
        ],
    }


@pytest.fixture
def years_response():
    """Time machine data - all the years you could have been rich"""
    return {"years": [{"year": 2022}, {"year": 2023}, {"year": 2024}]}


@pytest.fixture
def timestamps_response():
    """All the days you didn't win"""
    return {
        "days": [{"date": "2022-01-01"}, {"date": "2022-01-04"}, {"date": "2022-01-08"}]
    }


class MockResponse:
    """The response that pretends to be real"""

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def test_get_available_years_returns_lottery_gold(mock_exporter, years_response):
    """Test that we can fetch the years of broken dreams"""
    mock_exporter.make_request = Mock(return_value=MockResponse(years_response))

    result = get_available_years(mock_exporter)

    assert result == years_response
    mock_exporter.make_request.assert_called_once_with(
        "https://www.lotto.de/api/stats/entities.lotto/history/1"
    )


def test_get_year_timestamps_extracts_hope_dates(mock_exporter, timestamps_response):
    """Test extracting all the dates you could have won (but didn't)"""
    mock_exporter.make_request = Mock(return_value=MockResponse(timestamps_response))

    timestamps = get_year_timestamps(mock_exporter, 2022)

    assert len(timestamps) == 3
    assert all(isinstance(ts, int) for ts in timestamps)


def test_fetch_lotto_results_creates_dream_crusher(mock_exporter, jackpot_response):
    """Test converting API response into a proper dream-crushing result"""
    mock_exporter.make_request = Mock(return_value=MockResponse(jackpot_response))

    result = fetch_lotto_results(mock_exporter, 1640995200000)

    assert isinstance(result, DrawResult)
    assert result.draw_date == date(2022, 1, 1)
    assert result.regular_numbers == {7, 14, 21, 28, 35, 42}
    assert result.bonus_numbers == {9}
    assert result.prize_distribution["I"] == 50000000


def test_fetch_lotto_results_handles_empty_dreams(mock_exporter):
    """Test handling when the lottery gods return nothing"""
    mock_exporter.make_request = Mock(return_value=MockResponse(None))

    result = fetch_lotto_results(mock_exporter, 123456789)

    assert result is None


def test_fetch_lotto_results_survives_api_apocalypse(mock_exporter):
    """Test graceful failure when the API explodes"""
    mock_exporter.make_request = Mock(side_effect=Exception("API is having a bad day"))

    result = fetch_lotto_results(mock_exporter, 123456789)

    assert result is None
