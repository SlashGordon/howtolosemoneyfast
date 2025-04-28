
![Money Lost](https://img.shields.io/badge/Money%20Lost-€1234-red)
# 🎯 howtolosemoneyfast

**Welcome to _howtolosemoneyfast_** — the most accurate lottery simulator for tracking exactly **how much money you *could have* lost** playing EuroJackpot!  

This project fetches real EuroJackpot results, checks them against your saved lottery numbers, and keeps track of:  
- **How many times you almost got rich** (but didn't)  
- **How many euros you bravely donated** to the lottery gods  

---

## 💸 How It Works

- Loads your "lucky" numbers from a JSON file
- Checks historical EuroJackpot draws (Tuesdays and Fridays, because of course)
- Counts matches between your numbers and real draws
- Calculates **total money lost** (assuming each ticket costs €18.40)
- Logs the heartbreaking results with a smile :)

---

## 🚀 Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the magic
python howtolosemoneyfast.py --lookback-days 365 --ticket-file tickets.json --ticket-price 18.40
```

---

## 📦 Requirements

- Python 3.9+
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
