from lottery_base import DrawResult, LotteryExporter
from typing import List
from datetime import date
import logging
from howtolosemoneyfast import (
    generate_draw_dates,
    get_euro_jackpot_results,
    parse_draw_data,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def fetch_draw_results(
    exporter: LotteryExporter, lookback_days: int = 3000
) -> List[DrawResult]:
    """Fetch EuroJackpot draw results for the specified lookback period."""
    existing_dates = exporter.get_existing_dates()
    all_dates = list(generate_draw_dates(lookback_days=lookback_days))

    # Filter out existing dates
    filtered_dates = []
    for date_str in all_dates:
        draw_date = date.fromisoformat(date_str)
        if draw_date not in existing_dates:
            filtered_dates.append(date_str)

    logging.info(f"Total dates: {len(all_dates)}, New: {len(filtered_dates)}")
    logging.info(f"Will fire {len(filtered_dates)} API queries")
    results = []

    for i, date_str in enumerate(filtered_dates, 1):
        logging.info(f"Query {i}/{len(filtered_dates)}: {date_str}")
        try:
            raw_result = get_euro_jackpot_results(exporter, date_str)
            if raw_result is None:
                continue

            regular_numbers, bonus_numbers, prize_data = parse_draw_data(raw_result)
            results.append(
                DrawResult(
                    draw_date=date.fromisoformat(date_str),
                    regular_numbers=regular_numbers,
                    bonus_numbers=bonus_numbers,
                    prize_distribution=prize_data,
                )
            )
        except ValueError:
            continue

    return results


if __name__ == "__main__":
    exporter = LotteryExporter("eurojackpot_results.json")
    existing_dates = exporter.get_existing_dates()

    if existing_dates:
        logging.info(f"Found {len(existing_dates)} existing dates")

    latest_results = fetch_draw_results(exporter)
    exporter.export_results(latest_results)
