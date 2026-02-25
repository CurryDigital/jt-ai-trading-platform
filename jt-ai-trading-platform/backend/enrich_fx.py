from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
new_fx = [
    ('GBPUSD=X', 'GBP/USD', 'FX', 'Short Term'),
    ('AUDUSD=X', 'AUD/USD', 'FX', 'Short Term'),
    ('USDCAD=X', 'USD/CAD', 'FX', 'Short Term'),
    ('USDCHF=X', 'USD/CHF', 'FX', 'Long Term'),
    ('NZDUSD=X', 'NZD/USD', 'FX', 'Short Term'),
    ('EURJPY=X', 'EUR/JPY', 'FX', 'Short Term'),
    ('GBPJPY=X', 'GBP/JPY', 'FX', 'Short Term'),
    ('EURGBP=X', 'EUR/GBP', 'FX', 'Long Term'),
    ('EURCHF=X', 'EUR/CHF', 'FX', 'Long Term'),
    ('AUDJPY=X', 'AUD/JPY', 'FX', 'Short Term')
]

for ticker, name, asset_class, horizon in new_fx:
    db.execute(text("""
        INSERT INTO gold.asset_registry (ticker, name, asset_class, horizon, is_active) 
        VALUES (:t, :n, :ac, :h, True) 
        ON CONFLICT (ticker) DO UPDATE SET is_active = True
    """), {'t': ticker, 'n': name, 'ac': asset_class, 'h': horizon})

db.commit()
db.close()
print("Enriched Asset Registry with 10 more FX pairs.")
