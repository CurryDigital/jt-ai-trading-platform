"""
Update asset_registry with full 50+ stocks per market
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend')

from app.db.session import engine
from sqlalchemy import text

STOCKS = {
    # ========== US MARKET (100 stocks - S&P 500 + Nasdaq 100) ==========
    'US': [
        # Mega Cap Tech & Growth (30)
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'TSM',
        'NFLX', 'AMD', 'INTC', 'CRM', 'ADBE', 'ORCL', 'IBM', 'QCOM', 'AMAT', 'MU',
        'PLTR', 'SNOW', 'ZM', 'UBER', 'LYFT', 'SQ', 'SHOP', 'ROKU', 'TWLO', 'DDOG',
        # Software & Cloud (20)
        'MDB', 'NET', 'CRWD', 'OKTA', 'SPLK', 'NOW', 'VEEV', 'TDOC', 'PINS', 'DOCU',
        'TEAM', 'CPRT', 'DXCM', 'ABNB', 'INTU', 'ADSK', 'PANW', 'FTNT', 'CYBR', 'S',
        # Financials (15)
        'JPM', 'BAC', 'GS', 'MS', 'WFC', 'C', 'BLK', 'AXP', 'USB', 'PNC',
        'TFC', 'COF', 'SCHW', 'SPGI', 'ICE',
        # Healthcare & Pharma (15)
        'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY',
        'GILD', 'AMGN', 'CVS', 'CI', 'HUM',
        # Consumer & Retail (10)
        'V', 'MA', 'WMT', 'COST', 'HD', 'KO', 'PEP', 'PG', 'MCD', 'DIS',
        # Energy & Industrial (10)
        'XOM', 'CVX', 'COP', 'SLB', 'BA', 'CAT', 'GE', 'RTX', 'LMT', 'NOC',
    ],
    # ========== HONG KONG MARKET (100 stocks - Hang Seng Index + Large Caps) ==========
    'HK': [
        # Tech Giants (15)
        '0700.HK', '9988.HK', '3690.HK', '9618.HK', '1024.HK', '9888.HK', '1810.HK',
        '9866.HK', '9868.HK', '9999.HK', '2015.HK', '9616.HK', '9633.HK', '9992.HK', '6608.HK',
        # Banks & Financials (20)
        '0005.HK', '1299.HK', '0939.HK', '1398.HK', '2318.HK', '0388.HK', '3988.HK',
        '3968.HK', '3328.HK', '2628.HK', '2388.HK', '0023.HK', '0838.HK', '1658.HK',
        '1111.HK', '6098.HK', '1359.HK', '0668.HK', '6190.HK', '0998.HK',
        # Property & REITs (15)
        '0001.HK', '0016.HK', '0066.HK', '0002.HK', '0003.HK', '0083.HK', '0101.HK',
        '0688.HK', '0823.HK', '1109.HK', '1113.HK', '0012.HK', '0017.HK', '0069.HK', '0978.HK',
        # Telco & Utilities (10)
        '0941.HK', '0762.HK', '0267.HK', '0006.HK', '0008.HK', '0004.HK', '1038.HK',
        '0168.HK', '0270.HK', '0883.HK',
        # Conglomerates (10)
        '0001.HK', '0016.HK', '0083.HK', '0688.HK', '1109.HK', '1113.HK', '0012.HK',
        '0123.HK', '0144.HK', '0197.HK',
        # Consumer & Retail (15)
        '2319.HK', '2020.HK', '9633.HK', '9992.HK', '1876.HK', '1929.HK', '2331.HK',
        '6862.HK', '1928.HK', '1234.HK', '0151.HK', '0257.HK', '1880.HK', '0506.HK', '0788.HK',
        # Transport & Logistics (8)
        '293.HK', '0088.HK', '0192.HK', '0228.HK', '0316.HK', '0636.HK', '0668.HK', '0836.HK',
        # Others (7)
        '1211.HK', '2313.HK', '2382.HK', '2269.HK', '2688.HK', '2899.HK', '3323.HK',
    ],
    # ========== CHINA A-SHARES (100 stocks - CSI 300 constituents) ==========
    'CN': [
        # Tech & Semiconductors (20)
        '300750.SZ', '002594.SZ', '601012.SS', '300760.SZ', '002812.SZ', '300014.SZ',
        '688981.SS', '688012.SS', '688008.SS', '688126.SS', '688169.SS', '002230.SZ',
        '002415.SZ', '603501.SS', '600745.SS', '000725.SZ', '002049.SZ', '603986.SS',
        '300408.SZ', '600584.SS',
        # Financials (20)
        '601318.SS', '600036.SS', '601166.SS', '000001.SZ', '601398.SS', '601288.SS',
        '601939.SS', '601988.SS', '601628.SS', '601088.SS', '601211.SS', '600030.SS',
        '600999.SS', '601688.SS', '601377.SS', '000776.SZ', '601901.SS', '300059.SZ',
        '600958.SS', '601881.SS',
        # Consumer & Retail (20)
        '600519.SS', '000858.SZ', '000568.SZ', '000538.SZ', '600276.SS', '603288.SS',
        '000333.SZ', '000651.SZ', '002142.SZ', '002007.SZ', '300122.SZ', '002271.SZ',
        '600436.SS', '600809.SS', '601633.SS', '603259.SS', '300124.SZ', '002236.SZ',
        '000568.SZ', '603288.SS',
        # Energy & Resources (15)
        '601857.SS', '601888.SS', '600900.SS', '601899.SS', '601669.SS', '601186.SS',
        '601117.SS', '600028.SS', '601168.SS', '600489.SS', '600547.SS', '601899.SS',
        '603993.SS', '601600.SS', '600362.SS',
        # Industrials (15)
        '601766.SS', '601727.SS', '600089.SS', '601390.SS', '601800.SS', '601618.SS',
        '600196.SS', '601607.SS', '600104.SS', '000768.SZ', '600893.SS', '600372.SS',
        '600660.SS', '600690.SS', '600585.SS',
        # Healthcare & Pharma (10)
        '603259.SS', '300760.SZ', '600276.SS', '000538.SZ', '600436.SS', '300122.SZ',
        '002007.SZ', '600196.SS', '603392.SS', '688180.SS',
    ],
    # ========== SINGAPORE MARKET (100 stocks - STI + Large Caps) ==========
    'SG': [
        # Banks & Financials (20)
        'D05.SI', 'U11.SI', 'O39.SI', 'S68.SI', 'N2IU.SI', 'Y92.SI', 'T82U.SI',
        'C38U.SI', 'S63.SI', 'S61.SI', 'BS6.SI', 'OV8.SI', 'C07.SI', 'C09.SI',
        'C31.SI', 'C6L.SI', 'E5H.SI', 'F03.SI', 'G13.SI', 'H02.SI',
        # REITs (25)
        'A17U.SI', 'M44U.SI', 'P40U.SI', 'BUOU.SI', 'C61U.SI', 'J69U.SI', 'K71U.SI',
        'N2IU.SI', 'T82U.SI', 'ME8U.SI', 'RW0U.SI', 'AXJU.SI', 'CRPU.SI', 'KD8U.SI',
        'O5RU.SI', 'Q5T.SI', 'SGRU.SI', 'SK6U.SI', 'SV3U.SI', 'UD1U.SI', 'H78.SI',
        '5WH.SI', 'C2PU.SI', 'D5IU.SI', 'K2LU.SI',
        # Telecommunications (8)
        'Z74.SI', 'CC3.SI', 'H13.SI', 'T43.SI', 'T82U.SI', 'N2IU.SI', 'CJLU.SI', 'AWX.SI',
        # Conglomerates (15)
        'J36.SI', 'A35.SI', 'C31.SI', 'S58.SI', 'U14.SI', 'W05.SI', 'Y03.SI',
        'Q01.SI', 'Z25.SI', 'G50.SI', 'B68.SI', 'C52.SI', 'F03.SI', 'H78.SI', 'T14.SI',
        # Transport & Logistics (10)
        'C6L.SI', 'S59.SI', 'Y8Z.SI', 'W03.SI', 'N03.SI', 'P15.SI', 'S19.SI',
        'U11.SI', 'C29.SI', 'F17.SI',
        # Consumer & Retail (12)
        'C07.SI', 'D01.SI', 'F99.SI', 'G07.SI', 'J07.SI', 'M01.SI', 'S20.SI',
        'U09.SI', 'U11.SI', 'W01.SI', 'Y92.SI', 'Z59.SI',
        # Industrials & Engineering (10)
        'S63.SI', 'Y92.SI', '5AB.SI', '5JS.SI', '5ME.SI', '5PC.SI', '5TP.SI',
        '558.SI', '569.SI', '544.SI',
        # Technology (10)
        'H17.SI', 'C76.SI', 'V03.SI', 'S61.SI', '5CF.SI', 'C07.SI', 'BIX.SI',
        'Q0X.SI', 'CLN.SI', 'S63.SI',
    ]
}

def update_asset_registry():
    with engine.connect() as conn:
        # First, deactivate all existing stocks
        conn.execute(text("UPDATE gold.asset_registry SET is_active = FALSE WHERE asset_class = 'STOCK'"))
        conn.commit()
        print("Deactivated existing stocks")
        
        # Insert new stocks
        insert_sql = text("""
            INSERT INTO gold.asset_registry 
            (ticker, asset_class, market, horizon, is_active, created_at)
            VALUES (:ticker, 'STOCK', :market, 'Short Term', TRUE, NOW())
            ON CONFLICT (ticker) DO UPDATE SET
                market = EXCLUDED.market,
                is_active = TRUE,
                horizon = EXCLUDED.horizon
        """)
        
        total = 0
        for market, tickers in STOCKS.items():
            for ticker in tickers:
                conn.execute(insert_sql, {"ticker": ticker, "market": market})
                total += 1
            print(f"Inserted {len(tickers)} {market} stocks")
        
        conn.commit()
        print(f"\nTotal stocks in registry: {total}")
        
        # Verify
        result = conn.execute(text("SELECT market, COUNT(*) FROM gold.asset_registry WHERE asset_class='STOCK' AND is_active=TRUE GROUP BY market"))
        print("\nActive stocks by market:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    update_asset_registry()
