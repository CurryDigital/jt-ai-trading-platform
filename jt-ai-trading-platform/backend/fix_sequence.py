from app.db.session import SessionLocal, engine
from sqlalchemy import text

def fix_sequences():
    db = SessionLocal()
    try:
        print("Fixing trades sequence...")
        # Check max id
        res = db.execute(text("SELECT MAX(id) FROM consumption.trades"))
        max_id = res.scalar() or 1
        print(f"Max ID is {max_id}")
        
        # Reset sequence
        db.execute(text(f"SELECT setval('consumption.trades_id_seq', {max_id + 1}, false)"))
        db.commit()
        print("Sequence reset successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_sequences()
