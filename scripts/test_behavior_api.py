#!/usr/bin/env python3
"""
Diagnostic script to test behavior API endpoint and check for orphaned records.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from website import create_app
from website.models.behavior import BehaviorLog, BehaviorDefinition
from datetime import date, timedelta

app = create_app()

with app.app_context():
    print("=== Behavior API Diagnostics ===\n")

    # Check for orphaned behavior logs
    print("1. Checking for orphaned behavior logs...")
    all_logs = BehaviorLog.query.all()
    print(f"   Total behavior logs: {len(all_logs)}")

    orphaned_count = 0
    for log in all_logs:
        if log.behavior_definition is None:
            orphaned_count += 1
            print(f"   ⚠️  Orphaned log found: ID {log.id}, behavior_definition_id={log.behavior_definition_id}, tracked_date={log.tracked_date}")

    if orphaned_count == 0:
        print("   ✓ No orphaned logs found")
    else:
        print(f"   ❌ Found {orphaned_count} orphaned log(s)")

    print("\n2. Testing to_dict() method on all logs...")
    error_count = 0
    for i, log in enumerate(all_logs):
        try:
            log_dict = log.to_dict()
            if i < 3:  # Print first 3 for debugging
                print(f"   Log {log.id}: {log_dict.get('behavior_name')} on {log_dict.get('tracked_date')}")
        except Exception as e:
            error_count += 1
            print(f"   ❌ Error serializing log {log.id}: {e}")

    if error_count == 0:
        print(f"   ✓ All {len(all_logs)} logs serialized successfully")
    else:
        print(f"   ❌ {error_count} log(s) failed to serialize")

    print("\n3. Checking behavior definitions...")
    all_behaviors = BehaviorDefinition.query.all()
    active_behaviors = BehaviorDefinition.query.filter_by(is_active=True).all()
    print(f"   Total behavior definitions: {len(all_behaviors)}")
    print(f"   Active behavior definitions: {len(active_behaviors)}")

    print("\n4. Testing query for last 30 days...")
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    try:
        from sqlalchemy.orm import joinedload

        query = BehaviorLog.query.options(joinedload(BehaviorLog.behavior_definition))
        query = query.filter(BehaviorLog.tracked_date >= start_date)
        query = query.filter(BehaviorLog.tracked_date <= end_date)
        query = query.order_by(BehaviorLog.tracked_date.desc())

        logs = query.paginate(page=1, per_page=1000, error_out=False)

        print(f"   ✓ Query successful")
        print(f"   Found {logs.total} logs in date range")
        print(f"   Page: {logs.page}, Per page: {logs.per_page}")

        print("\n5. Testing serialization of paginated results...")
        serialized = [log.to_dict() for log in logs.items]
        print(f"   ✓ Successfully serialized {len(serialized)} logs")

        if serialized:
            print(f"   Sample log: {serialized[0]}")

    except Exception as e:
        print(f"   ❌ Query failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Diagnostic Complete ===")
