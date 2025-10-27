# test_time_link_extraction.py - Test extraction of PostLink from time links

import re

def test_time_link_extraction():
    """Test extraction of PostLink from time link HTML"""
    
    # Your example HTML
    html_example = '''<a attributionsrc="/privacy_sandbox/comet/register/source/?xt=AZVfUNN2ENP91W-iR6KIBQ6BlASZR1usbE2keC6wd28JQ-Fnssna70VNi7rc3Msr63vjVyRzBM0PV94hq0nXUdTaeMzLubv_VGk_fKncKthmMBLx5GOs_gZyISxd04V9qHFXk-8x60jkXku-hMBz2Q8wHVXRsUUFIVJZ9rL98FWlDBIgkJCygP8Byp-aDzFsRn-ZRT5UwaFrPOO03r9pQp7_r0FSc-76bv4gheLRwTj4TkY8W9XsdE9fqJ_jAGMtPmujneUt0ht5MeWQ8CDGweY9AylRBkanyOhegMsA6i2s4dQYMEzP0G15tIsv1ZiiC6e7n_poup7BEfD1fNbVxbecuU4hOVDFx3JXKkPiAjYuKwZXnphn3JIZsPTlnlhSmpkxNNBp4waK03O3IyyQdp1Qx_3lOjkXuXwuD3xumtEq1ZiJiNcEICY5F-wV9qNHqI3mC8OuWI_jrraO42o5WAAN3jd2ib3_WJ1_9D9uXmDXfucHqKxBMJg4oX84cQheqj6UFXq910lz2QQ4Ax5hFA4en-2xu5bmH6H81L_47CMVGvGag6QNF0nDL0TEkwZQGBFITehZJY84iilTF4vcn8Qgsm9mU-IQTJ5XnMtvfAxB9KaTqg20lsurKujFi_JagKufWlJxwm248IZdcje0xFYRsmP9rMgAjB9MMdXDddcf4XwY1gP0tWFEMBQMV2K6bV945uhsENF5yQKX0L4AiwT8PIvn69Dfzx6wkVz6MkiIq_IwLZFr6fnWy4YgFi0XAHMSvYFpJEt1F-vOEw3m16qy81sw8KUZultqwKBEWDywV03Axj9msV3rYPkmMqUiUTIpQCXiC4WCpTUMWIOXCEhqL78LK195NKD57il3B-81kZHTgDSBosaaoNkrE5bFf1CvbjOWhfBZXbvCh14Rco8itX1P-dL-L3OCbb_0_qlv1-bQ_B_-r1bL_VeKYkbdCEhr1pCSkovCYdL5PN-RZ6Yr8hlPQaS-dVwPVMgiR84179tOWP_nlq-Hgj5Ch4G5Cet4xrhK5JD4j6d6mcnTcwW6ExVbmuETwNKDiGolmgf0ow" class="x1i10hfl xjbqb8w x1ejq31n x18oe1m7 x1sy0etr xstzfhl x972fbf x10w94by x1qhh985 x14e42zd x9f619 x1ypdohk xt0psk2 x3ct3a4 xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xkrqix3 x1sur9pj xi81zsa x1s688f" href="https://www.facebook.com/groups/chaohanhmienphi/posts/31258488570464523/?comment_id=31294138870232826&__cft__[0]=AZV3rju64bo5ETDOx7DeKMJYTg3BZZ4qGxG1r4AYcJnR_KXPQrzY8lC3GVbUgWkE_FIJYPP6ZEA8wBWNn5olA-3an2q1IlvXNezjkVTf0nQB5nSaVyBAxPBWXzCzxMHt5xkiARMOC2kygpjJ8AKpfFXVYB1Y91pBhlHMk4gTUPG-r5mFTtXP9bBla3T6oowOOW4&__tn__=R]-R" role="link" tabindex="0">1 ngày</a>'''
    
    print("🧪 TESTING TIME LINK EXTRACTION")
    print("=" * 60)
    print(f"HTML: {html_example[:100]}...")
    print()
    
    # Extract href
    href_match = re.search(r'href="([^"]*)"', html_example)
    if href_match:
        href = href_match.group(1)
        # Decode HTML entities
        href = href.replace('&amp;', '&')
        print(f"🔗 Extracted href: {href}")
        
        # Extract components
        group_match = re.search(r'/groups/([^/]+)/', href)
        post_match = re.search(r'/posts/(\d+)', href)
        comment_match = re.search(r'comment_id=(\d+)', href)
        
        print(f"📊 Components:")
        print(f"   Group: {group_match.group(1) if group_match else 'Not found'}")
        print(f"   Post: {post_match.group(1) if post_match else 'Not found'}")
        print(f"   Comment: {comment_match.group(1) if comment_match else 'Not found'}")
        
        # Extract text
        text_match = re.search(r'>([^<]+)</a>', html_example)
        if text_match:
            text = text_match.group(1)
            print(f"🕐 Time text: '{text}'")
            
            # Test time pattern
            is_time = re.match(r'^\d+\s*(ngày|giờ|phút|giây|day|hour|min|sec|h|m|d)', text.lower())
            print(f"✅ Is time pattern: {bool(is_time)}")
        
        print()
        print(f"🎯 FINAL PostLink: {href}")
        
    else:
        print("❌ Could not extract href")

if __name__ == "__main__":
    test_time_link_extraction()