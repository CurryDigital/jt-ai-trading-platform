from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
new_assets = [
    ('XRP-USD', 'XRP', 'CRYPTO', 'Short Term'),
    ('ADA-USD', 'Cardano', 'CRYPTO', 'Long Term'),
    ('DOGE-USD', 'Dogecoin', 'CRYPTO', 'Short Term'),
    ('DOT-USD', 'Polkadot', 'CRYPTO', 'Long Term'),
    ('LINK-USD', 'Chainlink', 'CRYPTO', 'Short Term'),
    ('AVAX-USD', 'Avalanche', 'CRYPTO', 'Short Term')
]

for ticker, name, asset_class, horizon in new_assets:
    db.execute(text("""
        INSERT INTO gold.asset_registry (ticker, name, asset_class, horizon, is_active) 
        VALUES (:t, :n, :ac, :h, True) 
        ON CONFLICT (ticker) DO UPDATE SET is_active = True
    """), {'t': ticker, 'n': name, 'ac': asset_class, 'h': horizon})

db.commit()
db.close()
print("Enriched Asset Registry with more Crypto.")
