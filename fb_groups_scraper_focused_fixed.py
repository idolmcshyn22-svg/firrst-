# fb_groups_scraper_focused_fixed.py - FIXED: HTML div tags and scroll logic

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
# FIXED Facebook Groups Scraper
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

    def find_target_container(self):
        """FIXED: Find the specific Facebook container with enhanced detection"""
        print("🎯 Finding target container with specific Facebook classes...")
        
        try:
            # FIXED: Target the specific container structure you mentioned
            specific_selectors = [
                # Your exact container structure
                "//div[@class='x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq' and @data-visualcompletion='ignore' and @data-thumb='1']",
                
                # Fallback: partial class match with data attributes
                "//div[contains(@class, 'x14nfmen') and contains(@class, 'x1s85apg') and @data-thumb='1']",
                
                # Fallback: any container with data-thumb='1' and significant height
                "//div[@data-thumb='1' and @data-visualcompletion='ignore']",
                
                # General fallback
                "//div[@data-thumb='1']"
            ]
            
            target_container = None
            max_height = 0
            
            for selector_idx, selector in enumerate(specific_selectors, 1):
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    print(f"Selector {selector_idx}: Found {len(containers)} containers")
                    
                    if not containers:
                        continue
                    
                    for idx, container in enumerate(containers, 1):
                        try:
                            # Get multiple height measurements
                            offset_height = self.driver.execute_script("return arguments[0].offsetHeight;", container)
                            scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", container)
                            client_height = self.driver.execute_script("return arguments[0].clientHeight;", container)
                            
                            # Also check style height
                            style = container.get_attribute('style') or ""
                            style_height_match = re.search(r'height:\s*(\d+)px', style)
                            style_height = int(style_height_match.group(1)) if style_height_match else 0
                            
                            # Get class for verification
                            container_class = container.get_attribute('class') or ""
                            
                            # FIXED: Use the maximum height found
                            actual_height = max(offset_height, scroll_height, client_height, style_height)
                            
                            print(f"   Container {idx}: height={actual_height}px (offset:{offset_height}, scroll:{scroll_height}, client:{client_height}, style:{style_height})")
                            print(f"     Classes: {container_class[:100]}...")
                            
                            # FIXED: Prioritize containers with the specific classes you mentioned
                            is_target_class = ('x14nfmen' in container_class and 'x1s85apg' in container_class)
                            
                            if actual_height > max_height or (is_target_class and actual_height > 1000):
                                max_height = actual_height
                                target_container = container
                                print(f"     🎯 NEW BEST: height={actual_height}px, target_class={is_target_class}")
                                
                        except Exception as e:
                            print(f"   Container {idx}: error getting height - {e}")
                            continue
                    
                    # If we found a good container with the first selector, use it
                    if target_container and max_height > 1000:
                        break
                        
                except Exception as e:
                    print(f"Selector {selector_idx} failed: {e}")
                    continue
            
            if target_container and max_height > 100:
                print(f"✅ Selected container with height: {max_height}px")
                
                # FIXED: Better scroll into view
                try:
                    # Scroll to make the container visible
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});", target_container)
                    time.sleep(2)
                    
                    # Verify container is scrollable
                    is_scrollable = self.driver.execute_script("""
                        var elem = arguments[0];
                        return elem.scrollHeight > elem.clientHeight;
                    """, target_container)
                    
                    print(f"📊 Container scrollable: {is_scrollable}")
                    
                except Exception as e:
                    print(f"Error scrolling container into view: {e}")
                
                return target_container
            else:
                print("❌ No suitable container found with sufficient height")
                return None
                
        except Exception as e:
            print(f"❌ Error finding target container: {e}")
            return None

    def scroll_to_load_all_comments(self):
        """FIXED: Enhanced scroll targeting specific Facebook container"""
        print("📜 Starting FIXED scroll for specific Facebook container...")
        
        try:
            # FIXED: Direct targeting of your specific container
            specific_container_xpath = "//div[@class='x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq' and @data-visualcompletion='ignore' and @data-thumb='1']"
            
            target_containers = self.driver.find_elements(By.XPATH, specific_container_xpath)
            
            if not target_containers:
                print("⚠️ Specific container not found, trying fallback...")
                # Fallback to general method
                target_container = self.find_target_container()
            else:
                # FIXED: Select the container with largest height from specific matches
                target_container = None
                max_height = 0
                
                for idx, container in enumerate(target_containers, 1):
                    try:
                        style = container.get_attribute('style') or ""
                        height_match = re.search(r'height:\s*(\d+)px', style)
                        
                        if height_match:
                            height = int(height_match.group(1))
                            print(f"🎯 Specific container {idx}: height = {height}px")
                            
                            if height > max_height:
                                max_height = height
                                target_container = container
                                
                    except Exception as e:
                        print(f"Error checking container {idx}: {e}")
                        continue
                
                if target_container:
                    print(f"✅ Selected specific container with height: {max_height}px")
                else:
                    print("❌ No suitable specific container found")
                    return False
            
            if not target_container:
                print("❌ No container found (both specific and fallback failed)")
                return False
            
            # Get container dimensions and properties
            container_rect = target_container.rect
            container_top = container_rect['y']
            
            # Get scrolling properties
            container_scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", target_container)
            container_client_height = self.driver.execute_script("return arguments[0].clientHeight;", target_container)
            container_offset_height = self.driver.execute_script("return arguments[0].offsetHeight;", target_container)
            
            # Check if container is actually scrollable
            is_scrollable = container_scroll_height > container_client_height
            
            print(f"📐 FIXED Container analysis:")
            print(f"   Top position: {container_top}px")
            print(f"   Scroll height: {container_scroll_height}px")
            print(f"   Client height: {container_client_height}px")
            print(f"   Offset height: {container_offset_height}px")
            print(f"   Is scrollable: {is_scrollable}")
            
            # FIXED: If container is not scrollable, scroll the main window instead
            if not is_scrollable:
                print("⚠️ Container is not scrollable, using main window scroll...")
                return self.scroll_main_window_to_load_comments(target_container)
            
            
            # FIXED: Enhanced scroll strategy with absolute bottom guarantee
            scroll_step = 500  # Optimized steps for better loading
            scroll_pause = 2.5  # Longer pause for content loading
            max_attempts = 150  # Increased max attempts
            force_bottom_attempts = 5  # Number of times to force scroll to bottom
            
            current_scroll_position = 0
            no_change_count = 0
            previous_scroll_height = 0
            stuck_count = 0
            
            print("🚀 Starting FIXED enhanced scroll sequence with absolute bottom guarantee...")
            
            # Start from the top of container
            self.driver.execute_script("arguments[0].scrollTop = 0;", target_container)
            time.sleep(1)
            
            for attempt in range(max_attempts):
                if self._stop_flag:
                    break
                
                # Get current scroll position
                current_scroll_position = self.driver.execute_script("return arguments[0].scrollTop;", target_container)
                current_scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", target_container)
                
                print(f"📜 Attempt {attempt+1}: scroll_pos={current_scroll_position}px, scroll_height={current_scroll_height}px")
                
                # FIXED: Check if we've reached the absolute bottom
                max_scroll_position = current_scroll_height - container_client_height
                
                if current_scroll_position >= max_scroll_position - 10:  # 10px tolerance
                    print("🏁 FIXED: Reached absolute bottom of container!")
                    break
                
                # FIXED: Scroll to next position
                next_scroll_position = min(current_scroll_position + scroll_step, max_scroll_position)
                self.driver.execute_script(f"arguments[0].scrollTop = {next_scroll_position};", target_container)
                
                # Also scroll the main window to keep container in view
                window_scroll_y = container_top + (current_scroll_position * 0.5)  # Proportional scroll
                self.driver.execute_script(f"window.scrollTo(0, {window_scroll_y});")
                
                time.sleep(scroll_pause)
                
                # FIXED: Detect if content is still loading
                new_scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", target_container)
                
                if new_scroll_height > previous_scroll_height:
                    print(f"    ✅ Content expanded: {previous_scroll_height}px -> {new_scroll_height}px")
                    no_change_count = 0
                    previous_scroll_height = new_scroll_height
                else:
                    no_change_count += 1
                    
                # FIXED: Enhanced stuck detection and recovery
                if no_change_count >= 3:
                    stuck_count += 1
                    print(f"    ⚡ No content change detected (stuck #{stuck_count}), making big jump to bottom...")
                    
                    # FIXED: Multiple strategies to ensure we reach the absolute bottom
                    for bottom_attempt in range(force_bottom_attempts):
                        print(f"      🎯 Force bottom attempt {bottom_attempt + 1}/{force_bottom_attempts}")
                        
                        # Force scroll to absolute bottom
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", target_container)
                        time.sleep(3)  # Longer wait for potential lazy loading
                        
                        # Also scroll main window to keep container visible
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        # Check if this revealed more content
                        final_scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", target_container)
                        
                        if final_scroll_height > new_scroll_height:
                            print(f"      🎯 Bottom jump {bottom_attempt + 1} revealed more content: {new_scroll_height}px -> {final_scroll_height}px")
                            previous_scroll_height = final_scroll_height
                            no_change_count = 0
                            stuck_count = 0
                            break
                        elif bottom_attempt == force_bottom_attempts - 1:
                            print(f"      🏁 All {force_bottom_attempts} bottom attempts completed - confirmed at absolute bottom")
                            # Final verification
                            current_scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", target_container)
                            max_scroll_top = self.driver.execute_script("return arguments[0].scrollHeight - arguments[0].clientHeight;", target_container)
                            print(f"      📊 Final position: {current_scroll_top}px / {max_scroll_top}px")
                            return True
                    
                    # If we're still stuck after multiple attempts, break
                    if stuck_count >= 3:
                        print("    🛑 FIXED: Multiple stuck attempts completed, assuming all content loaded")
                        break
            
            # FIXED: Final verification - ensure we're truly at the bottom
            print("\n🔍 FIXED: Final verification of scroll position...")
            
            final_scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", target_container)
            final_scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", target_container)
            final_client_height = self.driver.execute_script("return arguments[0].clientHeight;", target_container)
            
            max_possible_scroll = final_scroll_height - final_client_height
            
            print(f"📊 Final metrics:")
            print(f"   Current scroll position: {final_scroll_top}px")
            print(f"   Max possible scroll: {max_possible_scroll}px")
            print(f"   Total scroll height: {final_scroll_height}px")
            
            if final_scroll_top < max_possible_scroll - 20:  # 20px tolerance
                print("⚡ FIXED: Force scrolling to absolute bottom...")
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", target_container)
                time.sleep(3)
                
                # Final check
                truly_final_scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", target_container)
                print(f"✅ FIXED: Final scroll position: {truly_final_scroll_top}px")
            
            print("🎯 FIXED scroll sequence completed - ensured absolute bottom reached!")
            return True
            
        except Exception as e:
            print(f"❌ Error during FIXED comment scrolling: {e}")
            return False

    def scroll_main_window_to_load_comments(self, reference_container=None):
        """FIXED: Scroll main window when container is not directly scrollable"""
        print("📜 FIXED: Scrolling main window to load all comments...")
        
        try:
            # Get initial page state
            initial_page_height = self.driver.execute_script("return document.body.scrollHeight;")
            window_height = self.driver.execute_script("return window.innerHeight;")
            
            print(f"📐 Initial page state:")
            print(f"   Page height: {initial_page_height}px")
            print(f"   Window height: {window_height}px")
            
            if reference_container:
                container_rect = reference_container.rect
                container_bottom = container_rect['y'] + container_rect['height']
                print(f"   Container bottom: {container_bottom}px")
            
            # FIXED: Enhanced main window scrolling
            scroll_step = 800
            scroll_pause = 3.0  # Longer pause for Facebook's lazy loading
            max_attempts = 100
            no_change_count = 0
            previous_page_height = initial_page_height
            
            for attempt in range(max_attempts):
                if self._stop_flag:
                    break
                
                # Get current scroll position
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                current_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                
                print(f"📜 Attempt {attempt+1}: scroll={current_scroll}px, page_height={current_page_height}px")
                
                # Check if we're at the bottom
                max_scroll = current_page_height - window_height
                if current_scroll >= max_scroll - 50:  # 50px tolerance
                    print("🏁 Reached bottom of main window")
                    
                    # FIXED: Force scroll to absolute bottom multiple times
                    for force_attempt in range(5):
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(4)  # Extra time for lazy loading
                        
                        new_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                        if new_page_height > current_page_height:
                            print(f"🎯 Force bottom {force_attempt+1} loaded more content: {current_page_height}px -> {new_page_height}px")
                            current_page_height = new_page_height
                        else:
                            print(f"✅ Force bottom {force_attempt+1} confirmed no more content")
                    
                    break
                
                # Scroll down
                next_scroll = min(current_scroll + scroll_step, max_scroll)
                self.driver.execute_script(f"window.scrollTo(0, {next_scroll});")
                time.sleep(scroll_pause)
                
                # Check for page height changes (new content loaded)
                if current_page_height > previous_page_height:
                    print(f"    ✅ Page expanded: {previous_page_height}px -> {current_page_height}px")
                    no_change_count = 0
                    previous_page_height = current_page_height
                else:
                    no_change_count += 1
                
                # If stuck, try jumping to bottom
                if no_change_count >= 3:
                    print("    ⚡ Main window stuck, jumping to bottom...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)  # Extra wait for potential content loading
                    
                    new_height = self.driver.execute_script("return document.body.scrollHeight;")
                    if new_height > current_page_height:
                        print(f"    🎯 Bottom jump revealed more content: {current_page_height}px -> {new_height}px")
                        no_change_count = 0
                        previous_page_height = new_height
                    elif no_change_count >= 6:
                        print("    🏁 No more content loading, stopping")
                        break
            
            print("✅ FIXED main window scroll completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during main window scrolling: {e}")
            return False

    def scroll_specific_facebook_container(self, target_container):
        """FIXED: Specialized scrolling for Facebook's specific container structure"""
        print("🎯 FIXED: Specialized scroll for Facebook container...")
        
        try:
            # Get container properties
            container_style = target_container.get_attribute('style') or ""
            container_class = target_container.get_attribute('class') or ""
            
            print(f"📊 Container info:")
            print(f"   Style: {container_style}")
            print(f"   Classes: {container_class[:100]}...")
            
            # FIXED: For Facebook's specific container, try different scroll approaches
            
            # Method 1: Try scrolling the container itself
            try:
                print("🔄 Method 1: Direct container scroll...")
                
                # Check if container has overflow scroll
                overflow_y = self.driver.execute_script("return getComputedStyle(arguments[0]).overflowY;", target_container)
                print(f"   Overflow-Y: {overflow_y}")
                
                if overflow_y in ['scroll', 'auto']:
                    # Container is scrollable
                    for i in range(20):  # More attempts
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", target_container)
                        time.sleep(2)
                        
                        current_scroll = self.driver.execute_script("return arguments[0].scrollTop;", target_container)
                        max_scroll = self.driver.execute_script("return arguments[0].scrollHeight - arguments[0].clientHeight;", target_container)
                        
                        print(f"     Scroll attempt {i+1}: {current_scroll}px / {max_scroll}px")
                        
                        if current_scroll >= max_scroll - 10:
                            print("     ✅ Container scrolled to bottom")
                            break
                else:
                    print("   ⚠️ Container not directly scrollable")
                    
            except Exception as e:
                print(f"   Method 1 failed: {e}")
            
            # Method 2: Scroll main window while monitoring container
            print("🔄 Method 2: Main window scroll with container monitoring...")
            
            container_rect = target_container.rect
            container_top = container_rect['y']
            container_height = container_rect['height']
            container_bottom = container_top + container_height
            
            print(f"   Container bounds: {container_top}px to {container_bottom}px")
            
            # Scroll in increments, focusing on the container area
            scroll_positions = []
            
            # Generate scroll positions that cover the entire container
            current_pos = max(0, container_top - 500)  # Start a bit above
            while current_pos < container_bottom + 500:  # Go a bit below
                scroll_positions.append(current_pos)
                current_pos += 400  # 400px increments
            
            # Add final position at absolute bottom
            final_bottom = self.driver.execute_script("return document.body.scrollHeight;")
            scroll_positions.append(final_bottom)
            
            print(f"   Generated {len(scroll_positions)} scroll positions")
            
            for i, scroll_pos in enumerate(scroll_positions):
                if self._stop_flag:
                    break
                    
                print(f"   📜 Scrolling to position {i+1}/{len(scroll_positions)}: {scroll_pos}px")
                
                self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(3)  # Longer wait for content loading
                
                # Check if page expanded
                new_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                if new_page_height > final_bottom:
                    print(f"     🎯 Page expanded during scroll: {final_bottom}px -> {new_page_height}px")
                    final_bottom = new_page_height
                    # Add new bottom position
                    scroll_positions.append(final_bottom)
            
            # Method 3: Final verification with multiple bottom attempts
            print("🔄 Method 3: Final bottom verification...")
            
            for final_attempt in range(10):  # 10 final attempts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                current_height = self.driver.execute_script("return document.body.scrollHeight;")
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                
                print(f"   Final attempt {final_attempt+1}: scroll={current_scroll}px, height={current_height}px")
                
                # Check if we're truly at bottom
                window_height = self.driver.execute_script("return window.innerHeight;")
                if current_scroll >= current_height - window_height - 10:
                    print(f"   ✅ Confirmed at absolute bottom")
                    break
            
            # Method 4: FIXED - Facebook lazy loading trigger
            print("🔄 Method 4: Triggering Facebook lazy loading...")
            
            try:
                # Simulate user scrolling behavior to trigger lazy loading
                for lazy_attempt in range(15):  # 15 attempts to trigger all lazy content
                    print(f"   🔄 Lazy loading attempt {lazy_attempt+1}/15...")
                    
                    # Scroll to different positions to trigger loading
                    positions = [
                        container_top,  # Top of container
                        container_top + (container_height * 0.25),  # 25%
                        container_top + (container_height * 0.5),   # 50%
                        container_top + (container_height * 0.75),  # 75%
                        container_bottom,  # Bottom of container
                        self.driver.execute_script("return document.body.scrollHeight;")  # Page bottom
                    ]
                    
                    for pos in positions:
                        self.driver.execute_script(f"window.scrollTo(0, {pos});")
                        time.sleep(1.5)
                    
                    # Final scroll to absolute bottom
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(4)  # Extra wait for lazy loading
                    
                    # Check if more content loaded
                    current_page_height = self.driver.execute_script("return document.body.scrollHeight;")
                    if current_page_height > final_bottom + 100:  # Significant change
                        print(f"     🎯 Lazy loading triggered: {final_bottom}px -> {current_page_height}px")
                        final_bottom = current_page_height
                    else:
                        print(f"     ✅ No more lazy content to load")
                        if lazy_attempt >= 3:  # Give it at least 3 attempts
                            break
                            
            except Exception as e:
                print(f"   Method 4 failed: {e}")
            
            print("✅ FIXED specialized container scroll completed")
            return True
            
        except Exception as e:
            print(f"❌ Error in specialized container scroll: {e}")
            return False

    def complete_scroll_sequence(self):
        """FIXED: Complete 2-phase scrolling with enhanced bottom detection"""
        print("🎬 Starting FIXED complete scroll sequence...")
        
        # Phase 1: Find and scroll to target container
        print("\n=== PHASE 1: Finding target container ===")
        target_container = self.find_target_container()
        
        if not target_container:
            print("❌ Phase 1 failed - no target container found")
            return False
        
        print("✅ Phase 1 completed - target container found and scrolled to")
        time.sleep(2)
        
        # Phase 2: FIXED gradual scroll through comments
        print("\n=== PHASE 2: FIXED - Loading all comments to absolute bottom ===")
        success = self.scroll_to_load_all_comments()
        
        if success:
            print("🎉 FIXED complete scroll sequence finished successfully!")
        else:
            print("⚠️ Comment loading phase had issues, but container was found")
        
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
                
                # FIXED: Aria-label selectors
                "//div[contains(@aria-label,'comment') and contains(normalize-space(text()),'All')]",
                "//div[contains(@aria-label,'bình luận') and contains(normalize-space(text()),'Tất cả')]",
                
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

    def extract_groups_comments(self):
        """FIXED: Comment extraction targeting larger height container"""
        print(f"=== EXTRACTING GROUPS COMMENTS (FIXED) ===")
        
        # FIXED: Find and focus on the target container
        print("🎯 Finding and scrolling to target container...")
        target_container = self.find_target_container()
        
        if not target_container:
            print("❌ Could not find target container")
            return []
        
        # FIXED: Use specialized scroll for your specific container
        print("🎯 FIXED: Using specialized scroll for your container...")
        if target_container:
            # Check if this is your specific container type
            container_class = target_container.get_attribute('class') or ""
            if 'x14nfmen' in container_class and 'x1s85apg' in container_class:
                print("🎯 Detected your specific Facebook container, using specialized scroll...")
                self.scroll_specific_facebook_container(target_container)
            else:
                print("🔄 Using general scroll sequence...")
                self.complete_scroll_sequence()
        else:
            self.complete_scroll_sequence()
        
        # Re-find container after scrolling (it might have changed)
        target_container = self.find_target_container()
        
        # Save page for debugging
        try:
            with open(f"debug_fixed_{self.current_layout}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Saved page to debug_fixed_{self.current_layout}.html")
        except:
            pass
        
        # FIXED: Search within the target container first
        all_comment_elements = []
        
        print("🎯 FIXED: Searching within target container...")
        
        # Strategy 1: Layout-specific selectors within target container
        if self.current_layout == "www":
            selectors = [
                ".//div[@role='article']",
                ".//div[contains(@aria-label, 'Comment by')]",
                ".//div[contains(@aria-label, 'Bình luận của')]",
                ".//div[.//a[contains(@href, '/user/') or contains(@href, '/profile/')]]",
                ".//div[.//h3//a[contains(@href, 'facebook.com')]]",
                # FIXED: Additional selectors for better coverage
                ".//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 20]",
                ".//div[contains(@class, 'comment') or contains(@data-testid, 'comment')]"
            ]
        elif self.current_layout == "mobile":
            selectors = [
                ".//div[@data-sigil='comment']",
                ".//div[contains(@data-ft, 'comment')]",
                ".//div[contains(@id, 'comment_')]",
                ".//div[.//a[contains(@href, 'profile.php') or contains(@href, 'user.php')]]",
                # FIXED: Additional mobile selectors
                ".//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 15]"
            ]
        else:  # mbasic
            selectors = [
                ".//div[@data-ft and contains(@data-ft, 'comment')]",
                ".//div[contains(@id, 'comment_')]",
                ".//table//div[.//a[contains(@href, 'profile.php')]]",
                ".//div[.//a[contains(@href, 'profile.php?id=')]]",
                # FIXED: Additional mbasic selectors
                ".//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 10]"
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
        
        # Strategy 3: FIXED fallback selectors with better filtering
        if len(all_comment_elements) == 0:
            print("⚠️ No comments with standard selectors, trying FIXED fallback...")
            
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
        
        print(f"FIXED: Processing {len(all_comment_elements)} potential comment elements...")
        
        # Process each element
        for i, element in enumerate(all_comment_elements):
            if self._stop_flag:
                break
                
            try:
                print(f"\n--- FIXED Element {i+1}/{len(all_comment_elements)} ---")
                
                comment_data = self.extract_comment_data_fixed(element, i)
                
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
                comment_data['Source'] = 'Target Container (FIXED)'
                
                comments.append(comment_data)
                print(f"  ✅ Added: {comment_data['Name']} - Profile: {comment_data['ProfileLink'][:50]}...")
                
            except Exception as e:
                print(f"  Error processing element {i}: {e}")
                continue
        
        print(f"\n=== FIXED EXTRACTION COMPLETE: {len(comments)} comments ===")
        return comments

    def extract_comment_data_fixed(self, element, index):
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
                
                # FIXED: Select the best profile link based on priority
                if potential_profile_links:
                    # Sort by priority (highest first)
                    potential_profile_links.sort(key=lambda x: x['priority'], reverse=True)
                    
                    best_link = potential_profile_links[0]
                    username = best_link['text']
                    profile_href = best_link['href']
                    uid = best_link['uid']
                    
                    print(f"      🎯 FIXED: Selected best profile: {username} (priority: {best_link['priority']}) -> UID: {uid}")
                
            except Exception as e:
                print(f"    Error in FIXED method: {e}")
            
            # Final validation
            if username == "Unknown":
                print("  ❌ FIXED extraction failed for this element")
                return None
                
            print(f"  ✅ FIXED: Successfully extracted username: {username}")
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,
                "CommentLink": "",
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "FIXED - Enhanced scroll to absolute bottom"
            }
            
        except Exception as e:
            print(f"Error in FIXED extraction: {e}")
            return None

    def expand_groups_comments(self, max_iterations=50):
        """FIXED: Enhanced expansion with better bottom detection"""
        print(f"=== EXPANDING GROUPS COMMENTS (FIXED) ===")
        
        # Find target container initially
        target_container = self.find_target_container()
        
        for iteration in range(max_iterations):
            if self._stop_flag:
                break
                
            print(f"[Iteration {iteration+1}] FIXED scrolling and expanding...")
            
            # Re-find target container every 5 iterations or if previous one is stale
            if iteration % 5 == 0 or not target_container:
                target_container = self.find_target_container()
            
            # FIXED: Enhanced container scrolling
            if target_container:
                try:
                    # Get current scroll state
                    current_scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", target_container)
                    scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", target_container)
                    client_height = self.driver.execute_script("return arguments[0].clientHeight;", target_container)
                    
                    # FIXED: Calculate how much more we can scroll
                    max_scroll = scroll_height - client_height
                    remaining_scroll = max_scroll - current_scroll_top
                    
                    print(f"    Container scroll state: {current_scroll_top}/{max_scroll}px (remaining: {remaining_scroll}px)")
                    
                    if remaining_scroll > 10:  # Still more to scroll
                        # Scroll down by a reasonable amount
                        new_scroll_position = min(current_scroll_top + 800, max_scroll)
                        self.driver.execute_script(f"arguments[0].scrollTop = {new_scroll_position};", target_container)
                    else:
                        # FIXED: We're at the bottom, force scroll to absolute bottom
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", target_container)
                        print("    🎯 FIXED: Forced scroll to absolute bottom of container")
                        
                    time.sleep(1)
                except Exception as e:
                    print(f"    Container scroll failed, re-finding: {e}")
                    target_container = self.find_target_container()
            
            # Also scroll the main page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            
            # FIXED: Look for expand links with enhanced detection
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
                                print(f"    ✓ FIXED: Clicked: {elem.text}")
                                time.sleep(3)
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    expanded = True
                                    print(f"    ✓ FIXED: JS clicked: {elem.text}")
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
        
        print("=== FIXED EXPANSION COMPLETE ===")

    def scrape_all_comments(self, limit=0, resolve_uid=True, progress_callback=None):
        """FIXED: Main scraping orchestrator with enhanced scroll logic"""
        print(f"=== STARTING FIXED GROUPS SCRAPING ===")
        
        # Step 1: Expand all content with FIXED logic
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
# FIXED GUI
# ----------------------------

class FBGroupsAppGUI:
    def __init__(self, root):
        self.root = root
        root.title("🎯 FB Groups Comment Scraper - FIXED")
        root.geometry("1100x950")
        root.configure(bg="#e8f5e8")

        # Main frame
        main_frame = tk.Frame(root, bg="#e8f5e8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_frame = tk.Frame(main_frame, bg="#e8f5e8")
        header_frame.pack(fill="x", pady=(0,20))
        
        title_label = tk.Label(header_frame, text="🎯 Facebook Groups Comment Scraper - FIXED", 
                              font=("Arial", 20, "bold"), bg="#e8f5e8", fg="#2d5a2d")
        title_label.pack()
        
        # FIXED: Proper HTML structure in subtitle
        subtitle_text = "🎯 FIXED version - Enhanced scroll to absolute bottom + Fixed HTML parsing"
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
        options_frame = tk.LabelFrame(main_frame, text="🎯 Cấu hình FIXED Version", font=("Arial", 12, "bold"), 
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
        self.entry_file.insert(0, "facebook_groups_comments_FIXED.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        tk.Button(file_row, text="📁 Chọn", command=self.choose_file, 
                 bg="#17a2b8", fg="white", font=("Arial", 9)).pack(side="right", padx=(10,0))

        # Status section
        status_frame = tk.LabelFrame(main_frame, text="📊 Trạng thái thực thi - FIXED", font=("Arial", 12, "bold"), 
                                    bg="#e8f5e8", fg="#2d5a2d", relief="groove", bd=2)
        status_frame.pack(fill="x", pady=(0,15))
        
        self.lbl_status = tk.Label(status_frame, text="✅ FIXED scraper sẵn sàng - Đã fix scroll logic và HTML parsing", fg="#28a745", 
                                  wraplength=900, justify="left", font=("Arial", 11), bg="#e8f5e8")
        self.lbl_status.pack(anchor="w", padx=15, pady=(15,5))

        # FIXED: Properly formatted status detail
        fixed_features_text = ("💡 FIXED features: 1) Enhanced scroll to absolute bottom, "
                              "2) Better link priority scoring, 3) Improved HTML structure parsing, "
                              "4) Force scroll verification, 5) Enhanced debugging output")
        
        self.lbl_progress_detail = tk.Label(status_frame, text=fixed_features_text,
                                          fg="#6c757d", wraplength=900, justify="left", font=("Arial", 9), bg="#e8f5e8")
        self.lbl_progress_detail.pack(anchor="w", padx=15, pady=(0,10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(0,15))

        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#e8f5e8")
        button_frame.pack(fill="x", pady=20)
        
        self.btn_start = tk.Button(button_frame, text="🚀 Bắt đầu FIXED Scraping", bg="#28a745", fg="white", 
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
            title="Chọn file để lưu FIXED Groups comments"
        )
        if f:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, f)

    def start_scrape_thread(self):
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "facebook_groups_comments_FIXED.xlsx"
        
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
        self.lbl_status.config(text="🔄 Đang khởi động FIXED Groups scraper...", fg="#fd7e14")
        self.lbl_progress_detail.config(text="⏳ Initializing FIXED extraction logic with enhanced scroll and HTML parsing...")
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
        self.lbl_status.config(text="⏹️ Đang dừng FIXED scraper...", fg="#dc3545")
        self.btn_stop.config(state=tk.DISABLED)

    def _progress_cb(self, count):
        self.progress_var.set(count)
        self.lbl_status.config(text=f"📈 FIXED processing... Đã lấy {count} comments", fg="#28a745")
        self.root.update_idletasks()

    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, resolve_uid):
        try:
            # Initialize
            self.lbl_status.config(text="🌐 Khởi tạo FIXED Groups scraper...", fg="#fd7e14")
            self.scraper = FacebookGroupsScraper(cookie_str, headless=headless)
            
            if self._stop_flag: return
            
            # Load post
            self.lbl_status.config(text="📄 Đang tải bài viết Groups với FIXED logic...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Loading post with enhanced error handling...")
            success = self.scraper.load_post(url)
            
            if not success:
                self.lbl_status.config(text="❌ Không thể tải bài viết Groups", fg="#dc3545")
                self.lbl_progress_detail.config(text="💡 Kiểm tra: 1) Cookie valid, 2) Quyền truy cập Groups, 3) Link chính xác")
                return
            
            # Show detected layout
            layout = getattr(self.scraper, 'current_layout', 'unknown')
            self.lbl_progress_detail.config(text=f"🎯 Layout detected: {layout} - Using FIXED extraction methods...")
                
            if self._stop_flag: return
            
            # Scrape with FIXED logic
            self.lbl_status.config(text=f"🔍 FIXED Groups extraction ({layout})...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Using enhanced scroll logic and username extraction...")
            
            comments = self.scraper.scrape_all_comments(limit=limit, resolve_uid=resolve_uid, 
                                                       progress_callback=self._progress_cb)
            
            if self._stop_flag: return
            
            # Save
            self.lbl_status.config(text="💾 Đang lưu FIXED Groups data...", fg="#fd7e14")
            
            if comments:
                df = pd.DataFrame(comments)
                
                # Add metadata
                df.insert(0, 'STT', range(1, len(df) + 1))
                df['Source'] = 'Facebook Groups - FIXED'
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
                
                self.lbl_status.config(text=f"🎉 FIXED GROUPS SCRAPING HOÀN THÀNH!", fg="#28a745")
                self.lbl_progress_detail.config(text=f"📊 FIXED Results: {len(comments)} comments | {unique_users} unique users | {profile_links} profile links | {uid_count} UIDs | Layout: {layout} | File: {file_out}")
                
                print(f"🎯 FIXED SCRAPING COMPLETE!")
                print(f"   📊 Results: {len(comments)} total comments")
                print(f"   👥 Unique users: {unique_users}")
                print(f"   🔗 Profile links: {profile_links}")
                print(f"   🆔 UIDs extracted: {uid_count}")
                print(f"   📱 Layout used: {layout}")
                print(f"   💾 Saved to: {file_out}")
                print(f"   🔍 Debug files: debug_fixed_{layout}.html")
                
            else:
                self.lbl_status.config(text="⚠️ Không tìm thấy comment với FIXED logic", fg="#ffc107")
                self.lbl_progress_detail.config(text=f"💡 Layout: {layout} | Kiểm tra debug files để phân tích Facebook structure")
                
                print(f"⚠️ No comments found with FIXED logic")
                print(f"   📱 Layout: {layout}")
                print(f"   🔍 Debug files created: debug_fixed_{layout}.html")
                print(f"   💡 FIXED Suggestions:")
                print(f"      1. Check if you have access to the Facebook Group")
                print(f"      2. Verify the post URL is correct and public in the group")
                print(f"      3. Try running without headless mode to see what's happening")
                print(f"      4. Check the debug HTML file to understand the page structure")
                print(f"      5. FIXED scroll logic should now reach absolute bottom")
                
        except Exception as e:
            error_msg = str(e)[:120]
            self.lbl_status.config(text=f"❌ Lỗi FIXED scraping: {error_msg}...", fg="#dc3545")
            self.lbl_progress_detail.config(text="🔍 Xem console để biết chi tiết. FIXED version cung cấp nhiều debug info.")
            print(f"FIXED Groups scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.stop()
            if self.scraper: 
                self.scraper.close()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

# ----------------------------
# Run FIXED app
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FBGroupsAppGUI(root)
    root.mainloop()