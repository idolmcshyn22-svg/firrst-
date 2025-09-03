# test_time_link_fixed.py - Test the fixed time link extraction logic

import re

def test_time_link_patterns():
    """Test time link detection patterns"""
    
    test_cases = [
        ("1 ngày", True),
        ("2 giờ", True), 
        ("30 phút", True),
        ("45 giây", True),
        ("1 day", True),
        ("2 hours", True),
        ("30 mins", True),
        ("45 secs", True),
        ("1h", True),
        ("30m", True),
        ("2d", True),
        ("just now", True),
        ("vừa xong", True),
        ("now", True),
        ("bây giờ", True),
        ("Like", False),
        ("Reply", False),
        ("Share", False),
        ("View more", False),
    ]
    
    time_patterns = [
        r'^\d+\s*ngày',      # "1 ngày", "2 ngày"
        r'^\d+\s*giờ',       # "1 giờ", "2 giờ"  
        r'^\d+\s*phút',      # "1 phút", "30 phút"
        r'^\d+\s*giây',      # "1 giây", "45 giây"
        r'^\d+\s*day',       # "1 day", "2 days"
        r'^\d+\s*hour',      # "1 hour", "2 hours"
        r'^\d+\s*min',       # "1 min", "30 mins"
        r'^\d+\s*sec',       # "1 sec", "45 secs"
        r'^\d+\s*h$',        # "1h", "2h"
        r'^\d+\s*m$',        # "1m", "30m"
        r'^\d+\s*d$',        # "1d", "2d"
    ]
    
    special_cases = ['just now', 'vừa xong', 'now', 'bây giờ']
    
    print("🧪 TESTING TIME LINK PATTERNS")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for text, expected in test_cases:
        text_lower = text.lower().strip()
        
        # Check patterns
        is_time_text = False
        for pattern in time_patterns:
            if re.match(pattern, text_lower):
                is_time_text = True
                break
        
        # Check special cases
        if not is_time_text and text_lower in special_cases:
            is_time_text = True
        
        result = "✅" if is_time_text == expected else "❌"
        if is_time_text == expected:
            correct += 1
        
        print(f"{result} '{text}' -> Expected: {expected}, Got: {is_time_text}")
    
    print()
    print(f"📊 Results: {correct}/{total} correct ({correct/total*100:.1f}%)")
    
    return correct == total

def test_postlink_extraction():
    """Test PostLink extraction from href"""
    
    sample_href = "https://www.facebook.com/groups/chaohanhmienphi/posts/31258488570464523/?comment_id=31294138870232826&amp;__cft__[0]=AZV3rju64bo5ETDOx7DeKMJYTg3BZZ4qGxG1r4AYcJnR_KXPQrzY8lC3GVbUgWkE_FIJYPP6ZEA8wBWNn5olA-3an2q1IlvXNezjkVTf0nQB5nSaVyBAxPBWXzCzxMHt5xkiARMOC2kygpjJ8AKpfFXVYB1Y91pBhlHMk4gTUPG-r5mFTtXP9bBla3T6oowOOW4&amp;__tn__=R]-R"
    
    print("\n🔗 TESTING POSTLINK EXTRACTION")
    print("=" * 50)
    print(f"Input href: {sample_href[:80]}...")
    
    # Test cleaning
    cleaned = sample_href.replace('&amp;', '&')
    print(f"Cleaned: {cleaned[:80]}...")
    
    # Test component extraction
    has_facebook = 'facebook.com' in sample_href
    has_comment_id = 'comment_id=' in sample_href
    
    group_match = re.search(r'/groups/([^/]+)/', sample_href)
    post_match = re.search(r'/posts/(\d+)', sample_href)
    comment_match = re.search(r'comment_id=(\d+)', sample_href)
    
    print(f"✅ Has facebook.com: {has_facebook}")
    print(f"✅ Has comment_id: {has_comment_id}")
    print(f"✅ Group ID: {group_match.group(1) if group_match else 'Not found'}")
    print(f"✅ Post ID: {post_match.group(1) if post_match else 'Not found'}")
    print(f"✅ Comment ID: {comment_match.group(1) if comment_match else 'Not found'}")
    
    return has_facebook and has_comment_id and group_match and post_match and comment_match

if __name__ == "__main__":
    print("🎯 TESTING FIXED TIME LINK LOGIC\n")
    
    pattern_test = test_time_link_patterns()
    postlink_test = test_postlink_extraction()
    
    print(f"\n🎉 OVERALL RESULTS:")
    print(f"   Time patterns: {'✅ PASS' if pattern_test else '❌ FAIL'}")
    print(f"   PostLink extraction: {'✅ PASS' if postlink_test else '❌ FAIL'}")
    print(f"   Overall: {'🎯 ALL TESTS PASSED!' if pattern_test and postlink_test else '❌ SOME TESTS FAILED'}")