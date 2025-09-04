# fb_groups_scraper_focused.py - Focus on larger height element

import time, random, threading, re, requests, pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ----------------------------
# Helper utils
# ----------------------------

def parse_cookies_to_list(cookie_str):
    cookies_list = []
    for pair in cookie_str.split(';'):
        pair = pair.strip()
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies_list.append({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
    return cookies_list

def parse_cookies_to_dict(cookie_str):
    d = {}
    for pair in cookie_str.split(';'):
        pair = pair.strip()
        if '=' in pair:
            name, value = pair.split('=', 1)
            d[name.strip()] = value.strip()
    return d

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip())
    ui_patterns = [
        r'\b(Like|Reply|Share|Comment|Translate|Hide|Report|Block)\b',
        r'\b(Thích|Trả lời|Chia sẻ|Bình luận|Dịch|Ẩn|Báo cáo|Chặn)\b',
        r'\b\d+\s*(min|minutes?|hours?|days?|seconds?|phút|giờ|ngày|giây)\s*(ago|trước)?\b',
        r'\b(Top fan|Most relevant|Newest|All comments|Bình luận hàng đầu)\b'
    ]
    for pattern in ui_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text.strip()

def extract_uid_from_profile_url(profile_url):
    """
    Extract UID từ Facebook profile URL
    Args:
        profile_url (str): URL profile Facebook
    Returns:
        str: UID hoặc "Unknown"
    """
    if not profile_url:
        return "Unknown"
    
    try:
        # Các pattern để extract UID từ URL
        uid_patterns = [
            r'profile\.php\?id=(\d+)',
            r'user\.php\?id=(\d+)', 
            r'/user/(\d+)',
            r'id=(\d+)',
            r'facebook\.com/profile\.php\?id=(\d+)',
            r'facebook\.com/(\d{10,})',  # Direct UID in URL
            r'(\d{10,})'  # Facebook UIDs thường có 10+ chữ số
        ]
        
        for pattern in uid_patterns:
            match = re.search(pattern, profile_url)
            if match:
                uid = match.group(1)
                if len(uid) >= 10:  # Validate UID length
                    print(f"    ✅ Extracted UID from URL: {uid}")
                    return uid
        
        # Nếu URL có dạng facebook.com/username, thử extract username
        username_match = re.search(r'facebook\.com/([^/?]+)', profile_url)
        if username_match:
            username = username_match.group(1)
            if not username.isdigit() and len(username) > 2:
                print(f"    🔄 Found username in URL: {username}, will try to resolve to UID")
                return f"username:{username}"  # Đánh dấu để xử lý sau
        
        return "Unknown"
        
    except Exception as e:
        print(f"    ⚠️ Error extracting UID from URL: {e}")
        return "Unknown"

def get_uid_from_username(username, cookies_dict=None, driver=None):
    """
    Lấy UID Facebook từ username
    Args:
        username (str): Username Facebook (có thể có hoặc không có facebook.com/)
        cookies_dict (dict): Dictionary cookies để authenticate
        driver: Selenium WebDriver instance (optional, để sử dụng session hiện tại)
    Returns:
        str: UID Facebook hoặc "Unknown" nếu không tìm thấy
    """
    if not username or username == "Unknown":
        return "Unknown"
    
    try:
        # Chuẩn hóa username
        clean_username = username.strip()
        if clean_username.startswith('https://'):
            # Nếu là URL đầy đủ, extract username
            if 'facebook.com/' in clean_username:
                clean_username = clean_username.split('facebook.com/')[-1].split('?')[0].split('/')[0]
        
        print(f"  🔍 Attempting to get UID for username: {clean_username}")
        
        # Method 1: Sử dụng Selenium driver nếu có sẵn (nhanh hơn và đáng tin cậy hơn)
        if driver:
            try:
                print(f"    🌐 Using Selenium driver to resolve UID...")
                
                # Tạo URL profile
                profile_url = f"https://www.facebook.com/{clean_username}"
                
                # Lưu current URL để restore sau
                current_url = driver.current_url
                
                # Navigate to profile
                driver.get(profile_url)
                time.sleep(3)
                
                # Check if redirected to profile.php?id= format
                final_url = driver.current_url
                print(f"    📍 Final URL: {final_url}")
                
                # Extract UID from final URL
                uid_match = re.search(r'profile\.php\?id=(\d+)', final_url)
                if uid_match:
                    uid = uid_match.group(1)
                    print(f"    ✅ Found UID via Selenium: {uid}")
                    
                    # Restore original URL
                    driver.get(current_url)
                    time.sleep(2)
                    
                    return uid
                
                # Tìm UID trong page source
                page_source = driver.page_source
                uid_patterns = [
                    r'"entity_id":"(\d+)"',
                    r'"userID":"(\d+)"',
                    r'"user_id":"(\d+)"',
                    r'"profile_id":"(\d+)"',
                    r'"actorID":"(\d+)"',
                    r'"pageID":"(\d+)"'
                ]
                
                for pattern in uid_patterns:
                    matches = re.findall(pattern, page_source)
                    if matches:
                        uid = matches[0]
                        if len(uid) >= 10:
                            print(f"    ✅ Found UID in page source: {uid}")
                            
                            # Restore original URL
                            driver.get(current_url)
                            time.sleep(2)
                            
                            return uid
                
                # Restore original URL
                driver.get(current_url)
                time.sleep(2)
                
            except Exception as e:
                print(f"    ⚠️ Selenium method failed: {e}")
                # Restore original URL nếu có lỗi
                try:
                    driver.get(current_url)
                    time.sleep(1)
                except:
                    pass
        
        # Method 2: Sử dụng requests (fallback)
        print(f"    🌐 Using requests to resolve UID...")
        
        # Tạo URL profile từ username
        profile_urls = [
            f"https://www.facebook.com/{clean_username}",
            f"https://m.facebook.com/{clean_username}",
            f"https://mbasic.facebook.com/{clean_username}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Thêm cookies nếu có
        if cookies_dict:
            cookie_string = '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])
            headers['Cookie'] = cookie_string
        
        for url in profile_urls:
            try:
                print(f"    🔍 Trying to get UID from: {url}")
                
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Tìm UID trong response
                    uid_patterns = [
                        r'"entity_id":"(\d+)"',
                        r'"userID":"(\d+)"',
                        r'"user_id":"(\d+)"',
                        r'"id":"(\d+)"',
                        r'profile\.php\?id=(\d+)',
                        r'user\.php\?id=(\d+)',
                        r'"profile_id":"(\d+)"',
                        r'entity_id=(\d+)',
                        r'profile_owner":"(\d+)"',
                        r'"pageID":"(\d+)"',
                        r'data-profileid="(\d+)"',
                        r'data-userid="(\d+)"',
                        r'"actorID":"(\d+)"',
                        r'"target_id":"(\d+)"'
                    ]
                    
                    for pattern in uid_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            # Lấy UID đầu tiên tìm thấy (thường là UID chính xác nhất)
                            uid = matches[0]
                            # Validate UID (Facebook UID thường có ít nhất 10 chữ số)
                            if len(uid) >= 10 and uid.isdigit():
                                print(f"    ✅ Found UID: {uid} using pattern: {pattern}")
                                return uid
                    
                    # Fallback: tìm trong redirected URL
                    if 'profile.php?id=' in response.url:
                        uid_match = re.search(r'profile\.php\?id=(\d+)', response.url)
                        if uid_match:
                            uid = uid_match.group(1)
                            print(f"    ✅ Found UID from redirect URL: {uid}")
                            return uid
                
            except requests.RequestException as e:
                print(f"    ⚠️ Request failed for {url}: {e}")
                continue
            except Exception as e:
                print(f"    ⚠️ Error processing {url}: {e}")
                continue
        
        print(f"    ❌ Could not find UID for username: {username}")
        return "Unknown"
        
    except Exception as e:
        print(f"❌ Error in get_uid_from_username: {e}")
        return "Unknown"

# ----------------------------
# FOCUSED Facebook Groups Scraper
# ----------------------------

class FacebookGroupsScraper:
    def __init__(self, cookie_str, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Better user agent for modern Facebook
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 15)
        self.cookie_str = cookie_str or ""
        self.cookies_list = parse_cookies_to_list(self.cookie_str)
        self.cookies_dict = parse_cookies_to_dict(self.cookie_str)
        self._stop_flag = False
        self.current_layout = None
        
        if self.cookies_list:
            self._login_with_cookies()

    def _login_with_cookies(self):
        # Start with regular Facebook for better groups access
        self.driver.get("https://www.facebook.com")
        time.sleep(3)
        
        for c in self.cookies_list:
            cookie = c.copy()
            cookie.pop('sameSite', None)
            cookie.pop('httpOnly', None) 
            cookie.pop('secure', None)
            cookie.setdefault('domain', '.facebook.com')
            try:
                self.driver.add_cookie(cookie)
            except: 
                pass
        
        self.driver.get("https://www.facebook.com")
        time.sleep(4)

    def load_post(self, post_url):
        print(f"Loading groups post: {post_url}")
        
        urls_to_try = []
        
        if "groups/" in post_url:
            # Try www first for groups, then mobile, then mbasic
            www_url = post_url.replace("mbasic.facebook.com", "www.facebook.com").replace("m.facebook.com", "www.facebook.com")
            mobile_url = post_url.replace("www.facebook.com", "m.facebook.com").replace("mbasic.facebook.com", "m.facebook.com")
            mbasic_url = post_url.replace("www.facebook.com", "mbasic.facebook.com").replace("m.facebook.com", "mbasic.facebook.com")
            
            urls_to_try = [www_url, mobile_url, mbasic_url]
        else:
            urls_to_try = [post_url]
        
        for url_attempt in urls_to_try:
            try:
                print(f"Trying URL: {url_attempt}")
                self.driver.get(url_attempt)
                time.sleep(6)
                
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                print(f"Current URL: {current_url}")
                print(f"Page title: {page_title}")
                
                # Detect layout
                if "m.facebook.com" in current_url:
                    self.current_layout = "mobile"
                elif "mbasic.facebook.com" in current_url:
                    self.current_layout = "mbasic"
                else:
                    self.current_layout = "www"
                
                print(f"Detected layout: {self.current_layout}")
                
                # Check login status
                if any(keyword in page_title.lower() for keyword in ["log in", "login", "đăng nhập"]):
                    print("❌ Not logged in with this URL, trying next...")
                    continue
                
                print(f"✅ Successfully loaded groups post with {self.current_layout} layout")
                
                # Try to switch to "All comments" view
                self._switch_to_all_comments()

                # Try to click "View more comments" button
                self._click_view_more()
                
                return True
                    
            except Exception as e:
                print(f"Failed to load {url_attempt}: {e}")
                continue
        
        print("❌ Failed to load post with any URL variant")
        return False

    def clear_page_cache(self):
        """Clear page cache and force reload to ensure fresh DOM"""
        try:
            print("🧹 Clearing page cache...")
            
            # Clear browser cache
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            
            # Force page refresh
            self.driver.refresh()
            time.sleep(5)  # Wait for fresh load
            
            print("✅ Page cache cleared and refreshed")
            
        except Exception as e:
            print(f"⚠️ Error clearing cache: {e}")

    def _switch_to_all_comments(self):
        """Switch to 'All comments' view to get more comments"""
        print("🔄 Attempting to switch to 'All comments' view...")
        
        try:
            time.sleep(3)
            
            # Enhanced selectors for all comments button
            all_comments_selectors = [
                # Vietnamese selectors
                "//span[contains(text(),'Tất cả bình luận')]",
                "//div[contains(text(),'Tất cả bình luận')]",
                "//a[contains(text(),'Tất cả bình luận')]",
                "//button[contains(text(),'Tất cả bình luận')]",
                
                # English selectors
                "//span[contains(text(),'All comments')]",
                "//div[contains(text(),'All comments')]",
                "//a[contains(text(),'All comments')]",
                "//button[contains(text(),'All comments')]",
                
                # Role-based selectors
                "//div[@role='button' and (contains(text(),'Tất cả') or contains(text(),'All'))]",
                "//span[@role='button' and (contains(text(),'Tất cả') or contains(text(),'All'))]",
                
                # Aria-label selectors
                "//div[contains(@aria-label,'comment') and contains(text(),'All')]",
                "//div[contains(@aria-label,'bình luận') and contains(text(),'Tất cả')]"
            ]
            
            clicked = False
            self.all_comments_button = None  # Store the button for later use
            
            for selector in all_comments_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"  Found 'All comments' button: {element.text}")
                            
                            # Store the button for later use
                            self.all_comments_button = element
                            
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                            time.sleep(1)
                            
                            # Try to click
                            try:
                                element.click()
                                clicked = True
                                print("  ✅ Successfully clicked 'All comments' button")
                                time.sleep(4)  # Wait for comments to load
                                break
                            except:
                                # Try JavaScript click
                                try:
                                    self.driver.execute_script("arguments[0].click();", element)
                                    clicked = True
                                    print("  ✅ Successfully clicked 'All comments' button (JS)")
                                except:
                                    continue

                            # Click on div with role="menuitem" and tabindex="0"
                            try:
                                menuitem_element = self.driver.find_element(By.XPATH, "//div[@role='menuitem' and @tabindex='0']")
                                self.driver.execute_script("arguments[0].click();", menuitem_element)
                                print("  ✅ Successfully clicked menuitem div")
                                time.sleep(2)  # Wait for any menu actions to complete
                            except Exception as e:
                                print(f"  ⚠️ Could not find or click menuitem div: {e}")
                            
                            time.sleep(4)
                            break
                    
                    if clicked:
                        break
                        
                except Exception as e:
                    continue
            
            if not clicked:
                print("  ⚠️ Could not find or click 'All comments' button, proceeding with current view")
            else:
                print("  🎯 Switched to 'All comments' view successfully")
                
        except Exception as e:
            print(f"  ⚠️ Error switching to 'All comments' view: {e}")
            print("  Proceeding with current view...")

    def _click_view_more(self):
        """Click on 'View more comments' button to load more comments"""
        print("🔄 Attempting to click 'View more comments' button...")
        
        try:
            time.sleep(3)
            
            # Enhanced selectors for view more button
            view_more_selectors = [
                "//div[contains(text(),'View more comments')]",
                "//button[contains(text(),'View more comments')]",
                "//a[contains(text(),'View more comments')]",
                "//span[contains(text(),'View more comments')]"
            ]

            clicked = False
            for selector in view_more_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"  Found 'View more comments' button: {element.text}")
                            
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                            time.sleep(1)
                            
                            # Try to click
                            try:
                                element.click()
                                clicked = True
                                print("  ✅ Successfully clicked 'View more comments' button")
                                time.sleep(4)  # Wait for comments to load
                                break
                            except:
                                # Try JavaScript click
                                try:
                                    self.driver.execute_script("arguments[0].click();", element)
                                    clicked = True
                                    print("  ✅ Successfully clicked 'View more comments' button (JS)")
                                    
                                    time.sleep(4)
                                    break
                                except:
                                    continue
                    
                    if clicked:
                        break
                        
                except Exception as e:
                    continue
            
            if not clicked:
                print("  ⚠️ Could not find or click 'View more comments' button, proceeding with current view")
            else:
                print("  🎯 Switched to 'View more comments' view successfully")
                
        except Exception as e:
            print(f"  ⚠️ Error switching to 'View more comments' view: {e}")
            print("  Proceeding with current view...")

    def is_comment_div(self, div_element):
        """Check if a div element contains comment-like content"""
        try:
            # Get text content
            text = div_element.text.strip()
            if len(text) < 10:  # Too short to be a meaningful comment
                return False
            
            # Check for profile links (common in comments)
            profile_links = div_element.find_elements(By.XPATH, ".//a[contains(@href, 'profile') or contains(@href, 'user') or contains(@href, 'facebook.com/')]")
            if profile_links:
                return True
            
            # Check for comment-specific attributes
            aria_label = div_element.get_attribute('aria-label') or ''
            if 'comment' in aria_label.lower() or 'bình luận' in aria_label.lower():
                return True
            
            # Check for comment-specific classes
            class_attr = div_element.get_attribute('class') or ''
            if any(keyword in class_attr.lower() for keyword in ['comment', 'reply', 'response']):
                return True
            
            # Check for comment-specific data attributes
            data_ft = div_element.get_attribute('data-ft') or ''
            if 'comment' in data_ft.lower():
                return True
            
            # Check for role attribute
            role = div_element.get_attribute('role') or ''
            if role == 'article':
                return True
            
            # Check for comment ID patterns
            element_id = div_element.get_attribute('id') or ''
            if 'comment' in element_id.lower():
                return True
            
            # Check for time elements (comments often have timestamps)
            time_elements = div_element.find_elements(By.XPATH, ".//time | .//span[contains(@class, 'time')] | .//a[contains(@class, 'time')]")
            if time_elements:
                return True
            
            # Check for like/reply buttons (common in comments)
            action_buttons = div_element.find_elements(By.XPATH, ".//*[contains(text(), 'Like') or contains(text(), 'Reply') or contains(text(), 'Thích') or contains(text(), 'Trả lời')]")
            if action_buttons:
                return True
            
            # Check for reasonable text length and structure
            if len(text) > 20 and ('@' in text or '.' in text or '!' in text or '?' in text):
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking if div is comment: {e}")
            return False

    def extract_groups_comments(self):
        """FOCUSED comment extraction targeting larger height container"""
        print(f"=== EXTRACTING GROUPS COMMENTS (FOCUSED) ===")

        # Find "All comments" button's parent with class html-div
        try:
            # Use the all_comments_button from _switch_to_all_comments if available
            all_comments_button = getattr(self, 'all_comments_button', None)
            
            if not all_comments_button:
                print("⚠️ No 'All comments' button found from previous method, searching again...")
                # Look for "All comments" button with various possible text variations
                all_comments_selectors = [
                    "//button[contains(text(), 'All comments')]",
                    "//a[contains(text(), 'All comments')]",
                    "//span[contains(text(), 'All comments')]",
                    "//div[contains(text(), 'All comments')]",
                    "//*[contains(text(), 'View all comments')]",
                    "//*[contains(text(), 'See all comments')]",
                    "//*[contains(text(), 'Show all comments')]"
                ]
                
                for selector in all_comments_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            all_comments_button = elements[0]
                            print(f"✅ Found 'All comments' button using selector: {selector}")
                            break
                    except Exception as e:
                        continue
            else:
                print("✅ Using 'All comments' button from _switch_to_all_comments method")
            
            if all_comments_button:
                # Find the parent with class html-div
                parent_with_html_div = None
                
                # Method 1: Get the closest parent with class containing 'html-div'
                try:
                    closest_parent = all_comments_button.find_element(By.XPATH, "ancestor::*[contains(@class, 'html-div')][1]")
                    if closest_parent:
                        parent_with_html_div = closest_parent
                        print("✅ Found closest parent with html-div class")
                except:
                    pass
                
                # Method 2: Look for immediate parent with class containing 'html-div' (fallback)
                if not parent_with_html_div:
                    try:
                        parent = all_comments_button.find_element(By.XPATH, "./..")
                        if 'html-div' in parent.get_attribute('class') or 'html-div' in parent.get_attribute('className'):
                            parent_with_html_div = parent
                            print("✅ Found parent with html-div class (immediate parent)")
                    except:
                        pass
                
                # Method 3: Look for any ancestor with class containing 'html-div' (fallback)
                if not parent_with_html_div:
                    try:
                        ancestors = all_comments_button.find_elements(By.XPATH, "ancestor::*[contains(@class, 'html-div')]")
                        if ancestors:
                            parent_with_html_div = ancestors[0]
                            print("✅ Found parent with html-div class (ancestor)")
                    except:
                        pass
                
                # Method 4: Look for any div with class containing 'html-div' that contains the button (fallback)
                if not parent_with_html_div:
                    try:
                        # More efficient: search only in the document body
                        html_div_containers = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'html-div')]")
                        for container in html_div_containers:
                            try:
                                # Check if the button is a descendant of this container
                                if container.find_element(By.XPATH, f".//*[contains(@text, '{all_comments_button.text}') or contains(@aria-label, '{all_comments_button.text}')]"):
                                    parent_with_html_div = container
                                    print("✅ Found parent with html-div class (container fallback)")
                                    break
                            except:
                                continue
                    except:
                        pass
                
                if parent_with_html_div:
                    print(f"✅ Successfully found 'All comments' button's parent with html-div class")
                    print(f"   Parent tag: {parent_with_html_div.tag_name}")
                    print(f"   Parent class: {parent_with_html_div.get_attribute('class')}")
                    
                    # Get comment parent divs that come after the "All comments" parent_with_html_div
                    print("🔍 Searching for comment parent divs after 'All comments' parent...")
                    
                    comment_parent_divs = []
                    
                    # Method 1: Find the next div that comes immediately after the parent_with_html_div
                    try:
                        # Get only the next div that is a sibling of the parent_with_html_div
                        next_div = parent_with_html_div.find_element(By.XPATH, "./following-sibling::div[1]")
                        print(f"Found next div after parent_with_html_div")
                        print(f"Next div class: {next_div.get_attribute('class')}")
                        
                        # Find and click "View more comments" button until no more comments
                        print("🔄 Starting 'View more comments' click loop...")
                        previous_comment_count = 0
                        no_new_comments_count = 0
                        max_no_new_comments = 3  # Stop after 3 consecutive checks with no new comments
                        
                        while no_new_comments_count < max_no_new_comments:
                            # Look for "View more comments" button
                            view_more_selectors = [
                                "//button[contains(text(), 'View more comments')]",
                                "//a[contains(text(), 'View more comments')]",
                                "//span[contains(text(), 'View more comments')]",
                                "//div[contains(text(), 'View more comments')]",
                                "//*[contains(text(), 'View more')]",
                                "//*[contains(text(), 'Show more comments')]",
                                "//*[contains(text(), 'Load more comments')]",
                                "//*[contains(text(), 'See more comments')]",
                                "//button[contains(@aria-label, 'View more comments')]",
                                "//a[contains(@aria-label, 'View more comments')]"
                            ]
                            
                            view_more_button = None
                            for selector in view_more_selectors:
                                try:
                                    elements = self.driver.find_elements(By.XPATH, selector)
                                    if elements:
                                        view_more_button = elements[0]
                                        print(f"✅ Found 'View more comments' button using selector: {selector}")
                                        break
                                except Exception as e:
                                    continue
                            
                            if view_more_button:
                                try:
                                    # Click the "View more comments" button
                                    self.driver.execute_script("arguments[0].click();", view_more_button)
                                    print("🖱️ Clicked 'View more comments' button")
                                except Exception as e:
                                    print(f"⚠️ Error clicking 'View more comments' button: {e}")
                                    # Try alternative click method
                                    try:
                                        view_more_button.click()
                                        print("🖱️ Clicked 'View more comments' button (alternative method)")
                                    except Exception as e2:
                                        print(f"⚠️ Alternative click also failed: {e2}")
                                        break
                            else:
                                print("⚠️ No 'View more comments' button found")
                                no_new_comments_count += 1
                                print(f"⚠️ No new comments button detected ({no_new_comments_count}/{max_no_new_comments})")
                                break
                            
                            # Wait 5 seconds for new comments to load
                            print("⏳ Waiting 5 seconds for new comments to load...")
                            time.sleep(5)
                            
                            # Count current comments
                            current_comment_divs = []
                            next_div_children = next_div.find_elements(By.XPATH, "./div")
                            for child in next_div_children:
                                if self.is_comment_div(child):
                                    print(f"✅ Found comment div: {child.text}")
                                    current_comment_divs.append(child)
                            
                            current_comment_count = len(current_comment_divs)
                            print(f"📊 Current comment count: {current_comment_count} (previous: {previous_comment_count})")
                            
                            # Check if new comments were loaded
                            if current_comment_count > previous_comment_count:
                                print(f"✅ New comments detected! (+{current_comment_count - previous_comment_count})")
                                previous_comment_count = current_comment_count
                                no_new_comments_count = 0  # Reset counter
                            else:
                                no_new_comments_count += 1
                                print(f"⚠️ No new comments detected ({no_new_comments_count}/{max_no_new_comments})")
                            
                            # Check for stop flag
                            if self._stop_flag:
                                print("⏹️ Stop flag detected, breaking click loop")
                                break
                        
                        print(f"🏁 Click loop completed. Final comment count: {current_comment_count}")
                        
                        # Use the final comment divs
                        comment_parent_divs = current_comment_divs
                        print(f"🎯 Final comment divs found: {len(comment_parent_divs)}")

                        if len(comment_parent_divs) > 0:
                            print(f"🎯 Found {len(comment_parent_divs)} comment divs in next_div children")
                            # Extract comment data from the found divs
                            comments_data = []
                            seen_content = set()
                            
                            for i, element in enumerate(comment_parent_divs):
                                if self._stop_flag:
                                    break
                                    
                                try:
                                    print(f"\n--- Processing comment div {i+1}/{len(comment_parent_divs)} ---")
                                    
                                    comment_data = self.extract_comment_data_focused(element, i)
                                    
                                    if not comment_data:
                                        continue
                                    
                                    # Deduplication
                                    if comment_data['Name'] == "Unknown":
                                        print("  ✗ Skipped: no username found")
                                        continue
                                        
                                    # Check for duplicates
                                    content_signature = f"{comment_data['Name']}_{comment_data['ProfileLink']}"
                                    if content_signature in seen_content:
                                        print("  ✗ Skipped: duplicate user")
                                        continue
                                    seen_content.add(content_signature)
                                    
                                    comment_data['Type'] = 'Comment'
                                    comment_data['Layout'] = self.current_layout
                                    comment_data['Source'] = 'All Comments Container'
                                    
                                    comments_data.append(comment_data)
                                    print(f"  ✅ Added: {comment_data['Name']} - Profile: {comment_data['ProfileLink'][:50]}...")
                                    
                                except Exception as e:
                                    print(f"  Error processing comment div {i}: {e}")
                                    continue
                            
                            print(f"\n=== EXTRACTION COMPLETE: {len(comments_data)} comments ===")
                            return comments_data
                            
                    except Exception as e:
                        print(f"Error finding next div: {e}")
                    
                    print(f"🎯 Total comment parent divs found after 'All comments': {len(comment_parent_divs)}")
                    # Extract comment data from the found divs
                    comments_data = []
                    seen_content = set()
                    
                    for i, element in enumerate(comment_parent_divs):
                        if self._stop_flag:
                            break
                            
                        try:
                            print(f"\n--- Processing comment div {i+1}/{len(comment_parent_divs)} ---")
                            
                            comment_data = self.extract_comment_data_focused(element, i)
                            
                            if not comment_data:
                                continue
                            
                            # Deduplication
                            if comment_data['Name'] == "Unknown":
                                print("  ✗ Skipped: no username found")
                                continue
                                
                            # Check for duplicates
                            content_signature = f"{comment_data['Name']}_{comment_data['ProfileLink']}"
                            if content_signature in seen_content:
                                print("  ✗ Skipped: duplicate user")
                                continue
                            seen_content.add(content_signature)
                            
                            comment_data['Type'] = 'Comment'
                            comment_data['Layout'] = self.current_layout
                            comment_data['Source'] = 'All Comments Container'
                            
                            comments_data.append(comment_data)
                            print(f"  ✅ Added: {comment_data['Name']} - Profile: {comment_data['ProfileLink'][:50]}...")
                            
                        except Exception as e:
                            print(f"  Error processing comment div {i}: {e}")
                            continue
                    
                    print(f"\n=== EXTRACTION COMPLETE: {len(comments_data)} comments ===")
                    return comments_data
                else:
                    print("❌ Could not find parent with html-div class for 'All comments' button")
                    
            else:
                print("❌ Could not find 'All comments' button")
                
        except Exception as e:
            print(f"❌ Error while searching for 'All comments' button's parent: {e}")
        
        # Save page for debugging
        try:
            with open(f"debug_focused_{self.current_layout}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Saved page to debug_focused_{self.current_layout}.html")
        except:
            pass
        
        # FOCUSED: Search within the target container first
        all_comment_elements = []
        
        print("🎯 Searching within target container...")
        
        # Strategy 1: Layout-specific selectors within target container
        if self.current_layout == "www":
            selectors = [
                ".//div[@role='article']",
                ".//div[contains(@aria-label, 'Comment by')]",
                ".//div[contains(@aria-label, 'Bình luận của')]",
                ".//div[.//a[contains(@href, '/user/') or contains(@href, '/profile/')]]",
                ".//div[.//h3//a[contains(@href, 'facebook.com')]]"
            ]
        elif self.current_layout == "mobile":
            selectors = [
                ".//div[@data-sigil='comment']",
                ".//div[contains(@data-ft, 'comment')]",
                ".//div[contains(@id, 'comment_')]",
                ".//div[.//a[contains(@href, 'profile.php') or contains(@href, 'user.php')]]"
            ]
        else:  # mbasic
            selectors = [
                ".//div[@data-ft and contains(@data-ft, 'comment')]",
                ".//div[contains(@id, 'comment_')]",
                ".//table//div[.//a[contains(@href, 'profile.php')]]",
                ".//div[.//a[contains(@href, 'profile.php?id=')]]"
            ]
        
        # Strategy 2: If not enough elements, expand search
        if len(all_comment_elements) < 10:
            print("⚠️ Not enough elements in target container, expanding search...")
            
            # Search in the entire page as fallback
            for i, selector in enumerate(selectors):
                try:
                    # Remove leading "./" to search entire document
                    global_selector = selector.replace(".//", "//")
                    elements = self.driver.find_elements(By.XPATH, global_selector)
                    print(f"Global search - Selector {i+1}: Found {len(elements)} elements")
                    
                    for elem in elements:
                        if elem not in all_comment_elements:
                            all_comment_elements.append(elem)
                            
                except Exception as e:
                    print(f"Global search - Selector {i+1} failed: {e}")
                    continue
        
        # Strategy 3: Fallback selectors
        if len(all_comment_elements) == 0:
            print("⚠️ No comments with standard selectors, trying fallback...")
            
            fallback_selectors = [
                # Look for any div with profile links
                "//div[.//a[contains(@href, 'facebook.com/')] and string-length(normalize-space(text())) > 20]",
                "//div[string-length(normalize-space(text())) > 30]",
                "//div[@role='article' and string-length(normalize-space(text())) > 20]",
                "//*[.//a[contains(@href, 'profile')] and string-length(normalize-space(text())) > 15]"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"Fallback selector: Found {len(elements)} elements")
                    for elem in elements:
                        if elem not in all_comment_elements:
                            all_comment_elements.append(elem)
                    
                    # Stop if we found enough elements
                    if len(all_comment_elements) > 20:
                        break
                except:
                    continue
        
        # Sort by position
        try:
            all_comment_elements.sort(key=lambda x: (x.location['y'], x.location['x']))
        except:
            pass
        
        comments = []
        seen_content = set()
        
        print(f"Processing {len(all_comment_elements)} potential comment elements...")
        
        # Process each element
        for i, element in enumerate(all_comment_elements):
            if self._stop_flag:
                break
                
            try:
                print(f"\n--- Element {i+1}/{len(all_comment_elements)} ---")
                
                comment_data = self.extract_comment_data_focused(element, i)
                
                if not comment_data:
                    continue
                
                # Deduplication
                if comment_data['Name'] == "Unknown":
                    print("  ✗ Skipped: no username found")
                    continue
                    
                # Check for duplicates
                content_signature = f"{comment_data['Name']}_{comment_data['ProfileLink']}"
                if content_signature in seen_content:
                    print("  ✗ Skipped: duplicate user")
                    continue
                seen_content.add(content_signature)
                
                comment_data['Type'] = 'Comment'
                comment_data['Layout'] = self.current_layout
                comment_data['Source'] = 'Target Container (FOCUSED)'
                
                comments.append(comment_data)
                print(f"  ✅ Added: {comment_data['Name']} - Profile: {comment_data['ProfileLink'][:50]}...")
                
            except Exception as e:
                print(f"  Error processing element {i}: {e}")
                continue
        
        print(f"\n=== FOCUSED EXTRACTION COMPLETE: {len(comments)} comments ===")
        return comments

    def extract_comment_data_focused(self, element, index):
        """FOCUSED comment data extraction với enhanced UID resolution"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 5:
                print(f"  ❌ Text too short: '{full_text}'")
                return None
            
            print(f"  Processing: '{full_text[:60]}...'")
            
            username = "Unknown"
            profile_href = ""
            uid = "Unknown"
            
            # FOCUSED: Enhanced username extraction
            print(f"    🎯 FOCUSED analysis of element structure...")
            
            # Method 1: Get ALL links and analyze each one
            try:
                all_links = element.find_elements(By.XPATH, ".//a")
                print(f"    Found {len(all_links)} total links in element")
                
                for link_index, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        print(f"      Link {link_index+1}: Text='{link_text}' | Href={link_href[:60]}...")
                        
                        # Check if this is a Facebook profile link
                        if ('facebook.com' in link_href and 
                            ('profile.php' in link_href or '/user/' in link_href or 'user.php' in link_href or 
                             (not any(x in link_href for x in ['groups', 'pages', 'events', 'photo', 'video'])))):
                            
                            # Enhanced name validation
                            if (link_text and 
                                len(link_text) >= 2 and 
                                len(link_text) <= 100 and
                                not link_text.isdigit() and
                                not link_text.startswith('http') and
                                not any(ui in link_text.lower() for ui in [
                                    'like', 'reply', 'share', 'comment', 'thích', 'trả lời', 
                                    'chia sẻ', 'bình luận', 'ago', 'trước', 'min', 'hour', 
                                    'day', 'phút', 'giờ', 'ngày', 'ẩn danh', 'anonymous',
                                    'view', 'xem', 'show', 'hiển thị', 'see more', 'view more'
                                ])):
                                
                                username = link_text
                                profile_href = link_href
                                
                                # Extract UID from URL trước
                                uid = extract_uid_from_profile_url(link_href)
                                
                                # Nếu UID vẫn chưa có hoặc là username, thử resolve
                                if uid == "Unknown" or uid.startswith("username:"):
                                    if uid.startswith("username:"):
                                        username_to_resolve = uid.split(":", 1)[1]
                                    else:
                                        username_to_resolve = username
                                    
                                    print(f"      🔄 Attempting to resolve UID for: {username_to_resolve}")
                                    resolved_uid = get_uid_from_username(username_to_resolve, self.cookies_dict, self.driver)
                                    if resolved_uid != "Unknown":
                                        uid = resolved_uid
                                        print(f"      ✅ Successfully resolved UID: {uid}")
                                    else:
                                        print(f"      ⚠️ Could not resolve UID for: {username_to_resolve}")
                                
                                print(f"      ✅ FOCUSED: Found valid profile: {username} -> UID: {uid}")
                                break
                                
                    except Exception as e:
                        print(f"      Error processing link {link_index+1}: {e}")
                        continue
                
            except Exception as e:
                print(f"    Error in focused method: {e}")
            
            # Fallback: If no username from links, try using the first line of the first child element's text
            if username == "Unknown":
                try:
                    children = element.find_elements(By.XPATH, "./*")
                    if children:
                        first_child_text = (children[0].text or "").strip()
                        if first_child_text:
                            first_line = first_child_text.splitlines()[0].strip()
                            # Basic validation for a plausible name line
                            if first_line and 2 <= len(first_line) <= 120 and not first_line.startswith("http"):
                                username = first_line
                                print(f"      ✅ Fallback name from first child: {username}")
                                
                                # Thử resolve UID từ username fallback
                                print(f"      🔄 Attempting to resolve UID for fallback username: {username}")
                                resolved_uid = get_uid_from_username(username, self.cookies_dict, self.driver)
                                if resolved_uid != "Unknown":
                                    uid = resolved_uid
                                    print(f"      ✅ Successfully resolved UID from fallback: {uid}")
                                
                except Exception as e:
                    print(f"      ⚠️ Fallback name extraction error: {e}")

            # Final validation
            if username == "Unknown":
                print("  ❌ FOCUSED extraction failed for this element")
                return None
                
            print(f"  ✅ FOCUSED: Successfully extracted username: {username} | UID: {uid}")
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,
                "CommentLink": "",
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "Focused on larger height container"
            }
            
        except Exception as e:
            print(f"Error in focused extraction: {e}")
            return None

    def scrape_all_comments(self, limit=0, resolve_uid=True, progress_callback=None):
        """Main scraping orchestrator with FOCUSED approach"""
        print(f"=== STARTING FOCUSED GROUPS SCRAPING ===")
        
        if self._stop_flag:
            return []
        
        # Step 1: Extract comments with focus
        comments = self.extract_groups_comments()
        
        # Step 2: Resolve UIDs cho những comment chưa có UID (nếu resolve_uid=True)
        if resolve_uid and comments:
            print(f"\n🔄 Resolving UIDs for {len(comments)} comments...")
            for i, comment in enumerate(comments):
                if self._stop_flag:
                    break
                    
                if comment.get('UID') == "Unknown" and comment.get('Name') != "Unknown":
                    print(f"  🔍 Resolving UID for: {comment['Name']}")
                    resolved_uid = get_uid_from_username(comment['Name'], self.cookies_dict, self.driver)
                    if resolved_uid != "Unknown":
                        comment['UID'] = resolved_uid
                        print(f"    ✅ Resolved UID: {resolved_uid}")
                    else:
                        print(f"    ⚠️ Could not resolve UID for: {comment['Name']}")
                
                # Update progress
                if progress_callback and i % 5 == 0:
                    progress_callback(len(comments))
        
        # Step 3: Apply limit
        if limit > 0 and len(comments) > limit:
            comments = comments[:limit]
            print(f"📊 Limited to {limit} comments")
        
        # Step 4: Progress reporting
        if progress_callback:
            progress_callback(len(comments))
        
        # Statistics
        uid_count = len([c for c in comments if c.get('UID', 'Unknown') != 'Unknown'])
        print(f"✅ FOCUSED scraping completed: {len(comments)} comments extracted | {uid_count} UIDs resolved")
        return comments

    def close(self):
        try: 
            self.driver.quit()
        except: 
            pass

# ----------------------------
# FOCUSED GUI
# ----------------------------

class FBGroupsAppGUI:
    def __init__(self, root):
        self.root = root
        root.title("🎯 FB Groups Comment Scraper - FOCUSED + UID")
        root.geometry("1100x950")
        root.configure(bg="#121212")

        # Main frame
        main_frame = tk.Frame(root, bg="#121212")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_frame = tk.Frame(main_frame, bg="#121212")
        header_frame.pack(fill="x", pady=(0,20))
        
        title_label = tk.Label(header_frame, text="🎯 Facebook Groups Comment Scraper - FOCUSED + UID", 
                              font=("Arial", 20, "bold"), bg="#121212", fg="#a5d6a7")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="🎯 Enhanced version - Extracts usernames + converts to UIDs", 
                                 font=("Arial", 11), bg="#121212", fg="#b0b0b0")
        subtitle_label.pack(pady=(5,0))

        # Input section
        input_frame = tk.LabelFrame(main_frame, text="📝 Thông tin bài viết Groups", font=("Arial", 12, "bold"), 
                                   bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        input_frame.pack(fill="x", pady=(0,15))

        tk.Label(input_frame, text="🔗 Link bài viết trong Groups:", bg="#121212", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15,5))
        self.entry_url = tk.Entry(input_frame, width=100, font=("Arial", 9))
        self.entry_url.pack(fill="x", padx=15, pady=(0,10))

        tk.Label(input_frame, text="🍪 Cookie Facebook (để truy cập Groups):", bg="#121212", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5,5))
        self.txt_cookie = tk.Text(input_frame, height=4, font=("Arial", 8))
        self.txt_cookie.pack(fill="x", padx=15, pady=(0,15))

        # Options section
        options_frame = tk.LabelFrame(main_frame, text="🎯 Cấu hình FOCUSED + UID Version", font=("Arial", 12, "bold"), 
                                     bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        options_frame.pack(fill="x", pady=(0,15))
        
        opt_grid = tk.Frame(options_frame, bg="#121212")
        opt_grid.pack(fill="x", padx=15, pady=15)
        
        # Options grid
        tk.Label(opt_grid, text="📊 Số lượng comment:", bg="#121212").grid(row=0, column=0, sticky="w")
        self.entry_limit = tk.Entry(opt_grid, width=10)
        self.entry_limit.insert(0, "0")
        self.entry_limit.grid(row=0, column=1, sticky="w", padx=(10,20))
        tk.Label(opt_grid, text="(0 = tất cả)", bg="#121212", fg="#6c757d").grid(row=0, column=2, sticky="w")

        self.headless_var = tk.BooleanVar(value=False)  # Default to visible for debugging
        tk.Checkbutton(opt_grid, text="👻 Chạy ẩn", variable=self.headless_var,
                      bg="#121212", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=(10,0))

        self.resolve_uid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_grid, text="🆔 Lấy UID từ username", variable=self.resolve_uid_var, 
                      bg="#121212", font=("Arial", 9)).grid(row=1, column=1, sticky="w", pady=(10,0))

        # File section
        file_frame = tk.LabelFrame(main_frame, text="💾 Xuất kết quả", font=("Arial", 12, "bold"), 
                                  bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        file_frame.pack(fill="x", pady=(0,15))
        
        file_row = tk.Frame(file_frame, bg="#121212")
        file_row.pack(fill="x", padx=15, pady=15)
        
        self.entry_file = tk.Entry(file_row, width=70, font=("Arial", 9))
        current_date = datetime.now().strftime("%d_%m_%Y")
        self.entry_file.insert(0, f"facebook_groups_comments_UID_{current_date}.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        self.btn_choose = tk.Button(file_row, text="📁 Chọn", command=self.choose_file, 
                 bg="#17a2b8", fg="black", font=("Arial", 9))
        self.btn_choose.pack(side="right", padx=(10,0))

        # Status section
        status_frame = tk.LabelFrame(main_frame, text="📊 Trạng thái thực thi - ENHANCED UID", font=("Arial", 12, "bold"), 
                                    bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        status_frame.pack(fill="x", pady=(0,15))
        
        self.lbl_status = tk.Label(status_frame, text="✅ Enhanced UID scraper sẵn sàng - Đã thêm chức năng lấy UID từ username", fg="#28a745", 
                                  wraplength=900, justify="left", font=("Arial", 11), bg="#121212")
        self.lbl_status.pack(anchor="w", padx=15, pady=(15,5))

        self.lbl_progress_detail = tk.Label(status_frame, text="💡 NEW: Username → UID conversion | URL UID extraction | Selenium + Requests methods | Enhanced debugging",
                                          fg="#b0b0b0", wraplength=900, justify="left", font=("Arial", 9), bg="#121212")
        self.lbl_progress_detail.pack(anchor="w", padx=15, pady=(0,10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(0,15))

        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#121212")
        button_frame.pack(fill="x", pady=20)
        
        self.btn_start = tk.Button(button_frame, text="🚀 Bắt đầu UID Scraping", bg="#28a745", fg="black", 
                                  font=("Arial", 14, "bold"), command=self.start_scrape_thread, 
                                  pady=12, padx=40)
        self.btn_start.pack(side="left")

        self.btn_stop = tk.Button(button_frame, text="⏹️ Dừng", bg="#dc3545", fg="black", 
                                 font=("Arial", 14, "bold"), command=self.stop_scrape, 
                                 state=tk.DISABLED, pady=12, padx=40)
        self.btn_stop.pack(side="left", padx=(25,0))

        self.progress_var = tk.IntVar(value=0)
        self.progress_label = tk.Label(button_frame, textvariable=self.progress_var, fg="#28a745", 
                                     font=("Arial", 18, "bold"), bg="#121212")
        self.progress_label.pack(side="right")

        self._scrape_thread = None
        self._stop_flag = False
        self.scraper = None

        # Apply dark theme across widgets
        self._apply_dark_theme()

        # Beautify primary (start) and danger (stop) buttons
        self._beautify_button(self.btn_start, base_bg="#2ecc71", hover_bg="#27ae60", active_bg="#1e874b")
        self._beautify_button(self.btn_stop, base_bg="#e74c3c", hover_bg="#c0392b", active_bg="#992d22")
        # Beautify choose file button with cyan palette
        self._beautify_button(self.btn_choose, base_bg="#17a2b8", hover_bg="#1491a1", active_bg="#0f6f7b")

    def _apply_dark_theme(self):
        """Apply a dark theme recursively to Tk widgets and ttk components."""
        dark_bg = "#121212"
        surface_bg = "#1e1e1e"
        light_fg = "#e0e0e0"
        subtle_fg = "#b0b0b0"

        # Root background
        try:
            self.root.configure(bg=dark_bg)
        except Exception:
            pass

        def apply(widget):
            # Background
            try:
                if 'background' in widget.configure():
                    widget.configure(bg=dark_bg)
            except Exception:
                pass

            # Foreground: only adjust if currently black/dark default
            try:
                # Skip changing foreground for clickable buttons so custom styles persist
                if isinstance(widget, tk.Button):
                    pass
                else:
                    cfg = widget.configure()
                    if 'foreground' in cfg:
                        current_fg = str(widget.cget('fg')).lower()
                        if current_fg in ('black', '#000000'):
                            widget.configure(fg=light_fg)
            except Exception:
                pass

            # Special cases
            try:
                if isinstance(widget, tk.Entry):
                    widget.configure(bg=surface_bg, fg=light_fg, insertbackground=light_fg)
                if isinstance(widget, tk.Text):
                    widget.configure(bg=surface_bg, fg=light_fg, insertbackground=light_fg)
                if isinstance(widget, tk.Listbox):
                    widget.configure(bg=surface_bg, fg=light_fg, selectbackground="#2a2a2a")
            except Exception:
                pass

            for child in widget.winfo_children():
                apply(child)

        apply(self.root)

        # ttk styling (progress bar)
        try:
            style = ttk.Style()
            # Use a theme that allows color customization
            try:
                style.theme_use('clam')
            except Exception:
                pass
            style.configure("TProgressbar",
                            troughcolor=surface_bg,
                            background="#00bcd4",
                            bordercolor=surface_bg,
                            lightcolor=surface_bg,
                            darkcolor=surface_bg)
        except Exception:
            pass

    def _beautify_button(self, button, base_bg="#2ecc71", hover_bg="#27ae60", active_bg="#1e874b"):
        """Apply modern flat styling and hover/active effects to tk.Button."""
        try:
            button.configure(
                bg=base_bg,
                fg="#000000",
                activebackground=active_bg,
                activeforeground="#000000",
                bd=0,
                highlightthickness=0,
                relief="flat",
                cursor="hand2",
                disabledforeground="#777777"
            )

            def on_enter(_):
                try:
                    button.configure(bg=hover_bg)
                except Exception:
                    pass

            def on_leave(_):
                try:
                    button.configure(bg=base_bg)
                except Exception:
                    pass

            def on_press(_):
                try:
                    button.configure(bg=active_bg)
                except Exception:
                    pass

            def on_release(_):
                try:
                    button.configure(bg=hover_bg)
                except Exception:
                    pass

            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
            button.bind("<ButtonPress-1>", on_press)
            button.bind("<ButtonRelease-1>", on_release)
        except Exception:
            pass

    def choose_file(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
            title="Chọn file để lưu Groups comments với UID"
        )
        if f:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, f)

    def start_scrape_thread(self):
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "facebook_groups_comments_UID.xlsx"
        
        if not url:
            messagebox.showerror("❌ Lỗi", "Vui lòng nhập link bài viết Groups.")
            return
        
        if "groups/" not in url:
            result = messagebox.askyesno("⚠️ Xác nhận", 
                                       "Link này có vẻ không phải Groups. Bạn có muốn tiếp tục không?")
            if not result:
                return
        
        try: 
            limit = int(self.entry_limit.get().strip())
        except: 
            limit = 0

        self._stop_flag = False
        self.progress_var.set(0)
        self.progress_bar.start()
        self.lbl_status.config(text="🔄 Đang khởi động Enhanced UID Groups scraper...", fg="#fd7e14")
        self.lbl_progress_detail.config(text="⏳ Initializing UID extraction with Selenium + Requests methods...")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self._scrape_thread = threading.Thread(target=self._scrape_worker, 
                                             args=(url, cookie_str, file_out, limit, 
                                                   self.headless_var.get(), self.resolve_uid_var.get()))
        self._scrape_thread.daemon = True
        self._scrape_thread.start()

    def stop_scrape(self):
        self._stop_flag = True
        if self.scraper:
            self.scraper._stop_flag = True
        self.lbl_status.config(text="⏹️ Đang dừng UID scraper...", fg="#dc3545")
        self.btn_stop.config(state=tk.DISABLED)

    def _progress_cb(self, count):
        self.progress_var.set(count)
        self.lbl_status.config(text=f"📈 UID processing... Đã lấy {count} comments", fg="#28a745")
        self.root.update_idletasks()

    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, resolve_uid):
        try:
            # Initialize
            self.lbl_status.config(text="🌐 Khởi tạo Enhanced UID Groups scraper...", fg="#fd7e14")
            self.scraper = FacebookGroupsScraper(cookie_str, headless=headless)
            
            if self._stop_flag: return
            
            # Load post
            self.lbl_status.config(text="📄 Đang tải bài viết Groups với UID logic...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Loading post with enhanced UID resolution...")
            success = self.scraper.load_post(url)
            
            if not success:
                self.lbl_status.config(text="❌ Không thể tải bài viết Groups", fg="#dc3545")
                self.lbl_progress_detail.config(text="💡 Kiểm tra: 1) Cookie valid, 2) Quyền truy cập Groups, 3) Link chính xác")
                return
            
            # Show detected layout
            layout = getattr(self.scraper, 'current_layout', 'unknown')
            self.lbl_progress_detail.config(text=f"🎯 Layout detected: {layout} - Using Enhanced UID extraction...")
                
            if self._stop_flag: return
            
            # Scrape with Enhanced UID logic
            self.lbl_status.config(text=f"🔍 Enhanced UID Groups extraction ({layout})...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Extracting usernames and resolving to UIDs...")
            
            comments = self.scraper.scrape_all_comments(limit=limit, resolve_uid=resolve_uid, 
                                                       progress_callback=self._progress_cb)
            
            print(f"✅ Comments with UIDs: {comments}")

            if self._stop_flag: return
            
            # Save
            self.lbl_status.config(text="💾 Đang lưu Enhanced UID Groups data...", fg="#fd7e14")
            
            if comments:
                df = pd.DataFrame(comments)
                
                # Add metadata
                df.insert(0, 'STT', range(1, len(df) + 1))
                df['Source'] = 'Facebook Groups - Enhanced UID'
                df['ScrapedAt'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # File handling
                if not file_out.lower().endswith((".xlsx", ".csv")):
                    file_out += ".xlsx"
                
                if file_out.lower().endswith(".csv"):
                    df.to_csv(file_out, index=False, encoding="utf-8-sig")
                else:
                    df.to_excel(file_out, index=False, engine="openpyxl")
                
                # Statistics
                unique_users = len(set(c['Name'] for c in comments if c['Name'] != 'Unknown'))
                profile_links = len([c for c in comments if c['ProfileLink']])
                uid_count = len([c for c in comments if c.get('UID', 'Unknown') != 'Unknown'])
                uid_success_rate = (uid_count / len(comments)) * 100 if comments else 0
                
                self.lbl_status.config(text=f"🎉 ENHANCED UID GROUPS SCRAPING HOÀN THÀNH!", fg="#28a745")
                self.lbl_progress_detail.config(text=f"📊 Enhanced Results: {len(comments)} comments | {unique_users} users | {profile_links} links | {uid_count} UIDs ({uid_success_rate:.1f}%) | Layout: {layout}")
                
                print(f"🎯 ENHANCED UID SCRAPING COMPLETE!")
                print(f"   📊 Results: {len(comments)} total comments")
                print(f"   👥 Unique users: {unique_users}")
                print(f"   🔗 Profile links: {profile_links}")
                print(f"   🆔 UIDs extracted: {uid_count} ({uid_success_rate:.1f}% success rate)")
                print(f"   📱 Layout used: {layout}")
                print(f"   💾 Saved to: {file_out}")
                
            else:
                self.lbl_status.config(text="⚠️ Không tìm thấy comment với Enhanced UID logic", fg="#ffc107")
                self.lbl_progress_detail.config(text=f"💡 Layout: {layout} | Kiểm tra debug files để phân tích Facebook structure")
                
                print(f"⚠️ No comments found with Enhanced UID logic")
                print(f"   📱 Layout: {layout}")
                print(f"   🔍 Debug files created: debug_focused_{layout}.html")
                print(f"   💡 Suggestions:")
                print(f"      1. Check if you have access to the Facebook Group")
                print(f"      2. Verify the post URL is correct and public in the group")
                print(f"      3. Try running without headless mode to see what's happening")
                print(f"      4. Check the debug HTML file to understand the page structure")
                
        except Exception as e:
            error_msg = str(e)[:120]
            self.lbl_status.config(text=f"❌ Lỗi Enhanced UID scraping: {error_msg}...", fg="#dc3545")
            self.lbl_progress_detail.config(text="🔍 Xem console để biết chi tiết. Enhanced UID version cung cấp debug info.")
            print(f"Enhanced UID Groups scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.stop()
            if self.scraper: 
                self.scraper.close()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

# ----------------------------
# Run Enhanced UID app
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FBGroupsAppGUI(root)
    root.mainloop()