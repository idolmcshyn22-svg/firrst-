# fb_groups_scraper_focused.py - Focus on larger height element

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
                
                return True
                    
            except Exception as e:
                print(f"Failed to load {url_attempt}: {e}")
                continue
        
        print("❌ Failed to load post with any URL variant")
        return False
    def scroll_to_load_all_comments(self):
        """FIXED: Scroll through ALL comments containers to load all content"""
        print("📜 FIXED: Starting scroll for ALL comments containers...")
        
        try:
            # FIXED: Find ALL containers that need scrolling
            container_selectors = [
                # Primary: Your specific container
                "//div[@class='x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq' and @data-visualcompletion='ignore' and @data-thumb='1']",
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