#!/usr/bin/env python3
"""
Batch runner for simulate_match.py — tests edge cases and normal scenarios.

Usage:
    python scripts/batch_simulate.py
    python scripts/batch_simulate.py --verbose
    python scripts/batch_simulate.py --filter boundary
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class Scenario:
    name: str
    category: str
    args: List[str]
    description: str


@dataclass
class ValidationResult:
    passed: bool
    errors: List[str]


def parse_output(output: str) -> dict:
    """Extract key metrics from simulate_match.py output."""
    metrics = {}
    
    # Extract numeric values
    patterns = {
        'players': r'Players:\s+(\d+)',
        'total_chars': r'Total characters:\s+(\d+)',
        'entry_fee': r'Entry fee:\s+([\d.]+)',
        'kill_award_rate': r'Kill award rate:\s+([\d.]+)%',
        'total_pool': r'Total pool:\s+([\d.]+)',
        'protocol_fee': r'Protocol fee:\s+([\d.]+)',
        'pool_after_protocol': r'Pool after protocol:\s+([\d.]+)',
        'total_kill_awards': r'Total kill awards:\s+([\d.]+)',
        'winner_payout': r'Winner payout:\s+([\d.]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            metrics[key] = float(match.group(1))
    
    # Extract char distribution
    dist_match = re.search(r'Char distribution:\s+\[([\d,\s]+)\]', output)
    if dist_match:
        metrics['char_distribution'] = [int(x.strip()) for x in dist_match.group(1).split(',')]
    
    return metrics


def validate_economics(metrics: dict) -> ValidationResult:
    """Validate economic invariants."""
    errors = []
    
    # Check total pool calculation
    expected_pool = metrics.get('total_chars', 0) * metrics.get('entry_fee', 0)
    actual_pool = metrics.get('total_pool', 0)
    if abs(expected_pool - actual_pool) > 0.01:
        errors.append(f"Pool mismatch: expected {expected_pool:.2f}, got {actual_pool:.2f}")
    
    # Check protocol fee + pool_after = total_pool
    protocol = metrics.get('protocol_fee', 0)
    after_protocol = metrics.get('pool_after_protocol', 0)
    if abs(protocol + after_protocol - actual_pool) > 0.01:
        errors.append(f"Protocol accounting error: {protocol:.2f} + {after_protocol:.2f} != {actual_pool:.2f}")
    
    # Check payouts don't exceed pool
    kill_awards = metrics.get('total_kill_awards', 0)
    winner = metrics.get('winner_payout', 0)
    total_payout = kill_awards + winner
    if total_payout > after_protocol + 0.01:
        errors.append(f"Payout exceeds pool: {total_payout:.2f} > {after_protocol:.2f}")
    
    # Check no negative values
    for key in ['protocol_fee', 'pool_after_protocol', 'total_kill_awards', 'winner_payout']:
        val = metrics.get(key, 0)
        if val < -0.01:
            errors.append(f"Negative value for {key}: {val:.2f}")
    
    return ValidationResult(passed=len(errors) == 0, errors=errors)


def run_scenario(scenario: Scenario, verbose: bool = False) -> tuple[bool, Optional[dict], Optional[ValidationResult]]:
    """Run a single scenario and validate results."""
    cmd = ['python', 'scripts/simulate_match.py'] + scenario.args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            if verbose:
                print(f"  STDERR: {result.stderr}")
            return False, None, None
        
        metrics = parse_output(result.stdout)
        validation = validate_economics(metrics)
        
        if verbose and result.stdout:
            print(result.stdout)
        
        return True, metrics, validation
        
    except subprocess.TimeoutExpired:
        return False, None, None
    except Exception as e:
        if verbose:
            print(f"  Exception: {e}")
        return False, None, None


def define_scenarios() -> List[Scenario]:
    """Define all test scenarios."""
    scenarios = []
    
    # ===== BOUNDARY TESTS =====
    scenarios.extend([
        Scenario(
            name="min_players",
            category="boundary",
            args=['--players', '3', '--chars-per-player', '1', '--entry-fee', '1.0', '--seed', '1'],
            description="Minimum viable match (3 players, 1 char each)"
        ),
        Scenario(
            name="max_players",
            category="boundary",
            args=['--players', '50', '--chars-per-player', '1', '--entry-fee', '1.0', '--seed', '2'],
            description="Maximum players (50)"
        ),
        Scenario(
            name="max_chars_per_player",
            category="boundary",
            args=['--players', '4', '--chars-per-player', '3', '--entry-fee', '1.0', '--seed', '3'],
            description="Maximum characters per player (3)"
        ),
        Scenario(
            name="min_entry_fee",
            category="boundary",
            args=['--players', '4', '--chars-per-player', '1', '--entry-fee', '0.5', '--seed', '4'],
            description="Minimum entry fee (0.5)"
        ),
        Scenario(
            name="max_entry_fee",
            category="boundary",
            args=['--players', '4', '--chars-per-player', '1', '--entry-fee', '5.0', '--seed', '5'],
            description="Maximum entry fee (5.0)"
        ),
        Scenario(
            name="zero_kill_rewards",
            category="boundary",
            args=['--players', '4', '--chars-per-player', '2', '--entry-fee', '1.0', '--kill-award-rate', '0.0', '--seed', '6'],
            description="Zero kill rewards (winner takes all)"
        ),
        Scenario(
            name="max_kill_rewards",
            category="boundary",
            args=['--players', '4', '--chars-per-player', '2', '--entry-fee', '1.0', '--kill-award-rate', '0.5', '--seed', '7'],
            description="Maximum kill rewards (0.5)"
        ),
    ])
    
    # ===== DISTRIBUTION TESTS =====
    scenarios.extend([
        Scenario(
            name="whale_vs_minnows",
            category="distribution",
            args=['--char-distribution', '3,1,1,1', '--entry-fee', '1.0', '--seed', '10'],
            description="One whale (3 chars) vs three minnows (1 char each)"
        ),
        Scenario(
            name="two_whales",
            category="distribution",
            args=['--char-distribution', '3,3,1,1', '--entry-fee', '1.0', '--seed', '11'],
            description="Two whales (3 chars each) vs two minnows"
        ),
        Scenario(
            name="all_whales",
            category="distribution",
            args=['--char-distribution', '3,3,3,3', '--entry-fee', '2.0', '--seed', '12'],
            description="All players with max characters"
        ),
        Scenario(
            name="asymmetric_5p",
            category="distribution",
            args=['--char-distribution', '3,2,2,1,1', '--entry-fee', '1.5', '--seed', '13'],
            description="Asymmetric 5-player distribution"
        ),
        Scenario(
            name="extreme_whale",
            category="distribution",
            args=['--char-distribution', '3,1,1,1,1,1,1,1', '--entry-fee', '1.0', '--seed', '14'],
            description="One whale vs many minnows (protocol fee tier test)"
        ),
    ])
    
    # ===== ECONOMIC TESTS =====
    scenarios.extend([
        Scenario(
            name="high_fee_high_kill",
            category="economic",
            args=['--players', '6', '--chars-per-player', '2', '--entry-fee', '5.0', '--kill-award-rate', '0.5', '--seed', '20'],
            description="High entry fee + high kill rewards"
        ),
        Scenario(
            name="low_fee_low_kill",
            category="economic",
            args=['--players', '6', '--chars-per-player', '2', '--entry-fee', '0.5', '--kill-award-rate', '0.05', '--seed', '21'],
            description="Low entry fee + low kill rewards"
        ),
        Scenario(
            name="protocol_tier_1",
            category="economic",
            args=['--char-distribution', '1,1,1,1', '--entry-fee', '1.0', '--seed', '22'],
            description="All players tier 1 (10% protocol fee)"
        ),
        Scenario(
            name="protocol_tier_2",
            category="economic",
            args=['--char-distribution', '2,2,2,2', '--entry-fee', '1.0', '--seed', '23'],
            description="All players tier 2 (8% protocol fee)"
        ),
        Scenario(
            name="protocol_tier_3",
            category="economic",
            args=['--char-distribution', '3,3,3,3', '--entry-fee', '1.0', '--seed', '24'],
            description="All players tier 3 (6% protocol fee)"
        ),
        Scenario(
            name="mixed_tiers",
            category="economic",
            args=['--char-distribution', '3,2,1,1', '--entry-fee', '1.0', '--seed', '25'],
            description="Mixed protocol fee tiers"
        ),
    ])
    
    # ===== NORMAL CASES =====
    scenarios.extend([
        Scenario(
            name="default_4p",
            category="normal",
            args=['--players', '4', '--chars-per-player', '1', '--entry-fee', '1.0', '--seed', '30'],
            description="Default 4-player match"
        ),
        Scenario(
            name="typical_8p",
            category="normal",
            args=['--players', '8', '--chars-per-player', '1', '--entry-fee', '1.0', '--seed', '31'],
            description="Typical 8-player match"
        ),
        Scenario(
            name="medium_stakes",
            category="normal",
            args=['--players', '6', '--chars-per-player', '2', '--entry-fee', '2.0', '--kill-award-rate', '0.15', '--seed', '32'],
            description="Medium stakes match"
        ),
    ])
    
    # ===== RANDOMNESS TESTS =====
    scenarios.extend([
        Scenario(
            name="same_config_seed_100",
            category="randomness",
            args=['--players', '5', '--chars-per-player', '2', '--entry-fee', '1.0', '--seed', '100'],
            description="Same config, seed 100"
        ),
        Scenario(
            name="same_config_seed_200",
            category="randomness",
            args=['--players', '5', '--chars-per-player', '2', '--entry-fee', '1.0', '--seed', '200'],
            description="Same config, seed 200"
        ),
        Scenario(
            name="same_config_seed_300",
            category="randomness",
            args=['--players', '5', '--chars-per-player', '2', '--entry-fee', '1.0', '--seed', '300'],
            description="Same config, seed 300"
        ),
    ])
    
    return scenarios


def main():
    parser = argparse.ArgumentParser(description="Batch test simulate_match.py")
    parser.add_argument('--verbose', '-v', action='store_true', help="Show full output")
    parser.add_argument('--filter', '-f', type=str, help="Filter by category")
    args = parser.parse_args()
    
    scenarios = define_scenarios()
    
    if args.filter:
        scenarios = [s for s in scenarios if s.category == args.filter]
        if not scenarios:
            print(f"No scenarios found for category: {args.filter}")
            sys.exit(1)
    
    print(f"Running {len(scenarios)} scenarios...\n")
    
    passed = 0
    failed = 0
    validation_failures = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] {scenario.name} ({scenario.category})")
        print(f"    {scenario.description}")
        
        success, metrics, validation = run_scenario(scenario, args.verbose)
        
        if not success:
            print("    ❌ FAILED (execution error)")
            failed += 1
        elif validation and not validation.passed:
            print("    ❌ FAILED (validation errors)")
            for error in validation.errors:
                print(f"       - {error}")
            validation_failures.append((scenario.name, validation.errors))
            failed += 1
        else:
            print("    ✅ PASSED")
            passed += 1
        
        if not args.verbose:
            print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total:  {len(scenarios)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if validation_failures:
        print("\nValidation Failures:")
        for name, errors in validation_failures:
            print(f"  {name}:")
            for error in errors:
                print(f"    - {error}")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
