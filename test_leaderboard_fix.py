#!/usr/bin/env python3
"""
Test script to verify leaderboard functionality is fixed
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_leaderboard_functions():
    """Test all leaderboard functions"""
    print("🧪 Testing Leaderboard Fix...")
    
    try:
        from database import db
        
        # Test that functions exist
        assert hasattr(db, 'get_leaderboard'), "❌ get_leaderboard function missing"
        assert hasattr(db, 'get_paginated_leaderboard'), "❌ get_paginated_leaderboard function missing"
        assert hasattr(db, 'get_streak_leaderboard'), "❌ get_streak_leaderboard function missing"
        
        print("✅ All leaderboard functions exist")
        
        # Test with sample data
        test_users = [
            {'user_id': 999001, 'xp': 1500, 'coins': 500, 'cookies': 25, 'daily_streak': 7},
            {'user_id': 999002, 'xp': 2200, 'coins': 800, 'cookies': 40, 'daily_streak': 12},
            {'user_id': 999003, 'xp': 900, 'coins': 300, 'cookies': 15, 'daily_streak': 3}
        ]
        
        # Add test data
        for user in test_users:
            result = db.update_user_data(user['user_id'], user)
            assert result, f"❌ Failed to add test user {user['user_id']}"
        
        print("✅ Test data added successfully")
        
        # Test basic leaderboard
        lb = db.get_leaderboard('xp', 5)
        assert isinstance(lb, list), "❌ get_leaderboard should return a list"
        assert len(lb) >= 3, f"❌ Expected at least 3 users, got {len(lb)}"
        
        # Check sorting (highest XP first)
        if len(lb) >= 2:
            assert lb[0].get('xp', 0) >= lb[1].get('xp', 0), "❌ Leaderboard not sorted correctly"
        
        print("✅ Basic leaderboard working")
        
        # Test paginated leaderboard
        paginated = db.get_paginated_leaderboard('coins', 1, 5)
        assert isinstance(paginated, dict), "❌ get_paginated_leaderboard should return a dict"
        assert 'users' in paginated, "❌ Missing 'users' key in paginated result"
        assert 'total_pages' in paginated, "❌ Missing 'total_pages' key in paginated result"
        assert 'total_users' in paginated, "❌ Missing 'total_users' key in paginated result"
        
        print("✅ Paginated leaderboard working")
        
        # Test streak leaderboard
        streak = db.get_streak_leaderboard(1, 5)
        assert isinstance(streak, dict), "❌ get_streak_leaderboard should return a dict"
        assert 'users' in streak, "❌ Missing 'users' key in streak result"
        assert len(streak['users']) >= 3, f"❌ Expected at least 3 users with streaks, got {len(streak['users'])}"
        
        print("✅ Streak leaderboard working")
        
        # Test Discord cog imports
        try:
            from cogs.leveling import Leveling
            print("✅ Leveling cog imports successfully")
        except Exception as e:
            print(f"⚠️ Leveling cog import warning: {e}")
        
        print("\n🎉 ALL LEADERBOARD TESTS PASSED!")
        print("The 'Failed to load leaderboard data' error should be fixed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n🧪 Testing Error Scenarios...")
    
    try:
        from database import db
        
        # Test with empty database
        empty_lb = db.get_paginated_leaderboard('nonexistent_field', 1, 5)
        assert empty_lb['users'] == [], "❌ Should return empty list for nonexistent field"
        assert empty_lb['total_users'] == 0, "❌ Should return 0 total users for empty result"
        
        print("✅ Empty database scenario handled correctly")
        
        # Test with invalid page number
        invalid_page = db.get_paginated_leaderboard('xp', 999, 5)
        assert isinstance(invalid_page, dict), "❌ Should return dict even for invalid page"
        assert invalid_page['current_page'] == 999, "❌ Should preserve requested page number"
        
        print("✅ Invalid page number handled correctly")
        
        print("✅ All error scenarios handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error scenario test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Leaderboard Fix Verification Test")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_leaderboard_functions()
    success &= test_error_scenarios()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 LEADERBOARD FIX SUCCESSFUL!")
        print("✅ Your Discord bot's leaderboard should now work correctly")
        print("✅ No more 'Failed to load leaderboard data' errors")
        sys.exit(0)
    else:
        print("❌ LEADERBOARD FIX FAILED!")
        print("❌ Additional debugging may be needed")
        sys.exit(1)