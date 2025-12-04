import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from lottery_base import DrawResult, LotteryExporter
from howtolosemoneyfast import (
    get_euro_jackpot_results,
    parse_draw_data,
    evaluate_ticket,
    generate_draw_dates,
)
from eurojackpot_export import fetch_draw_results


@pytest.fixture
def mock_exporter():
    """European dream crusher that never sleeps"""
    return LotteryExporter("test_euro.json", enable_wait=False, cache_dir=".test_cache")


@pytest.fixture
def eurojackpot_response():
    """The EuroJackpot response that crushes European dreams"""
    return {
        "zahlen": {
            "hauptlotterie": {
                "ziehungen": [
                    {"zahlen": ["7", "14", "21", "28", "35"]},
                    {"zahlen": ["3", "9"]},
                ]
            }
        },
        "auswertung": {
            "quoten": {
                "hauptlotterie": {
                    "ziehungen": [
                        {
                            "gewinnklassen": [
                                {"kurzbeschreibung": "5 + 2", "quote": 90000000},
                                {"kurzbeschreibung": "5 + 1", "quote": 500000},
                                {"kurzbeschreibung": "2 + 1", "quote": 8.50},
                            ]
                        }
                    ]
                }
            }
        },
    }


@pytest.fixture
def dream_ticket():
    """The ticket that will never win but keeps hope alive"""
    return [7, 14, 21, 28, 35, 3, 9]


@pytest.fixture
def losing_ticket():
    """The ticket that represents reality"""
    return [1, 2, 3, 4, 5, 1, 2]


class MockResponse:
    """European response simulator"""

    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception("API meltdown")


def test_get_euro_jackpot_results_fetches_disappointment(
    mock_exporter, eurojackpot_response
):
    """Test fetching EuroJackpot results that will crush your soul"""
    mock_exporter.make_request = Mock(return_value=MockResponse(eurojackpot_response))

    result = get_euro_jackpot_results(mock_exporter, "2022-01-01")

    assert result == eurojackpot_response
    assert "zahlen" in result
    assert "auswertung" in result


def test_parse_draw_data_extracts_winning_numbers(eurojackpot_response):
    """Test parsing the numbers that you definitely didn't pick"""
    main_numbers, euro_numbers, prizes = parse_draw_data(eurojackpot_response)

    assert main_numbers == {7, 14, 21, 28, 35}
    assert euro_numbers == {3, 9}
    assert prizes["5 + 2"] == 90000000
    assert prizes["2 + 1"] == 8.50


def test_parse_draw_data_handles_broken_dreams():
    """Test handling malformed data when the lottery API has issues"""
    broken_data = {"broken": "dreams"}

    with pytest.raises(ValueError):
        parse_draw_data(broken_data)


def test_evaluate_ticket_perfect_match_jackpot(dream_ticket):
    """Test the one-in-a-million chance of actually winning"""
    drawn_main = {7, 14, 21, 28, 35}
    drawn_euro = {3, 9}

    main_matches, euro_matches = evaluate_ticket(dream_ticket, drawn_main, drawn_euro)

    assert main_matches == 5
    assert euro_matches == 2


def test_evaluate_ticket_reality_check(losing_ticket):
    """Test the harsh reality of lottery mathematics"""
    drawn_main = {7, 14, 21, 28, 35}
    drawn_euro = {3, 9}

    main_matches, euro_matches = evaluate_ticket(losing_ticket, drawn_main, drawn_euro)

    assert main_matches == 0
    assert euro_matches == 0


def test_generate_draw_dates_creates_hope_schedule():
    """Test generating all the dates you could lose money"""
    dates = list(generate_draw_dates(lookback_days=14))

    # Should only include Tuesdays (1) and Fridays (4)
    for date_str in dates:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        assert date_obj.weekday() in [1, 4]


def test_fetch_draw_results_processes_euro_dreams(mock_exporter, eurojackpot_response):
    """Test fetching and processing EuroJackpot results into dream-crushing format"""
    with patch("eurojackpot_export.generate_draw_dates") as mock_dates, patch(
        "eurojackpot_export.get_euro_jackpot_results"
    ) as mock_get_results, patch("eurojackpot_export.parse_draw_data") as mock_parse:
        mock_dates.return_value = ["2022-01-01"]
        mock_get_results.return_value = eurojackpot_response
        mock_parse.return_value = ({7, 14, 21, 28, 35}, {3, 9}, {"5 + 2": 90000000})

        results = fetch_draw_results(mock_exporter, lookback_days=1)

        assert len(results) == 1
        assert isinstance(results[0], DrawResult)
        assert results[0].regular_numbers == {7, 14, 21, 28, 35}
        assert results[0].bonus_numbers == {3, 9}
