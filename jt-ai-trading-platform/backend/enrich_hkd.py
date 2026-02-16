from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
new_fx = [
    ('USDHKD=X', 'USD/HKD', 'FX', 'Long Term'),
]

for ticker, name, asset_class, horizon in new_fx:
    db.execute(text("""
        INSERT INTO gold.asset_registry (ticker, name, asset_class, horizon, is_active) 
        VALUES (:t, :n, :ac, :h, True) 
        ON CONFLICT (ticker) DO UPDATE SET is_active = True
    """), {'t': ticker, 'n': name, 'ac': asset_class, 'h': horizon})

db.commit()
db.close()
print("Enriched Asset Registry with USD/HKD.")
