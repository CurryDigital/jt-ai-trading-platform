#!/usr/bin/env python3
"""
TAQ (Trade Algo QA) - Complete Trading Strategy Verification Tool
"""
import argparse
import boto3
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, date
import sys
import re

def get_db_connection():
    """Connect to RDS using IAM auth"""
    session = boto3.Session(region_name='ap-southeast-1')
    rds = session.client('rds')
    token = rds.generate_db_auth_token(
        DBHostname='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        Port=5432, DBUsername='openclaw_user', Region='ap-southeast-1'
    )
    return psycopg2.connect(
        host='openclaw.cjs04usueagu.ap-southeast-1.rds.amazonaws.com',
        port=5432, database='aitrading', user='openclaw_user',
        password=token, sslmode='require'
    )

def check_data_availability(start_date, end_date):
    """Check if we have data for the claimed period"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT ticker) as tickers,
            MIN(date) as earliest,
            MAX(date) as latest
        FROM silver.unified_prices
        WHERE date BETWEEN %s AND %s
    """, (start_date, end_date))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {'tickers': 0, 'earliest': None, 'latest': None, 'markets': {}, 'has_data': False}
    
    # Get market breakdown
    market_query = """
        SELECT 
            CASE 
                WHEN ticker LIKE '%%.HK' THEN 'HK'
                WHEN ticker LIKE '%%.SI' THEN 'SG'
                WHEN ticker LIKE '%%.SS' OR ticker LIKE '%%.SZ' THEN 'CN'
                WHEN ticker LIKE '%%-USD' OR ticker LIKE '%%-USDT' THEN 'CRYPTO'
                ELSE 'US'
            END as market,
            COUNT(DISTINCT ticker) as count
        FROM silver.unified_prices
        WHERE date BETWEEN %s AND %s
        GROUP BY 1
        ORDER BY count DESC
    """
    cursor.execute(market_query, (start_date, end_date))
    markets = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    
    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)
    
    return {
        'tickers': result[0],
        'earliest': result[1],
        'latest': result[2],
        'markets': markets,
        'has_data': result[0] > 0 and result[1] <= start_dt and result[2] >= end_dt
    }

def verify_claims(strategy_id, claimed_trades, claimed_wr, start_date, end_date):
    """Verify researcher claims against database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT total_trades, win_rate_pct, sharpe_ratio, max_drawdown_pct, parameters
        FROM openclaw_researcher.backtest_results
        WHERE hypothesis_name = %s
        AND start_date >= %s AND end_date <= %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (strategy_id, start_date, end_date))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {'verified': False, 'error': f'No database records found for {strategy_id}'}
    
    db_trades, db_wr, db_sharpe, db_dd, params = result
    trade_tolerance = max(claimed_trades * 0.1, 20) if claimed_trades else 50
    
    return {
        'verified': True,
        'claimed_trades': claimed_trades,
        'db_trades': db_trades,
        'trades_match': abs(db_trades - claimed_trades) <= trade_tolerance if claimed_trades else None,
        'claimed_wr': claimed_wr,
        'db_wr': db_wr,
        'wr_match': abs(db_wr - claimed_wr) <= 3.0 if claimed_wr else None,
        'sharpe': db_sharpe,
        'max_dd': db_dd,
        'params': params
    }

def analyze_backtest_quality(trades_count, win_rate, start_date, end_date):
    """Analyze statistical significance and quality metrics"""
    start_dt = date.fromisoformat(start_date)
    end_dt = date.fromisoformat(end_date)
    days = (end_dt - start_dt).days
    years = days / 365.25
    trades_per_year = trades_count / years if years > 0 else 0
    
    if trades_count >= 100 and win_rate >= 55:
        significance = "✅ Statistically significant"
    elif trades_count >= 50 and win_rate >= 52:
        significance = "🟡 Marginally significant"
    else:
        significance = "❌ Insufficient sample size"
    
    return {
        'period_years': round(years, 2),
        'trades_per_year': round(trades_per_year, 1),
        'significance': significance,
        'minimum_trades': 100,
        'has_sufficient_data': trades_count >= 100
    }

def detect_lookahead(script_content):
    """Scan script for potential lookahead patterns"""
    issues = []
    warnings = []
    
    critical_patterns = [
        (r'\.iloc\[i\][\s\]]*\[.*close', "Using current bar close without shift"),
        (r'df\[.*close.*\]\s*<\s*df\[.*open', "Comparing close to open on same day"),
        (r'current.*close|today.*close', "Possible same-day lookahead in logic"),
        (r'entry_price\s*=\s*.*\[i\].*close', "Entry at current close (lookahead)"),
    ]
    
    warning_patterns = [
        (r'\.rolling\([^)]+\)(?!.*shift)', "Rolling calculation without shift"),
        (r'\.mean\(\)(?!.*shift)', "Mean calculation without shift"),
        (r'\.std\(\)(?!.*shift)', "Std calculation without shift"),
        (r'RSI.*\(.*\)(?!.*shift)', "RSI without shift"),
        (r'MACD.*\(.*\)(?!.*shift)', "MACD without shift"),
    ]
    
    good_patterns = [r'\.shift\(1\)', r'entry.*next.*open', r'prev_close|previous.*close']
    has_shift = any(re.search(p, script_content, re.IGNORECASE) for p in good_patterns)
    
    for pattern, desc in critical_patterns:
        if re.search(pattern, script_content, re.IGNORECASE):
            issues.append(desc)
    for pattern, desc in warning_patterns:
        if re.search(pattern, script_content, re.IGNORECASE):
            warnings.append(desc)
    
    return {'has_protection': has_shift, 'critical_issues': issues, 'warnings': warnings, 'is_safe': len(issues) == 0 and has_shift}

def print_report(strategy_id, claims_result, data_result, quality_result, lookahead_result):
    print("=" * 70)
    print(f"🔍 QA VERIFICATION REPORT: {strategy_id}")
    print("=" * 70)
    print()
    print("📊 DATA AVAILABILITY")
    print(f"   Total Tickers: {data_result['tickers']}")
    print(f"   Markets: {', '.join([f'{k}({v})' for k, v in data_result['markets'].items()])}")
    print(f"   Date Range: {data_result['earliest']} to {data_result['latest']}")
    print(f"   Status: {'✅ OK' if data_result['has_data'] else '❌ INSUFFICIENT'}")
    print()
    
    if claims_result.get('verified'):
        print("📈 CLAIM VERIFICATION")
        if claims_result['claimed_trades']:
            icon = "✅" if claims_result['trades_match'] else "❌"
            print(f"   Trades: {claims_result['claimed_trades']} vs {claims_result['db_trades']} DB {icon}")
        if claims_result['claimed_wr']:
            icon = "✅" if claims_result['wr_match'] else "❌"
            print(f"   Win Rate: {claims_result['claimed_wr']:.1f}% vs {claims_result['db_wr']:.1f}% DB {icon}")
        print(f"   Sharpe: {claims_result['sharpe']:.2f}" if claims_result['sharpe'] else "   Sharpe: N/A")
        print(f"   Max DD: {claims_result['max_dd']:.1f}%" if claims_result['max_dd'] else "   Max DD: N/A")
        print()
    elif 'error' in claims_result:
        print("❌ DATABASE VERIFICATION")
        print(f"   {claims_result['error']}")
        print()
    
    print("📉 STATISTICAL QUALITY")
    print(f"   Period: {quality_result['period_years']} years")
    print(f"   Trades/Year: {quality_result['trades_per_year']}")
    print(f"   Significance: {quality_result['significance']}")
    print()
    
    print("🔎 LOOKAHEAD BIAS CHECK")
    if lookahead_result['is_safe']:
        print("   ✅ Proper protection detected (.shift(1) used)")
    else:
        if lookahead_result['critical_issues']:
            print("   ❌ CRITICAL:")
            for issue in lookahead_result['critical_issues']:
                print(f"      - {issue}")
        if lookahead_result['warnings']:
            print("   ⚠️  WARNINGS:")
            for warning in lookahead_result['warnings']:
                print(f"      - {warning}")
        if not lookahead_result['has_protection'] and not lookahead_result['critical_issues']:
            print("   ⚠️  No shift protection detected — verify manually")
    print()
    
    print("=" * 70)
    issues = []
    if not data_result['has_data']:
        issues.append("Insufficient data")
    if claims_result.get('verified') and claims_result['claimed_trades'] and not claims_result['trades_match']:
        issues.append("Trade count mismatch")
    if not lookahead_result['is_safe']:
        issues.append("Lookahead bias detected")
    if not quality_result['has_sufficient_data']:
        issues.append("Insufficient sample size")
    
    if not issues:
        print("✅ VERDICT: APPROVED")
    else:
        print(f"❌ VERDICT: REJECTED — {', '.join(issues)}")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Verify trading strategy claims')
    parser.add_argument('--strategy', required=True, help='Strategy ID (e.g., S001)')
    parser.add_argument('--trades', type=int, help='Claimed trade count')
    parser.add_argument('--wr', type=float, help='Claimed win rate %')
    parser.add_argument('--start', default='2023-01-01', help='Start date')
    parser.add_argument('--end', default='2024-12-31', help='End date')
    parser.add_argument('--script', help='Path to backtest script for lookahead check')
    args = parser.parse_args()
    
    data_result = check_data_availability(args.start, args.end)
    
    claims_result = {}
    if args.trades:
        claims_result = verify_claims(args.strategy, args.trades, args.wr, args.start, args.end)
        quality_result = analyze_backtest_quality(
            claims_result.get('db_trades') or args.trades,
            claims_result.get('db_wr') or args.wr or 50,
            args.start, args.end
        )
    else:
        quality_result = analyze_backtest_quality(0, 50, args.start, args.end)
    
    lookahead_result = {'is_safe': False, 'has_protection': False, 'critical_issues': [], 'warnings': []}
    if args.script:
        try:
            with open(args.script, 'r') as f:
                lookahead_result = detect_lookahead(f.read())
        except Exception as e:
            lookahead_result = {'is_safe': False, 'error': str(e), 'critical_issues': [], 'warnings': []}
    
    print_report(args.strategy, claims_result, data_result, quality_result, lookahead_result)

if __name__ == '__main__':
    main()
