import random
from faker import Faker
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
import datetime as dt

from typing import Optional, List

app = FastAPI()

fake = Faker()

class TradeDetails(BaseModel):
    buySellIndicator: str = Field(default_factory=lambda: fake.random_element(["BUY", "SELL"]), description="A value of BUY for buys, SELL for sells.")
    price: float = Field(default_factory=lambda: fake.pyfloat(min_value=0, max_value=100), description="The price of the Trade.")
    quantity: int = Field(default_factory=lambda: fake.random_int(min=1, max=1000), description="The amount of units traded.")

class Trade(BaseModel):
    asset_class: str = Field(default_factory=lambda: fake.random_element(["Equity", "Bond", "FX"]), alias="assetClass", description="The asset class of the instrument traded. E.g. Bond, Equity, FX...etc")
    counterparty: str = Field(default_factory=lambda: fake.company(), description="The counterparty the trade was executed with. May not always be available")
    instrument_id: str = Field(default_factory=lambda: fake.word().upper(), alias="instrumentId", description="The ISIN/ID of the instrument traded. E.g. TSLA, AAPL, AMZN...etc")
    instrument_name: str = Field(default_factory=lambda: fake.word(), alias="instrumentName", description="The name of the instrument traded.")
    trade_date_time: dt.datetime = Field(default_factory=dt.datetime.now, alias="tradeDateTime", description="The date-time the Trade was executed")
    trade_details: TradeDetails = Field(default_factory=TradeDetails, alias="tradeDetails", description="The details of the trade, i.e. price, quantity")
    trade_id: str = Field(default_factory=lambda: fake.uuid4(), alias="tradeId", description="The unique ID of the trade")
    trader: str = Field(default_factory=lambda: fake.uuid4(), description="The name of the Trader")

def generate_random_trades(num_trades: int) -> List[Trade]:
    trades = []
    for _ in range(num_trades):
        trade = Trade()
        trades.append(trade)
    return trades

# Generate random trades
trades = generate_random_trades(100)

@app.get("/trades", response_model=List[Trade])
async def get_trades(
    assetClass: Optional[str] = Query(None, description="Filter trades by asset class"),
    end: Optional[dt.datetime] = Query(None, description="Filter trades with tradeDateTime before or on the specified date"),
    maxPrice: Optional[float] = Query(None, description="Filter trades with tradeDetails.price less than or equal to the specified value"),
    minPrice: Optional[float] = Query(None, description="Filter trades with tradeDetails.price greater than or equal to the specified value"),
    start: Optional[dt.datetime] = Query(None, description="Filter trades with tradeDateTime after or on the specified date"),
    tradeType: Optional[str] = Query(None, description="Filter trades by tradeDetails.buySellIndicator (BUY or SELL)"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    perPage: int = Query(10, ge=1, le=100, description="Number of trades per page"),
    sort: Optional[str] = Query(None, description="Sort trades by field")
):
    filtered_trades = trades

    if assetClass:
        filtered_trades = [trade for trade in filtered_trades if trade.asset_class.lower() == assetClass.lower()]

    if end:
        filtered_trades = [trade for trade in filtered_trades if trade.trade_date_time <= end]

    if maxPrice is not None:
        filtered_trades = [trade for trade in filtered_trades if trade.trade_details.price <= maxPrice]

    if minPrice is not None:
        filtered_trades = [trade for trade in filtered_trades if trade.trade_details.price >= minPrice]

    if start:
        filtered_trades = [trade for trade in filtered_trades if trade.trade_date_time >= start]

    if tradeType:
        filtered_trades = [trade for trade in filtered_trades if trade.trade_details.buySellIndicator.lower() == tradeType.lower()]

    # Sorting trades
    if sort:
        field_name = sort.strip().lower()
        if field_name == "assetclass":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.asset_class)
        elif field_name == "counterparty":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.counterparty)
        elif field_name == "instrumentid":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.instrument_id)
        elif field_name == "instrumentname":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.instrument_name)
        elif field_name == "tradedatetime":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.trade_date_time)
        elif field_name == "tradeid":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.trade_id)
        elif field_name == "trader":
            filtered_trades = sorted(filtered_trades, key=lambda trade: trade.trader)

    # Pagination
    total_trades = len(filtered_trades)
    start_index = (page - 1) * perPage
    end_index = start_index + perPage
    paginated_trades = filtered_trades[start_index:end_index]

    return paginated_trades

@app.get("/trades/{trade_id}", response_model=Trade)
async def get_trade(trade_id: str):
    for trade in trades:
        if trade.trade_id == trade_id:
            return trade
    return {"error": "Trade not found"}