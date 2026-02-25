#!/usr/bin/env python3
"""
Strategy Parser for JT Platform Integration
Parses all strategy.yaml files and returns structured data

CLI Usage:
    python parse_strategies.py --all
    python parse_strategies.py --status backtested
    python parse_strategies.py --asset equities --direction neutral
    python parse_strategies.py --all --format json
    python parse_strategies.py --jt-ready

Python API Usage:
    from parse_strategies import list_strategies, get_strategy_by_name, print_strategy_summary
    
    # List all strategies (lightweight)
    strategies = list_strategies()
    
    # List with filters
    backtested = list_strategies(status='backtested')
    equities = list_strategies(status='backtested', verbose=True)
    
    # Get specific strategy
    araso = get_strategy_by_name('ARASO')
    
    # Get by asset class
    crypto = get_strategies_by_asset('crypto')
    
    # Print formatted summary
    print_strategy_summary()
"""

import yaml
import json
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime

STRATEGIES_DIR = Path(__file__).parent

def parse_strategy_yaml(strategy_path: Path) -> Dict:
    """
    Parse a single strategy.yaml file.
    Returns strategy dict with file metadata including last_modified timestamp.
    """
    yaml_path = strategy_path / "strategy.yaml"
    
    if not yaml_path.exists():
        return None
    
    # Get file modification time
    stat = yaml_path.stat()
    last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    with open(yaml_path) as f:
        strategy = yaml.safe_load(f)
    
    if strategy:
        strategy['_meta'] = {
            'file_path': str(strategy_path.relative_to(STRATEGIES_DIR)),
            'last_modified': last_modified,
            'file_size_bytes': stat.st_size
        }
    
    return strategy

def get_all_strategies() -> List[Dict]:
    """
    Parse all strategies in the directory.
    Returns strategies with _meta.last_modified timestamp for caching.
    """
    strategies = []
    
    for asset_dir in STRATEGIES_DIR.iterdir():
        if not asset_dir.is_dir():
            continue
        
        for strategy_dir in asset_dir.iterdir():
            if not strategy_dir.is_dir():
                continue
            
            strategy = parse_strategy_yaml(strategy_dir)
            if strategy:
                strategies.append(strategy)
    
    return strategies

def filter_strategies(strategies: List[Dict], **filters) -> List[Dict]:
    """Filter strategies by criteria."""
    result = strategies
    
    if 'status' in filters:
        result = [s for s in result if s.get('status') == filters['status']]
    
    if 'asset_class' in filters:
        result = [s for s in result if s.get('asset_class') == filters['asset_class']]
    
    if 'direction' in filters:
        result = [s for s in result if s.get('direction') == filters['direction']]
    
    if 'horizon' in filters:
        result = [s for s in result if s.get('horizon') == filters['horizon']]
    
    if 'jt_integration' in filters:
        result = [s for s in result if s.get('deployment', {}).get('jt_integration') == filters['jt_integration']]
    
    return result

def check_jt_compatibility(strategy: Dict) -> tuple:
    """Check if strategy is ready for JT platform."""
    required_fields = [
        'name', 'asset_class', 'direction', 'horizon',
        'universe', 'risk', 'execution', 'deployment'
    ]
    
    missing = []
    for field in required_fields:
        if field not in strategy:
            missing.append(field)
    
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    
    if not strategy.get('deployment', {}).get('jt_integration'):
        return False, "JT integration not enabled"
    
    return True, "Ready for deployment"


def list_strategies(status: str = None, verbose: bool = False) -> List[Dict]:
    """
    List all available strategies with optional filtering.
    
    Each strategy includes a 'last_modified' timestamp from the file system,
    allowing JT platform to cache strategies and only re-parse updated ones.
    
    Args:
        status: Filter by status (backtested, paper, live)
        verbose: If True, return full strategy dicts; if False, return summaries
    
    Returns:
        List of strategy summaries or full dicts.
        Each summary contains: name, path, asset_class, direction, horizon,
        status, sharpe, jt_ready, last_modified
    
    Example:
        # Quick list all
        strategies = list_strategies()
        
        # List ready for live trading
        live_ready = list_strategies(status='backtested')
        
        # Full details
        details = list_strategies(verbose=True)
        
        # JT caching: check last_modified vs cached timestamp
        for s in strategies:
            if s['last_modified'] > cached_timestamp:
                # Re-parse this strategy
                full = get_strategy_by_name(s['name'])
    """
    strategies = get_all_strategies()
    
    if status:
        strategies = [s for s in strategies if s.get('status') == status]
    
    if not verbose:
        # Return lightweight summaries with timestamp for caching
        return [
            {
                'name': s.get('name', 'Unknown'),
                'path': s.get('_meta', {}).get('file_path', ''),
                'asset_class': s.get('asset_class', 'N/A'),
                'direction': s.get('direction', 'N/A'),
                'horizon': s.get('horizon', 'N/A'),
                'status': s.get('status', 'N/A'),
                'sharpe': s.get('actual_sharpe', 0),
                'jt_ready': check_jt_compatibility(s)[0],
                'last_modified': s.get('_meta', {}).get('last_modified', '')
            }
            for s in strategies
        ]
    
    return strategies


def get_strategy_by_name(name: str) -> Dict:
    """
    Get a specific strategy by name.
    
    Args:
        name: Strategy name (case-insensitive partial match)
    
    Returns:
        Strategy dict or None if not found
    
    Example:
        araso = get_strategy_by_name('ARASO')
        funding = get_strategy_by_name('funding')
    """
    strategies = get_all_strategies()
    name_lower = name.lower()
    
    for s in strategies:
        if name_lower in s.get('name', '').lower():
            return s
    
    return None


def get_strategies_by_asset(asset_class: str) -> List[Dict]:
    """
    Get all strategies for a specific asset class.
    
    Args:
        asset_class: equities, fx, crypto, commodities, cross_asset
    
    Returns:
        List of strategy dicts
    
    Example:
        equities = get_strategies_by_asset('equities')
        crypto = get_strategies_by_asset('crypto')
    """
    strategies = get_all_strategies()
    return [s for s in strategies if s.get('asset_class') == asset_class]


def print_strategy_summary(strategies: List[Dict] = None):
    """
    Print a formatted summary of strategies to console.
    Includes last_modified timestamp for caching decisions.
    
    Example:
        print_strategy_summary()  # All strategies
        print_strategy_summary(list_strategies(status='live'))  # Only live
    """
    if strategies is None:
        strategies = list_strategies()
    
    print(f"\n{'Name':<35} {'Asset':<10} {'Dir':<8} {'Status':<12} {'Sharpe':<8} {'JT':<4} {'Last Modified':<20}")
    print("-" * 105)
    
    for s in strategies:
        name = s.get('name', 'Unknown')[:33]
        asset = s.get('asset_class', 'N/A')
        direction = s.get('direction', 'N/A')
        status = s.get('status', 'N/A')
        sharpe = s.get('sharpe', s.get('actual_sharpe', 0))
        jt = '✓' if s.get('jt_ready', False) else '✗'
        modified = s.get('last_modified', '')[:19]  # Truncate to YYYY-MM-DD HH:MM:SS
        print(f"{name:<35} {asset:<10} {direction:<8} {status:<12} {sharpe:<8.2f} {jt:<4} {modified:<20}")
    
    print(f"\nTotal: {len(strategies)} strategies")

def main():
    parser = argparse.ArgumentParser(description='Parse strategies for JT platform')
    parser.add_argument('--all', action='store_true', help='Show all strategies')
    parser.add_argument('--status', type=str, help='Filter by status (backtested, paper, live)')
    parser.add_argument('--asset', type=str, help='Filter by asset class (equities, fx, crypto, commodities)')
    parser.add_argument('--direction', type=str, help='Filter by direction (long, short, neutral)')
    parser.add_argument('--horizon', type=str, help='Filter by horizon (short_term, long_term)')
    parser.add_argument('--jt-ready', action='store_true', help='Only JT-compatible strategies')
    parser.add_argument('--name', type=str, help='Find strategy by name (partial match)')
    parser.add_argument('--format', type=str, choices=['json', 'table'], default='table')
    
    args = parser.parse_args()
    
    # If name search
    if args.name:
        strategy = get_strategy_by_name(args.name)
        if strategy:
            if args.format == 'json':
                print(json.dumps(strategy, indent=2))
            else:
                print(f"\nFound: {strategy.get('name')}")
                print(f"Path: {strategy.get('path')}")
                print(f"Asset: {strategy.get('asset_class')}")
                print(f"Direction: {strategy.get('direction')}")
                print(f"Status: {strategy.get('status')}")
                print(f"Sharpe: {strategy.get('actual_sharpe')}")
        else:
            print(f"No strategy found matching '{args.name}'")
        return
    
    # Get strategies with filters
    strategies = list_strategies(status=args.status, verbose=(args.format == 'json'))
    
    # Apply additional filters
    if args.asset:
        strategies = [s for s in strategies if s.get('asset_class') == args.asset]
    if args.direction:
        strategies = [s for s in strategies if s.get('direction') == args.direction]
    if args.horizon:
        strategies = [s for s in strategies if s.get('horizon') == args.horizon]
    
    if args.jt_ready:
        strategies = [s for s in strategies if s.get('jt_ready', False)]
    
    # Output
    if args.format == 'json':
        # For JSON, we need full strategy objects
        if not strategies or 'universe' not in strategies[0]:
            strategies = get_all_strategies()
            if args.status:
                strategies = [s for s in strategies if s.get('status') == args.status]
            if args.asset:
                strategies = [s for s in strategies if s.get('asset_class') == args.asset]
            if args.direction:
                strategies = [s for s in strategies if s.get('direction') == args.direction]
            if args.horizon:
                strategies = [s for s in strategies if s.get('horizon') == args.horizon]
            if args.jt_ready:
                strategies = [s for s in strategies if check_jt_compatibility(s)[0]]
        print(json.dumps(strategies, indent=2))
    else:
        print_strategy_summary(strategies)

if __name__ == '__main__':
    main()
