#!/usr/bin/env python3
"""
Universe Expansion - Classify unclassified tickers
Adds 14 US stocks to asset registry with proper sectors
"""
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend')

from app.db.session import get_connection
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 14 unclassified US stocks with proposed sectors
UNCLASSIFIED_STOCKS = {
    # Tech sector
    'AVGO': {'sector': 'TECH', 'name': 'Broadcom Inc.'},
    'MDB': {'sector': 'TECH', 'name': 'MongoDB Inc.'},
    'NFLX': {'sector': 'TECH', 'name': 'Netflix Inc.'},
    'SHOP': {'sector': 'TECH', 'name': 'Shopify Inc.'},
    'TWLO': {'sector': 'TECH', 'name': 'Twilio Inc.'},
    'VEEV': {'sector': 'TECH', 'name': 'Veeva Systems Inc.'},
    'ZM': {'sector': 'TECH', 'name': 'Zoom Video Communications'},
    
    # Equity/Other sectors
    'C': {'sector': 'FINANCIAL', 'name': 'Citigroup Inc.'},
    'DOCU': {'sector': 'TECH', 'name': 'DocuSign Inc.'},
    'IBM': {'sector': 'TECH', 'name': 'International Business Machines'},
    'LCID': {'sector': 'AUTO', 'name': 'Lucid Group Inc.'},
    'LYFT': {'sector': 'TECH', 'name': 'Lyft Inc.'},
    'PINS': {'sector': 'TECH', 'name': 'Pinterest Inc.'},
    'UBER': {'sector': 'TECH', 'name': 'Uber Technologies Inc.'},
}

def classify_stocks():
    """Classify the 14 unclassified US stocks"""
    
    logger.info("="*60)
    logger.info("UNIVERSE EXPANSION - Classifying 14 US stocks")
    logger.info("="*60)
    
    # Check current count
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gold.asset_registry WHERE is_active = TRUE")
    before_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    logger.info(f"Active tickers before: {before_count}")
    
    # Check which of these already exist
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM gold.asset_registry WHERE ticker = ANY(%s)", 
                   (list(UNCLASSIFIED_STOCKS.keys()),))
    existing = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    logger.info(f"Already in registry: {len(existing)} - {existing}")
    
    # Insert/update classifications
    inserted = 0
    updated = 0
    
    for ticker, info in UNCLASSIFIED_STOCKS.items():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Check if exists
            cursor.execute("SELECT 1 FROM gold.asset_registry WHERE ticker = %s", (ticker,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing
                cursor.execute("""
                    UPDATE gold.asset_registry 
                    SET sector = %s, 
                        description = %s,
                        is_active = TRUE,
                        updated_at = NOW()
                    WHERE ticker = %s
                """, (info['sector'], info['name'], ticker))
                updated += 1
                logger.info(f"  Updated {ticker} -> {info['sector']}")
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO gold.asset_registry 
                    (ticker, name, asset_class, market, sector, description, is_active, created_at)
                    VALUES (%s, %s, 'STOCK', 'US', %s, %s, TRUE, NOW())
                    ON CONFLICT (ticker) DO UPDATE SET
                        sector = EXCLUDED.sector,
                        description = EXCLUDED.description,
                        is_active = TRUE,
                        updated_at = NOW()
                """, (ticker, info['name'], info['sector'], info['name']))
                inserted += 1
                logger.info(f"  Inserted {ticker} -> {info['sector']}")
            
            conn.commit()
                
        except Exception as e:
            logger.error(f"  Error with {ticker}: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    # Get new count
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM gold.asset_registry WHERE is_active = TRUE")
    after_count = cursor.fetchone()[0]
    
    # Count by sector
    cursor.execute("""
        SELECT sector, COUNT(*) 
        FROM gold.asset_registry 
        WHERE is_active = TRUE AND market = 'US'
        GROUP BY sector
        ORDER BY COUNT(*) DESC
    """)
    sector_counts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    logger.info("\n" + "="*60)
    logger.info("CLASSIFICATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Inserted: {inserted}")
    logger.info(f"Updated: {updated}")
    logger.info(f"Total active tickers: {before_count} -> {after_count}")
    logger.info(f"\nUS Stocks by Sector:")
    for sector, count in sector_counts:
        logger.info(f"  {sector}: {count}")
    
    return {
        'inserted': inserted,
        'updated': updated,
        'before': before_count,
        'after': after_count
    }

def add_reit_placeholder():
    """Add REIT tickers as placeholders for future data import"""
    REITS = [
        ('O', 'Realty Income Corp', 'REIT'),
        ('AMT', 'American Tower Corp', 'REIT'),
        ('PLD', 'Prologis Inc', 'REIT'),
        ('CCI', 'Crown Castle Inc', 'REIT'),
        ('EQIX', 'Equinix Inc', 'REIT'),
        ('PSA', 'Public Storage', 'REIT'),
        ('SPG', 'Simon Property Group', 'REIT'),
        ('WELL', 'Welltower Inc', 'REIT'),
        ('DLR', 'Digital Realty Trust', 'REIT'),
        ('AVB', 'AvalonBay Communities', 'REIT'),
    ]
    
    logger.info("\n" + "="*60)
    logger.info("ADDING REIT PLACEHOLDERS (inactive)")
    logger.info("="*60)
    
    added = 0
    for ticker, name, sector in REITS:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO gold.asset_registry 
                (ticker, name, asset_class, market, sector, description, is_active, created_at)
                VALUES (%s, %s, 'STOCK', 'US', %s, %s, FALSE, NOW())
                ON CONFLICT (ticker) DO NOTHING
            """, (ticker, name, sector, name))
            if cursor.rowcount > 0:
                added += 1
                logger.info(f"  Added {ticker} ({name})")
            conn.commit()
        except Exception as e:
            logger.warning(f"  {ticker}: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    logger.info(f"Added {added} REIT placeholders (inactive - pending data)")
    return added

if __name__ == "__main__":
    result = classify_stocks()
    reit_count = add_reit_placeholder()
    
    print(f"\n✅ Universe expansion complete!")
    print(f"   - Classified {result['updated']} existing stocks")
    print(f"   - Added {result['inserted']} new stocks")
    print(f"   - Added {reit_count} REIT placeholders (inactive)")
    print(f"   - Total active: {result['after']} tickers")
