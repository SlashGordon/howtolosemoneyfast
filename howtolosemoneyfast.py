import logging
import requests
from datetime import datetime, timedelta
import click
import json
import os
from lottery_base import LotteryExporter

# Setup logger
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://www.eurojackpot.de/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
    "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

CACHE_DIR = "cache"


def ensure_cache_dir():
    """Ensure the cache directory exists."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_filepath(date: str) -> str:
    """Get the filepath for the cache file of a given date."""
    return os.path.join(CACHE_DIR, f"{date}.json")


def get_euro_jackpot_results(exporter: LotteryExporter, date: str) -> dict:
    """Fetches Eurojackpot results for a given date, using cache if available."""
    cache_filepath = get_cache_filepath(date)

    # Check if the result is already cached
    if os.path.exists(cache_filepath):
        logger.debug(f"Loading cached results for {date}...")
        with open(cache_filepath, "r") as f:
            return json.load(f)

    # Fetch the results from the API
    url = (
        f"https://www.eurojackpot.de/wlinfo/WL_InfoService"
        f"?client=jsn&gruppe=ZahlenUndQuoten&ewGewsum=ja&historie=ja"
        f"&spielart=EJ&adg=ja&lang=de&datum={date}"
    )
    response = exporter.make_request(url)
    response.raise_for_status()
    data = response.json()

    # Save the results to the cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_filepath, "w") as f:
        json.dump(data, f)

    return data


def generate_draw_dates(lookback_days: int = 365):
    """Yields draw dates (Tuesdays and Fridays) for the given lookback period."""
    today = datetime.today()
    start_date = today - timedelta(days=lookback_days)

    current_date = start_date
    while current_date <= today:
        if current_date.weekday() in (1, 4):  # Tuesday or Friday
            yield current_date.strftime("%Y-%m-%d")
        current_date += timedelta(days=1)


def evaluate_ticket(ticket: list, drawn_main: set, drawn_euro: set) -> tuple:
    """Compares a ticket to drawn numbers and returns the match count."""
    main_numbers = set(ticket[:5])
    euro_numbers = set(ticket[5:])
    matched_main = len(drawn_main & main_numbers)
    matched_euro = len(drawn_euro & euro_numbers)
    return matched_main, matched_euro


def load_tickets(filepath: str) -> list:
    """Loads tickets from a JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Ticket file not found: {filepath}")
        raise FileNotFoundError(f"Ticket file not found: {filepath}")

    with open(filepath, "r") as f:
        tickets = json.load(f)

    if not isinstance(tickets, list):
        raise ValueError("Ticket file must contain a list of tickets.")

    logger.info(f"Loaded {len(tickets)} tickets from {filepath}")
    return tickets


def parse_draw_data(data: dict) -> tuple:
    """Parses the draw data to extract main and Euro numbers."""
    if "zahlen" not in data or "auswertung" not in data:
        raise ValueError(f"No valid data. Skipping.")
    draws = data["zahlen"]["hauptlotterie"]["ziehungen"]

    drawn_main_numbers = set(map(lambda x: int(x), draws[0].get("zahlen", [])))
    drawn_euro_numbers = set(map(lambda x: int(x), draws[1].get("zahlen", [])))

    stats = (
        data.get("auswertung", {})
        .get("quoten", {})
        .get("hauptlotterie", {})
        .get("ziehungen", [{}])[0]
        .get("gewinnklassen", {})
    )
    stats_dict = {item["kurzbeschreibung"]: item["quote"] for item in stats}
    return drawn_main_numbers, drawn_euro_numbers, stats_dict


@click.command()
@click.option(
    "--lookback-days",
    default=3650,
    show_default=True,
    help="How many days to look back.",
)
@click.option(
    "--ticket-price", default=18.40, show_default=True, help="Price per ticket in Euro."
)
@click.option(
    "--ticket-file",
    default="tickets.json",
    show_default=True,
    help="Path to your tickets JSON file.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose debug output.")
def main(lookback_days, ticket_price, ticket_file, verbose):
    """Eurojackpot Checker: See how much you lost (or won) playing lotto!"""
    if verbose:
        logger.setLevel(logging.DEBUG)

    ensure_cache_dir()

    try:
        my_tickets = load_tickets(ticket_file)
    except Exception as e:
        logger.error(str(e))
        return

    exporter = LotteryExporter("eurojackpot_cache.json")
    draw_dates = list(generate_draw_dates(lookback_days=lookback_days))
    logger.info(f"Will fire {len(draw_dates)} API queries")

    total_spent = 0
    total_won = 0

    logger.info("Starting Eurojackpot analysis...")

    for i, date in enumerate(draw_dates, 1):
        logger.info(f"Query {i}/{len(draw_dates)}: {date}")
        try:
            data = get_euro_jackpot_results(exporter, date)
        except requests.HTTPError as e:
            logger.warning(f"Failed to fetch data for {date}: {e}")
            continue

        try:
            drawn_main_numbers, drawn_euro_numbers, stats = parse_draw_data(data)
        except ValueError as e:
            logger.warning(str(e))
            continue
        total_spent += ticket_price
        for ticket in my_tickets:
            matched_main, matched_euro = evaluate_ticket(
                ticket, drawn_main_numbers, drawn_euro_numbers
            )
            match_key = f"{matched_main} + {matched_euro}"
            win_info = stats.get(match_key)
            if win_info:
                total_won += win_info
                logger.info(
                    f"💰 {date} - Ticket {ticket} matched {match_key} and WON {win_info:.2f}€"
                )
            else:
                logger.debug(
                    f"💸 {date} - Ticket {ticket} matched {match_key} and WON nothing"
                )

    total_loss = total_spent - total_won

    logger.info("📊 Final Summary:")
    logger.info(f"Total spent on tickets: {total_spent:.2f}€")
    logger.info(f"Total won: {total_won:.2f}€")
    logger.info(f"Net loss: {total_loss:.2f}€")


if __name__ == "__main__":
    main()
