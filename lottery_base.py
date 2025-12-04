from dataclasses import dataclass, asdict
from typing import List, Set, Dict, Any
import json
import logging
import requests
import time
import random
import hashlib
import os
from datetime import date


@dataclass
class DrawResult:
    draw_date: date
    regular_numbers: Set[int]
    bonus_numbers: Set[int]
    prize_distribution: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
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


class LotteryExporter:
    def __init__(
        self, filename: str, enable_wait: bool = True, cache_dir: str = ".cache"
    ):
        self.filename = filename
        self.enable_wait = enable_wait
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    def make_request(self, url: str) -> requests.Response:
        """Make HTTP request with caching and optional human-like wait times"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if os.path.exists(cache_file):
            logging.info(f"Cache hit: {url}")
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            response = requests.Response()
            response._content = json.dumps(cached_data).encode()
            response.status_code = 200
            return response

        if self.enable_wait:
            time.sleep(random.uniform(1, 3))
        logging.info(f"Requesting: {url}")
        response = self.session.get(url)

        if response.status_code == 200:
            with open(cache_file, "w") as f:
                json.dump(response.json(), f)

        return response

    def export_results(self, latest_results: List[DrawResult]):
        existing_results = self._load_existing()
        merged_results = self._merge_results(existing_results, latest_results)
        self._save_results(merged_results)

    def _load_existing(self) -> List[DrawResult]:
        try:
            with open(self.filename, "r") as f:
                existing_data = json.load(f)

            results = []
            for item in existing_data:
                results.append(
                    DrawResult(
                        draw_date=date.fromisoformat(item["draw_date"]),
                        regular_numbers=set(item["regular_numbers"]),
                        bonus_numbers=set(item["bonus_numbers"]),
                        prize_distribution=item["prize_distribution"],
                    )
                )
            logging.info(
                f"Loaded {len(results)} existing draw results from {self.filename}"
            )
            return results
        except (FileNotFoundError, json.JSONDecodeError):
            logging.info(
                "No existing results found or file is corrupted. Creating new file."
            )
            return []

    def _merge_results(
        self, existing: List[DrawResult], latest: List[DrawResult]
    ) -> List[DrawResult]:
        existing_dates = {result.draw_date for result in existing}
        merged = list(existing)
        new_count = 0

        for result in latest:
            if result.draw_date not in existing_dates:
                merged.append(result)
                existing_dates.add(result.draw_date)
                new_count += 1

        merged_cleaned = list({result.draw_date: result for result in merged}.values())
        merged_cleaned.sort(key=lambda x: x.draw_date)
        logging.info(
            f"Merged {len(merged_cleaned)} draw results to {self.filename} ({new_count} new entries)"
        )
        return merged_cleaned

    def _save_results(self, results: List[DrawResult]):
        serializable_results = [result.to_dict() for result in results]
        with open(self.filename, "w") as f:
            json.dump(serializable_results, f, indent=2)

    def get_existing_dates(self) -> Set[date]:
        existing_results = self._load_existing()
        return {result.draw_date for result in existing_results}
