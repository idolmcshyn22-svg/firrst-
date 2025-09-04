# fb_groups_scraper_focused.py - Focus on larger height element with enhanced UID extraction

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
# Helper utils (unchanged)
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

# ----------------------------
# ENHANCED Facebook Groups Scraper with UID Click Functionality
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

    def find_target_container(self):
        """Find the container with larger height (3000+ px) instead of smaller one"""
        print("🎯 Looking for target container with larger height...")
        
        try:
            # Look for divs with data-visualcompletion="ignore" and data-thumb="1"
            container_selector = "//div[@data-visualcompletion='ignore' and @data-thumb='1']"
            containers = self.driver.find_elements(By.XPATH, container_selector)
            
            print(f"Found {len(containers)} potential containers with data-thumb='1'")
            
            target_container = None
            max_height = 0

            for i, container in enumerate(containers):
                try:
                    # Get style attribute
                    style = container.get_attribute('style') or ""
                    
                    # Extract height from style
                    height_match = re.search(r'height:\s*(\d+)px', style)
                    if height_match:
                        height = int(height_match.group(1))
                        print(f"  Container {i+1}: height = {height}px")
                        
                        # Select the container with the largest height (prefer 3000+ px)
                        if height > max_height:
                            max_height = height
                            target_container = container
                            
                except Exception as e:
                    print(f"  Error analyzing container {i+1}: {e}")
                    continue

            if target_container:
                print(f"✅ Selected container with height: {max_height}px")
                
                # Scroll to this container
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target_container)
                time.sleep(2)
                
                return target_container
            else:
                print("⚠️ No suitable container found, using document body")
                return self.driver.find_element(By.TAG_NAME, "body")

        except Exception as e:
            print(f"Error finding target container: {e}")
            return self.driver.find_element(By.TAG_NAME, "body")

    def scroll_to_target_container(self):
        """Find target container and scroll to it"""
        print("🎯 Finding and scrolling to target container...")
        
        # Find the target container
        target_container = self.find_target_container()
        
        if target_container:
            # Scroll through the comments in this container
            success = self.scroll_through_comments_container(target_container)
            if success:
                print("✅ Successfully scrolled through target container")
            else:
                print("⚠️ Had issues scrolling, but continuing with container")
        
        return target_container

    def scroll_through_comments_container(self, target_container):
        """Scroll gradually through the comments container to load all content"""
        print("📜 Starting gradual scroll through comments container...")
        
        try:
            if not target_container:
                print("❌ No target container provided")
                return False
            
            # Get container height
            style = target_container.get_attribute('style') or ""
            height_match = re.search(r'height:\s*(\d+)px', style)
            
            if not height_match:
                print("⚠️ Could not determine container height")
                return False
            
            container_height = int(height_match.group(1))
            print(f"📐 Container height: {container_height}px")
            
            # Get container position
            container_rect = target_container.rect
            container_top = container_rect['y']
            
            print(f"📍 Container position: top={container_top}px")
            
            # Scroll parameters
            scroll_step = 600  # Smaller steps for better loading
            scroll_pause = 2   # Longer pause to ensure loading
            current_position = container_top
            
            # Start from the top of container
            self.driver.execute_script(f"window.scrollTo(0, {container_top});")
            time.sleep(3)
            
            print("🚀 Starting gradual scroll through comments...")
            
            step_count = 0
            max_steps = (container_height // scroll_step) + 3  # +3 for safety
            
            while step_count < max_steps:
                step_count += 1
                current_position += scroll_step
                
                # Scroll to next position
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Check current scroll position
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                page_height = self.driver.execute_script("return document.body.scrollHeight;")
                
                print(f"📜 Step {step_count}/{max_steps}: scrolled to {current_scroll}px")
                
                # Wait for content to load
                time.sleep(scroll_pause)
                
                # Check if we've scrolled past the container or reached page bottom
                if current_scroll >= (container_top + container_height - 300):
                    print("🏁 Reached end of comments container")
                    break
                    
                if current_scroll >= (page_height - 1000):
                    print("🏁 Reached page bottom")
                    break
            
            print(f"✅ Completed comment scrolling in {step_count} steps")
            
            # Final scroll to make sure we're at the bottom of container
            final_position = min(container_top + container_height, 
                            self.driver.execute_script("return document.body.scrollHeight;") - 500)
            self.driver.execute_script(f"window.scrollTo(0, {final_position});")
            time.sleep(3)
            
            print("🎯 Final positioning completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during comment scrolling: {e}")
            return False

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
            for selector in all_comments_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"  Found 'All comments' button: {element.text}")
                            
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
                                    time.sleep(4)
                                    break
                                except:
                                    continue
                    
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

    def click_name_and_extract_uid(self, element):
        """Click on user name to get profile link and extract UID"""
        try:
            print("👤 Searching for clickable user name elements...")
            
            # Find clickable name elements within the comment element
            name_selectors = [
                # Look for profile links first (most reliable)
                ".//a[contains(@href, 'facebook.com') and (contains(@href, 'profile.php') or contains(@href, '/user/') or contains(@href, 'user.php'))]",
                # Look for any Facebook links that are NOT posts, photos, videos, or groups
                ".//a[contains(@href, 'facebook.com') and not(contains(@href, 'posts/')) and not(contains(@href, 'photo')) and not(contains(@href, 'video')) and not(contains(@href, 'groups/'))]",
                # Look for any clickable links with role='link'
                ".//a[@role='link' and contains(@href, 'facebook.com') and not(contains(@href, 'posts/'))]",
                # Broader search for any Facebook links
                ".//a[contains(@href, 'facebook.com')]"
            ]
            
            profile_info = {
                "ProfileLink": "",
                "UID": "Unknown",
                "NameText": "",
                "ClickedURL": ""
            }
            
            for selector in name_selectors:
                try:
                    name_links = element.find_elements(By.XPATH, selector)
                    
                    for name_link in name_links:
                        try:
                            link_text = name_link.text.strip()
                            link_href = name_link.get_attribute("href") or ""
                            
                            # Check if this looks like a user name (not UI elements or time elements)
                            ui_keywords = ['like', 'reply', 'share', 'comment', 'thích', 'trả lời', 
                                         'chia sẻ', 'bình luận', 'ago', 'trước', 'min', 'hour', 
                                         'day', 'phút', 'giờ', 'ngày', 'view', 'xem', 'show', 'see more']
                            time_keywords = ['ngày', 'giờ', 'phút', 'giây', 'day', 'hour', 'minute', 'second', 'min', 'hr', 'h', 'm', 's']
                            
                            # Skip if this is a post/time link
                            is_post_link = ('posts/' in link_href or 'permalink' in link_href) and any(time_word in link_text.lower() for time_word in time_keywords)
                            
                            if (link_text and 
                                len(link_text) >= 2 and 
                                len(link_text) <= 100 and
                                not link_text.isdigit() and
                                not link_text.startswith('http') and
                                not is_post_link and
                                not any(ui in link_text.lower() for ui in ui_keywords)):
                                
                                # This looks like a user name, let's click it
                                print(f"      🖱️ Clicking on name: '{link_text}'")
                                
                                try:
                                    # Click the name element
                                    self.driver.execute_script("arguments[0].click();", name_link)
                                    time.sleep(3)  # Wait for navigation
                                    
                                    # Get the new URL after clicking
                                    clicked_url = self.driver.current_url
                                    print(f"      🌐 Clicked URL: {clicked_url[:80]}...")
                                    
                                    profile_info["ClickedURL"] = clicked_url
                                    profile_info["NameText"] = link_text
                                    profile_info["ProfileLink"] = link_href  # Original href
                                    
                                    # Extract UID from the clicked URL using enhanced method
                                    extracted_uid = self.extract_uid_from_any_link(clicked_url)
                                    if extracted_uid != "Unknown":
                                        profile_info["UID"] = extracted_uid
                                    else:
                                        # Try original href as fallback
                                        extracted_uid = self.extract_uid_from_any_link(link_href)
                                        if extracted_uid != "Unknown":
                                            profile_info["UID"] = extracted_uid
                                    
                                    print(f"      ✅ Extracted UID from clicked URL: {profile_info['UID']}")
                                    
                                    # Navigate back to continue processing
                                    self.driver.back()
                                    time.sleep(2)
                                    
                                    return profile_info
                                    
                                except Exception as click_error:
                                    print(f"      ⚠️ Could not click name element: {click_error}")
                                    # Still try to extract from original href
                                    profile_info["ProfileLink"] = link_href
                                    profile_info["NameText"] = link_text
                                    
                                    # Extract UID from original href using enhanced method
                                    extracted_uid = self.extract_uid_from_any_link(link_href)
                                    if extracted_uid != "Unknown":
                                        profile_info["UID"] = extracted_uid
                                    
                                    return profile_info
                                
                        except Exception as link_error:
                            print(f"      Error processing name link: {link_error}")
                            continue
                            
                except Exception as selector_error:
                    print(f"    Error with selector {selector}: {selector_error}")
                    continue
            
            return profile_info
            
        except Exception as e:
            print(f"Error in click_name_and_extract_uid: {e}")
            return {"ProfileLink": "", "UID": "Unknown", "NameText": "", "ClickedURL": ""}

    def click_time_element_and_extract_info(self, element):
        """Click on time elements to extract post link and UID"""
        try:
            print("🕒 Searching for clickable time elements...")
            
            # Find time elements within the comment element
            time_selectors = [
                # Look for time-like links with specific patterns
                ".//a[contains(@href, 'facebook.com') and (contains(@href, 'posts/') or contains(@href, 'permalink'))]",
                # Look for spans or divs that might contain time text
                ".//a[contains(text(), 'ngày') or contains(text(), 'giờ') or contains(text(), 'phút') or contains(text(), 'day') or contains(text(), 'hour') or contains(text(), 'min')]",
                # Look for elements with time-related attributes
                ".//a[@role='link' and contains(@href, 'facebook.com')]"
            ]
            
            post_info = {
                "PostLink": "",
                "PostUID": "Unknown",
                "TimeText": ""
            }
            
            for selector in time_selectors:
                try:
                    time_links = element.find_elements(By.XPATH, selector)
                    
                    for time_link in time_links:
                        try:
                            link_text = time_link.text.strip()
                            link_href = time_link.get_attribute("href") or ""
                            
                            # Check if this looks like a time element
                            time_indicators = ['ngày', 'giờ', 'phút', 'giây', 'day', 'hour', 'minute', 'second', 'min', 'hr', 'h', 'm', 's']
                            
                            if (link_href and 'facebook.com' in link_href and 
                                ('posts/' in link_href or 'permalink' in link_href) and
                                link_text and any(indicator in link_text.lower() for indicator in time_indicators)):
                                
                                post_info["PostLink"] = link_href
                                post_info["TimeText"] = link_text
                                
                                # Extract post UID from URL
                                post_uid_patterns = [
                                    r'/posts/(\d+)',  # /posts/31258488570464523/
                                    r'story_fbid=(\d+)',  # story_fbid=31258488570464523
                                    r'permalink/(\d+)',  # permalink/31258488570464523
                                    r'/(\d{15,})',  # Any very long number (Facebook post IDs are usually 15+ digits)
                                    r'posts/.*?(\d{10,})',  # Any long number in posts path
                                ]
                                
                                for pattern in post_uid_patterns:
                                    post_match = re.search(pattern, link_href)
                                    if post_match:
                                        post_info["PostUID"] = post_match.group(1)
                                        break
                                
                                print(f"      ✅ Found time element: '{link_text}' -> Post UID: {post_info['PostUID']}")
                                print(f"      📝 Post Link: {link_href[:80]}...")
                                
                                # Optional: Click the time element to navigate to the post
                                try:
                                    print(f"      🖱️ Clicking time element: {link_text}")
                                    self.driver.execute_script("arguments[0].click();", time_link)
                                    time.sleep(2)  # Wait for navigation
                                    
                                    # Get the new URL after clicking
                                    new_url = self.driver.current_url
                                    print(f"      🌐 Navigated to: {new_url[:80]}...")
                                    
                                    # Navigate back to continue processing
                                    self.driver.back()
                                    time.sleep(2)
                                    
                                except Exception as click_error:
                                    print(f"      ⚠️ Could not click time element: {click_error}")
                                
                                return post_info
                                
                        except Exception as link_error:
                            print(f"      Error processing time link: {link_error}")
                            continue
                            
                except Exception as selector_error:
                    print(f"    Error with selector {selector}: {selector_error}")
                    continue
            
            return post_info
            
        except Exception as e:
            print(f"Error in click_time_element_and_extract_info: {e}")
            return {"PostLink": "", "PostUID": "Unknown", "TimeText": ""}

    def convert_username_to_uid(self, username_or_url):
        """Convert Facebook username/URL to UID by making a request"""
        try:
            print(f"🔄 Converting '{username_or_url}' to UID...")
            
            # Determine if input is a URL or username
            if username_or_url.startswith('http'):
                profile_url = username_or_url
                # Extract username from URL for logging
                username_match = re.search(r'facebook\.com/([^/?]+)', username_or_url)
                display_name = username_match.group(1) if username_match else "URL"
            else:
                profile_url = f"https://www.facebook.com/{username_or_url}"
                display_name = username_or_url
            
            # Use requests with cookies to get the profile page
            if hasattr(self, 'cookies_dict') and self.cookies_dict:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                try:
                    response = requests.get(profile_url, cookies=self.cookies_dict, headers=headers, timeout=15)
                    
                    # Look for UID patterns in the response
                    uid_patterns = [
                        r'"profile_id":"(\d+)"',
                        r'"userID":"(\d+)"',
                        r'"user_id":"(\d+)"',
                        r'"entity_id":"(\d+)"',
                        r'profile\.php\?id=(\d+)',
                        r'"id":(\d{10,})',
                        r'entity_id=(\d+)',
                        r'"target_id":"(\d+)"',
                        r'"owner_id":"(\d+)"',
                        r'"profile_owner":"(\d+)"',
                        r'data-profileid="(\d+)"',
                        r'profileid=(\d+)',
                        # Look in JSON data structures
                        r'"__isProfile":"(\d+)"',
                        r'"profile":{"id":"(\d+)"',
                    ]
                    
                    for pattern in uid_patterns:
                        uid_matches = re.findall(pattern, response.text)
                        if uid_matches:
                            # Take the first valid UID (10+ digits)
                            for uid in uid_matches:
                                if len(uid) >= 10:
                                    print(f"      ✅ Converted '{display_name}' to UID: {uid}")
                                    return uid
                            
                except Exception as req_error:
                    print(f"      ⚠️ Request error: {req_error}")
            
            # Fallback: try with Selenium
            try:
                current_url = self.driver.current_url
                self.driver.get(profile_url)
                time.sleep(3)
                
                # Check if redirected to profile.php?id=
                final_url = self.driver.current_url
                uid_match = re.search(r'profile\.php\?id=(\d+)', final_url)
                if uid_match:
                    uid = uid_match.group(1)
                    print(f"      ✅ Converted '{display_name}' to UID via redirect: {uid}")
                    # Go back to original page
                    self.driver.get(current_url)
                    time.sleep(2)
                    return uid
                
                # Try to find UID in page source
                page_source = self.driver.page_source
                uid_patterns = [
                    r'"profile_id":"(\d+)"',
                    r'"userID":"(\d+)"',
                    r'"user_id":"(\d+)"',
                    r'"entity_id":"(\d+)"',
                    r'data-profileid="(\d+)"'
                ]
                
                for pattern in uid_patterns:
                    uid_matches = re.findall(pattern, page_source)
                    if uid_matches:
                        for uid in uid_matches:
                            if len(uid) >= 10:
                                print(f"      ✅ Found UID in page source: {uid}")
                                # Go back to original page
                                self.driver.get(current_url)
                                time.sleep(2)
                                return uid
                
                # Go back to original page
                self.driver.get(current_url)
                time.sleep(2)
                
            except Exception as selenium_error:
                print(f"      ⚠️ Selenium conversion error: {selenium_error}")
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error converting username to UID: {e}")
            return "Unknown"

    def extract_uid_from_any_link(self, link_url):
        """Extract UID from any type of Facebook link"""
        try:
            print(f"🔍 Analyzing link for UID extraction: {link_url[:80]}...")
            
            # Direct UID patterns in URL
            direct_uid_patterns = [
                r'profile\.php\?id=(\d+)',        # profile.php?id=123456789
                r'user\.php\?id=(\d+)',           # user.php?id=123456789
                r'/user/(\d+)',                   # /user/123456789
                r'id=(\d+)',                      # id=123456789
                r'/(\d{10,})(?:[/?]|$)',          # Direct UID in path (10+ digits)
                r'u=(\d+)',                       # u=123456789
                r'profile_id=(\d+)',              # profile_id=123456789
                r'entity_id=(\d+)',               # entity_id=123456789
            ]
            
            # Try direct extraction from URL first
            for pattern in direct_uid_patterns:
                uid_match = re.search(pattern, link_url)
                if uid_match:
                    uid = uid_match.group(1)
                    if len(uid) >= 10:  # Facebook UIDs are typically 10+ digits
                        print(f"      ✅ Direct UID extraction: {uid}")
                        return uid
            
            # If no direct UID found, try username conversion
            username_match = re.search(r'facebook\.com/([^/?]+)', link_url)
            if username_match:
                username = username_match.group(1)
                # Skip common non-username paths
                skip_paths = ['profile', 'user', 'photo', 'video', 'posts', 'groups', 'pages', 'events']
                if username.lower() not in skip_paths and not username.isdigit():
                    print(f"      🔄 Found username '{username}', converting to UID...")
                    return self.convert_username_to_uid(username)
            
            print(f"      ❌ Could not extract UID from link")
            return "Unknown"
            
        except Exception as e:
            print(f"Error extracting UID from link: {e}")
            return "Unknown"

    def extract_groups_comments(self, click_name=True, click_time=True):
        """FOCUSED comment extraction targeting larger height container"""
        print(f"=== EXTRACTING GROUPS COMMENTS (FOCUSED) ===")
        
        # Find and focus on the target container
        target_container = self.scroll_to_target_container()
        
        if not target_container:
            print("❌ Could not find target container")
            return []
        
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
        
        # Apply selectors within target container
        for i, selector in enumerate(selectors):
            try:
                elements = target_container.find_elements(By.XPATH, selector)
                print(f"Target container - Selector {i+1}: Found {len(elements)} elements")
                
                for elem in elements:
                    if elem not in all_comment_elements:
                        all_comment_elements.append(elem)
                        
            except Exception as e:
                print(f"Target container - Selector {i+1} failed: {e}")
                continue
        
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
                
                comment_data = self.extract_comment_data_focused(element, i, click_name=click_name, click_time=click_time)
                
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

    def extract_comment_data_focused(self, element, index, click_name=True, click_time=True):
        """ENHANCED comment data extraction with click functionality"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 5:
                print(f"  ❌ Text too short: '{full_text}'")
                return None
            
            print(f"  Processing: '{full_text[:60]}...'")
            
            # Skip anonymous users
            if any(keyword in full_text.lower() for keyword in ['ẩn danh', 'người tham gia ẩn danh', 'anonymous']):
                print("  ⚠️ Skipping anonymous user comment")
                return None
            
            username = "Unknown"
            profile_href = ""
            uid = "Unknown"
            post_link = ""
            post_uid = "Unknown"
            clicked_profile_url = ""
            
            # ENHANCED: Username extraction with click functionality
            print(f"    🎯 ENHANCED analysis of element structure...")
            
            # Method 1: Click on user name to get profile info and UID (if enabled)
            if click_name:
                print(f"    👤 Attempting to click user name for UID extraction...")
                profile_click_info = self.click_name_and_extract_uid(element)
                clicked_profile_url = profile_click_info.get("ClickedURL", "")
                
                if profile_click_info["UID"] != "Unknown":
                    username = profile_click_info["NameText"]
                    profile_href = profile_click_info["ProfileLink"] or profile_click_info["ClickedURL"]
                    uid = profile_click_info["UID"]
                    print(f"      ✅ Successfully extracted via name click: {username} -> UID: {uid}")
            
            # Fallback or primary method if click_name is disabled
            if username == "Unknown":
                print(f"    🔄 Using traditional link analysis...")
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
                                ('profile.php' in link_href or '/user/' in link_href or 'user.php' in link_href)):
                                
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
                                    
                                    # Extract UID using enhanced method
                                    uid = self.extract_uid_from_any_link(link_href)
                                    
                                    print(f"      ✅ ENHANCED: Found valid profile: {username} -> UID: {uid}")
                                    break
                            
                            # Check if this is a Facebook post time link
                            elif ('facebook.com' in link_href and 
                                  ('posts/' in link_href or 'permalink' in link_href) and
                                  ('comment_id=' in link_href or '?' in link_href)):
                                
                                # Check if link text looks like time (e.g., "4 ngày", "2 hours", etc.)
                                time_indicators = ['ngày', 'giờ', 'phút', 'giây', 'day', 'hour', 'minute', 'second', 'min', 'hr', 'h', 'm', 's']
                                if (link_text and 
                                    any(indicator in link_text.lower() for indicator in time_indicators)):
                                    
                                    post_link = link_href
                                    
                                    # Extract post UID from URL patterns
                                    post_uid_patterns = [
                                        r'/posts/(\d+)',  # /posts/31258488570464523/
                                        r'story_fbid=(\d+)',  # story_fbid=31258488570464523
                                        r'permalink/(\d+)',  # permalink/31258488570464523
                                        r'posts/.*?(\d{10,})',  # Any long number in posts path
                                    ]
                                    
                                    for pattern in post_uid_patterns:
                                        post_match = re.search(pattern, link_href)
                                        if post_match:
                                            post_uid = post_match.group(1)
                                            break
                                    
                                    print(f"      ✅ ENHANCED: Found post time link: {link_text} -> Post UID: {post_uid}")
                                    print(f"      📝 Post Link: {post_link[:80]}...")
                                    
                        except Exception as e:
                            print(f"      Error processing link {link_index+1}: {e}")
                            continue
                    
                except Exception as e:
                    print(f"    Error in fallback method: {e}")
            
            # Final validation
            if username == "Unknown":
                print("  ❌ ENHANCED extraction failed for this element")
                return None
                
            print(f"  ✅ ENHANCED: Successfully extracted username: {username}")
            
            # Extract post information from time elements (if enabled)
            post_info = {"PostLink": "", "PostUID": "Unknown", "TimeText": ""}
            if click_time:
                print(f"    🕒 Extracting post information from time elements...")
                post_info = self.click_time_element_and_extract_info(element)
            
            # Use extracted post info if available, otherwise use the values found during link processing
            final_post_link = post_info["PostLink"] if post_info["PostLink"] else post_link
            final_post_uid = post_info["PostUID"] if post_info["PostUID"] != "Unknown" else post_uid
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,
                "CommentLink": "",
                "PostLink": final_post_link,
                "PostUID": final_post_uid,
                "TimeText": post_info.get("TimeText", ""),
                "ClickedProfileURL": clicked_profile_url,
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "Focused on larger height container"
            }
            
        except Exception as e:
            print(f"Error in enhanced extraction: {e}")
            return None

    def expand_groups_comments(self, max_iterations=50):
        """Simplified but effective expansion focused on target container"""
        print(f"=== EXPANDING GROUPS COMMENTS (FOCUSED) ===")
        
        # Focus on target container first
        target_container = self.find_target_container()
        
        for iteration in range(max_iterations):
            if self._stop_flag:
                break
                
            print(f"[Iteration {iteration+1}] FOCUSED scrolling and expanding...")
            
            # Scroll within target container if possible
            if target_container:
                try:
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", target_container)
                    time.sleep(1)
                except:
                    pass
            
            # Also scroll the main page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            
            # Look for expand links
            expand_selectors = [
                "//a[contains(text(),'View more comments')]",
                "//a[contains(text(),'Xem thêm bình luận')]",
                "//a[contains(text(),'Show more')]",
                "//a[contains(text(),'See more')]",
                "//div[@role='button' and (contains(text(),'more') or contains(text(),'thêm'))]"
            ]
            
            expanded = False
            for selector in expand_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            try:
                                elem.click()
                                expanded = True
                                print(f"    ✓ FOCUSED: Clicked: {elem.text}")
                                time.sleep(3)
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    expanded = True
                                    print(f"    ✓ FOCUSED: JS clicked: {elem.text}")
                                    time.sleep(3)
                                    break
                                except:
                                    continue
                    if expanded:
                        break
                except:
                    continue
            
            if not expanded and iteration > 5:
                print(f"    No expansion found, stopping early")
                break
        
        print("=== FOCUSED EXPANSION COMPLETE ===")

    def scrape_all_comments(self, limit=0, resolve_uid=True, click_name=True, click_time=True, progress_callback=None):
        """Main scraping orchestrator with ENHANCED approach"""
        print(f"=== STARTING ENHANCED GROUPS SCRAPING ===")
        print(f"🎛️ Settings: resolve_uid={resolve_uid}, click_name={click_name}, click_time={click_time}")
        
        # Step 1: Expand all content with focus
        self.expand_groups_comments()
        
        if self._stop_flag:
            return []
        
        # Step 2: Extract comments with enhanced functionality
        comments = self.extract_groups_comments(click_name=click_name, click_time=click_time)
        
        # Step 3: Apply limit
        if limit > 0 and len(comments) > limit:
            comments = comments[:limit]
            print(f"📊 Limited to {limit} comments")
        
        # Step 4: Progress reporting
        if progress_callback:
            progress_callback(len(comments))
        
        print(f"🎯 ENHANCED SCRAPING COMPLETE: {len(comments)} comments extracted")
        return comments

    def close(self):
        try: 
            self.driver.quit()
        except: 
            pass

# ----------------------------
# Enhanced GUI Application
# ----------------------------

class FacebookGroupsScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Enhanced Facebook Groups Comment Scraper with UID Click")
        self.root.geometry("900x700")
        self.root.configure(bg="#121212")
        
        # Apply dark theme
        self._apply_dark_theme()
        
        self._stop_flag = False
        self.scraper = None
        self._scrape_thread = None
        
        # Create main frame
        main_frame = tk.Frame(root, bg="#121212", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🎯 Enhanced Facebook Groups Comment Scraper", 
                              font=("Arial", 18, "bold"), bg="#121212", fg="#a5d6a7")
        title_label.pack(pady=(0,20))
        
        subtitle_label = tk.Label(main_frame, text="✨ With Name Click UID Extraction & Post Link Detection", 
                                 font=("Arial", 12), bg="#121212", fg="#81c784")
        subtitle_label.pack(pady=(0,15))
        
        # URL section
        url_frame = tk.LabelFrame(main_frame, text="🔗 Link bài viết Groups", font=("Arial", 12, "bold"), 
                                 bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        url_frame.pack(fill="x", pady=(0,15))
        
        self.entry_url = tk.Entry(url_frame, width=80, font=("Arial", 10))
        self.entry_url.pack(padx=15, pady=15)
        self.entry_url.insert(0, "https://www.facebook.com/groups/...")
        
        # Cookie section
        cookie_frame = tk.LabelFrame(main_frame, text="🍪 Facebook Cookies", font=("Arial", 12, "bold"), 
                                   bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        cookie_frame.pack(fill="x", pady=(0,15))
        
        self.txt_cookie = tk.Text(cookie_frame, height=4, font=("Consolas", 9))
        self.txt_cookie.pack(fill="x", padx=15, pady=15)
        self.txt_cookie.insert("1.0", "Dán cookies Facebook vào đây...")
        
        # Options section
        options_frame = tk.LabelFrame(main_frame, text="⚙️ Tùy chọn nâng cao", font=("Arial", 12, "bold"), 
                                    bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        options_frame.pack(fill="x", pady=(0,15))
        
        opt_grid = tk.Frame(options_frame, bg="#121212")
        opt_grid.pack(fill="x", padx=15, pady=15)
        
        # Limit
        tk.Label(opt_grid, text="📊 Giới hạn:", bg="#121212", fg="#ffffff", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        self.entry_limit = tk.Entry(opt_grid, width=10, font=("Arial", 9))
        self.entry_limit.grid(row=0, column=1, padx=(10,20), sticky="w")
        self.entry_limit.insert(0, "0")
        tk.Label(opt_grid, text="(0 = tất cả)", bg="#121212", fg="#6c757d").grid(row=0, column=2, sticky="w")

        # Options checkboxes
        self.headless_var = tk.BooleanVar(value=False)  # Default to visible for debugging
        tk.Checkbutton(opt_grid, text="👻 Chạy ẩn", variable=self.headless_var,
                      bg="#121212", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=(10,0))

        self.resolve_uid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_grid, text="🆔 Lấy UID", variable=self.resolve_uid_var, 
                      bg="#121212", font=("Arial", 9)).grid(row=1, column=1, sticky="w", pady=(10,0))

        # New enhanced options
        self.click_name_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_grid, text="🖱️ Click tên lấy UID", variable=self.click_name_var, 
                      bg="#121212", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=(5,0))

        self.click_time_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_grid, text="🕒 Click time lấy link", variable=self.click_time_var, 
                      bg="#121212", font=("Arial", 9)).grid(row=2, column=1, sticky="w", pady=(5,0))

        # File section
        file_frame = tk.LabelFrame(main_frame, text="💾 Xuất kết quả", font=("Arial", 12, "bold"), 
                                  bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        file_frame.pack(fill="x", pady=(0,15))
        
        file_row = tk.Frame(file_frame, bg="#121212")
        file_row.pack(fill="x", padx=15, pady=15)
        
        self.entry_file = tk.Entry(file_row, width=70, font=("Arial", 9))
        current_date = datetime.now().strftime("%d%m%Y")
        self.entry_file.insert(0, f"facebook_groups_comments_ENHANCED_{current_date}.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        btn_choose = tk.Button(file_row, text="📁 Chọn", command=self.choose_file, 
                              bg="#6c757d", fg="white", font=("Arial", 9))
        self._beautify_button(btn_choose, "#6c757d", "#5a6268", "#495057")
        btn_choose.pack(side="right", padx=(10,0))
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg="#121212")
        control_frame.pack(fill="x", pady=(0,15))
        
        self.btn_start = tk.Button(control_frame, text="🚀 Bắt đầu Enhanced Scrape", 
                                  font=("Arial", 14, "bold"), command=self.start_scrape_thread, 
                                  bg="#28a745", fg="white", height=2)
        self._beautify_button(self.btn_start, "#28a745", "#218838", "#1e7e34")
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0,10))
        
        self.btn_stop = tk.Button(control_frame, text="⏹️ Dừng", 
                                 font=("Arial", 14, "bold"), command=self.stop_scrape,
                                 bg="#dc3545", fg="white", height=2, state=tk.DISABLED)
        self._beautify_button(self.btn_stop, "#dc3545", "#c82333", "#bd2130")
        self.btn_stop.pack(side="right", fill="x", expand=True, padx=(10,0))
        
        # Progress section
        progress_frame = tk.LabelFrame(main_frame, text="📈 Tiến trình Enhanced", font=("Arial", 12, "bold"), 
                                     bg="#121212", fg="#a5d6a7", relief="groove", bd=2)
        progress_frame.pack(fill="x", pady=(0,15))
        
        progress_inner = tk.Frame(progress_frame, bg="#121212")
        progress_inner.pack(fill="x", padx=15, pady=15)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(progress_inner, mode='indeterminate')
        self.progress_bar.pack(fill="x", pady=(0,10))
        
        self.lbl_status = tk.Label(progress_inner, text="⏳ Sẵn sàng Enhanced scraping...", 
                                  bg="#121212", fg="#17a2b8", font=("Arial", 11, "bold"))
        self.lbl_status.pack(anchor="w")
        
        self.lbl_progress_detail = tk.Label(progress_inner, text="🎯 Enhanced scraper với click functionality", 
                                          bg="#121212", fg="#6c757d", font=("Arial", 9))
        self.lbl_progress_detail.pack(anchor="w", pady=(5,0))

    def _apply_dark_theme(self):
        """Apply dark theme to ttk widgets"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure dark theme colors
        style.configure('TProgressbar', 
                       background='#28a745',
                       troughcolor='#495057',
                       borderwidth=0,
                       lightcolor='#28a745',
                       darkcolor='#28a745')

    def _beautify_button(self, button, base_bg="#2ecc71", hover_bg="#27ae60", active_bg="#1e874b"):
        """Add hover effects to buttons"""
        def on_enter(e):
            button.config(bg=hover_bg)
        def on_leave(e):
            button.config(bg=base_bg)
        def on_click(e):
            button.config(bg=active_bg)
        def on_release(e):
            button.config(bg=hover_bg)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_click)
        button.bind("<ButtonRelease-1>", on_release)

    def choose_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, filename)

    def start_scrape_thread(self):
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "facebook_groups_comments_ENHANCED.xlsx"
        
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
        self.lbl_status.config(text="🔄 Đang khởi động Enhanced Groups scraper...", fg="#fd7e14")
        self.lbl_progress_detail.config(text="⏳ Initializing ENHANCED extraction with click functionality...")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self._scrape_thread = threading.Thread(target=self._scrape_worker, 
                                             args=(url, cookie_str, file_out, limit, 
                                                   self.headless_var.get(), self.resolve_uid_var.get(),
                                                   self.click_name_var.get(), self.click_time_var.get()))
        self._scrape_thread.daemon = True
        self._scrape_thread.start()

    def stop_scrape(self):
        self._stop_flag = True
        if self.scraper:
            self.scraper._stop_flag = True
        self.lbl_status.config(text="⏹️ Đang dừng Enhanced scraper...", fg="#dc3545")

    def _progress_cb(self, count):
        self.progress_var.set(count)
        self.lbl_status.config(text=f"📈 ENHANCED processing... Đã lấy {count} comments", fg="#28a745")
        self.root.update_idletasks()

    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, resolve_uid, click_name, click_time):
        try:
            # Initialize
            self.lbl_status.config(text="🌐 Khởi tạo ENHANCED Groups scraper...", fg="#fd7e14")
            self.scraper = FacebookGroupsScraper(cookie_str, headless=headless)
            
            if self._stop_flag: return
            
            # Load post
            self.lbl_status.config(text="📄 Đang tải ENHANCED Groups post...", fg="#fd7e14")
            if not self.scraper.load_post(url):
                raise Exception("Could not load Groups post")
            
            layout = self.scraper.current_layout or "unknown"
            
            if self._stop_flag: return
            
            # Scrape with ENHANCED logic
            self.lbl_status.config(text=f"🔍 ENHANCED Groups extraction ({layout})...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Using enhanced extraction with name click and time click functionality...")
            
            comments = self.scraper.scrape_all_comments(limit=limit, resolve_uid=resolve_uid,
                                                       click_name=click_name, click_time=click_time,
                                                       progress_callback=self._progress_cb)
            
            print(f"✅ Comments: {comments}")

            if self._stop_flag: return
            
            # Save
            self.lbl_status.config(text="💾 Đang lưu ENHANCED Groups data...", fg="#fd7e14")
            
            if comments:
                df = pd.DataFrame(comments)
                df.to_excel(file_out, index=False, engine='openpyxl')
                
                unique_users = len(df['Name'].unique())
                profile_links = len([c for c in comments if c['ProfileLink']])
                uid_count = len([c for c in comments if c['UID'] != 'Unknown'])
                post_links = len([c for c in comments if c.get('PostLink', '')])
                clicked_profiles = len([c for c in comments if c.get('ClickedProfileURL', '')])
                
                self.lbl_status.config(text="✅ ENHANCED Groups scraping hoàn tất!", fg="#28a745")
                self.lbl_progress_detail.config(text=f"🎯 ENHANCED Results: {len(comments)} comments | {unique_users} unique users | {profile_links} profile links | {uid_count} UIDs | {post_links} post links | {clicked_profiles} clicked profiles | Layout: {layout} | File: {file_out}")
                
                print(f"📊 ENHANCED Summary:")
                print(f"   💬 Total comments: {len(comments)}")
                print(f"   👥 Unique users: {unique_users}")
                print(f"   🔗 Profile links: {profile_links}")
                print(f"   🆔 UIDs extracted: {uid_count}")
                print(f"   📝 Post links: {post_links}")
                print(f"   🖱️ Clicked profiles: {clicked_profiles}")
                print(f"   🎯 Layout: {layout}")
                print(f"   💾 File: {file_out}")
                
                messagebox.showinfo("✅ Thành công", 
                                  f"🎯 ENHANCED scraping hoàn tất!\n\n"
                                  f"📊 Kết quả:\n"
                                  f"• {len(comments)} comments\n"
                                  f"• {unique_users} người dùng unique\n"
                                  f"• {uid_count} UIDs được trích xuất\n"
                                  f"• {post_links} post links\n"
                                  f"• {clicked_profiles} profiles được click\n\n"
                                  f"💾 Đã lưu: {file_out}")
            else:
                self.lbl_status.config(text="⚠️ Không tìm thấy comments nào", fg="#ffc107")
                messagebox.showwarning("⚠️ Cảnh báo", "Không tìm thấy comments nào để xuất.")
                
        except Exception as e:
            error_msg = str(e)
            self.lbl_status.config(text=f"❌ Lỗi ENHANCED: {error_msg}", fg="#dc3545")
            messagebox.showerror("❌ Lỗi", f"Đã xảy ra lỗi:\n{error_msg}")
            
        finally:
            # Cleanup
            if self.scraper:
                self.scraper.close()
            
            self.progress_bar.stop()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

# ----------------------------
# Main execution
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FacebookGroupsScraperGUI(root)
    root.mainloop()