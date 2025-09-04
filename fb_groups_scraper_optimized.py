# fb_groups_scraper_optimized.py - Optimized version combining best features from both versions

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
# OPTIMIZED Facebook Groups Scraper - Best of Both Worlds
# ----------------------------

class FacebookGroupsScraper:
    def __init__(self, cookie_str, headless=True):
        # OPTIMIZED: Store current post info for PostLink generation (from version 1)
        self.current_post_url = ""
        self.current_group_id = ""
        self.current_post_id = ""
        self.current_comment_id = None
        
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
        
        # OPTIMIZED: Store button references for enhanced scroll logic (from version 2)
        self.all_comments_button = None
        
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
        
        # OPTIMIZED: Extract post info for PostLink generation (from version 1)
        self.current_post_url = post_url
        self._extract_post_info(post_url)
        
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
                
                # OPTIMIZED: Enhanced comment loading sequence (from version 2)
                self._switch_to_all_comments()
                self._click_view_more_initial()
                
                return True
                    
            except Exception as e:
                print(f"Failed to load {url_attempt}: {e}")
                continue
        
        print("❌ Failed to load post with any URL variant")
        return False

    def _extract_post_info(self, post_url):
        """OPTIMIZED: Extract group and post IDs for PostLink generation (from version 1)"""
        try:
            print(f"🔍 OPTIMIZED: Extracting post info from URL: {post_url}")
            
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(post_url)
            path_parts = parsed.path.strip("/").split("/")
            query = parse_qs(parsed.query)
            
            # Extract group ID
            if "groups" in path_parts:
                idx = path_parts.index("groups")
                if len(path_parts) > idx + 1:
                    self.current_group_id = path_parts[idx + 1]
                    print(f"📊 Extracted Group ID: {self.current_group_id}")
            
            # Extract post ID
            if "posts" in path_parts:
                idx_post = path_parts.index("posts")
                if len(path_parts) > idx_post + 1:
                    self.current_post_id = path_parts[idx_post + 1]
                    print(f"📊 Extracted Post ID: {self.current_post_id}")
            
            # Extract comment ID from query parameter
            if "comment_id" in query:
                self.current_comment_id = query["comment_id"][0]
                print(f"📊 Found comment ID: {self.current_comment_id}")
            else:
                self.current_comment_id = None
                
        except Exception as e:
            print(f"⚠️ Error extracting post info: {e}")

    def generate_post_link(self, user_id="", username=""):
        """OPTIMIZED: Generate link to the original post with comment_id (from version 1)"""
        try:
            if not self.current_group_id or not self.current_post_id:
                return ""
            
            # Generate link to the original Groups post
            post_link = f"https://www.facebook.com/groups/{self.current_group_id}/posts/{self.current_post_id}/"
            
            # Add comment_id if available
            if self.current_comment_id:
                post_link += f"?comment_id={self.current_comment_id}"
            
            print(f"🔗 OPTIMIZED: Generated post link: {post_link}")
            return post_link
            
        except Exception as e:
            print(f"❌ Error generating post link: {e}")
            return ""

    def _switch_to_all_comments(self):
        """OPTIMIZED: Switch to 'All comments' view (enhanced from version 2)"""
        print("🔄 OPTIMIZED: Attempting to switch to 'All comments' view...")
        
        try:
            time.sleep(3)
            
            # Enhanced selectors for all comments button
            all_comments_selectors = [
                # Vietnamese selectors
                "//span[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//div[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//a[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//button[contains(normalize-space(text()),'Tất cả bình luận')]",
                
                # English selectors
                "//span[contains(normalize-space(text()),'All comments')]",
                "//div[contains(normalize-space(text()),'All comments')]",
                "//a[contains(normalize-space(text()),'All comments')]",
                "//button[contains(normalize-space(text()),'All comments')]",
                
                # Role-based selectors
                "//div[@role='button' and (contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments'))]",
                "//span[@role='button' and (contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments'))]",
                
                # Additional fallback selectors
                "//*[contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments')]"
            ]
            
            clicked = False
            
            for selector in all_comments_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.strip()
                            print(f"  Found 'All comments' button: {element_text}")
                            
                            # Better validation of the button text
                            if ('tất cả bình luận' in element_text.lower() or 
                                'all comments' in element_text.lower()):
                                
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

    def _click_view_more_initial(self):
        """OPTIMIZED: Initial click on 'View more comments' button (from version 2)"""
        print("🔄 OPTIMIZED: Initial click on 'View more comments' button...")
        
        try:
            time.sleep(3)
            
            view_more_selectors = [
                "//div[contains(normalize-space(text()),'View more comments')]",
                "//button[contains(normalize-space(text()),'View more comments')]",
                "//a[contains(normalize-space(text()),'View more comments')]",
                "//span[contains(normalize-space(text()),'View more comments')]",
                "//div[contains(normalize-space(text()),'Xem thêm bình luận')]",
                "//button[contains(normalize-space(text()),'Xem thêm bình luận')]"
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
                print("  ⚠️ Could not find or click 'View more comments' button initially")
            else:
                print("  🎯 Initial 'View more comments' click successful")
                
        except Exception as e:
            print(f"  ⚠️ Error with initial 'View more comments' click: {e}")

    def is_comment_div(self, div_element):
        """OPTIMIZED: Check if a div element contains comment-like content (from version 2)"""
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
        """OPTIMIZED: Comment extraction combining both approaches"""
        print(f"=== OPTIMIZED GROUPS COMMENT EXTRACTION ===")

        # OPTIMIZED: Enhanced scroll and load sequence (from version 2)
        try:
            # Find "All comments" button's parent with class html-div
            all_comments_button = getattr(self, 'all_comments_button', None)
            
            if not all_comments_button:
                print("⚠️ No 'All comments' button found from previous method, searching again...")
                # Look for "All comments" button with various possible text variations
                all_comments_selectors = [
                    "//button[contains(text(), 'All comments')]",
                    "//a[contains(text(), 'All comments')]",
                    "//span[contains(text(), 'All comments')]",
                    "//div[contains(text(), 'All comments')]",
                    "//*[contains(text(), 'Tất cả bình luận')]",
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
                
                # Fallback methods for finding parent
                if not parent_with_html_div:
                    try:
                        parent = all_comments_button.find_element(By.XPATH, "./..")
                        if 'html-div' in (parent.get_attribute('class') or ''):
                            parent_with_html_div = parent
                            print("✅ Found parent with html-div class (immediate parent)")
                    except:
                        pass
                
                if parent_with_html_div:
                    print(f"✅ Successfully found 'All comments' button's parent with html-div class")
                    
                    # Get comment parent divs that come after the "All comments" parent_with_html_div
                    print("🔍 OPTIMIZED: Searching for comment parent divs with enhanced loading...")
                    
                    try:
                        # Get the next div that is a sibling of the parent_with_html_div
                        next_div = parent_with_html_div.find_element(By.XPATH, "./following-sibling::div[1]")
                        print(f"Found next div after parent_with_html_div")
                        print(f"Next div class: {next_div.get_attribute('class')}")
                        
                        # OPTIMIZED: Enhanced "View more comments" click loop
                        print("🔄 OPTIMIZED: Starting enhanced 'View more comments' click loop...")
                        previous_comment_count = 0
                        no_new_comments_count = 0
                        max_no_new_comments = 5  # More attempts
                        max_total_attempts = 50  # Maximum total attempts
                        total_attempts = 0
                        
                        while no_new_comments_count < max_no_new_comments and total_attempts < max_total_attempts:
                            total_attempts += 1
                            
                            # Look for "View more comments" button with enhanced selectors
                            view_more_selectors = [
                                "//button[contains(text(), 'View more comments')]",
                                "//a[contains(text(), 'View more comments')]",
                                "//span[contains(text(), 'View more comments')]",
                                "//div[contains(text(), 'View more comments')]",
                                "//button[contains(text(), 'Xem thêm bình luận')]",
                                "//a[contains(text(), 'Xem thêm bình luận')]",
                                "//*[contains(text(), 'View more')]",
                                "//*[contains(text(), 'Show more comments')]",
                                "//*[contains(text(), 'Load more comments')]",
                                "//*[contains(text(), 'See more comments')]",
                                "//button[contains(@aria-label, 'View more comments')]",
                                "//a[contains(@aria-label, 'View more comments')]",
                                # Additional Vietnamese selectors
                                "//*[contains(text(), 'Xem thêm')]",
                                "//*[contains(text(), 'Hiển thị thêm')]"
                            ]
                            
                            view_more_button = None
                            for selector in view_more_selectors:
                                try:
                                    elements = self.driver.find_elements(By.XPATH, selector)
                                    if elements:
                                        # Filter for visible and enabled elements
                                        for element in elements:
                                            if element.is_displayed() and element.is_enabled():
                                                view_more_button = element
                                                print(f"✅ Found 'View more comments' button using selector: {selector}")
                                                break
                                        if view_more_button:
                                            break
                                except Exception as e:
                                    continue
                            
                            if view_more_button:
                                try:
                                    # Scroll button into view
                                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", view_more_button)
                                    time.sleep(1)
                                    
                                    # Click the "View more comments" button
                                    self.driver.execute_script("arguments[0].click();", view_more_button)
                                    print(f"🖱️ Clicked 'View more comments' button (attempt {total_attempts})")
                                except Exception as e:
                                    print(f"⚠️ Error clicking 'View more comments' button: {e}")
                                    # Try alternative click method
                                    try:
                                        view_more_button.click()
                                        print(f"🖱️ Clicked 'View more comments' button (alternative method, attempt {total_attempts})")
                                    except Exception as e2:
                                        print(f"⚠️ Alternative click also failed: {e2}")
                                        no_new_comments_count += 1
                                        continue
                            else:
                                print(f"⚠️ No 'View more comments' button found (attempt {total_attempts})")
                                no_new_comments_count += 1
                            
                            # Wait for new comments to load with progressive delay
                            wait_time = min(3 + (total_attempts * 0.1), 8)  # Progressive wait time
                            print(f"⏳ Waiting {wait_time:.1f} seconds for new comments to load...")
                            time.sleep(wait_time)
                            
                            # Count current comments
                            current_comment_divs = []
                            next_div_children = next_div.find_elements(By.XPATH, "./div")
                            for child in next_div_children:
                                if self.is_comment_div(child):
                                    current_comment_divs.append(child)
                            
                            current_comment_count = len(current_comment_divs)
                            print(f"📊 Current comment count: {current_comment_count} (previous: {previous_comment_count}) [attempt {total_attempts}]")
                            
                            # Check if new comments were loaded
                            if current_comment_count > previous_comment_count:
                                new_comments = current_comment_count - previous_comment_count
                                print(f"✅ New comments detected! (+{new_comments})")
                                previous_comment_count = current_comment_count
                                no_new_comments_count = 0  # Reset counter
                            else:
                                no_new_comments_count += 1
                                print(f"⚠️ No new comments detected ({no_new_comments_count}/{max_no_new_comments})")
                            
                            # Check for stop flag
                            if self._stop_flag:
                                print("⏹️ Stop flag detected, breaking click loop")
                                break
                        
                        print(f"🏁 Enhanced click loop completed. Final comment count: {previous_comment_count} (total attempts: {total_attempts})")
                        
                        # Use the final comment divs for extraction
                        final_comment_divs = []
                        next_div_children = next_div.find_elements(By.XPATH, "./div")
                        for child in next_div_children:
                            if self.is_comment_div(child):
                                final_comment_divs.append(child)
                        
                        print(f"🎯 Final comment divs for extraction: {len(final_comment_divs)}")

                        if len(final_comment_divs) > 0:
                            # OPTIMIZED: Extract comment data with enhanced features from version 1
                            comments_data = []
                            seen_content = set()
                            
                            for i, element in enumerate(final_comment_divs):
                                if self._stop_flag:
                                    break
                                    
                                try:
                                    print(f"\n--- OPTIMIZED: Processing comment div {i+1}/{len(final_comment_divs)} ---")
                                    
                                    comment_data = self.extract_comment_data_optimized(element, i)
                                    
                                    if not comment_data:
                                        continue
                                    
                                    # Deduplication
                                    if comment_data['Name'] == "Unknown":
                                        print("  ✗ Skipped: no username found")
                                        continue
                                        
                                    # Check for duplicates using PostLink
                                    content_signature = f"{comment_data['Name']}_{comment_data['PostLink']}"
                                    if content_signature in seen_content:
                                        print("  ✗ Skipped: duplicate user")
                                        continue
                                    seen_content.add(content_signature)
                                    
                                    comment_data['Type'] = 'Comment'
                                    comment_data['Layout'] = self.current_layout
                                    comment_data['Source'] = 'OPTIMIZED All Comments Container'
                                    
                                    comments_data.append(comment_data)
                                    print(f"  ✅ Added: {comment_data['Name']} - PostLink: {comment_data['PostLink'][:70]}...")
                                    
                                except Exception as e:
                                    print(f"  Error processing comment div {i}: {e}")
                                    continue
                            
                            print(f"\n=== OPTIMIZED EXTRACTION COMPLETE: {len(comments_data)} comments ===")
                            return comments_data
                            
                    except Exception as e:
                        print(f"Error finding next div: {e}")
                        
                else:
                    print("❌ Could not find parent with html-div class for 'All comments' button")
                    
            else:
                print("❌ Could not find 'All comments' button")
                
        except Exception as e:
            print(f"❌ Error while searching for 'All comments' button's parent: {e}")
        
        # OPTIMIZED: Fallback extraction using multi-container approach (from version 1)
        print("🔄 OPTIMIZED: Using fallback multi-container extraction...")
        
        # Save page for debugging
        try:
            with open(f"debug_optimized_{self.current_layout}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Saved page to debug_optimized_{self.current_layout}.html")
        except:
            pass
        
        all_comment_elements = []
        
        # Strategy 1: Layout-specific selectors
        if self.current_layout == "www":
            selectors = [
                "//div[@role='article']",
                "//div[contains(@aria-label, 'Comment by')]",
                "//div[contains(@aria-label, 'Bình luận của')]",
                "//div[.//a[contains(@href, '/user/') or contains(@href, '/profile/')]]",
                "//div[.//h3//a[contains(@href, 'facebook.com')]]",
                # Additional selectors for better coverage
                "//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 20]",
                "//div[contains(@class, 'comment') or contains(@data-testid, 'comment')]"
            ]
        elif self.current_layout == "mobile":
            selectors = [
                "//div[@data-sigil='comment']",
                "//div[contains(@data-ft, 'comment')]",
                "//div[contains(@id, 'comment_')]",
                "//div[.//a[contains(@href, 'profile.php') or contains(@href, 'user.php')]]",
                # Additional mobile selectors
                "//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 15]"
            ]
        else:  # mbasic
            selectors = [
                "//div[@data-ft and contains(@data-ft, 'comment')]",
                "//div[contains(@id, 'comment_')]",
                "//table//div[.//a[contains(@href, 'profile.php')]]",
                "//div[.//a[contains(@href, 'profile.php?id=')]]",
                # Additional mbasic selectors
                "//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 10]"
            ]
        
        # Apply selectors to entire page
        for i, selector in enumerate(selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                print(f"Fallback search - Selector {i+1}: Found {len(elements)} elements")
                
                for elem in elements:
                    if elem not in all_comment_elements:
                        all_comment_elements.append(elem)
                        
            except Exception as e:
                print(f"Fallback search - Selector {i+1} failed: {e}")
                continue
        
        # Strategy 2: Fallback selectors with better filtering
        if len(all_comment_elements) < 10:
            print("⚠️ Not enough elements found, trying enhanced fallback...")
            
            fallback_selectors = [
                # Look for any div with profile links and meaningful text
                "//div[.//a[contains(@href, 'facebook.com/')] and string-length(normalize-space(text())) > 20]",
                "//div[string-length(normalize-space(text())) > 30 and .//a[@href]]",
                "//div[@role='article' and string-length(normalize-space(text())) > 20]",
                "//*[.//a[contains(@href, 'profile')] and string-length(normalize-space(text())) > 15]",
                # Additional patterns
                "//div[contains(@class, 'x') and .//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 25]"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"Enhanced fallback selector: Found {len(elements)} elements")
                    for elem in elements:
                        if elem not in all_comment_elements:
                            all_comment_elements.append(elem)
                    
                    # Stop if we found enough elements
                    if len(all_comment_elements) > 50:
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
        
        print(f"OPTIMIZED: Processing {len(all_comment_elements)} potential comment elements from fallback extraction...")
        
        # Process each element with optimized extraction
        for i, element in enumerate(all_comment_elements):
            if self._stop_flag:
                break
                
            try:
                print(f"\n--- OPTIMIZED Fallback Element {i+1}/{len(all_comment_elements)} ---")
                
                comment_data = self.extract_comment_data_optimized(element, i)
                
                if not comment_data:
                    continue
                
                # Deduplication
                if comment_data['Name'] == "Unknown":
                    print("  ✗ Skipped: no username found")
                    continue
                    
                # Check for duplicates using PostLink
                content_signature = f"{comment_data['Name']}_{comment_data['PostLink']}"
                if content_signature in seen_content:
                    print("  ✗ Skipped: duplicate user")
                    continue
                seen_content.add(content_signature)
                
                comment_data['Type'] = 'Comment'
                comment_data['Layout'] = self.current_layout
                comment_data['Source'] = 'OPTIMIZED Fallback Extraction'
                
                comments.append(comment_data)
                print(f"  ✅ Added: {comment_data['Name']} - PostLink: {comment_data['PostLink'][:70]}...")
                
            except Exception as e:
                print(f"  Error processing element {i}: {e}")
                continue
        
        print(f"\n=== OPTIMIZED FALLBACK EXTRACTION COMPLETE: {len(comments)} comments ===")
        return comments

    def extract_comment_data_optimized(self, element, index):
        """OPTIMIZED: Enhanced comment data extraction combining both versions"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 5:
                print(f"  ❌ Text too short: '{full_text}'")
                return None
            
            print(f"  OPTIMIZED Processing: '{full_text[:60]}...'")
            
            # Skip anonymous users
            if any(keyword in full_text.lower() for keyword in ['ẩn danh', 'người tham gia ẩn danh', 'anonymous']):
                print("  ⚠️ Skipping anonymous user comment")
                return None
            
            username = "Unknown"
            profile_href = ""
            uid = "Unknown"
            
            # OPTIMIZED: Enhanced username extraction combining both approaches
            print(f"    🎯 OPTIMIZED analysis of element structure...")
            
            try:
                all_links = element.find_elements(By.XPATH, ".//a")
                print(f"    Found {len(all_links)} total links in element")
                
                # Prioritize links that are more likely to be usernames
                potential_profile_links = []
                time_links = []
                
                for link_index, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        print(f"      Link {link_index+1}: Text='{link_text}' | Href={link_href[:60]}...")
                        
                        # Enhanced Facebook profile link detection
                        is_facebook_profile = ('facebook.com' in link_href and 
                                             ('profile.php' in link_href or 
                                              '/user/' in link_href or 
                                              'user.php' in link_href or
                                              re.search(r'facebook\.com/[^/]+/?$', link_href)))
                        
                        if is_facebook_profile:
                            # Enhanced name validation
                            is_valid_name = (link_text and 
                                           len(link_text) >= 2 and 
                                           len(link_text) <= 100 and
                                           not link_text.isdigit() and
                                           not link_text.startswith('http') and
                                           not re.match(r'^\d+$', link_text) and
                                           not any(ui in link_text.lower() for ui in [
                                               'like', 'reply', 'share', 'comment', 'thích', 'trả lời', 
                                               'chia sẻ', 'bình luận', 'ago', 'trước', 'min', 'hour', 
                                               'day', 'phút', 'giờ', 'ngày', 'ẩn danh', 'anonymous',
                                               'view', 'xem', 'show', 'hiển thị', 'see more', 'view more',
                                               'translate', 'dịch', 'hide', 'ẩn', 'report', 'báo cáo'
                                           ]))
                            
                            if is_valid_name:
                                # Calculate priority score for this link
                                priority_score = 0
                                
                                # Higher priority for shorter, cleaner names
                                if len(link_text) < 50:
                                    priority_score += 10
                                
                                # Higher priority for names with proper capitalization
                                if link_text[0].isupper():
                                    priority_score += 5
                                
                                # Higher priority for names with spaces (likely full names)
                                if ' ' in link_text:
                                    priority_score += 3
                                
                                # Enhanced UID extraction with more patterns
                                extracted_uid = "Unknown"
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
                                
                                print(f"        🔍 OPTIMIZED: Extracting UID from: {link_href}")
                                
                                for pattern_idx, pattern in enumerate(uid_patterns, 1):
                                    try:
                                        uid_match = re.search(pattern, link_href)
                                        if uid_match:
                                            potential_uid = uid_match.group(1)
                                            
                                            # Validate UID
                                            if potential_uid.isdigit() and len(potential_uid) >= 8:
                                                extracted_uid = potential_uid
                                                priority_score += 10
                                                print(f"        ✅ UID found with pattern {pattern_idx}: {extracted_uid}")
                                                break
                                            elif not potential_uid.isdigit() and len(potential_uid) >= 3:
                                                extracted_uid = f"username:{potential_uid}"
                                                priority_score += 5
                                                print(f"        ✅ Username found with pattern {pattern_idx}: {potential_uid}")
                                                break
                                                
                                    except Exception as e:
                                        print(f"        ⚠️ Pattern {pattern_idx} failed: {e}")
                                        continue
                                
                                potential_profile_links.append({
                                    'text': link_text,
                                    'href': link_href,
                                    'uid': extracted_uid,
                                    'priority': priority_score,
                                    'index': link_index
                                })
                                
                                print(f"      ✅ OPTIMIZED: Valid profile candidate: {link_text} (priority: {priority_score}) -> UID: {extracted_uid}")
                        
                        # Enhanced time link detection
                        time_patterns = [
                            r'^\d+\s*ngày',           # "1 ngày", "2 ngày", "4 ngày"
                            r'^\d+\s*giờ',            # "1 giờ", "2 giờ"  
                            r'^\d+\s*phút',           # "1 phút", "30 phút"
                            r'^\d+\s*giây',           # "1 giây", "45 giây"
                            r'^\d+\s*tuần',           # "1 tuần", "2 tuần"
                            r'^\d+\s*tháng',          # "1 tháng", "2 tháng"
                            r'^\d+\s*năm',            # "1 năm", "2 năm"
                            r'^\d+\s*day',            # "1 day", "2 days"
                            r'^\d+\s*hour',           # "1 hour", "2 hours"
                            r'^\d+\s*min',            # "1 min", "30 mins"
                            r'^\d+\s*sec',            # "1 sec", "45 secs"
                            r'^\d+\s*week',           # "1 week", "2 weeks"
                            r'^\d+\s*month',          # "1 month", "2 months"
                            r'^\d+\s*year',           # "1 year", "2 years"
                            r'^\d+\s*h$',             # "1h", "2h"
                            r'^\d+\s*m$',             # "1m", "30m"
                            r'^\d+\s*d$',             # "1d", "2d"
                            r'^\d+\s*w$',             # "1w", "2w"
                            r'^\d+\s*y$',             # "1y", "2y"
                        ]
                        
                        # Check if text matches time patterns
                        is_time_text = False
                        matched_pattern = ""
                        
                        if link_text:
                            text_lower = link_text.lower().strip()
                            
                            # Check against patterns
                            for pattern in time_patterns:
                                if re.match(pattern, text_lower):
                                    is_time_text = True
                                    matched_pattern = pattern
                                    print(f"        ✅ Time pattern matched: '{pattern}' for '{text_lower}'")
                                    break
                            
                            # Check special cases
                            special_time_cases = ['just now', 'vừa xong', 'now', 'bây giờ', 'vài giây', 'một lúc']
                            if not is_time_text and text_lower in special_time_cases:
                                is_time_text = True
                                matched_pattern = "special_case"
                                print(f"        ✅ Special time text: '{text_lower}'")
                        
                        # Enhanced Facebook comment link detection
                        is_facebook_comment_link = False
                        if link_href:
                            # Must contain facebook.com and comment_id
                            has_facebook = 'facebook.com' in link_href
                            has_comment_id = 'comment_id=' in link_href
                            has_groups = '/groups/' in link_href
                            has_posts = '/posts/' in link_href
                            
                            is_facebook_comment_link = has_facebook and has_comment_id and has_groups and has_posts
                            
                            print(f"        📊 Link analysis: FB={has_facebook}, Comment={has_comment_id}, Groups={has_groups}, Posts={has_posts}")
                        
                        print(f"        🎯 Final: Time text={is_time_text}, FB comment link={is_facebook_comment_link}")
                        
                        # Accept as time link if it has time text AND Facebook comment link
                        if is_time_text and is_facebook_comment_link:
                            # Clean the href
                            cleaned_href = link_href.replace('&amp;', '&')
                            
                            time_links.append({
                                'text': link_text,
                                'href': cleaned_href,
                                'original_href': link_href,
                                'pattern': matched_pattern,
                                'index': link_index
                            })
                            print(f"        🎯 OPTIMIZED: Added time link: '{link_text}' (pattern: {matched_pattern})")
                            print(f"             Href: {cleaned_href[:80]}...")
                        
                        # Relaxed criteria for potential time links
                        elif (link_href and 'facebook.com' in link_href and 'comment_id=' in link_href and 
                              link_text and len(link_text) <= 15 and 
                              not any(ui_word in link_text.lower() for ui_word in ['like', 'reply', 'share', 'thích', 'trả lời', 'chia sẻ', 'view', 'xem'])):
                            
                            cleaned_href = link_href.replace('&amp;', '&')
                            
                            time_links.append({
                                'text': link_text,
                                'href': cleaned_href,
                                'original_href': link_href,
                                'pattern': 'relaxed_criteria',
                                'index': link_index
                            })
                            print(f"        🎯 OPTIMIZED: Added potential time link (relaxed): '{link_text}'")
                            print(f"             Href: {cleaned_href[:80]}...")
                            
                    except Exception as e:
                        print(f"        ❌ Error processing link {link_index+1}: {e}")
                        continue
                
                print(f"    📊 OPTIMIZED: Found {len(time_links)} time links total")
                
                # Select the best profile link based on priority
                if potential_profile_links:
                    # Sort by priority (highest first)
                    potential_profile_links.sort(key=lambda x: x['priority'], reverse=True)
                    
                    best_link = potential_profile_links[0]
                    username = best_link['text']
                    profile_href = best_link['href']
                    uid = best_link['uid']
                    
                    print(f"      🎯 OPTIMIZED: Selected best profile: {username} (priority: {best_link['priority']}) -> UID: {uid}")
                
                # Get PostLink from time link with enhanced selection
                comment_post_link = ""
                if time_links:
                    # Select the best time link (prefer ones with clear time text)
                    best_time_link = None
                    
                    for time_link in time_links:
                        link_text = time_link['text'].lower().strip()
                        
                        # Priority 1: Clear time patterns
                        if re.match(r'^\d+\s*(ngày|giờ|phút|day|hour|min)', link_text):
                            best_time_link = time_link
                            print(f"      🎯 OPTIMIZED: Selected priority time link: '{time_link['text']}'")
                            break
                        
                        # Priority 2: Any time-like text
                        elif not best_time_link:
                            best_time_link = time_link
                    
                    if best_time_link:
                        comment_post_link = best_time_link['href']
                        
                        # Clean up the URL (remove HTML entities)
                        comment_post_link = comment_post_link.replace('&amp;', '&')
                        
                        print(f"      🔗 OPTIMIZED: Extracted PostLink from time link '{best_time_link['text']}':")
                        print(f"          {comment_post_link[:100]}...")
                    else:
                        print(f"      ⚠️ Time links found but none selected")
                else:
                    print(f"      ⚠️ No time links found in this comment")
                
                # Fallback if no time link PostLink found
                if not comment_post_link:
                    comment_post_link = self.generate_post_link(uid, username)
                    print(f"      🔗 OPTIMIZED: Using generated fallback PostLink: {comment_post_link[:80]}...")
                
            except Exception as e:
                print(f"    Error in OPTIMIZED method: {e}")
            
            # Final validation
            if username == "Unknown":
                print("  ❌ OPTIMIZED extraction failed for this element")
                return None
                
            print(f"  ✅ OPTIMIZED: Successfully extracted username: {username}")
            
            # Use PostLink from time link if available, otherwise generate
            final_post_link = comment_post_link if comment_post_link else self.generate_post_link(uid, username)
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,  # Keep original profile link
                "PostLink": final_post_link,  # OPTIMIZED: PostLink from time link or generated
                "CommentLink": "",
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "OPTIMIZED Multi-Method Extraction",
                "PostLinkSource": "TimeLink" if comment_post_link else "Generated"
            }
            
        except Exception as e:
            print(f"Error in OPTIMIZED extraction: {e}")
            return None

    def expand_groups_comments(self, max_iterations=50):
        """OPTIMIZED: Enhanced expansion with better logic"""
        print(f"=== EXPANDING GROUPS COMMENTS (OPTIMIZED) ===")
        
        for iteration in range(max_iterations):
            if self._stop_flag:
                break
                
            print(f"[Iteration {iteration+1}] OPTIMIZED expanding...")
            
            # Regular scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            
            # Look for expand links
            expand_selectors = [
                "//a[contains(normalize-space(text()),'View more comments')]",
                "//a[contains(normalize-space(text()),'Xem thêm bình luận')]",
                "//a[contains(normalize-space(text()),'Show more')]",
                "//a[contains(normalize-space(text()),'See more')]",
                "//div[@role='button' and (contains(normalize-space(text()),'more') or contains(normalize-space(text()),'thêm'))]",
                # Additional expand selectors
                "//span[contains(normalize-space(text()),'View more') or contains(normalize-space(text()),'Xem thêm')]",
                "//*[@role='button' and (contains(normalize-space(text()),'more comments') or contains(normalize-space(text()),'thêm bình luận'))]"
            ]
            
            expanded = False
            for selector in expand_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            try:
                                # Scroll element into view before clicking
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                                time.sleep(1)
                                
                                elem.click()
                                expanded = True
                                print(f"    ✓ OPTIMIZED: Clicked: {elem.text}")
                                time.sleep(3)
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    expanded = True
                                    print(f"    ✓ OPTIMIZED: JS clicked: {elem.text}")
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
        
        print("=== OPTIMIZED EXPANSION COMPLETE ===")

    def scrape_all_comments(self, limit=0, resolve_uid=True, progress_callback=None):
        """OPTIMIZED: Main scraping orchestrator combining best features"""
        print(f"=== STARTING OPTIMIZED GROUPS SCRAPING ===")
        
        # Step 1: Expand all content with optimized logic
        self.expand_groups_comments()
        
        if self._stop_flag:
            return []
        
        # Step 2: Extract comments with optimized logic
        comments = self.extract_groups_comments()
        
        # Step 3: Apply limit
        if limit > 0:
            comments = comments[:limit]
        
        # Step 4: Progress reporting
        if progress_callback:
            progress_callback(len(comments))
        
        return comments

    def close(self):
        try: 
            self.driver.quit()
        except: 
            pass

# ----------------------------
# OPTIMIZED GUI
# ----------------------------

class FBGroupsAppGUI:
    def __init__(self, root):
        self.root = root
        root.title("🚀 FB Groups Comment Scraper - OPTIMIZED")
        root.geometry("1100x950")
        root.configure(bg="#0a0a0a")

        # Main frame
        main_frame = tk.Frame(root, bg="#0a0a0a")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_frame = tk.Frame(main_frame, bg="#0a0a0a")
        header_frame.pack(fill="x", pady=(0,20))
        
        title_label = tk.Label(header_frame, text="🚀 Facebook Groups Comment Scraper - OPTIMIZED", 
                              font=("Arial", 20, "bold"), bg="#0a0a0a", fg="#00d4aa")
        title_label.pack()
        
        # OPTIMIZED: Updated subtitle
        subtitle_text = "🚀 OPTIMIZED - Best features from both versions: Enhanced scroll + PostLink generation + Multi-container support"
        subtitle_label = tk.Label(header_frame, text=subtitle_text, 
                                 font=("Arial", 11), bg="#0a0a0a", fg="#888888")
        subtitle_label.pack(pady=(5,0))

        # Input section
        input_frame = tk.LabelFrame(main_frame, text="📝 Thông tin bài viết Groups", font=("Arial", 12, "bold"), 
                                   bg="#0a0a0a", fg="#00d4aa", relief="groove", bd=2)
        input_frame.pack(fill="x", pady=(0,15))

        tk.Label(input_frame, text="🔗 Link bài viết trong Groups:", bg="#0a0a0a", fg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15,5))
        self.entry_url = tk.Entry(input_frame, width=100, font=("Arial", 9), bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff")
        self.entry_url.pack(fill="x", padx=15, pady=(0,10))

        tk.Label(input_frame, text="🍪 Cookie Facebook (để truy cập Groups):", bg="#0a0a0a", fg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5,5))
        self.txt_cookie = tk.Text(input_frame, height=4, font=("Arial", 8), bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff")
        self.txt_cookie.pack(fill="x", padx=15, pady=(0,15))

        # Options section
        options_frame = tk.LabelFrame(main_frame, text="🚀 Cấu hình OPTIMIZED Version", font=("Arial", 12, "bold"), 
                                     bg="#0a0a0a", fg="#00d4aa", relief="groove", bd=2)
        options_frame.pack(fill="x", pady=(0,15))
        
        opt_grid = tk.Frame(options_frame, bg="#0a0a0a")
        opt_grid.pack(fill="x", padx=15, pady=15)
        
        # Options grid
        tk.Label(opt_grid, text="📊 Số lượng comment:", bg="#0a0a0a", fg="#ffffff").grid(row=0, column=0, sticky="w")
        self.entry_limit = tk.Entry(opt_grid, width=10, bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff")
        self.entry_limit.insert(0, "0")
        self.entry_limit.grid(row=0, column=1, sticky="w", padx=(10,20))
        tk.Label(opt_grid, text="(0 = tất cả)", bg="#0a0a0a", fg="#6c757d").grid(row=0, column=2, sticky="w")

        self.headless_var = tk.BooleanVar(value=False)  # Default to visible for debugging
        tk.Checkbutton(opt_grid, text="👻 Chạy ẩn", variable=self.headless_var,
                      bg="#0a0a0a", fg="#ffffff", font=("Arial", 9), selectcolor="#1a1a1a").grid(row=1, column=0, sticky="w", pady=(10,0))

        self.resolve_uid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_grid, text="🆔 Lấy UID", variable=self.resolve_uid_var, 
                      bg="#0a0a0a", fg="#ffffff", font=("Arial", 9), selectcolor="#1a1a1a").grid(row=1, column=1, sticky="w", pady=(10,0))

        # File section
        file_frame = tk.LabelFrame(main_frame, text="💾 Xuất kết quả", font=("Arial", 12, "bold"), 
                                  bg="#0a0a0a", fg="#00d4aa", relief="groove", bd=2)
        file_frame.pack(fill="x", pady=(0,15))
        
        file_row = tk.Frame(file_frame, bg="#0a0a0a")
        file_row.pack(fill="x", padx=15, pady=15)
        
        self.entry_file = tk.Entry(file_row, width=70, font=("Arial", 9), bg="#1a1a1a", fg="#ffffff", insertbackground="#ffffff")
        current_date = datetime.now().strftime("%Y%m%d")
        self.entry_file.insert(0, f"facebook_groups_comments_OPTIMIZED_{current_date}.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        self.btn_choose = tk.Button(file_row, text="📁 Chọn", command=self.choose_file, 
                 bg="#17a2b8", fg="white", font=("Arial", 9), relief="flat", bd=0)
        self.btn_choose.pack(side="right", padx=(10,0))

        # Status section
        status_frame = tk.LabelFrame(main_frame, text="📊 Trạng thái thực thi - OPTIMIZED", font=("Arial", 12, "bold"), 
                                    bg="#0a0a0a", fg="#00d4aa", relief="groove", bd=2)
        status_frame.pack(fill="x", pady=(0,15))
        
        self.lbl_status = tk.Label(status_frame, text="✅ OPTIMIZED scraper sẵn sàng - Kết hợp tốt nhất từ cả 2 phiên bản!", fg="#00d4aa", 
                                  wraplength=900, justify="left", font=("Arial", 11), bg="#0a0a0a")
        self.lbl_status.pack(anchor="w", padx=15, pady=(15,5))

        # OPTIMIZED: Updated features description
        optimized_features_text = ("💡 OPTIMIZED features: 1) Enhanced scroll từ version 2, 2) PostLink generation từ version 1, "
                                  "3) Multi-container support, 4) Time link extraction, 5) Comprehensive fallback strategies, "
                                  "6) Enhanced debugging, 7) Progressive loading with better click detection")
        
        self.lbl_progress_detail = tk.Label(status_frame, text=optimized_features_text,
                                          fg="#888888", wraplength=900, justify="left", font=("Arial", 9), bg="#0a0a0a")
        self.lbl_progress_detail.pack(anchor="w", padx=15, pady=(0,10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(0,15))

        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#0a0a0a")
        button_frame.pack(fill="x", pady=20)
        
        self.btn_start = tk.Button(button_frame, text="🚀 Bắt đầu OPTIMIZED Scraping", bg="#00d4aa", fg="black", 
                                  font=("Arial", 14, "bold"), command=self.start_scrape_thread, 
                                  pady=12, padx=40, relief="flat", bd=0)
        self.btn_start.pack(side="left")

        self.btn_stop = tk.Button(button_frame, text="⏹️ Dừng", bg="#dc3545", fg="white", 
                                 font=("Arial", 14, "bold"), command=self.stop_scrape, 
                                 state=tk.DISABLED, pady=12, padx=40, relief="flat", bd=0)
        self.btn_stop.pack(side="left", padx=(25,0))

        self.progress_var = tk.IntVar(value=0)
        self.progress_label = tk.Label(button_frame, textvariable=self.progress_var, fg="#00d4aa", 
                                     font=("Arial", 18, "bold"), bg="#0a0a0a")
        self.progress_label.pack(side="right")

        self._scrape_thread = None
        self._stop_flag = False
        self.scraper = None

        # Apply enhanced dark theme
        self._apply_enhanced_dark_theme()

        # Beautify buttons with modern styling
        self._beautify_button(self.btn_start, base_bg="#00d4aa", hover_bg="#00b894", active_bg="#00a085")
        self._beautify_button(self.btn_stop, base_bg="#dc3545", hover_bg="#c82333", active_bg="#bd2130")
        self._beautify_button(self.btn_choose, base_bg="#17a2b8", hover_bg="#138496", active_bg="#117a8b")

    def _apply_enhanced_dark_theme(self):
        """Apply enhanced dark theme for OPTIMIZED version."""
        dark_bg = "#0a0a0a"
        surface_bg = "#1a1a1a"
        light_fg = "#ffffff"
        accent_fg = "#00d4aa"

        def apply(widget):
            try:
                if 'background' in widget.configure():
                    widget.configure(bg=dark_bg)
            except Exception:
                pass

            try:
                if isinstance(widget, tk.Button):
                    pass  # Skip buttons to preserve custom styling
                else:
                    cfg = widget.configure()
                    if 'foreground' in cfg:
                        current_fg = str(widget.cget('fg')).lower()
                        if current_fg in ('black', '#000000', 'systemwindowtext'):
                            widget.configure(fg=light_fg)
            except Exception:
                pass

            for child in widget.winfo_children():
                apply(child)

        apply(self.root)

        # Enhanced ttk styling
        try:
            style = ttk.Style()
            try:
                style.theme_use('clam')
            except Exception:
                pass
            style.configure("TProgressbar",
                            troughcolor=surface_bg,
                            background=accent_fg,
                            bordercolor=surface_bg,
                            lightcolor=surface_bg,
                            darkcolor=surface_bg)
        except Exception:
            pass

    def _beautify_button(self, button, base_bg="#00d4aa", hover_bg="#00b894", active_bg="#00a085"):
        """Apply modern flat styling and hover/active effects to tk.Button."""
        try:
            button.configure(
                bg=base_bg,
                fg="#000000" if base_bg in ["#00d4aa"] else "#ffffff",
                activebackground=active_bg,
                activeforeground="#000000" if base_bg in ["#00d4aa"] else "#ffffff",
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
            title="Chọn file để lưu OPTIMIZED Groups comments"
        )
        if f:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, f)

    def start_scrape_thread(self):
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "facebook_groups_comments_OPTIMIZED.xlsx"
        
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
        self.lbl_status.config(text="🔄 Đang khởi động OPTIMIZED Groups scraper...", fg="#ffc107")
        self.lbl_progress_detail.config(text="⏳ Initializing OPTIMIZED extraction with best features from both versions...")
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
        self.lbl_status.config(text="⏹️ Đang dừng OPTIMIZED scraper...", fg="#dc3545")
        self.btn_stop.config(state=tk.DISABLED)

    def _progress_cb(self, count):
        self.progress_var.set(count)
        self.lbl_status.config(text=f"📈 OPTIMIZED processing... Đã lấy {count} comments", fg="#00d4aa")
        self.root.update_idletasks()

    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, resolve_uid):
        try:
            # Initialize
            self.lbl_status.config(text="🌐 Khởi tạo OPTIMIZED Groups scraper...", fg="#ffc107")
            self.scraper = FacebookGroupsScraper(cookie_str, headless=headless)
            
            if self._stop_flag: return
            
            # Load post
            self.lbl_status.config(text="📄 Đang tải bài viết Groups với OPTIMIZED logic...", fg="#ffc107")
            self.lbl_progress_detail.config(text="⏳ Loading post with enhanced scroll and PostLink generation...")
            success = self.scraper.load_post(url)
            
            if not success:
                self.lbl_status.config(text="❌ Không thể tải bài viết Groups", fg="#dc3545")
                self.lbl_progress_detail.config(text="💡 Kiểm tra: 1) Cookie valid, 2) Quyền truy cập Groups, 3) Link chính xác")
                return
            
            # Show detected layout
            layout = getattr(self.scraper, 'current_layout', 'unknown')
            self.lbl_progress_detail.config(text=f"🎯 Layout detected: {layout} - Using OPTIMIZED extraction methods...")
                
            if self._stop_flag: return
            
            # Scrape with OPTIMIZED logic
            self.lbl_status.config(text=f"🔍 OPTIMIZED Groups extraction ({layout})...", fg="#ffc107")
            self.lbl_progress_detail.config(text="⏳ Using enhanced scroll + PostLink generation + multi-container support...")
            
            comments = self.scraper.scrape_all_comments(limit=limit, resolve_uid=resolve_uid, 
                                                       progress_callback=self._progress_cb)
            
            if self._stop_flag: return
            
            # Save
            self.lbl_status.config(text="💾 Đang lưu OPTIMIZED Groups data...", fg="#ffc107")
            
            if comments:
                df = pd.DataFrame(comments)
                
                # Add metadata
                df.insert(0, 'STT', range(1, len(df) + 1))
                df['Source'] = 'Facebook Groups - OPTIMIZED'
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
                uid_count = len([c for c in comments if c['UID'] != 'Unknown'])
                post_links = len([c for c in comments if c['PostLink']])
                time_links = len([c for c in comments if c.get('PostLinkSource') == 'TimeLink'])
                
                self.lbl_status.config(text=f"🎉 OPTIMIZED GROUPS SCRAPING HOÀN THÀNH!", fg="#00d4aa")
                self.lbl_progress_detail.config(text=f"📊 OPTIMIZED Results: {len(comments)} comments | {unique_users} unique users | {profile_links} profile links | {uid_count} UIDs | {post_links} PostLinks | {time_links} TimeLinks | Layout: {layout}")
                
                print(f"🚀 OPTIMIZED SCRAPING COMPLETE!")
                print(f"   📊 Results: {len(comments)} total comments")
                print(f"   👥 Unique users: {unique_users}")
                print(f"   🔗 Profile links: {profile_links}")
                print(f"   🆔 UIDs extracted: {uid_count}")
                print(f"   📎 PostLinks generated: {post_links}")
                print(f"   ⏰ TimeLinks extracted: {time_links}")
                print(f"   📱 Layout used: {layout}")
                print(f"   💾 Saved to: {file_out}")
                print(f"   🔍 Debug files: debug_optimized_{layout}.html")
                
            else:
                self.lbl_status.config(text="⚠️ Không tìm thấy comment với OPTIMIZED logic", fg="#ffc107")
                self.lbl_progress_detail.config(text=f"💡 Layout: {layout} | Kiểm tra debug files để phân tích Facebook structure")
                
                print(f"⚠️ No comments found with OPTIMIZED logic")
                print(f"   📱 Layout: {layout}")
                print(f"   🔍 Debug files created: debug_optimized_{layout}.html")
                print(f"   💡 OPTIMIZED suggestions:")
                print(f"      1. Check if you have access to the Facebook Group")
                print(f"      2. Verify the post URL is correct and public in the group")
                print(f"      3. Try running without headless mode to see what's happening")
                print(f"      4. Check the debug HTML file to understand the page structure")
                print(f"      5. OPTIMIZED version combines best features - check both extraction methods")
                
        except Exception as e:
            error_msg = str(e)[:120]
            self.lbl_status.config(text=f"❌ Lỗi OPTIMIZED scraping: {error_msg}...", fg="#dc3545")
            self.lbl_progress_detail.config(text="🔍 Xem console để biết chi tiết. OPTIMIZED version cung cấp comprehensive debug info.")
            print(f"OPTIMIZED Groups scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.stop()
            if self.scraper: 
                self.scraper.close()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

# ----------------------------
# Run OPTIMIZED app
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FBGroupsAppGUI(root)
    root.mainloop()