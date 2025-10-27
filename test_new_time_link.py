# test_new_time_link.py - Test extraction với HTML structure mới

import re

def test_new_html_structure():
    """Test với HTML structure mới của bạn"""
    
    # HTML mới của bạn
    html_new = '''<ul aria-hidden="false" class="html-ul x3ct3a4 xdj266r xyri2b x18d9i69 x1c1uobl x1w5wx5t x78zum5 x1wfe3co xat24cr xdwrcjd x1o1nzlu xyqdw3p"><li class="html-li xdj266r xat24cr xexx8yu xyri2b x18d9i69 x1c1uobl x1rg5ohu x1xegmmw x13fj5qh"><span class="html-span xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x1hl2dhg x16tdsg8 x1vvkbs x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"><div class="html-div xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl"><a attributionsrc="/privacy_sandbox/comet/register/source/?xt=AZWwcy1x-dgeqlGK8T8MartnKsujY6gvF3H7d_qZCWJe6qYhcCPudwBII36Fhejbk4ncPr0LwuCxcM27hC-V6WUJWRkuneeebQ15uW1-cZpLSr71iLhCD1sw7DrnID0dgE0vDWN5dV3F6MPWeItcUGt2BL1Yk1B87B3Uw2EA7C8wIK9h3RsZ90MrhRzk9e2-2Wb-T73iWgt2UxSK3-jK_xi-v7YGbgSlK7XrM-QcTJFrSZjCMq6xJ_WMbqni9yYbCqPrXa2EKb1xPlZMuC4FVa2q2sj3rbUX57CJR7Lolh2gmVgtZ0EnDA1fmvYLp8NXk03gzGvMcqI1kXHDPoJPRzjyI8hy_G4jqjtY-AidO6llQeMN_6YnGZ0j9FT3QUnEUlykDCZ6bVg-EuTEfcNnsdd73_5xYx-1Cj2ryE7VmNg5_H5DsmI6F_-DjatgM4jucoI-qrIY1dt4aTc40yYWBHq293ClxgvdbYc_XjT3Z5K-oBaCz75Bt5LSCeuUhJoUE4vnVfm6D4Ayqpte0lNhDLDbJSP3KTLblwqULS4s7hrUQdlzq_-Rw6mqhgWiO0kVDMN_0daacs-x40IvneAD9ocj3JWB08x_puP4Qc3QnicDi3bAytwSYeBRZcRJ-H67MwqzuoEcnoK6barkxsHAhzcQTFnwwSOgjWAtwL7m6XkjPVmsN9ue954Oq7dZeHMZrzagGtx6pViG9r4F0yWvLy-e_Kabx3kLH-H4lUdNMOLRAqp2y1JO-Mt3tuWW1N3Nj6u_oHUJhJpofW-zPZcX_zCHc8Gjy2dp0c_jOqI0eHWcWCUycxX5XAk7OwpWxtyKAcBJjN33hK7TpIEr_zc5W5kYD4MWIHTPleXJcrCB4CTson3CgS7dqUScu_PjU2jsPGHMaX4c-4lxcg9jMZjRaEr6tcT-7dK9-VekN8LEuCbExcsmkIqNW1miDQ2Ja6Chypj2xYBizO32BuwrpMpVkcdkiJEewHt08uG2TVE_RvlZtNy1rbPFUshH3xkViEv5jxSpIwT43TjH7ZizKEpSDuxeU1MFNfg3Ua38l9oIoVK98-QkfKhH2spZQFo8qlkyZamdqfgVU5zxLN3Ho_AmsssgJVLfmaNcutH3XJquaGDHC0HcysAhgR7rbFFQd3RKBGnNIWbaknyN1teBZtrzdw6SXoWx0vXPxbNa1GjLONY5xA" class="x1i10hfl xjbqb8w x1ejq31n x18oe1m7 x1sy0etr xstzfhl x972fbf x10w94by x1qhh985 x14e42zd x9f619 x1ypdohk xt0psk2 x3ct3a4 xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xkrqix3 x1sur9pj xi81zsa x1s688f" href="https://www.facebook.com/groups/chaohanhmienphi/posts/31258488570464523/?comment_id=31258554110457969&amp;__cft__[0]=AZV5SYjr0nzcKhB3f0b51toERLp6BtKhuvS25PVLXLOvsEkoWYoe4QIWVroKAZACqg2SblriNRUnMRriIrucASczYurcAjuzWeJcNgrXKgKRPcZfJvwH6YfxG1h6FLUwzTXuBX0Z9T0J8Yejr6xLqbzNGY0-xwwNsZoOBdTcWoAZ4HrkmQ8ltlZMjACckoZW29Z3Lrt0UvGzD_6aTWbLWbV3ckX7-j2QUZXEL_oq4izZ1A&amp;__tn__=R]-R" role="link" tabindex="0">4 ngày</a></div></span></li></ul>'''
    
    print("🧪 TESTING NEW HTML STRUCTURE")
    print("=" * 60)
    print(f"HTML: {html_new[:100]}...")
    print()
    
    # Extract href
    href_match = re.search(r'href="([^"]*)"', html_new)
    if href_match:
        href = href_match.group(1)
        print(f"🔗 Raw href: {href[:80]}...")
        
        # Clean HTML entities
        cleaned_href = href.replace('&amp;', '&')
        print(f"🔗 Cleaned href: {cleaned_href[:80]}...")
        
        # Extract text
        text_match = re.search(r'>([^<]+)</a>', html_new)
        if text_match:
            time_text = text_match.group(1).strip()
            print(f"🕐 Time text: '{time_text}'")
            
            # Test time pattern
            time_patterns = [r'^\d+\s*ngày', r'^\d+\s*giờ', r'^\d+\s*phút', r'^\d+\s*day', r'^\d+\s*hour', r'^\d+\s*min']
            
            is_time = False
            for pattern in time_patterns:
                if re.match(pattern, time_text.lower()):
                    is_time = True
                    print(f"✅ Matches time pattern: {pattern}")
                    break
            
            if not is_time:
                print(f"❌ No time pattern matched")
        
        # Test Facebook link components
        has_facebook = 'facebook.com' in href
        has_comment_id = 'comment_id=' in href
        has_groups = '/groups/' in href
        has_posts = '/posts/' in href
        
        print(f"\n📊 Link validation:")
        print(f"   ✅ Has facebook.com: {has_facebook}")
        print(f"   ✅ Has comment_id: {has_comment_id}")
        print(f"   ✅ Has /groups/: {has_groups}")
        print(f"   ✅ Has /posts/: {has_posts}")
        
        is_valid_time_link = has_facebook and has_comment_id and has_groups and has_posts and is_time
        print(f"\n🎯 Is valid time link: {is_valid_time_link}")
        
        if is_valid_time_link:
            # Extract components
            group_match = re.search(r'/groups/([^/]+)/', cleaned_href)
            post_match = re.search(r'/posts/(\d+)', cleaned_href)
            comment_match = re.search(r'comment_id=(\d+)', cleaned_href)
            
            print(f"\n📊 Extracted components:")
            print(f"   Group ID: {group_match.group(1) if group_match else 'Not found'}")
            print(f"   Post ID: {post_match.group(1) if post_match else 'Not found'}")
            print(f"   Comment ID: {comment_match.group(1) if comment_match else 'Not found'}")
            print(f"\n🎯 FINAL PostLink: {cleaned_href}")
            
            return True
        else:
            print(f"\n❌ Not a valid time link")
            return False
    else:
        print("❌ Could not extract href")
        return False

def test_uid_extraction_patterns():
    """Test enhanced UID extraction patterns"""
    
    test_urls = [
        ("https://www.facebook.com/profile.php?id=123456789", "123456789"),
        ("https://www.facebook.com/user.php?id=987654321", "987654321"),
        ("https://www.facebook.com/username", "username:username"),
        ("https://www.facebook.com/john.doe", "username:john.doe"),
        ("https://www.facebook.com/user/555666777", "555666777"),
        ("https://m.facebook.com/profile.php?id=111222333", "111222333"),
    ]
    
    print("\n🆔 TESTING UID EXTRACTION PATTERNS")
    print("=" * 50)
    
    uid_patterns = [
        r'profile\.php\?id=(\d+)',
        r'user\.php\?id=(\d+)',
        r'/user/(\d+)',
        r'[?&]id=(\d+)',
        r'facebook\.com/profile\.php\?id=(\d+)',
        r'facebook\.com/([^/?&]+)/?$',
        r'facebook\.com/([^/?&]+)/?[?&]',
        r'(\d{10,})',
        r'/(\d{8,})',
    ]
    
    correct = 0
    total = len(test_urls)
    
    for url, expected in test_urls:
        print(f"\n🔍 Testing: {url}")
        print(f"   Expected: {expected}")
        
        extracted_uid = "Unknown"
        
        for pattern_idx, pattern in enumerate(uid_patterns, 1):
            try:
                uid_match = re.search(pattern, url)
                if uid_match:
                    potential_uid = uid_match.group(1)
                    
                    if potential_uid.isdigit() and len(potential_uid) >= 8:
                        extracted_uid = potential_uid
                        print(f"   ✅ UID found with pattern {pattern_idx}: {extracted_uid}")
                        break
                    elif not potential_uid.isdigit() and len(potential_uid) >= 3:
                        extracted_uid = f"username:{potential_uid}"
                        print(f"   ✅ Username found with pattern {pattern_idx}: {potential_uid}")
                        break
                        
            except Exception as e:
                continue
        
        result = "✅" if extracted_uid == expected else "❌"
        if extracted_uid == expected:
            correct += 1
        
        print(f"   {result} Got: {extracted_uid}")
    
    print(f"\n📊 UID Results: {correct}/{total} correct ({correct/total*100:.1f}%)")
    return correct == total

if __name__ == "__main__":
    print("🎯 TESTING ENHANCED TIME LINK & UID EXTRACTION\n")
    
    html_test = test_new_html_structure()
    uid_test = test_uid_extraction_patterns()
    
    print(f"\n🎉 OVERALL RESULTS:")
    print(f"   HTML structure: {'✅ PASS' if html_test else '❌ FAIL'}")
    print(f"   UID extraction: {'✅ PASS' if uid_test else '❌ FAIL'}")
    print(f"   Overall: {'🎯 ALL TESTS PASSED!' if html_test and uid_test else '❌ SOME TESTS FAILED'}")