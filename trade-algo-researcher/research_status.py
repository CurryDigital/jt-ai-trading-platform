#!/usr/bin/env python3
"""
Research Status Tracker
Tracks progress of active hypotheses and strategies

Usage:
    python research_status.py
    python research_status.py --update pead --status testing
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

RESEARCH_DIR = Path(__file__).parent
STATUS_FILE = RESEARCH_DIR / "research_status.json"


def load_status() -> Dict:
    """Load research status from JSON."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {
        "last_updated": datetime.now().isoformat(),
        "hypotheses": {},
        "strategies": {}
    }


def save_status(status: Dict):
    """Save research status to JSON."""
    status["last_updated"] = datetime.now().isoformat()
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def get_active_hypotheses() -> List[Dict]:
    """Get all active hypotheses from markdown files."""
    hypotheses_dir = RESEARCH_DIR / "hypotheses" / "active"
    hypotheses = []
    
    if not hypotheses_dir.exists():
        return hypotheses
    
    for md_file in hypotheses_dir.glob("*.md"):
        # Parse basic info from filename
        name = md_file.stem
        hypotheses.append({
            "name": name,
            "file": str(md_file),
            "status": "active"
        })
    
    return hypotheses


def get_strategies() -> List[Dict]:
    """Get all strategies from strategy folders."""
    strategies_dir = RESEARCH_DIR / "strategies"
    strategies = []
    
    for asset_dir in strategies_dir.iterdir():
        if not asset_dir.is_dir() or asset_dir.name.startswith('.') or asset_dir.name.endswith('.py') or asset_dir.name.endswith('.md'):
            continue
        
        for strategy_dir in asset_dir.iterdir():
            if not strategy_dir.is_dir():
                continue
            
            yaml_file = strategy_dir / "strategy.yaml"
            if yaml_file.exists():
                strategies.append({
                    "name": strategy_dir.name,
                    "path": str(strategy_dir.relative_to(strategies_dir)),
                    "asset": asset_dir.name
                })
    
    return strategies


def print_dashboard():
    """Print research dashboard."""
    print(f"\n{'='*70}")
    print("RESEARCH STATUS DASHBOARD")
    print(f"{'='*70}")
    print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")
    
    # Hypotheses
    hypotheses = get_active_hypotheses()
    print(f"ACTIVE HYPOTHESES ({len(hypotheses)})")
    print("-" * 70)
    
    for h in hypotheses:
        name = h['name'].replace('_', ' ').title()
        print(f"  • {name}")
    
    # Strategies
    strategies = get_strategies()
    print(f"\nGOLDEN STRATEGIES ({len(strategies)})")
    print("-" * 70)
    
    for s in strategies:
        print(f"  • {s['name']} ({s['asset']})")
    
    # Pipeline
    print(f"\n{'='*70}")
    print("RESEARCH PIPELINE")
    print(f"{'='*70}")
    
    pipeline = [
        ("PEAD Earnings Drift", "idea → backtest", "Week 1-2"),
        ("Commodity Seasonality", "idea → backtest", "Week 1-2"),
        ("Job Postings Lead", "testing", "Ongoing"),
        ("Lead-Lag Timing", "testing", "Ongoing"),
    ]
    
    print(f"{'Strategy':<30} {'Status':<20} {'Timeline':<15}")
    print("-" * 70)
    for name, status, timeline in pipeline:
        print(f"{name:<30} {status:<20} {timeline:<15}")
    
    print(f"\n{'='*70}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Research Status Tracker')
    parser.add_argument('--update', type=str, help='Update hypothesis status')
    parser.add_argument('--status', type=str, help='New status value')
    parser.add_argument('--dashboard', action='store_true', help='Show dashboard')
    
    args = parser.parse_args()
    
    if args.dashboard or not any([args.update, args.status]):
        print_dashboard()
    
    if args.update and args.status:
        status = load_status()
        status["hypotheses"][args.update] = {
            "status": args.status,
            "updated_at": datetime.now().isoformat()
        }
        save_status(status)
        print(f"Updated {args.update} to status: {args.status}")


if __name__ == '__main__':
    main()
