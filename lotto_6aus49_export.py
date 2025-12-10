import requests
import logging
from lottery_base import DrawResult, LotteryExporter
from datetime import date, datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_available_years(exporter: LotteryExporter):
    """Get available years from LOTTO API"""
    response = exporter.make_request(
        "https://www.lotto.de/api/stats/entities.lotto/history/1"
    )
    return response.json()


def get_year_timestamps(exporter: LotteryExporter, year: int):
    """Get all draw timestamps for a specific year"""
    dec_31_timestamp = int(datetime(year, 12, 31).timestamp() * 1000)
    current_year = datetime.now().year
    skip_cache = year == current_year

    response = exporter.make_request(
        f"https://www.lotto.de/api/stats/entities.lotto/history/{dec_31_timestamp}",
        skip_cache=skip_cache,
    )
    data = response.json()
    if not data or "days" not in data:
        return []

    timestamps = []
    for item in data["days"]:
        date_str = item["date"]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        timestamp = int(dt.timestamp() * 1000)
        timestamps.append(timestamp)
    return timestamps


def generate_draw_timestamps(exporter: LotteryExporter):
    """Generate draw timestamps using LOTTO API"""
    years_data = get_available_years(exporter)
    for year_info in years_data["years"]:
        year = year_info["year"]
        timestamps = get_year_timestamps(exporter, year)
        for timestamp in timestamps:
            yield timestamp


def fetch_lotto_results(exporter: LotteryExporter, timestamp: int):
    url = f"https://www.lotto.de/api/stats/entities.lotto/draws/{timestamp}"
    try:
        response = exporter.make_request(url)
        response_data = response.json()

        if not response_data:
            return None

        data = response_data[0] if isinstance(response_data, list) else response_data

        # Extract numbers from drawNumbersCollection
        numbers = [item["drawNumber"] for item in data.get("drawNumbersCollection", [])]

        # Build prize distribution from oddsCollection
        prizes = {}
        for odds in data.get("oddsCollection", []):
            class_name = odds.get("winningClassDescription", {}).get(
                "winningClassShortName", ""
            )
            if class_name:
                prizes[class_name] = odds.get("odds", 0)
        super_number = (
            data.get("superNumber") if data.get("superNumber") is not None else -1
        )
        extra_number = (
            data.get("extraNumber") if data.get("extraNumber") is not None else -1
        )

        return DrawResult(
            draw_date=date.fromtimestamp(data["drawDate"] / 1000),
            regular_numbers=set(numbers),
            bonus_numbers=set([super_number, extra_number]),
            prize_distribution=prizes,
        )
    except Exception as e:
        logging.error(f"Failed to fetch data for timestamp {timestamp}: {e}")
        return None


if __name__ == "__main__":
    exporter = LotteryExporter("lotto_6aus49_results.json", enable_wait=False)
    existing_dates = exporter.get_existing_dates()

    if existing_dates:
        logging.info(f"Found {len(existing_dates)} existing dates")

    all_timestamps = list(generate_draw_timestamps(exporter))

    # Filter out existing dates and invalid timestamps
    filtered_timestamps = []
    filtered_count = 0
    for timestamp in all_timestamps:
        try:
            draw_date = date.fromtimestamp(timestamp / 1000)
            # Skip if date is unreasonable (before 1950 or after 2100)
            if draw_date.year < 1950 or draw_date.year > 2100:
                logging.debug(f"Filtered out timestamp {timestamp} (date: {draw_date})")
                filtered_count += 1
                continue
            # Skip if not Wednesday (2) or Saturday (5)
            if draw_date.weekday() not in [2, 5, 6]:
                logging.debug(
                    f"Filtered out timestamp {timestamp} (date: {draw_date}, not Wed/Sat)"
                )
                filtered_count += 1
                continue
            if draw_date not in existing_dates:
                filtered_timestamps.append(timestamp)
        except (ValueError, OSError) as e:
            logging.debug(f"Filtered out invalid timestamp {timestamp}: {e}")
            filtered_count += 1
            continue

    if filtered_count > 0:
        logging.info(f"Filtered out {filtered_count} invalid/out-of-range timestamps")

    logging.info(
        f"Total timestamps: {len(all_timestamps)}, New: {len(filtered_timestamps)}"
    )
    logging.info(f"Will fire {len(filtered_timestamps)} API queries")

    results = []
    for i, timestamp in enumerate(filtered_timestamps, 1):
        result = fetch_lotto_results(exporter, timestamp)
        if result:
            logging.info(
                f"Query {i}/{len(filtered_timestamps)}: {timestamp} -> {result.draw_date}"
            )
            results.append(result)

            if len(results) >= 50:
                exporter.export_results(results)
                results = []

    if results:
        exporter.export_results(results)

    logging.info(f"Successfully processed {len(results)} new draws")
