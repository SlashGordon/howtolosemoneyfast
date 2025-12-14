
![Money Lost](https://img.shields.io/badge/Money%20Lost-€1234-red)
# 🎯 howtolosemoneyfast

**Welcome to _howtolosemoneyfast_** — the most accurate lottery simulator for tracking exactly **how much money you *could have* lost** playing EuroJackpot!  

This project fetches real EuroJackpot results, checks them against your saved lottery numbers, and keeps track of:  
- **How many times you almost got rich** (but didn't)  
- **How many euros you bravely donated** to the lottery gods  

---

## 💸 How It Works



## 🚀 Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the magic
python howtolosemoneyfast.py --lookback-days 365 --ticket-file tickets.json --ticket-price 18.40
```

### Dividend dataset builder

This repo now includes a simple data builder to aggregate dividend-related data from pre-dumped Yahoo Finance JSON files for static site generation elsewhere.

Inputs expected under `dividends/` per symbol:
- `{SYMBOL}.json` (ticker info)
- `{SYMBOL}_calendar.json` (calendar snapshot)
- `{SYMBOL}_dividends.json` (historical cash dividends)

Run the builder to generate a flat dataset for your site:

```bash
python build_dividend_data.py
```

Output: `data/dividends_dataset.json` — a list of per-symbol rows including key fields and derived metrics such as TTM dividends, inferred payout frequency, forward annual dividend, and forward yield.

---

## 🛠 CI/CD (Monthly Dividends Build)

A GitHub Actions workflow refreshes dividend datasets monthly:

- Schedule: Runs at 03:00 on the 1st day of each month
- File: `.github/workflows/monthly-dividends.yml`
- Steps: checkout, set up Python, install requirements, run `build_dividend_data.py` (fallback to `dividends.py`), then upload JSONs from `dividends/` as artifacts
- Manual Trigger: Use "Run workflow" in GitHub; you may optionally pass an index name

### Local dividend build

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-div.txt
```

Run all indices via the simple builder:

```bash
python dividends.py
```

Or using the dedicated aggregator:

```bash
python build_dividend_data.py
```

Outputs are written under `dividends/` (one JSON file per index) and the aggregated dataset under `data/dividends_dataset.json`.

- `requests`
- `click`

Install them easily:

```bash
pip install requests click
```

---

## 🎟 Example `my_numbers.json`

```json
[
    [3, 12, 26, 28, 47, 2, 11],
    [8, 11, 18, 19, 47, 4, 6],
    [1, 2, 29, 40, 49, 6, 7],
    [14, 18, 34, 36, 42, 4, 6]
]
```

Each ticket has **5 main numbers** and **2 Euro numbers**. 
The first 5 numbers are the main ones, and the last 2 are the Euro numbers.
You can have as many tickets as you want, just make sure to keep the format.



## 🤡 Why?

Because hope is expensive, but at least now you can **track it properly**.
