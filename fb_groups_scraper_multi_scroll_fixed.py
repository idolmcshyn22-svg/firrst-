# fb_groups_scraper_multi_scroll_fixed.py - FIXED: Scroll ALL containers, not just the first one

import time, random, threading, re, requests, pandas as pd
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
# MULTI-SCROLL FIXED Facebook Groups Scraper
# ----------------------------

class FacebookGroupsScraper:
    def __init__(self, cookie_str, headless=True):
        # FIXED: Store current post info for PostLink generation
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
        
        # FIXED: Extract post info for PostLink generation
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
                
                # Try to switch to "All comments" view
                self._switch_to_all_comments()
                
                return True
                    
            except Exception as e:
                print(f"Failed to load {url_attempt}: {e}")
                continue
        
        print("❌ Failed to load post with any URL variant")
        return False

    def _extract_post_info(self, post_url):
        """FIXED: Extract group and post IDs for PostLink generation"""
        try:
            print(f"🔍 FIXED: Extracting post info from URL: {post_url}")
            
            # FIXED: Use the same parsing logic as your example
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
        """FIXED: Generate link to the original post with comment_id like your example"""
        try:
            if not self.current_group_id or not self.current_post_id:
                return ""
            
            # FIXED: Generate link to the original Groups post
            # Format: https://www.facebook.com/groups/GROUP_ID/posts/POST_ID/
            post_link = f"https://www.facebook.com/groups/{self.current_group_id}/posts/{self.current_post_id}/"
            
            # FIXED: Add comment_id if available (like your example)
            if self.current_comment_id:
                post_link += f"?comment_id={self.current_comment_id}"
            
            print(f"🔗 FIXED: Generated post link: {post_link}")
            return post_link
            
        except Exception as e:
            print(f"❌ Error generating post link: {e}")
            return ""

    def scroll_to_load_all_comments(self):
        """FIXED: Scroll through ALL comments containers to load all content"""
        print("📜 FIXED: Starting scroll for ALL comments containers...")
        
        try:
            # FIXED: Find ALL containers that need scrolling (including new container type)
            container_selectors = [
                # Primary: Your original specific container
                "//div[@class='x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq' and @data-visualcompletion='ignore' and @data-thumb='1']",
                
                # FIXED: Your new container type
                "//div[@class='x9f619 x1s85apg xtijo5x xg01cxk xexx8yu x18d9i69 x135b78x x11lfxj5 x47corl x10l6tqk x13vifvy x1n4smgl x1d8287x x19991ni xwji4o3 x1kky2od' and @data-visualcompletion='ignore' and @data-thumb='1']",
                
                # Fallback: Partial class matches for both types
                "//div[contains(@class, 'x14nfmen') and contains(@class, 'x1s85apg') and @data-thumb='1']",
                "//div[contains(@class, 'x9f619') and contains(@class, 'x1s85apg') and @data-thumb='1']",
                
                # Secondary: Any container with data-thumb="1" and significant height
                "//div[@data-visualcompletion='ignore' and @data-thumb='1']",
                
                # Tertiary: Any scrollable container with data-thumb
                "//div[@data-thumb='1']"
            ]
            
            all_containers = []
            
            # FIXED: Collect ALL potential containers
            for selector_idx, selector in enumerate(container_selectors, 1):
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    print(f"Selector {selector_idx}: Found {len(containers)} containers")
                    
                    for container in containers:
                        if container not in all_containers:
                            all_containers.append(container)
                            
                except Exception as e:
                    print(f"Selector {selector_idx} failed: {e}")
                    continue
            
            if not all_containers:
                print("❌ No suitable containers found for comment scrolling")
                return False
            
            print(f"🎯 FIXED: Found {len(all_containers)} total containers to process")
            
            # FIXED: Analyze ALL containers and prioritize them
            scrollable_containers = []
            
            for idx, container in enumerate(all_containers, 1):
                try:
                    # Get multiple height measurements
                    style = container.get_attribute('style') or ""
                    height_match = re.search(r'height:\s*(\d+)px', style)
                    style_height = int(height_match.group(1)) if height_match else 0
                    
                    offset_height = self.driver.execute_script("return arguments[0].offsetHeight;", container)
                    scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
                    client_height = self.driver.execute_script("return arguments[0].clientHeight;", container)
                    
                    # Get container position
                    rect = container.rect
                    container_top = rect['y']
                    
                    # Check if container is scrollable
                    is_scrollable = scroll_height > client_height
                    
                    actual_height = max(style_height, offset_height, scroll_height)
                    
                    print(f"📐 Container {idx}: height={actual_height}px (style:{style_height}, offset:{offset_height}, scroll:{scroll_height}, client:{client_height})")
                    print(f"    Position: top={container_top}px, scrollable={is_scrollable}")
                    
                    # FIXED: Include containers with reasonable height (not just the largest)
                    if actual_height >= 100:  # Include more containers
                        scrollable_containers.append({
                            'container': container,
                            'height': actual_height,
                            'top': container_top,
                            'scrollable': is_scrollable,
                            'scroll_height': scroll_height,
                            'client_height': client_height,
                            'index': idx
                        })
                        print(f"    ✅ Added to scrollable list")
                    else:
                        print(f"    ❌ Height too small, skipped")
                        
                except Exception as e:
                    print(f"Container {idx}: error analyzing - {e}")
                    continue
            
            if not scrollable_containers:
                print("❌ No containers with sufficient height found")
                return False
            
            # FIXED: Sort containers by height (largest first) then by position
            scrollable_containers.sort(key=lambda x: (-x['height'], x['top']))
            
            print(f"🎯 FIXED: Will scroll {len(scrollable_containers)} containers in priority order")
            
            # FIXED: Scroll EACH container individually
            successfully_scrolled = 0
            
            for container_info in scrollable_containers:
                if self._stop_flag:
                    break
                    
                container = container_info['container']
                height = container_info['height']
                top = container_info['top']
                is_scrollable = container_info['scrollable']
                index = container_info['index']
                
                print(f"\n🔄 FIXED: Scrolling container {index} (height: {height}px, top: {top}px)")
                
                try:
                    # Method 1: Try scrolling the container itself if it's scrollable
                    if is_scrollable:
                        print(f"  📜 Method 1: Direct container scroll...")
                        success = self.scroll_individual_container(container, height)
                        if success:
                            successfully_scrolled += 1
                            print(f"  ✅ Container {index} scrolled successfully")
                        else:
                            print(f"  ⚠️ Container {index} direct scroll failed")
                    
                    # Method 2: Scroll main window to cover this container area
                    print(f"  📜 Method 2: Main window scroll for container {index}...")
                    success = self.scroll_window_for_container(container, height, top)
                    if success:
                        print(f"  ✅ Window scroll for container {index} completed")
                    else:
                        print(f"  ⚠️ Window scroll for container {index} had issues")
                        
                except Exception as e:
                    print(f"  ❌ Error scrolling container {index}: {e}")
                    continue
            
            print(f"\n🎯 FIXED: Completed scrolling {successfully_scrolled}/{len(scrollable_containers)} containers")
            
            # FIXED: Final comprehensive scroll to ensure everything is loaded
            print(f"🔄 FIXED: Final comprehensive scroll...")
            self.final_comprehensive_scroll()
            
            return True
            
        except Exception as e:
            print(f"❌ Error during FIXED multi-container scrolling: {e}")
            return False

    def scroll_individual_container(self, container, height):
        """FIXED: Scroll an individual container to its absolute bottom"""
        print(f"  🎯 FIXED: Scrolling individual container (height: {height}px)...")
        
        try:
            # FIXED: Check for transform/scale containers (like your new container)
            container_style = container.get_attribute('style') or ""
            has_transform = 'transform:' in container_style or 'matrix3d' in container_style
            has_scale = 'scale(' in container_style
            
            if has_transform or has_scale:
                print(f"    🎯 FIXED: Detected transform/scale container, using special scroll logic...")
                return self.scroll_transform_container(container, height, container_style)
            
            # Get container scroll properties
            scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
            client_height = self.driver.execute_script("return arguments[0].clientHeight;", container)
            max_scroll = scroll_height - client_height
            
            if max_scroll <= 0:
                print(f"    ⚠️ Container not scrollable (scroll:{scroll_height}, client:{client_height})")
                return False
            
            print(f"    📊 Container scroll info: max_scroll={max_scroll}px")
            
            # FIXED: Progressive scroll with multiple bottom attempts
            scroll_step = 400
            current_scroll = 0
            
            # Progressive scroll
            while current_scroll < max_scroll:
                current_scroll = min(current_scroll + scroll_step, max_scroll)
                self.driver.execute_script(f"arguments[0].scrollTop = {current_scroll};", container)
                time.sleep(2)
                
                actual_scroll = self.driver.execute_script("return arguments[0].scrollTop;", container)
                print(f"    📜 Scrolled to: {actual_scroll}px / {max_scroll}px")
                
                if actual_scroll >= max_scroll - 10:
                    break
            
            # FIXED: Force scroll to absolute bottom multiple times
            for attempt in range(10):
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                time.sleep(2)
                
                final_scroll = self.driver.execute_script("return arguments[0].scrollTop;", container)
                final_max = self.driver.execute_script("return arguments[0].scrollHeight - arguments[0].clientHeight;", container)
                
                print(f"    🎯 Bottom attempt {attempt+1}: {final_scroll}px / {final_max}px")
                
                if final_scroll >= final_max - 5:
                    print(f"    ✅ Reached absolute bottom of container")
                    break
            
            return True
            
        except Exception as e:
            print(f"    ❌ Error in individual container scroll: {e}")
            return False

    def scroll_transform_container(self, container, height, container_style):
        """FIXED: Special scroll logic for containers with transform/scale"""
        print(f"  🎯 FIXED: Scrolling transform/scale container...")
        
        try:
            print(f"    📊 Container style: {container_style[:100]}...")
            
            # FIXED: For transform containers, focus on main window scroll
            # These containers are often visual overlays that don't scroll directly
            
            # Get container position
            rect = container.rect
            container_top = rect['y']
            container_height = rect['height']
            container_bottom = container_top + container_height
            
            print(f"    📍 Transform container bounds: {container_top}px to {container_bottom}px (height: {container_height}px)")
            
            # FIXED: Intensive scroll sequence for transform containers
            scroll_attempts = []
            
            # Generate intensive scroll positions
            current_pos = max(0, container_top - 500)
            while current_pos <= container_bottom + 1000:
                scroll_attempts.append(current_pos)
                current_pos += 200  # Smaller increments for transform containers
            
            # Add page bottom
            page_height = self.driver.execute_script("return document.body.scrollHeight;")
            scroll_attempts.append(page_height)
            
            print(f"    📜 Generated {len(scroll_attempts)} intensive scroll positions")
            
            # FIXED: Execute intensive scroll sequence
            for i, scroll_pos in enumerate(scroll_attempts):
                if self._stop_flag:
                    break
                    
                print(f"    📜 Transform scroll {i+1}/{len(scroll_attempts)}: {scroll_pos}px")
                
                # Scroll to position
                self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(2.5)  # Longer wait for transform containers
                
                # Check for page expansion
                new_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                if new_page_height > page_height + 100:
                    print(f"      🎯 Transform scroll triggered content: {page_height}px -> {new_page_height}px")
                    page_height = new_page_height
                    # Add new positions
                    additional_positions = range(scroll_pos + 200, new_page_height + 200, 200)
                    scroll_attempts.extend(additional_positions)
            
            # FIXED: Final bottom verification for transform containers
            print(f"    🔄 Final verification for transform container...")
            
            for final_attempt in range(15):  # More attempts for transform containers
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                current_height = self.driver.execute_script("return document.body.scrollHeight;")
                window_height = self.driver.execute_script("return window.innerHeight;")
                
                print(f"      Transform final {final_attempt+1}/15: scroll={current_scroll}px, height={current_height}px")
                
                if current_scroll >= current_height - window_height - 20:
                    print(f"      ✅ Transform container: confirmed at bottom")
                    break
            
            print(f"    ✅ Transform container scroll completed")
            return True
            
        except Exception as e:
            print(f"    ❌ Error scrolling transform container: {e}")
            return False

    def scroll_window_for_container(self, container, height, top):
        """FIXED: Scroll main window to fully cover a container area"""
        print(f"  🌐 FIXED: Window scroll for container area (top: {top}px, height: {height}px)...")
        
        try:
            container_bottom = top + height
            
            # FIXED: Generate scroll positions to cover entire container
            scroll_positions = []
            
            # Start above container
            start_pos = max(0, top - 300)
            current_pos = start_pos
            
            # Generate positions every 600px through the container
            while current_pos < container_bottom + 300:
                scroll_positions.append(current_pos)
                current_pos += 600
            
            # Always add the absolute bottom
            page_bottom = self.driver.execute_script("return document.body.scrollHeight;")
            scroll_positions.append(page_bottom)
            
            print(f"    📍 Generated {len(scroll_positions)} scroll positions from {start_pos}px to {page_bottom}px")
            
            # FIXED: Scroll through all positions
            for i, pos in enumerate(scroll_positions):
                if self._stop_flag:
                    break
                    
                print(f"    📜 Position {i+1}/{len(scroll_positions)}: scrolling to {pos}px")
                
                self.driver.execute_script(f"window.scrollTo(0, {pos});")
                time.sleep(3)  # Wait for content loading
                
                # Check if page expanded
                new_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                if new_page_height > page_bottom:
                    print(f"    🎯 Page expanded: {page_bottom}px -> {new_page_height}px")
                    page_bottom = new_page_height
                    # Add new bottom to scroll positions
                    if page_bottom not in scroll_positions:
                        scroll_positions.append(page_bottom)
            
            return True
            
        except Exception as e:
            print(f"    ❌ Error in window scroll for container: {e}")
            return False

    def final_comprehensive_scroll(self):
        """FIXED: Final comprehensive scroll to ensure all content is loaded"""
        print(f"🔄 FIXED: Final comprehensive scroll sequence...")
        
        try:
            # Get current page state
            initial_height = self.driver.execute_script("return document.body.scrollHeight;")
            window_height = self.driver.execute_script("return window.innerHeight;")
            
            print(f"📊 Page state: height={initial_height}px, window={window_height}px")
            
            # FIXED: Multiple comprehensive scroll attempts
            for comprehensive_attempt in range(20):  # 20 attempts
                if self._stop_flag:
                    break
                    
                print(f"🔄 Comprehensive attempt {comprehensive_attempt+1}/20")
                
                # Scroll to absolute bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(4)  # Extra time for lazy loading
                
                # Check for content expansion
                new_height = self.driver.execute_script("return document.body.scrollHeight;")
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                
                print(f"    📏 Height: {new_height}px, Scroll: {current_scroll}px")
                
                if new_height > initial_height + 100:  # Significant expansion
                    print(f"    🎯 Content expanded: {initial_height}px -> {new_height}px")
                    initial_height = new_height
                elif current_scroll >= new_height - window_height - 20:  # At bottom with tolerance
                    print(f"    ✅ Confirmed at absolute bottom")
                    if comprehensive_attempt >= 3:  # Minimum 3 attempts
                        break
                        
            # FIXED: Final verification with container re-check
            print(f"🔍 FIXED: Final container verification...")
            
            # Re-find all containers after comprehensive scroll
            all_containers_final = self.driver.find_elements(By.XPATH, "//div[@data-thumb='1']")
            print(f"📊 Final verification: found {len(all_containers_final)} containers after comprehensive scroll")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in comprehensive scroll: {e}")
            return False

    def complete_scroll_sequence(self):
        """FIXED: Complete multi-container scrolling sequence"""
        print("🎬 Starting FIXED multi-container scroll sequence...")
        
        # FIXED: Use the enhanced scroll method that handles ALL containers
        success = self.scroll_to_load_all_comments()
        
        if success:
            print("🎉 FIXED multi-container scroll sequence finished successfully!")
        else:
            print("⚠️ Multi-container scroll had issues")
        
        return success

    def _switch_to_all_comments(self):
        """FIXED: Switch to 'All comments' view with proper HTML parsing"""
        print("🔄 Attempting to switch to 'All comments' view...")
        
        try:
            time.sleep(3)
            
            # FIXED: Enhanced selectors for all comments button with proper HTML structure
            all_comments_selectors = [
                # FIXED: Properly formed XPath selectors for Vietnamese
                "//span[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//div[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//a[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//button[contains(normalize-space(text()),'Tất cả bình luận')]",
                
                # FIXED: English selectors
                "//span[contains(normalize-space(text()),'All comments')]",
                "//div[contains(normalize-space(text()),'All comments')]",
                "//a[contains(normalize-space(text()),'All comments')]",
                "//button[contains(normalize-space(text()),'All comments')]",
                
                # FIXED: Role-based selectors with proper text matching
                "//div[@role='button' and (contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments'))]",
                "//span[@role='button' and (contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments'))]",
                
                # FIXED: Additional fallback selectors
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
                            
                            # FIXED: Better validation of the button text
                            if ('tất cả bình luận' in element_text.lower() or 
                                'all comments' in element_text.lower()):
                                
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

    def find_target_container(self):
        """FIXED: Find target container (for backward compatibility)"""
        print("🎯 Finding target container...")
        
        try:
            containers = self.driver.find_elements(By.XPATH, "//div[@data-thumb='1']")
            
            if not containers:
                return None
            
            target_container = None
            max_height = 0
            
            for container in containers:
                try:
                    style = container.get_attribute('style') or ""
                    height_match = re.search(r'height:\s*(\d+)px', style)
                    
                    if height_match:
                        height = int(height_match.group(1))
                        if height > max_height:
                            max_height = height
                            target_container = container
                            
                except Exception as e:
                    continue
            
            return target_container
            
        except Exception as e:
            print(f"Error finding target container: {e}")
            return None

    def extract_groups_comments(self):
        """FIXED: Comment extraction after multi-container scrolling"""
        print(f"=== EXTRACTING GROUPS COMMENTS (MULTI-SCROLL FIXED) ===")
        
        # FIXED: Use multi-container scroll first
        print("🎯 FIXED: Ensuring all containers are scrolled...")
        self.scroll_to_load_all_comments()
        
        # Save page for debugging
        try:
            with open(f"debug_multi_scroll_{self.current_layout}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Saved page to debug_multi_scroll_{self.current_layout}.html")
        except:
            pass
        
        # FIXED: Search for comments across ALL containers
        all_comment_elements = []
        
        print("🎯 FIXED: Searching across all scrolled containers...")
        
        # Strategy 1: Layout-specific selectors for entire page (since all containers are now loaded)
        if self.current_layout == "www":
            selectors = [
                "//div[@role='article']",
                "//div[contains(@aria-label, 'Comment by')]",
                "//div[contains(@aria-label, 'Bình luận của')]",
                "//div[.//a[contains(@href, '/user/') or contains(@href, '/profile/')]]",
                "//div[.//h3//a[contains(@href, 'facebook.com')]]",
                # FIXED: Additional selectors for better coverage
                "//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 20]",
                "//div[contains(@class, 'comment') or contains(@data-testid, 'comment')]"
            ]
        elif self.current_layout == "mobile":
            selectors = [
                "//div[@data-sigil='comment']",
                "//div[contains(@data-ft, 'comment')]",
                "//div[contains(@id, 'comment_')]",
                "//div[.//a[contains(@href, 'profile.php') or contains(@href, 'user.php')]]",
                # FIXED: Additional mobile selectors
                "//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 15]"
            ]
        else:  # mbasic
            selectors = [
                "//div[@data-ft and contains(@data-ft, 'comment')]",
                "//div[contains(@id, 'comment_')]",
                "//table//div[.//a[contains(@href, 'profile.php')]]",
                "//div[.//a[contains(@href, 'profile.php?id=')]]",
                # FIXED: Additional mbasic selectors
                "//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 10]"
            ]
        
        # Apply selectors to entire page (since all containers are loaded)
        for i, selector in enumerate(selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                print(f"Global search - Selector {i+1}: Found {len(elements)} elements")
                
                for elem in elements:
                    if elem not in all_comment_elements:
                        all_comment_elements.append(elem)
                        
            except Exception as e:
                print(f"Global search - Selector {i+1} failed: {e}")
                continue
        
        # Strategy 2: FIXED fallback selectors with better filtering
        if len(all_comment_elements) < 10:
            print("⚠️ Not enough elements found, trying FIXED fallback...")
            
            fallback_selectors = [
                # FIXED: Look for any div with profile links and meaningful text
                "//div[.//a[contains(@href, 'facebook.com/')] and string-length(normalize-space(text())) > 20]",
                "//div[string-length(normalize-space(text())) > 30 and .//a[@href]]",
                "//div[@role='article' and string-length(normalize-space(text())) > 20]",
                "//*[.//a[contains(@href, 'profile')] and string-length(normalize-space(text())) > 15]",
                # FIXED: Additional patterns
                "//div[contains(@class, 'x') and .//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 25]"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"FIXED fallback selector: Found {len(elements)} elements")
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
        
        print(f"FIXED: Processing {len(all_comment_elements)} potential comment elements from ALL containers...")
        
        # Process each element
        for i, element in enumerate(all_comment_elements):
            if self._stop_flag:
                break
                
            try:
                print(f"\n--- MULTI-SCROLL Element {i+1}/{len(all_comment_elements)} ---")
                
                comment_data = self.extract_comment_data_focused(element, i)
                
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
                comment_data['Source'] = 'Multi-Container Scroll (FIXED)'
                
                comments.append(comment_data)
                print(f"  ✅ Added: {comment_data['Name']} - PostLink: {comment_data['PostLink'][:70]}...")
                
            except Exception as e:
                print(f"  Error processing element {i}: {e}")
                continue
        
        print(f"\n=== MULTI-SCROLL EXTRACTION COMPLETE: {len(comments)} comments ===")
        return comments

    def extract_comment_data_focused(self, element, index):
        """FIXED: Enhanced comment data extraction with better link analysis"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 5:
                print(f"  ❌ Text too short: '{full_text}'")
                return None
            
            print(f"  FIXED Processing: '{full_text[:60]}...'")
            
            # Skip anonymous users
            if any(keyword in full_text.lower() for keyword in ['ẩn danh', 'người tham gia ẩn danh', 'anonymous']):
                print("  ⚠️ Skipping anonymous user comment")
                return None
            
            username = "Unknown"
            profile_href = ""
            uid = "Unknown"
            
            # FIXED: Enhanced username extraction with better validation
            print(f"    🎯 FIXED analysis of element structure...")
            
            try:
                all_links = element.find_elements(By.XPATH, ".//a")
                print(f"    Found {len(all_links)} total links in element")
                
                # FIXED: Prioritize links that are more likely to be usernames
                potential_profile_links = []
                
                for link_index, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        print(f"      Link {link_index+1}: Text='{link_text}' | Href={link_href[:60]}...")
                        
                        # FIXED: Enhanced Facebook profile link detection
                        is_facebook_profile = ('facebook.com' in link_href and 
                                             ('profile.php' in link_href or 
                                              '/user/' in link_href or 
                                              'user.php' in link_href or
                                              re.search(r'facebook\.com/[^/]+/?$', link_href)))  # Direct profile URLs
                        
                        if is_facebook_profile:
                            # FIXED: Enhanced name validation
                            is_valid_name = (link_text and 
                                           len(link_text) >= 2 and 
                                           len(link_text) <= 100 and
                                           not link_text.isdigit() and
                                           not link_text.startswith('http') and
                                           not re.match(r'^\d+$', link_text) and  # Not just numbers
                                           not any(ui in link_text.lower() for ui in [
                                               'like', 'reply', 'share', 'comment', 'thích', 'trả lời', 
                                               'chia sẻ', 'bình luận', 'ago', 'trước', 'min', 'hour', 
                                               'day', 'phút', 'giờ', 'ngày', 'ẩn danh', 'anonymous',
                                               'view', 'xem', 'show', 'hiển thị', 'see more', 'view more',
                                               'translate', 'dịch', 'hide', 'ẩn', 'report', 'báo cáo'
                                           ]))
                            
                            if is_valid_name:
                                # FIXED: Calculate priority score for this link
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
                                
                                # Extract UID
                                extracted_uid = "Unknown"
                                uid_patterns = [
                                    r'profile\.php\?id=(\d+)',
                                    r'user\.php\?id=(\d+)',
                                    r'/user/(\d+)',
                                    r'id=(\d+)',
                                    r'facebook\.com/([^/?]+)',  # Username from URL
                                    r'(\d{10,})'  # Facebook UIDs are usually 10+ digits
                                ]
                                
                                for pattern in uid_patterns:
                                    uid_match = re.search(pattern, link_href)
                                    if uid_match:
                                        extracted_uid = uid_match.group(1)
                                        priority_score += 5  # Bonus for having UID
                                        break
                                
                                potential_profile_links.append({
                                    'text': link_text,
                                    'href': link_href,
                                    'uid': extracted_uid,
                                    'priority': priority_score,
                                    'index': link_index
                                })
                                
                                print(f"      ✅ FIXED: Valid profile candidate: {link_text} (priority: {priority_score}) -> UID: {extracted_uid}")
                                
                    except Exception as e:
                        print(f"      Error processing link {link_index+1}: {e}")
                        continue
                
                # FIXED: Enhanced time link detection with better patterns
                time_links = []
                
                print(f"    🕐 FIXED: Searching for time links in {len(all_links)} total links...")
                
                for link_index, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        print(f"      Link {link_index+1}: Text='{link_text}' | Href={link_href[:60]}...")
                        
                        # FIXED: Enhanced time link detection patterns
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
                        
                        # Check if text matches time patterns
                        is_time_text = False
                        if link_text:
                            text_lower = link_text.lower().strip()
                            
                            # Check against patterns
                            for pattern in time_patterns:
                                if re.match(pattern, text_lower):
                                    is_time_text = True
                                    print(f"        ✅ Time pattern matched: '{pattern}' for '{text_lower}'")
                                    break
                            
                            # Check special cases
                            if not is_time_text and text_lower in ['just now', 'vừa xong', 'now', 'bây giờ']:
                                is_time_text = True
                                print(f"        ✅ Special time text: '{text_lower}'")
                        
                        # Check if href contains Facebook and comment_id
                        is_facebook_comment_link = (link_href and 
                                                   'facebook.com' in link_href and 
                                                   'comment_id=' in link_href)
                        
                        print(f"        Time text: {is_time_text}, FB comment link: {is_facebook_comment_link}")
                        
                        # FIXED: Accept as time link if it has time text AND Facebook comment link
                        if is_time_text and is_facebook_comment_link:
                            time_links.append({
                                'text': link_text,
                                'href': link_href,
                                'index': link_index
                            })
                            print(f"        🎯 FIXED: Added time link: '{link_text}' -> {link_href[:80]}...")
                        
                        # FIXED: Also accept links that look like Facebook comment links even without perfect time text
                        elif (link_href and 'facebook.com' in link_href and 'comment_id=' in link_href and 
                              link_text and len(link_text) < 20 and not any(char in link_text.lower() for char in ['like', 'reply', 'share'])):
                            time_links.append({
                                'text': link_text,
                                'href': link_href,
                                'index': link_index
                            })
                            print(f"        🎯 FIXED: Added potential time link: '{link_text}' -> {link_href[:80]}...")
                            
                    except Exception as e:
                        print(f"        ❌ Error processing link {link_index+1}: {e}")
                        continue
                
                print(f"    📊 FIXED: Found {len(time_links)} time links total")
                
                # FIXED: Select the best profile link based on priority
                if potential_profile_links:
                    # Sort by priority (highest first)
                    potential_profile_links.sort(key=lambda x: x['priority'], reverse=True)
                    
                    best_link = potential_profile_links[0]
                    username = best_link['text']
                    profile_href = best_link['href']
                    uid = best_link['uid']
                    
                    print(f"      🎯 FIXED: Selected best profile: {username} (priority: {best_link['priority']}) -> UID: {uid}")
                
                # FIXED: Get PostLink from time link with enhanced selection
                comment_post_link = ""
                if time_links:
                    # FIXED: Select the best time link (prefer ones with clear time text)
                    best_time_link = None
                    
                    for time_link in time_links:
                        link_text = time_link['text'].lower().strip()
                        
                        # Priority 1: Clear time patterns
                        if re.match(r'^\d+\s*(ngày|giờ|phút|day|hour|min)', link_text):
                            best_time_link = time_link
                            print(f"      🎯 FIXED: Selected priority time link: '{time_link['text']}'")
                            break
                        
                        # Priority 2: Any time-like text
                        elif not best_time_link:
                            best_time_link = time_link
                    
                    if best_time_link:
                        comment_post_link = best_time_link['href']
                        
                        # FIXED: Clean up the URL (remove HTML entities)
                        comment_post_link = comment_post_link.replace('&amp;', '&')
                        
                        print(f"      🔗 FIXED: Extracted PostLink from time link '{best_time_link['text']}':")
                        print(f"          {comment_post_link[:100]}...")
                    else:
                        print(f"      ⚠️ Time links found but none selected")
                else:
                    print(f"      ⚠️ No time links found in this comment")
                
                # FIXED: Fallback if no time link PostLink found
                if not comment_post_link:
                    comment_post_link = self.generate_post_link(uid, username)
                    print(f"      🔗 FIXED: Using generated fallback PostLink: {comment_post_link[:80]}...")
                
            except Exception as e:
                print(f"    Error in FIXED method: {e}")
            
            # Final validation
            if username == "Unknown":
                print("  ❌ FIXED extraction failed for this element")
                return None
                
            print(f"  ✅ FIXED: Successfully extracted username: {username}")
            
            # FIXED: Use PostLink from time link if available, otherwise generate
            final_post_link = comment_post_link if comment_post_link else self.generate_post_link(uid, username)
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,  # Keep original profile link
                "PostLink": final_post_link,  # FIXED: PostLink from time link or generated
                "CommentLink": "",
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "Multi-Container Scroll FIXED",
                "PostLinkSource": "TimeLink" if comment_post_link else "Generated"
            }
            
        except Exception as e:
            print(f"Error in FIXED extraction: {e}")
            return None

    def expand_groups_comments(self, max_iterations=50):
        """FIXED: Enhanced expansion with multi-container support"""
        print(f"=== EXPANDING GROUPS COMMENTS (MULTI-SCROLL FIXED) ===")
        
        for iteration in range(max_iterations):
            if self._stop_flag:
                break
                
            print(f"[Iteration {iteration+1}] MULTI-SCROLL FIXED expanding...")
            
            # FIXED: Use the multi-container scroll method
            if iteration % 10 == 0:  # Every 10 iterations, do full multi-container scroll
                print("🔄 Performing full multi-container scroll...")
                self.scroll_to_load_all_comments()
            else:
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
                # FIXED: Additional expand selectors
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
                                # FIXED: Scroll element into view before clicking
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                                time.sleep(1)
                                
                                elem.click()
                                expanded = True
                                print(f"    ✓ MULTI-SCROLL FIXED: Clicked: {elem.text}")
                                time.sleep(3)
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    expanded = True
                                    print(f"    ✓ MULTI-SCROLL FIXED: JS clicked: {elem.text}")
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
        
        print("=== MULTI-SCROLL FIXED EXPANSION COMPLETE ===")

    def scrape_all_comments(self, limit=0, resolve_uid=True, progress_callback=None):
        """FIXED: Main scraping orchestrator with multi-container approach"""
        print(f"=== STARTING MULTI-SCROLL FIXED GROUPS SCRAPING ===")
        
        # Step 1: Expand all content with FIXED multi-container logic
        self.expand_groups_comments()
        
        if self._stop_flag:
            return []
        
        # Step 2: Extract comments with FIXED logic
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
# MULTI-SCROLL FIXED GUI
# ----------------------------

class FBGroupsAppGUI:
    def __init__(self, root):
        self.root = root
        root.title("🎯 FB Groups Comment Scraper - MULTI-SCROLL FIXED")
        root.geometry("1100x950")
        root.configure(bg="#e8f5e8")

        # Main frame
        main_frame = tk.Frame(root, bg="#e8f5e8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_frame = tk.Frame(main_frame, bg="#e8f5e8")
        header_frame.pack(fill="x", pady=(0,20))
        
        title_label = tk.Label(header_frame, text="🎯 Facebook Groups Comment Scraper - MULTI-SCROLL FIXED", 
                              font=("Arial", 20, "bold"), bg="#e8f5e8", fg="#2d5a2d")
        title_label.pack()
        
        # FIXED: Updated subtitle
        subtitle_text = "🎯 MULTI-SCROLL FIXED - Scrolls ALL containers, not just the first one!"
        subtitle_label = tk.Label(header_frame, text=subtitle_text, 
                                 font=("Arial", 11), bg="#e8f5e8", fg="#5a5a5a")
        subtitle_label.pack(pady=(5,0))

        # Input section
        input_frame = tk.LabelFrame(main_frame, text="📝 Thông tin bài viết Groups", font=("Arial", 12, "bold"), 
                                   bg="#e8f5e8", fg="#2d5a2d", relief="groove", bd=2)
        input_frame.pack(fill="x", pady=(0,15))

        tk.Label(input_frame, text="🔗 Link bài viết trong Groups:", bg="#e8f5e8", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15,5))
        self.entry_url = tk.Entry(input_frame, width=100, font=("Arial", 9))
        self.entry_url.pack(fill="x", padx=15, pady=(0,10))

        tk.Label(input_frame, text="🍪 Cookie Facebook (để truy cập Groups):", bg="#e8f5e8", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5,5))
        self.txt_cookie = tk.Text(input_frame, height=4, font=("Arial", 8))
        self.txt_cookie.pack(fill="x", padx=15, pady=(0,15))

        # Options section
        options_frame = tk.LabelFrame(main_frame, text="🎯 Cấu hình MULTI-SCROLL FIXED", font=("Arial", 12, "bold"), 
                                     bg="#e8f5e8", fg="#2d5a2d", relief="groove", bd=2)
        options_frame.pack(fill="x", pady=(0,15))
        
        opt_grid = tk.Frame(options_frame, bg="#e8f5e8")
        opt_grid.pack(fill="x", padx=15, pady=15)
        
        # Options grid
        tk.Label(opt_grid, text="📊 Số lượng comment:", bg="#e8f5e8").grid(row=0, column=0, sticky="w")
        self.entry_limit = tk.Entry(opt_grid, width=10)
        self.entry_limit.insert(0, "0")
        self.entry_limit.grid(row=0, column=1, sticky="w", padx=(10,20))
        tk.Label(opt_grid, text="(0 = tất cả)", bg="#e8f5e8", fg="#6c757d").grid(row=0, column=2, sticky="w")

        self.headless_var = tk.BooleanVar(value=False)  # Default to visible for debugging
        tk.Checkbutton(opt_grid, text="👻 Chạy ẩn", variable=self.headless_var,
                      bg="#e8f5e8", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=(10,0))

        self.resolve_uid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_grid, text="🆔 Lấy UID", variable=self.resolve_uid_var, 
                      bg="#e8f5e8", font=("Arial", 9)).grid(row=1, column=1, sticky="w", pady=(10,0))

        # File section
        file_frame = tk.LabelFrame(main_frame, text="💾 Xuất kết quả", font=("Arial", 12, "bold"), 
                                  bg="#e8f5e8", fg="#2d5a2d", relief="groove", bd=2)
        file_frame.pack(fill="x", pady=(0,15))
        
        file_row = tk.Frame(file_frame, bg="#e8f5e8")
        file_row.pack(fill="x", padx=15, pady=15)
        
        self.entry_file = tk.Entry(file_row, width=70, font=("Arial", 9))
        self.entry_file.insert(0, "facebook_groups_comments_MULTI_SCROLL_FIXED.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        tk.Button(file_row, text="📁 Chọn", command=self.choose_file, 
                 bg="#17a2b8", fg="white", font=("Arial", 9)).pack(side="right", padx=(10,0))

        # Status section
        status_frame = tk.LabelFrame(main_frame, text="📊 Trạng thái thực thi - MULTI-SCROLL FIXED", font=("Arial", 12, "bold"), 
                                    bg="#e8f5e8", fg="#2d5a2d", relief="groove", bd=2)
        status_frame.pack(fill="x", pady=(0,15))
        
        self.lbl_status = tk.Label(status_frame, text="✅ MULTI-SCROLL FIXED scraper sẵn sàng - Scroll TẤT CẢ containers!", fg="#28a745", 
                                  wraplength=900, justify="left", font=("Arial", 11), bg="#e8f5e8")
        self.lbl_status.pack(anchor="w", padx=15, pady=(15,5))

        # FIXED: Updated features description
        fixed_features_text = ("💡 MULTI-SCROLL FIXED: 1) Scroll ALL containers (not just first), "
                              "2) Individual container scroll, 3) Window scroll for each container, "
                              "4) Final comprehensive scroll, 5) Enhanced debugging for each container")
        
        self.lbl_progress_detail = tk.Label(status_frame, text=fixed_features_text,
                                          fg="#6c757d", wraplength=900, justify="left", font=("Arial", 9), bg="#e8f5e8")
        self.lbl_progress_detail.pack(anchor="w", padx=15, pady=(0,10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(0,15))

        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#e8f5e8")
        button_frame.pack(fill="x", pady=20)
        
        self.btn_start = tk.Button(button_frame, text="🚀 Bắt đầu MULTI-SCROLL FIXED", bg="#28a745", fg="white", 
                                  font=("Arial", 14, "bold"), command=self.start_scrape_thread, 
                                  pady=12, padx=40)
        self.btn_start.pack(side="left")

        self.btn_stop = tk.Button(button_frame, text="⏹️ Dừng", bg="#dc3545", fg="white", 
                                 font=("Arial", 14, "bold"), command=self.stop_scrape, 
                                 state=tk.DISABLED, pady=12, padx=40)
        self.btn_stop.pack(side="left", padx=(25,0))

        self.progress_var = tk.IntVar(value=0)
        self.progress_label = tk.Label(button_frame, textvariable=self.progress_var, fg="#28a745", 
                                     font=("Arial", 18, "bold"), bg="#e8f5e8")
        self.progress_label.pack(side="right")

        self._scrape_thread = None
        self._stop_flag = False
        self.scraper = None

    def choose_file(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
            title="Chọn file để lưu MULTI-SCROLL FIXED Groups comments"
        )
        if f:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, f)

    def start_scrape_thread(self):
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "facebook_groups_comments_MULTI_SCROLL_FIXED.xlsx"
        
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
        self.lbl_status.config(text="🔄 Đang khởi động MULTI-SCROLL FIXED scraper...", fg="#fd7e14")
        self.lbl_progress_detail.config(text="⏳ Initializing MULTI-SCROLL FIXED - Will scroll ALL containers...")
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
        self.lbl_status.config(text="⏹️ Đang dừng MULTI-SCROLL FIXED scraper...", fg="#dc3545")
        self.btn_stop.config(state=tk.DISABLED)

    def _progress_cb(self, count):
        self.progress_var.set(count)
        self.lbl_status.config(text=f"📈 MULTI-SCROLL FIXED processing... Đã lấy {count} comments", fg="#28a745")
        self.root.update_idletasks()

    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, resolve_uid):
        try:
            # Initialize
            self.lbl_status.config(text="🌐 Khởi tạo MULTI-SCROLL FIXED scraper...", fg="#fd7e14")
            self.scraper = FacebookGroupsScraper(cookie_str, headless=headless)
            
            if self._stop_flag: return
            
            # Load post
            self.lbl_status.config(text="📄 Đang tải bài viết Groups với MULTI-SCROLL FIXED...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Loading post with multi-container scroll logic...")
            success = self.scraper.load_post(url)
            
            if not success:
                self.lbl_status.config(text="❌ Không thể tải bài viết Groups", fg="#dc3545")
                self.lbl_progress_detail.config(text="💡 Kiểm tra: 1) Cookie valid, 2) Quyền truy cập Groups, 3) Link chính xác")
                return
            
            # Show detected layout
            layout = getattr(self.scraper, 'current_layout', 'unknown')
            self.lbl_progress_detail.config(text=f"🎯 Layout detected: {layout} - Using MULTI-SCROLL FIXED methods...")
                
            if self._stop_flag: return
            
            # Scrape with MULTI-SCROLL FIXED logic
            self.lbl_status.config(text=f"🔍 MULTI-SCROLL FIXED extraction ({layout})...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Scrolling ALL containers and extracting comments...")
            
            comments = self.scraper.scrape_all_comments(limit=limit, resolve_uid=resolve_uid, 
                                                       progress_callback=self._progress_cb)
            
            if self._stop_flag: return
            
            # Save
            self.lbl_status.config(text="💾 Đang lưu MULTI-SCROLL FIXED data...", fg="#fd7e14")
            
            if comments:
                df = pd.DataFrame(comments)
                
                # Add metadata
                df.insert(0, 'STT', range(1, len(df) + 1))
                df['Source'] = 'Facebook Groups - MULTI-SCROLL FIXED'
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
                
                self.lbl_status.config(text=f"🎉 MULTI-SCROLL FIXED HOÀN THÀNH!", fg="#28a745")
                self.lbl_progress_detail.config(text=f"📊 MULTI-SCROLL Results: {len(comments)} comments | {unique_users} unique users | {profile_links} profile links | {uid_count} UIDs | Layout: {layout}")
                
                print(f"🎯 MULTI-SCROLL FIXED SCRAPING COMPLETE!")
                print(f"   📊 Results: {len(comments)} total comments")
                print(f"   👥 Unique users: {unique_users}")
                print(f"   🔗 Profile links: {profile_links}")
                print(f"   🆔 UIDs extracted: {uid_count}")
                print(f"   📱 Layout used: {layout}")
                print(f"   💾 Saved to: {file_out}")
                print(f"   🔍 Debug files: debug_multi_scroll_{layout}.html")
                
            else:
                self.lbl_status.config(text="⚠️ Không tìm thấy comment với MULTI-SCROLL FIXED", fg="#ffc107")
                self.lbl_progress_detail.config(text=f"💡 Layout: {layout} | Đã scroll tất cả containers nhưng không tìm thấy comments")
                
                print(f"⚠️ No comments found with MULTI-SCROLL FIXED logic")
                print(f"   📱 Layout: {layout}")
                print(f"   🔍 Debug files created: debug_multi_scroll_{layout}.html")
                print(f"   💡 MULTI-SCROLL FIXED ran but no comments found:")
                print(f"      1. Check if you have access to the Facebook Group")
                print(f"      2. Verify the post URL is correct and public in the group")
                print(f"      3. All containers were scrolled - check debug file")
                print(f"      4. Try running without headless mode to see what's happening")
                
        except Exception as e:
            error_msg = str(e)[:120]
            self.lbl_status.config(text=f"❌ Lỗi MULTI-SCROLL FIXED: {error_msg}...", fg="#dc3545")
            self.lbl_progress_detail.config(text="🔍 Xem console để biết chi tiết. MULTI-SCROLL FIXED cung cấp debug info.")
            print(f"MULTI-SCROLL FIXED Groups scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.stop()
            if self.scraper: 
                self.scraper.close()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

# ----------------------------
# Run MULTI-SCROLL FIXED app
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FBGroupsAppGUI(root)
    root.mainloop()