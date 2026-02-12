from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
new_assets = [
    ('SI=F', 'Silver Futures', 'COMMODITY', 'Short Term'),
    ('HG=F', 'Copper Futures', 'COMMODITY', 'Short Term'),
    ('NG=F', 'Natural Gas Futures', 'COMMODITY', 'Long Term'),
    ('PL=F', 'Platinum Futures', 'COMMODITY', 'Long Term')
]

for ticker, name, asset_class, horizon in new_assets:
    db.execute(text("""
        INSERT INTO gold.asset_registry (ticker, name, asset_class, horizon, is_active) 
        VALUES (:t, :n, :ac, :h, True) 
        ON CONFLICT (ticker) DO UPDATE SET is_active = True
    """), {'t': ticker, 'n': name, 'ac': asset_class, 'h': horizon})

db.commit()
db.close()
print("Enriched Asset Registry with more Hard Assets.")
