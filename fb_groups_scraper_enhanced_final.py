# fb_groups_scraper_enhanced_final.py - Original working code + FIXED enhancements

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
from urllib.parse import urlparse, parse_qs

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
# ENHANCED FINAL Facebook Groups Scraper
# ----------------------------

class FacebookGroupsScraper:
    def __init__(self, cookie_str, headless=True):
        # ENHANCED: Store post info for PostLink generation
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
        
        # ENHANCED: Extract post info for PostLink generation
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
        """ENHANCED: Extract group and post IDs for PostLink generation"""
        try:
            print(f"🔍 ENHANCED: Extracting post info from URL: {post_url}")
            
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

    def generate_fallback_post_link(self, user_id="", username=""):
        """ENHANCED: Generate fallback PostLink if time link not found"""
        try:
            if not self.current_group_id or not self.current_post_id:
                return ""
            
            post_link = f"https://www.facebook.com/groups/{self.current_group_id}/posts/{self.current_post_id}/"
            
            if self.current_comment_id:
                post_link += f"?comment_id={self.current_comment_id}"
            
            return post_link
            
        except Exception as e:
            print(f"❌ Error generating fallback post link: {e}")
            return ""

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
            # ENHANCED: Look for multiple container types
            container_selectors = [
                # Original container
                "//div[@data-visualcompletion='ignore' and @data-thumb='1']",
                # New container types
                "//div[@class='x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq' and @data-thumb='1']",
                "//div[@class='x9f619 x1s85apg xtijo5x xg01cxk xexx8yu x18d9i69 x135b78x x11lfxj5 x47corl x10l6tqk x13vifvy x1n4smgl x1d8287x x19991ni xwji4o3 x1kky2od' and @data-thumb='1']",
                # Fallback
                "//div[@data-thumb='1']"
            ]
            
            all_containers = []
            
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    for container in containers:
                        if container not in all_containers:
                            all_containers.append(container)
                except:
                    continue
            
            print(f"Found {len(all_containers)} potential containers with data-thumb='1'")
            
            target_container = None
            max_height = 0

            for i, container in enumerate(all_containers):
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
        """Find target container and scroll to it - THIS WAS THE MISSING METHOD"""
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
        """ENHANCED: Scroll gradually through the comments container to load all content"""
        print("📜 ENHANCED: Starting gradual scroll through comments container...")
        
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
            
            # ENHANCED: Better scroll parameters
            scroll_step = 500  # Optimized steps
            scroll_pause = 2.5   # Longer pause to ensure loading
            current_position = container_top
            
            # Start from the top of container
            self.driver.execute_script(f"window.scrollTo(0, {container_top});")
            time.sleep(3)
            
            print("🚀 ENHANCED: Starting gradual scroll through comments...")
            
            step_count = 0
            max_steps = (container_height // scroll_step) + 5  # +5 for extra safety
            
            while step_count < max_steps:
                if self._stop_flag:
                    break
                    
                step_count += 1
                current_position += scroll_step
                
                # Scroll to next position
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Check current scroll position
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                page_height = self.driver.execute_script("return document.body.scrollHeight;")
                
                print(f"📜 Step {step_count}/{max_steps}: scrolled to {current_scroll}px (page: {page_height}px)")
                
                # Wait for content to load
                time.sleep(scroll_pause)
                
                # ENHANCED: Check if we've scrolled past the container or reached page bottom
                if current_scroll >= (container_top + container_height - 200):
                    print("🏁 Reached end of comments container")
                    break
                    
                if current_scroll >= (page_height - 500):
                    print("🏁 Reached page bottom")
                    break
            
            print(f"✅ Completed comment scrolling in {step_count} steps")
            
            # ENHANCED: Final comprehensive scroll to ensure everything is loaded
            print("🔄 ENHANCED: Final comprehensive scroll...")
            
            for final_attempt in range(10):  # 10 final attempts
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                current_height = self.driver.execute_script("return document.body.scrollHeight;")
                current_scroll = self.driver.execute_script("return window.pageYOffset;")
                window_height = self.driver.execute_script("return window.innerHeight;")
                
                print(f"  Final attempt {final_attempt+1}: scroll={current_scroll}px, height={current_height}px")
                
                if current_scroll >= current_height - window_height - 20:
                    print("  ✅ Confirmed at absolute bottom")
                    break
            
            print("🎯 ENHANCED: Final positioning completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during enhanced comment scrolling: {e}")
            return False

    def _switch_to_all_comments(self):
        """ENHANCED: Switch to 'All comments' view with better detection"""
        print("🔄 ENHANCED: Attempting to switch to 'All comments' view...")
        
        try:
            time.sleep(3)
            
            # ENHANCED: More comprehensive selectors
            all_comments_selectors = [
                # Vietnamese selectors with normalize-space
                "//span[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//div[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//a[contains(normalize-space(text()),'Tất cả bình luận')]",
                "//button[contains(normalize-space(text()),'Tất cả bình luận')]",
                
                # English selectors with normalize-space
                "//span[contains(normalize-space(text()),'All comments')]",
                "//div[contains(normalize-space(text()),'All comments')]",
                "//a[contains(normalize-space(text()),'All comments')]",
                "//button[contains(normalize-space(text()),'All comments')]",
                
                # Role-based selectors
                "//div[@role='button' and (contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments'))]",
                "//span[@role='button' and (contains(normalize-space(text()),'Tất cả bình luận') or contains(normalize-space(text()),'All comments'))]",
                
                # Fallback
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
                            
                            # Better validation
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
        """ENHANCED: Comment extraction with PostLink from time links"""
        print(f"=== EXTRACTING GROUPS COMMENTS (ENHANCED FINAL) ===")
        
        # Find and focus on the target container
        target_container = self.scroll_to_target_container()
        
        if not target_container:
            print("❌ Could not find target container")
            return []
        
        # Save page for debugging
        try:
            with open(f"debug_enhanced_{self.current_layout}.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"Saved page to debug_enhanced_{self.current_layout}.html")
        except:
            pass
        
        # ENHANCED: Search within the target container first
        all_comment_elements = []
        
        print("🎯 ENHANCED: Searching within target container...")
        
        # Strategy 1: Layout-specific selectors within target container
        if self.current_layout == "www":
            selectors = [
                ".//div[@role='article']",
                ".//div[contains(@aria-label, 'Comment by')]",
                ".//div[contains(@aria-label, 'Bình luận của')]",
                ".//div[.//a[contains(@href, '/user/') or contains(@href, '/profile/')]]",
                ".//div[.//h3//a[contains(@href, 'facebook.com')]]",
                # ENHANCED: Additional selectors
                ".//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 20]",
                ".//div[contains(@class, 'comment') or contains(@data-testid, 'comment')]"
            ]
        elif self.current_layout == "mobile":
            selectors = [
                ".//div[@data-sigil='comment']",
                ".//div[contains(@data-ft, 'comment')]",
                ".//div[contains(@id, 'comment_')]",
                ".//div[.//a[contains(@href, 'profile.php') or contains(@href, 'user.php')]]",
                # ENHANCED: Additional mobile selectors
                ".//div[.//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 15]"
            ]
        else:  # mbasic
            selectors = [
                ".//div[@data-ft and contains(@data-ft, 'comment')]",
                ".//div[contains(@id, 'comment_')]",
                ".//table//div[.//a[contains(@href, 'profile.php')]]",
                ".//div[.//a[contains(@href, 'profile.php?id=')]]",
                # ENHANCED: Additional mbasic selectors
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
        
        # Strategy 3: ENHANCED fallback selectors
        if len(all_comment_elements) == 0:
            print("⚠️ No comments with standard selectors, trying ENHANCED fallback...")
            
            fallback_selectors = [
                # ENHANCED: Look for any div with profile links and meaningful text
                "//div[.//a[contains(@href, 'facebook.com/')] and string-length(normalize-space(text())) > 20]",
                "//div[string-length(normalize-space(text())) > 30 and .//a[@href]]",
                "//div[@role='article' and string-length(normalize-space(text())) > 20]",
                "//*[.//a[contains(@href, 'profile')] and string-length(normalize-space(text())) > 15]",
                # ENHANCED: Additional patterns
                "//div[contains(@class, 'x') and .//a[contains(@href, 'facebook.com')] and string-length(normalize-space(text())) > 25]"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"ENHANCED fallback selector: Found {len(elements)} elements")
                    for elem in elements:
                        if elem not in all_comment_elements:
                            all_comment_elements.append(elem)
                    
                    # Stop if we found enough elements
                    if len(all_comment_elements) > 30:
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
        
        print(f"ENHANCED: Processing {len(all_comment_elements)} potential comment elements...")
        
        # Process each element
        for i, element in enumerate(all_comment_elements):
            if self._stop_flag:
                break
                
            try:
                print(f"\n--- ENHANCED Element {i+1}/{len(all_comment_elements)} ---")
                
                comment_data = self.extract_comment_data_enhanced(element, i)
                
                if not comment_data:
                    continue
                
                # Deduplication
                if comment_data['Name'] == "Unknown":
                    print("  ✗ Skipped: no username found")
                    continue
                    
                # ENHANCED: Check for duplicates using PostLink
                content_signature = f"{comment_data['Name']}_{comment_data.get('PostLink', comment_data['ProfileLink'])}"
                if content_signature in seen_content:
                    print("  ✗ Skipped: duplicate user")
                    continue
                seen_content.add(content_signature)
                
                comment_data['Type'] = 'Comment'
                comment_data['Layout'] = self.current_layout
                comment_data['Source'] = 'Target Container (ENHANCED FINAL)'
                
                comments.append(comment_data)
                post_link_preview = comment_data.get('PostLink', 'No PostLink')[:70]
                print(f"  ✅ Added: {comment_data['Name']} - PostLink: {post_link_preview}...")
                
            except Exception as e:
                print(f"  Error processing element {i}: {e}")
                continue
        
        print(f"\n=== ENHANCED FINAL EXTRACTION COMPLETE: {len(comments)} comments ===")
        return comments

    def extract_comment_data_enhanced(self, element, index):
        """ENHANCED: Comment data extraction with PostLink from time links"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 5:
                print(f"  ❌ Text too short: '{full_text}'")
                return None
            
            print(f"  ENHANCED Processing: '{full_text[:60]}...'")
            
            # Skip anonymous users
            if any(keyword in full_text.lower() for keyword in ['ẩn danh', 'người tham gia ẩn danh', 'anonymous']):
                print("  ⚠️ Skipping anonymous user comment")
                return None
            
            username = "Unknown"
            profile_href = ""
            uid = "Unknown"
            post_link = ""
            
            # ENHANCED: Get ALL links and analyze
            print(f"    🎯 ENHANCED analysis of element structure...")
            
            try:
                all_links = element.find_elements(By.XPATH, ".//a")
                print(f"    Found {len(all_links)} total links in element")
                
                # ENHANCED: Separate profile links and time links
                potential_profile_links = []
                time_links = []
                
                for link_index, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        print(f"      Link {link_index+1}: Text='{link_text}' | Href={link_href[:60]}...")
                        
                        # ENHANCED: Detect time links first
                        time_patterns = [
                            r'^\d+\s*ngày',      # "1 ngày", "4 ngày"
                            r'^\d+\s*giờ',       # "1 giờ", "2 giờ"  
                            r'^\d+\s*phút',      # "1 phút", "30 phút"
                            r'^\d+\s*giây',      # "1 giây", "45 giây"
                            r'^\d+\s*day',       # "1 day", "2 days"
                            r'^\d+\s*hour',      # "1 hour", "2 hours"
                            r'^\d+\s*min',       # "1 min", "30 mins"
                            r'^\d+\s*h$',        # "1h", "2h"
                            r'^\d+\s*m$',        # "1m", "30m"
                            r'^\d+\s*d$',        # "1d", "2d"
                        ]
                        
                        is_time_link = False
                        if link_text:
                            text_lower = link_text.lower().strip()
                            
                            # Check time patterns
                            for pattern in time_patterns:
                                if re.match(pattern, text_lower):
                                    is_time_link = True
                                    break
                            
                            # Special cases
                            if not is_time_link and text_lower in ['just now', 'vừa xong', 'now', 'bây giờ']:
                                is_time_link = True
                        
                        # Check if it's a Facebook comment link
                        is_facebook_comment_link = (link_href and 
                                                   'facebook.com' in link_href and 
                                                   'comment_id=' in link_href)
                        
                        # ENHANCED: Collect time links
                        if is_time_link and is_facebook_comment_link:
                            cleaned_href = link_href.replace('&amp;', '&')
                            time_links.append({
                                'text': link_text,
                                'href': cleaned_href,
                                'index': link_index
                            })
                            print(f"        🕐 ENHANCED: Found time link: '{link_text}' -> {cleaned_href[:60]}...")
                        
                        # ENHANCED: Collect profile links
                        elif ('facebook.com' in link_href and 
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
                                
                                # ENHANCED: Extract UID with comprehensive patterns
                                extracted_uid = "Unknown"
                                uid_patterns = [
                                    r'profile\.php\?id=(\d+)',
                                    r'user\.php\?id=(\d+)',
                                    r'/user/(\d+)',
                                    r'[?&]id=(\d+)',
                                    r'facebook\.com/([^/?&]+)/?$',       # username
                                    r'(\d{10,})'  # 10+ digit UIDs
                                ]
                                
                                for pattern in uid_patterns:
                                    uid_match = re.search(pattern, link_href)
                                    if uid_match:
                                        potential_uid = uid_match.group(1)
                                        
                                        if potential_uid.isdigit() and len(potential_uid) >= 8:
                                            extracted_uid = potential_uid
                                            break
                                        elif not potential_uid.isdigit() and len(potential_uid) >= 3:
                                            extracted_uid = f"username:{potential_uid}"
                                            break
                                
                                potential_profile_links.append({
                                    'text': link_text,
                                    'href': link_href,
                                    'uid': extracted_uid,
                                    'priority': len(link_text) if len(link_text) < 50 else 0
                                })
                                
                                print(f"        👤 ENHANCED: Found profile: {link_text} -> UID: {extracted_uid}")
                                
                    except Exception as e:
                        print(f"      Error processing link {link_index+1}: {e}")
                        continue
                
                print(f"    📊 ENHANCED: Found {len(potential_profile_links)} profile links, {len(time_links)} time links")
                
                # ENHANCED: Select best profile link
                if potential_profile_links:
                    # Sort by priority (higher is better)
                    potential_profile_links.sort(key=lambda x: x['priority'], reverse=True)
                    
                    best_link = potential_profile_links[0]
                    username = best_link['text']
                    profile_href = best_link['href']
                    uid = best_link['uid']
                    
                    print(f"      🎯 ENHANCED: Selected best profile: {username} -> UID: {uid}")
                
                # ENHANCED: Get PostLink from time link
                if time_links:
                    # Use the first time link found
                    best_time_link = time_links[0]
                    post_link = best_time_link['href']
                    print(f"      🔗 ENHANCED: Found PostLink from time link '{best_time_link['text']}':")
                    print(f"          {post_link[:80]}...")
                else:
                    # Fallback: generate PostLink
                    post_link = self.generate_fallback_post_link(uid, username)
                    print(f"      🔗 ENHANCED: Using fallback PostLink: {post_link[:60]}...")
                
            except Exception as e:
                print(f"    Error in ENHANCED method: {e}")
            
            # Final validation
            if username == "Unknown":
                print("  ❌ ENHANCED extraction failed for this element")
                return None
                
            print(f"  ✅ ENHANCED: Successfully extracted username: {username}")
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,
                "PostLink": post_link,  # ENHANCED: PostLink from time links
                "CommentLink": "",
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "Enhanced Final - Larger height container",
                "PostLinkSource": "TimeLink" if time_links else "Generated"
            }
            
        except Exception as e:
            print(f"Error in ENHANCED extraction: {e}")
            return None

    def expand_groups_comments(self, max_iterations=50):
        """ENHANCED: Expansion focused on target container with better scroll"""
        print(f"=== EXPANDING GROUPS COMMENTS (ENHANCED FINAL) ===")
        
        # Focus on target container first
        target_container = self.find_target_container()
        
        for iteration in range(max_iterations):
            if self._stop_flag:
                break
                
            print(f"[Iteration {iteration+1}] ENHANCED scrolling and expanding...")
            
            # ENHANCED: Try multiple scroll approaches
            if target_container:
                try:
                    # Method 1: Container scroll
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", target_container)
                    time.sleep(1)
                    
                    # Method 2: Check if container is scrollable
                    is_scrollable = self.driver.execute_script("return arguments[0].scrollHeight > arguments[0].clientHeight;", target_container)
                    if not is_scrollable:
                        print(f"    ⚠️ Container not scrollable, using window scroll")
                        
                except Exception as e:
                    print(f"    Container scroll failed: {e}")
                    target_container = self.find_target_container()
            
            # Also scroll the main page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.5, 4))  # Longer wait
            
            # ENHANCED: Look for expand links with better detection
            expand_selectors = [
                "//a[contains(normalize-space(text()),'View more comments')]",
                "//a[contains(normalize-space(text()),'Xem thêm bình luận')]",
                "//a[contains(normalize-space(text()),'Show more')]",
                "//a[contains(normalize-space(text()),'See more')]",
                "//div[@role='button' and (contains(normalize-space(text()),'more') or contains(normalize-space(text()),'thêm'))]",
                # ENHANCED: Additional expand selectors
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
                                # Scroll into view before clicking
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                                time.sleep(1)
                                
                                elem.click()
                                expanded = True
                                print(f"    ✓ ENHANCED: Clicked: {elem.text}")
                                time.sleep(3)
                                break
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    expanded = True
                                    print(f"    ✓ ENHANCED: JS clicked: {elem.text}")
                                    time.sleep(3)
                                    break
                                except:
                                    continue
                    if expanded:
                        break
                except:
                    continue
            
            if not expanded and iteration > 7:  # More patience
                print(f"    No expansion found, stopping early")
                break
        
        print("=== ENHANCED FINAL EXPANSION COMPLETE ===")

    def scrape_all_comments(self, limit=0, resolve_uid=True, progress_callback=None):
        """ENHANCED: Main scraping orchestrator"""
        print(f"=== STARTING ENHANCED FINAL GROUPS SCRAPING ===")
        
        # Step 1: Expand all content with enhanced logic
        self.expand_groups_comments()
        
        if self._stop_flag:
            return []
        
        # Step 2: Extract comments with enhanced logic
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
# ENHANCED FINAL GUI
# ----------------------------

class FBGroupsAppGUI:
    def __init__(self, root):
        self.root = root
        root.title("🎯 FB Groups Comment Scraper - ENHANCED FINAL")
        root.geometry("1100x950")
        root.configure(bg="#e8f5e8")

        # Main frame
        main_frame = tk.Frame(root, bg="#e8f5e8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_frame = tk.Frame(main_frame, bg="#e8f5e8")
        header_frame.pack(fill="x", pady=(0,20))
        
        title_label = tk.Label(header_frame, text="🎯 Facebook Groups Comment Scraper - ENHANCED FINAL", 
                              font=("Arial", 20, "bold"), bg="#e8f5e8", fg="#2d5a2d")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="🎯 Enhanced Final - UID extraction + PostLink from time links + Multi-container scroll", 
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
        options_frame = tk.LabelFrame(main_frame, text="🎯 Cấu hình ENHANCED FINAL", font=("Arial", 12, "bold"), 
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
        self.entry_file.insert(0, "facebook_groups_comments_ENHANCED_FINAL.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        tk.Button(file_row, text="📁 Chọn", command=self.choose_file, 
                 bg="#17a2b8", fg="white", font=("Arial", 9)).pack(side="right", padx=(10,0))

        # Status section
        status_frame = tk.LabelFrame(main_frame, text="📊 Trạng thái thực thi - ENHANCED FINAL", font=("Arial", 12, "bold"), 
                                    bg="#e8f5e8", fg="#2d5a2d", relief="groove", bd=2)
        status_frame.pack(fill="x", pady=(0,15))
        
        self.lbl_status = tk.Label(status_frame, text="✅ ENHANCED FINAL scraper sẵn sàng - UID + PostLink from time links", fg="#28a745", 
                                  wraplength=900, justify="left", font=("Arial", 11), bg="#e8f5e8")
        self.lbl_status.pack(anchor="w", padx=15, pady=(15,5))

        enhanced_features_text = ("💡 ENHANCED FINAL: 1) UID extraction with 6 patterns, "
                                "2) PostLink from time links ('4 ngày', '1 giờ'), "
                                "3) Multi-container scroll support, 4) Enhanced debugging, "
                                "5) Comprehensive fallback strategies")
        
        self.lbl_progress_detail = tk.Label(status_frame, text=enhanced_features_text,
                                          fg="#6c757d", wraplength=900, justify="left", font=("Arial", 9), bg="#e8f5e8")
        self.lbl_progress_detail.pack(anchor="w", padx=15, pady=(0,10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(0,15))

        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#e8f5e8")
        button_frame.pack(fill="x", pady=20)
        
        self.btn_start = tk.Button(button_frame, text="🚀 Bắt đầu ENHANCED FINAL", bg="#28a745", fg="white", 
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
            title="Chọn file để lưu ENHANCED FINAL Groups comments"
        )
        if f:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, f)

    def start_scrape_thread(self):
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "facebook_groups_comments_ENHANCED_FINAL.xlsx"
        
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
        self.lbl_status.config(text="🔄 Đang khởi động ENHANCED FINAL scraper...", fg="#fd7e14")
        self.lbl_progress_detail.config(text="⏳ Initializing ENHANCED FINAL - UID + PostLink from time links...")
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
        self.lbl_status.config(text="⏹️ Đang dừng ENHANCED FINAL scraper...", fg="#dc3545")
        self.btn_stop.config(state=tk.DISABLED)

    def _progress_cb(self, count):
        self.progress_var.set(count)
        self.lbl_status.config(text=f"📈 ENHANCED FINAL processing... Đã lấy {count} comments", fg="#28a745")
        self.root.update_idletasks()

    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, resolve_uid):
        try:
            # Initialize
            self.lbl_status.config(text="🌐 Khởi tạo ENHANCED FINAL scraper...", fg="#fd7e14")
            self.scraper = FacebookGroupsScraper(cookie_str, headless=headless)
            
            if self._stop_flag: return
            
            # Load post
            self.lbl_status.config(text="📄 Đang tải bài viết Groups với ENHANCED FINAL...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Loading post with enhanced UID + PostLink extraction...")
            success = self.scraper.load_post(url)
            
            if not success:
                self.lbl_status.config(text="❌ Không thể tải bài viết Groups", fg="#dc3545")
                self.lbl_progress_detail.config(text="💡 Kiểm tra: 1) Cookie valid, 2) Quyền truy cập Groups, 3) Link chính xác")
                return
            
            # Show detected layout
            layout = getattr(self.scraper, 'current_layout', 'unknown')
            self.lbl_progress_detail.config(text=f"🎯 Layout detected: {layout} - Using ENHANCED FINAL methods...")
                
            if self._stop_flag: return
            
            # Scrape with ENHANCED FINAL logic
            self.lbl_status.config(text=f"🔍 ENHANCED FINAL extraction ({layout})...", fg="#fd7e14")
            self.lbl_progress_detail.config(text="⏳ Extracting UID + PostLink from time links...")
            
            comments = self.scraper.scrape_all_comments(limit=limit, resolve_uid=resolve_uid, 
                                                       progress_callback=self._progress_cb)
            
            if self._stop_flag: return
            
            # Save
            self.lbl_status.config(text="💾 Đang lưu ENHANCED FINAL data...", fg="#fd7e14")
            
            if comments:
                df = pd.DataFrame(comments)
                
                # Add metadata
                df.insert(0, 'STT', range(1, len(df) + 1))
                df['Source'] = 'Facebook Groups - ENHANCED FINAL'
                df['ScrapedAt'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # File handling
                if not file_out.lower().endswith((".xlsx", ".csv")):
                    file_out += ".xlsx"
                
                if file_out.lower().endswith(".csv"):
                    df.to_csv(file_out, index=False, encoding="utf-8-sig")
                else:
                    df.to_excel(file_out, index=False, engine="openpyxl")
                
                # ENHANCED: Statistics
                unique_users = len(set(c['Name'] for c in comments if c['Name'] != 'Unknown'))
                profile_links = len([c for c in comments if c['ProfileLink']])
                uid_count = len([c for c in comments if c['UID'] != 'Unknown'])
                post_links = len([c for c in comments if c.get('PostLink')])
                time_link_count = len([c for c in comments if c.get('PostLinkSource') == 'TimeLink'])
                
                self.lbl_status.config(text=f"🎉 ENHANCED FINAL HOÀN THÀNH!", fg="#28a745")
                self.lbl_progress_detail.config(text=f"📊 Results: {len(comments)} comments | {unique_users} users | {uid_count} UIDs | {post_links} PostLinks | {time_link_count} from TimeLinks")
                
                print(f"🎯 ENHANCED FINAL SCRAPING COMPLETE!")
                print(f"   📊 Results: {len(comments)} total comments")
                print(f"   👥 Unique users: {unique_users}")
                print(f"   🔗 Profile links: {profile_links}")
                print(f"   🆔 UIDs extracted: {uid_count}")
                print(f"   🔗 PostLinks: {post_links}")
                print(f"   🕐 PostLinks from TimeLinks: {time_link_count}")
                print(f"   📱 Layout used: {layout}")
                print(f"   💾 Saved to: {file_out}")
                print(f"   🔍 Debug files: debug_enhanced_{layout}.html")
                
            else:
                self.lbl_status.config(text="⚠️ Không tìm thấy comment với ENHANCED FINAL", fg="#ffc107")
                self.lbl_progress_detail.config(text=f"💡 Layout: {layout} | Kiểm tra debug files để phân tích")
                
                print(f"⚠️ No comments found with ENHANCED FINAL logic")
                print(f"   📱 Layout: {layout}")
                print(f"   🔍 Debug files created: debug_enhanced_{layout}.html")
                print(f"   💡 ENHANCED FINAL Suggestions:")
                print(f"      1. Check if you have access to the Facebook Group")
                print(f"      2. Verify the post URL is correct and public in the group")
                print(f"      3. Try running without headless mode to see what's happening")
                print(f"      4. Check the debug HTML file to understand the page structure")
                
        except Exception as e:
            error_msg = str(e)[:120]
            self.lbl_status.config(text=f"❌ Lỗi ENHANCED FINAL: {error_msg}...", fg="#dc3545")
            self.lbl_progress_detail.config(text="🔍 Xem console để biết chi tiết. ENHANCED FINAL cung cấp debug info.")
            print(f"ENHANCED FINAL Groups scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.progress_bar.stop()
            if self.scraper: 
                self.scraper.close()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

# ----------------------------
# Run ENHANCED FINAL app
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = FBGroupsAppGUI(root)
    root.mainloop()