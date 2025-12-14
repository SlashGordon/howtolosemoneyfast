from __future__ import annotations

"""Build dividend datasets for selected stock indices.

This script fetches dividend and related company data from Yahoo Finance
for a set of indices provided by `pytickersymbols`, converts the raw data
into a normalized `DividendModel`, and writes per-index JSON files under
the `dividends/` folder.
"""

import json
import logging
from pathlib import Path

import pytickersymbols as pts
import yfinance as yf
import click

from dividend_model import DividendModel


logger = logging.getLogger(__name__)


# Indices to process (values from pytickersymbols)
INDICES: list[str] = [
    pts.Statics.Indices.DE_DAX,
    pts.Statics.Indices.DE_TECDAX,
    pts.Statics.Indices.US_DOW,
    pts.Statics.Indices.US_NASDAQ,
    pts.Statics.Indices.EU_50,
]

# Friendly names -> pytickersymbols values
INDEX_NAME_MAP: dict[str, str] = {
    "DE_DAX": pts.Statics.Indices.DE_DAX,
    "DE_TECDAX": pts.Statics.Indices.DE_TECDAX,
    "US_DOW": pts.Statics.Indices.US_DOW,
    "US_NASDAQ": pts.Statics.Indices.US_NASDAQ,
    "EU_50": pts.Statics.Indices.EU_50,
}

# Indices where the primary symbol is used directly (US-specific)
US_INDICES: set[str] = {
    pts.Statics.Indices.US_DOW,
    pts.Statics.Indices.US_NASDAQ,
    pts.Statics.Indices.US_SP_500,
    pts.Statics.Indices.US_SP_100,
    pts.Statics.Indices.US_SP_600,
}


def resolve_symbol(symbol: dict, index: str) -> str | None:
    """Resolve the Yahoo Finance ticker symbol for a stock entry.

    For US indices, use the top-level `symbol`. Otherwise, prefer the first
    Yahoo-specific entry in `symbols[0]['yahoo']` when available, falling back
    to the top-level `symbol`.

    Returns `None` if no symbol could be determined.
    """

    if index in US_INDICES:
        return symbol.get("symbol")

    syms = symbol.get("symbols") or []
    first = syms[0] if syms else None
    yahoo = first.get("yahoo") if isinstance(first, dict) else None
    return yahoo or symbol.get("symbol")


def build_index_dividends(
    index: str, pts_client: pts.PyTickerSymbols, out_file: Path
) -> int:
    """Build dividend JSON for a single index and write it to `out_file`.

    Returns the number of successfully processed symbols.
    """

    profiles: dict[str, dict] = {}
    symbols = pts_client.get_stocks_by_index(index)

    for symbol in symbols:
        sym = resolve_symbol(symbol, index)
        if not sym:
            logger.warning("Skipping record without yahoo symbol: %s", symbol)
            continue
        try:
            ticker = yf.Ticker(sym)
            profile = DividendModel.from_yfinance(
                index, symbol, ticker.info, ticker.calendar, ticker.dividends
            )
            profiles[sym] = profile.to_dict()
            logger.info("Processed %s", sym)
        except Exception:
            # Include traceback to aid debugging while continuing processing
            logger.exception("Error processing %s", sym)

    # Write output for the index
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4)

    return len(profiles)


def _resolve_indices_from_option(index_opt: str | None) -> list[str]:
    if index_opt:
        names = [n.strip() for n in index_opt.split(",") if n.strip()]
        unknown = [n for n in names if n not in INDEX_NAME_MAP]
        if unknown:
            raise click.BadParameter(
                f"Unknown index names: {', '.join(unknown)}",
                param=index_opt,
                param_hint="--index",
            )
        return [INDEX_NAME_MAP[n] for n in names]
    return INDICES


@click.command()
@click.option(
    "index",
    "--index",
    "-i",
    help=(
        "Optional index name to process (DE_DAX, DE_TECDAX, US_DOW, US_NASDAQ, EU_50). "
        "Pass multiple as comma-separated values."
    ),
)
def main(index: str | None) -> None:
    """Entry point for building dividend datasets for configured indices."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logger.info("Starting dividend dataset build")

    pts_client = pts.PyTickerSymbols()
    out_path = Path(__file__).parent / "dividends"
    out_path.mkdir(parents=True, exist_ok=True)

    selected_indices = _resolve_indices_from_option(index)

    for index in selected_indices:
        logger.info("Processing index: %s", index)
        out_file = out_path / f"{index}_dividends.json"
        if out_file.exists():
            logger.info("Output exists, skipping index: %s", out_file)
            continue

        count = build_index_dividends(index, pts_client, out_file)
        logger.info("Wrote %d symbols to %s", count, out_file)


if __name__ == "__main__":
    main()
