# load data
from dataclasses import dataclass, asdict
from typing import List, Set, Dict, Any, Optional
import json
from datetime import date

from howtolosemoneyfast import (
    generate_draw_dates,
    get_euro_jackpot_results,
    parse_draw_data,
)


@dataclass
class DrawResult:
    draw_date: date
    regular_numbers: Set[int]
    bonus_numbers: Set[int]
    prize_distribution: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with sets converted to sorted lists."""
        result = asdict(self)
        result["draw_date"] = str(result["draw_date"])
        result["regular_numbers"] = sorted(list(result["regular_numbers"]))
        result["bonus_numbers"] = sorted(list(result["bonus_numbers"]))
        result["prize_distribution"] = {
            k: v
            for k, v in sorted(
                result["prize_distribution"].items(), key=lambda item: item[0]
            )
        }
        return result


def fetch_draw_results(lookback_days: int = 3000) -> List[DrawResult]:
    """Fetch EuroJackpot draw results for the specified lookback period."""
    dates = list(generate_draw_dates(lookback_days=lookback_days))
    results = []

    for draw_date in dates:
        try:
            raw_result = get_euro_jackpot_results(draw_date)
            if raw_result is None:
                continue

            regular_numbers, bonus_numbers, prize_data = parse_draw_data(raw_result)
            results.append(
                DrawResult(
                    draw_date=draw_date,
                    regular_numbers=regular_numbers,
                    bonus_numbers=bonus_numbers,
                    prize_distribution=prize_data,
                )
            )
        except ValueError:
            continue

    return results


# Main execution
if __name__ == "__main__":
    # Fetch results
    draw_results = fetch_draw_results()

    # Convert to serializable format
    serializable_results = [result.to_dict() for result in draw_results]

    # Save to JSON file
    with open("results.json", "w") as f:
        json.dump(serializable_results, f, indent=2)

    # Print summary
    print(f"Saved {len(draw_results)} EuroJackpot draw results to results.json")
