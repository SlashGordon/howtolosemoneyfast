from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class DividendEx:
    exdividend_date: datetime
    earnings_date: list[datetime]
    earnings_high: float
    earnings_low: float
    earnings_average: float
    revenue_high: float
    revenue_low: float
    revenue_average: float

    @classmethod
    def from_dict(cls, data: dict) -> DividendEx:
        return cls(
            exdividend_date=data.get("Ex-Dividend Date"),
            earnings_date=data.get("Earnings Date", []),
            earnings_high=data.get("Earnings High", 0.0),
            earnings_low=data.get("Earnings Low", 0.0),
            earnings_average=data.get("Earnings Average", 0.0),
            revenue_high=data.get("Revenue High", 0.0),
            revenue_low=data.get("Revenue Low", 0.0),
            revenue_average=data.get("Revenue Average", 0.0),
        )

    def to_dict(self) -> dict:
        return {
            "exdividend_date": self.exdividend_date.isoformat()
            if self.exdividend_date
            else None,
            "earnings_date": [dt.isoformat() for dt in self.earnings_date],
            "earnings_high": self.earnings_high,
            "earnings_low": self.earnings_low,
            "earnings_average": self.earnings_average,
            "revenue_high": self.revenue_high,
            "revenue_low": self.revenue_low,
            "revenue_average": self.revenue_average,
        }


@dataclass
class DividenItem:
    amount: float
    date: datetime


@dataclass
class DividendModel:
    symbol: str
    name: str
    indices: list[str]
    sector: str
    industry: str
    country: str
    current_price: float | None
    currency: str | None
    dividend_count: int
    history: list[DividenItem]
    expected_ex_dividend_dates: DividendEx

    @classmethod
    def from_yfinance(
        cls, index, symbol_info, info, calendar, dividends
    ) -> DividendModel:
        history = [DividenItem(amount=amt, date=dt) for dt, amt in dividends.items()]
        expected_dates = DividendEx.from_dict(calendar)
        price = info.get("regularMarketPrice")
        if price is None:
            price = info.get("currentPrice")
        currency = info.get("currency")

        return cls(
            symbol=info.get("symbol", ""),
            name=symbol_info.get("name", ""),
            indices=symbol_info.get("indices", [index]),
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            country=info.get("country", ""),
            current_price=price,
            currency=currency,
            dividend_count=len(history),
            history=history,
            expected_ex_dividend_dates=expected_dates,
        )

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "indices": self.indices,
            "sector": self.sector,
            "industry": self.industry,
            "country": self.country,
            "current_price": self.current_price,
            "currency": self.currency,
            "dividend_count": self.dividend_count,
            "history": [
                {"amount": item.amount, "date": item.date.isoformat()}
                for item in self.history
            ],
            "expected_ex_dividend_dates": self.expected_ex_dividend_dates.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)
