import sys
import csv
import requests

def run_stock_retriever(sd: int, ed: int, ticker: str, interval: str) -> list:
    ticker.capitalize()

    yahooHeaders = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
        "cache-control": "max-age=0",
        "dnt": "1",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"
    }

    response = requests.get(
        f"https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={sd}&period2={ed}&interval=1{interval}&events=history&includeAdjustedClose=true",
        allow_redirects=True,
        headers=yahooHeaders,
        stream=True
        )

    decoded = response.content.decode("utf-8")
    read = csv.reader(decoded.splitlines(), delimiter=',')
    return list(read)