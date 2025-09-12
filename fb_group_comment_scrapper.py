#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Facebook Groups Ultra Fast Scraper - Optimized for 30k+ Comments
Tối ưu hóa để lấy 30k comments nhanh nhất có thể
"""

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
import os
import json

# ----------------------------
# Ultra Fast Helper Functions
# ----------------------------

def parse_cookies_to_list(cookie_str):
    cookies_list = []
    for pair in cookie_str.split(';'):
        pair = pair.strip()
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies_list.append({'name': name.strip(), 'value': value.strip(), 'domain': '.facebook.com'})
    return cookies_list

def save_to_excel_fast(data, filename):
    """Ultra fast Excel saving with optimizations - Fixed"""
    try:
        if not data:
            print("⚠️ No data to save")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Ensure required columns exist
        required_columns = ['UID', 'Name', 'ProfileLink', 'CommentLink', 'Type', 'Layout', 'Source']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Reorder columns for better readability
        column_order = ['UID', 'Name', 'ProfileLink', 'CommentLink', 'Type', 
                       'Layout', 'Source', 'ElementIndex', 'TextPreview', 'ContainerHeight']
        
        # Only include columns that exist in the dataframe
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        # Save to Excel - Fixed without options parameter
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Comments', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Comments']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✅ Successfully saved {len(data)} records to {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to Excel: {e}")
        return False

# ----------------------------
# Ultra Fast Facebook Groups Scraper
# ----------------------------

class UltraFastFacebookGroupsScraper:
    def __init__(self, cookie_str, headless=True):
        # Ultra optimized Chrome options
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        
        # ULTRA PERFORMANCE optimizations for 30k+ comments
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-images")  # Disable images for faster loading
        options.add_argument("--disable-javascript")  # Disable JS for faster parsing
        options.add_argument("--disable-plugins")  # Disable plugins
        options.add_argument("--disable-extensions")  # Disable extensions
        options.add_argument("--disable-web-security")  # Disable web security
        options.add_argument("--disable-features=VizDisplayCompositor")  # Disable compositor
        options.add_argument("--memory-pressure-off")  # Disable memory pressure
        options.add_argument("--max_old_space_size=4096")  # Increase memory limit
        options.add_argument("--disable-css")  # Disable CSS for speed
        # Fix WebGL fallback error
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        # Faster user agent
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        # Set multiple timeout configurations to prevent HTTPConnectionPool errors
        self.driver.set_page_load_timeout(60)  # Page load timeout
        self.driver.implicitly_wait(10)  # Implicit wait for elements
        self.wait = WebDriverWait(self.driver, 30)  # Explicit wait timeout
        self.cookie_str = cookie_str or ""
        self.cookies_list = parse_cookies_to_list(self.cookie_str)
        self._stop_flag = False
        self.current_layout = None
        
        # Ultra fast tracking
        self.comment_limit = 0
        self.extracted_count = 0
        self.total_estimated = 0
        self.progress_callback = None
        self.batch_size = 100  # Process in batches for speed
        self.current_comments_data = []  # Store comments for save on stop
        
        # Timeout tracking for browser restart
        self.timeout_count = 0
        self.max_timeouts = 5  # Restart browser after 5 timeouts
        
        # Progress preservation for browser restart
        self.current_post_url = None
        self.scroll_position = 0
        self.extracted_elements = []  # Store extracted elements to avoid re-extraction
        self.scroll_progress = 0  # Track scroll progress
        self.loaded_comments_count = 0  # Track how many comments were loaded before restart
        self.page_height_before_restart = 0  # Track page height before restart
        
        if self.cookies_list:
            self._login_with_cookies()

    def _login_with_cookies(self):
        """Ultra fast login"""
        self.driver.get("https://www.facebook.com")
        time.sleep(2)  # Reduced wait time
        
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
        time.sleep(3)  # Reduced wait time

    def _restart_browser_on_timeout(self):
        """Restart browser when too many timeouts occur"""
        try:
            print("🔄 Restarting browser due to timeout issues...")
            
            # Close current browser
            try:
                self.driver.quit()
            except:
                pass
            
            # Reinitialize browser with same settings
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-features=VizDisplayCompositor")
            # Fix WebGL fallback error
            options.add_argument("--enable-unsafe-swiftshader")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-gpu-sandbox")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Create new driver
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Reset timeout count
            self.timeout_count = 0
            
            # Re-login
            self._login_with_cookies()
            
            print("✅ Browser restarted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to restart browser: {e}")
            return False

    def _save_scroll_progress(self, scroll_index, comments_data):
        """Save current scroll progress to avoid losing data"""
        try:
            self.scroll_progress = scroll_index
            self.current_comments_data = comments_data.copy() if comments_data else []
            self.loaded_comments_count = len(comments_data) if comments_data else 0
            
            # Get current scroll position and page height
            try:
                self.scroll_position = self.driver.execute_script("return window.pageYOffset;")
                self.page_height_before_restart = self.driver.execute_script("return document.body.scrollHeight")
            except:
                self.scroll_position = 0
                self.page_height_before_restart = 0
            
            print(f"💾 Progress saved: {self.loaded_comments_count} comments, scroll {scroll_index}, height {self.page_height_before_restart}px")
            
        except Exception as e:
            print(f"⚠️ Error saving progress: {e}")

    def _restore_scroll_progress(self):
        """Restore to previous scroll position after browser restart with aggressive comment loading"""
        try:
            if not self.current_post_url:
                return False
                
            print(f"🔄 Restoring progress: {len(self.current_comments_data)} comments, scroll {self.scroll_progress}")
            
            # Reload the post
            if not self.load_post_ultra_fast(self.current_post_url):
                print("❌ Failed to reload post")
                return False
            
            # Wait for page to load
            time.sleep(5)
            
            # AGGRESSIVE COMMENT LOADING: Simulate the scrolling process to load comments
            print(f"🔄 Aggressively loading comments to restore position (target scroll: {self.scroll_progress})...")
            
            # Step 1: Switch to "All comments" view
            self._switch_to_all_comments()
            time.sleep(3)
            
            # Step 2: Simulate scrolling process to trigger comment loading
            restored_scrolls = 0
            target_scrolls = min(self.scroll_progress, 300)  # Increased limit for better restoration
            
            # Track restoration progress
            restoration_start_time = time.time()
            last_height = 0
            no_growth_count = 0
            
            for i in range(target_scrolls):
                try:
                    # Fast scroll to trigger loading
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.15)  # Very fast scrolling for restoration
                    
                    # Click "View more comments" aggressively
                    if i % 3 == 0:  # Every 3 scrolls, try to click "View more" (more aggressive)
                        clicked = self._click_view_more_comments_fast()
                        if clicked:
                            time.sleep(0.3)  # Brief wait after successful click
                    
                    # Check if page is growing (comments being loaded)
                    if i % 10 == 0:
                        try:
                            current_height = self.driver.execute_script("return document.body.scrollHeight")
                            if current_height > last_height:
                                last_height = current_height
                                no_growth_count = 0
                                print(f"  📈 Page growing: {current_height}px (target: ~{self.page_height_before_restart}px)")
                            else:
                                no_growth_count += 1
                                
                            # If page stops growing for too long, try more aggressive clicking
                            if no_growth_count > 3:
                                print("  🔥 Page not growing, trying aggressive comment loading...")
                                for _ in range(3):
                                    self._click_view_more_comments_fast()
                                    time.sleep(0.2)
                                no_growth_count = 0
                                
                        except:
                            pass
                    
                    restored_scrolls += 1
                    
                    # Progress indicator
                    if i % 20 == 0:
                        elapsed_time = time.time() - restoration_start_time
                        print(f"  📊 Restoration progress: {i}/{target_scrolls} scrolls ({elapsed_time:.1f}s)")
                    
                    # Early exit if we've likely restored enough
                    if i > 50 and last_height >= self.page_height_before_restart * 0.8:
                        print(f"  ✅ Early completion: Page height {last_height}px ≈ target {self.page_height_before_restart}px")
                        break
                    
                except Exception as restore_scroll_e:
                    print(f"⚠️ Error during restoration scroll {i}: {restore_scroll_e}")
                    continue
            
            print(f"✅ Restoration complete: {restored_scrolls}/{target_scrolls} scrolls restored")
            
            # Step 3: Final scroll to approximate position
            try:
                final_height = self.driver.execute_script("return document.body.scrollHeight")
                print(f"📏 Final page height after restoration: {final_height}px")
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring progress: {e}")
            return False

    def _click_view_more_comments_fast(self):
        """Fast click on View more comments during restoration"""
        try:
            view_more_selectors = [
                "//*[contains(text(), 'View more comments')]",
                "//*[contains(text(), 'Xem thêm bình luận')]",
                "//*[contains(text(), 'Load more')]",
                "//*[contains(text(), 'Show more')]"
            ]
            
            for selector in view_more_selectors[:2]:  # Only try first 2 selectors for speed
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        element = elements[0]
                        if element.is_displayed() and element.is_enabled():
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(0.5)  # Short wait
                            return True
                except:
                    continue
            return False
        except:
            return False

    def _scroll_to_specific_comment(self, comment_url):
        """Scroll to specific comment when using comment link"""
        try:
            print("🎯 Attempting to scroll to specific comment...")
            
            # Extract comment ID from URL
            comment_id = None
            if "comment_id=" in comment_url:
                comment_id = comment_url.split("comment_id=")[1].split("&")[0]
                print(f"📝 Comment ID: {comment_id}")
            
            if not comment_id:
                print("⚠️ Could not extract comment ID from URL")
                return False
            
            # Wait for page to load
            time.sleep(3)
            
            # Try to find the specific comment element
            comment_selectors = [
                f"//div[@data-ft*='{comment_id}']",
                f"//div[contains(@id, '{comment_id}')]",
                f"//div[contains(@data-sigil, 'comment') and contains(@data-ft, '{comment_id}')]",
                f"//div[@role='article' and contains(@data-ft, '{comment_id}')]",
                f"//a[contains(@href, 'comment_id={comment_id}')]"
            ]
            
            comment_element = None
            for selector in comment_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        comment_element = elements[0]
                        print(f"✅ Found comment element with selector: {selector}")
                        break
                except:
                    continue
            
            if comment_element:
                # Scroll to the comment
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", comment_element)
                    time.sleep(2)
                    print("✅ Scrolled to specific comment successfully")
                    
                    # Highlight the comment briefly
                    self.driver.execute_script("arguments[0].style.border = '3px solid red';", comment_element)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].style.border = '';", comment_element)
                    
                    return True
                except Exception as e:
                    print(f"⚠️ Error scrolling to comment: {e}")
                    return False
            else:
                print("⚠️ Could not find specific comment element, will continue with normal scrolling")
                return False
                
        except Exception as e:
            print(f"❌ Error in scroll to specific comment: {e}")
            return False

    def load_post_ultra_fast(self, post_url):
        """Ultra fast post loading"""
        print(f"🚀 Ultra fast loading: {post_url}")
        
        # Save URL for progress restoration
        self.current_post_url = post_url
        
        # Check if this is a comment link
        self.is_comment_link = "comment_id=" in post_url
        
        # Try mobile first for speed
        if "groups/" in post_url:
            mobile_url = post_url.replace("www.facebook.com", "m.facebook.com").replace("mbasic.facebook.com", "m.facebook.com")
            urls_to_try = [mobile_url, post_url]
        else:
            urls_to_try = [post_url]
        
        for url_attempt in urls_to_try:
            try:
                print(f"⚡ Trying: {url_attempt}")
                self.driver.get(url_attempt)
                time.sleep(3)  # Reduced wait time
                
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                # Detect layout
                if "m.facebook.com" in current_url:
                    self.current_layout = "mobile"
                elif "mbasic.facebook.com" in current_url:
                    self.current_layout = "mbasic"
                else:
                    self.current_layout = "www"
                
                print(f"📱 Layout: {self.current_layout}")
                
                # Check login status
                if any(keyword in page_title.lower() for keyword in ["log in", "login", "đăng nhập"]):
                    print("❌ Not logged in, trying next...")
                    continue
                
                print(f"✅ Loaded with {self.current_layout} layout")
                
                # If this is a comment link, scroll to the specific comment first
                if self.is_comment_link:
                    print("🔗 Comment link detected - scrolling to specific comment...")
                    self._scroll_to_specific_comment(post_url)
                
                # Ultra fast comment loading
                self._ultra_fast_load_comments()
                
                return True
                    
            except Exception as e:
                print(f"❌ Failed: {e}")
                continue
        
        print("❌ Failed to load post")
        return False

    def _ultra_fast_load_comments(self):
        """Ultra fast comment loading strategy - Enhanced with All Comments logic from focused code"""
        print("⚡ Ultra fast comment loading for 30k+ comments...")
        
        try:
            # Step 1: Try to switch to "All comments" view first (from focused code)
            self._switch_to_all_comments()
            
            # Step 2: Enhanced scrolling strategy for maximum comments - TARGET 3K COMMENTS
            max_scroll_attempts = 275  # Optimized for 3k comments (275 scrolls = 3k comments)
            scroll_count = 0
            no_new_comments_count = 0
            max_no_new_comments = 25  # Balanced tolerance for no new comments
            consecutive_empty_scrolls = 0
            max_consecutive_empty = 50  # Stop if 50 consecutive scrolls yield no new content
            
            for i in range(max_scroll_attempts):
                if self._stop_flag:
                    break
                
                # Store current page height before scrolling with timeout protection
                try:
                    previous_height = self.driver.execute_script("return document.body.scrollHeight")
                except Exception as height_e:
                    print(f"⚠️ Error getting initial height: {height_e}")
                    previous_height = 0
                
                # Scroll to bottom with multiple scroll attempts - OPTIMIZED FOR 8K COMMENTS
                for scroll_step in range(4):  # Optimized scroll steps for 8k target
                    try:
                        # Add timeout protection for each scroll operation
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(0.4)  # Balanced wait time for stability
                        
                        # Additional scroll variations for better comment loading
                        if scroll_step % 2 == 0:
                            # Scroll to middle of page occasionally
                            try:
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                                time.sleep(0.3)
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            except Exception as mid_scroll_e:
                                print(f"⚠️ Mid scroll error: {mid_scroll_e}")
                                continue
                    except Exception as scroll_e:
                        print(f"⚠️ Scroll step {scroll_step} error: {scroll_e}")
                        
                        # Check if it's a timeout error
                        if "HTTPConnectionPool" in str(scroll_e) or "timeout" in str(scroll_e).lower():
                            self.timeout_count += 1
                            print(f"⚠️ Timeout count: {self.timeout_count}/{self.max_timeouts}")
                            
                            # Restart browser if too many timeouts
                            if self.timeout_count >= self.max_timeouts:
                                # Extract current comments before restart to preserve data
                                print("🚨 CRITICAL: Extracting comments before browser restart to preserve data...")
                                try:
                                    current_extracted_comments = self.extract_comments_ultra_fast()
                                    print(f"💾 Extracted {len(current_extracted_comments)} comments before restart")
                                except Exception as extract_e:
                                    print(f"⚠️ Could not extract comments before restart: {extract_e}")
                                    current_extracted_comments = self.current_comments_data if hasattr(self, 'current_comments_data') else []
                                
                                # Save progress with actual extracted comments
                                self._save_scroll_progress(i, current_extracted_comments)
                                
                                if self._restart_browser_on_timeout():
                                    # Try to restore progress
                                    print("🔄 Attempting to restore progress after browser restart...")
                                    if self._restore_scroll_progress():
                                        print("✅ Progress restored successfully")
                                        print(f"📊 Preserved data: {len(self.current_comments_data)} comments")
                                        # Continue from where we left off, but adjust scroll index
                                        i = max(0, self.scroll_progress - 10)  # Resume a bit earlier for safety
                                        print(f"🔄 Resuming from scroll {i} (was {self.scroll_progress})")
                                        time.sleep(3)
                                    else:
                                        print("⚠️ Could not restore progress, continuing from current position")
                                        time.sleep(5)
                                else:
                                    print("❌ Browser restart failed, stopping scroll")
                                    break
                        
                        # Try to continue scrolling even if one step fails
                        time.sleep(1)
                        continue
                
                # Wait for content to load
                time.sleep(2)  # Increased wait time for content loading
                
                # Check if page height increased (new content loaded) with timeout protection
                try:
                    current_height = self.driver.execute_script("return document.body.scrollHeight")
                except Exception as final_height_e:
                    print(f"⚠️ Error getting final height: {final_height_e}")
                    current_height = previous_height
                height_increased = current_height > previous_height
                
                # Look for "View more comments" and click rapidly - ENHANCED FOR 30K COMMENTS
                view_more_selectors = [
                    "//*[contains(text(), 'View more comments')]",
                    "//*[contains(text(), 'Xem thêm bình luận')]",
                    "//*[contains(text(), 'Load more')]",
                    "//*[contains(text(), 'Show more')]",
                    "//*[contains(text(), 'See more comments')]",
                    "//*[contains(text(), 'View all comments')]",
                    "//*[contains(text(), 'Tất cả bình luận')]",
                    "//*[contains(text(), 'Load more comments')]",
                    "//*[contains(text(), 'Show more comments')]",
                    "//*[contains(text(), 'See more')]",
                    "//button[contains(@aria-label, 'View more')]",
                    "//div[@role='button' and contains(text(), 'more')]",
                    "//a[contains(@href, 'more_comments')]"
                ]
                
                # Click multiple "View more" buttons per scroll - OPTIMIZED FOR 8K COMMENTS
                clicked_any = False
                max_clicks_per_scroll = 2  # Click up to 2 buttons per scroll for balance
                clicks_this_scroll = 0
                
                for selector in view_more_selectors:
                    if clicks_this_scroll >= max_clicks_per_scroll:
                        break
                        
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if clicks_this_scroll >= max_clicks_per_scroll:
                                break
                                
                            if element.is_displayed() and element.is_enabled():
                                try:
                                    # Scroll element into view first
                                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                                    time.sleep(0.3)  # Faster wait
                                    
                                    # Click the element
                                    self.driver.execute_script("arguments[0].click();", element)
                                    clicked_any = True
                                    clicks_this_scroll += 1
                                    print(f"🖱️ Clicked: {element.text[:30]}... (scroll {i+1}, click {clicks_this_scroll})")
                                    time.sleep(0.5)  # Short wait between clicks
                                except:
                                    continue
                        if clicked_any:
                            break
                    except:
                        continue
                
                # Check if we found new comments or content
                if clicked_any or height_increased:
                    no_new_comments_count = 0
                    consecutive_empty_scrolls = 0
                    scroll_count += 1
                    print(f"📊 Scroll {scroll_count}: Found new content (height: {previous_height} -> {current_height})")
                else:
                    no_new_comments_count += 1
                    consecutive_empty_scrolls += 1
                    print(f"📊 Scroll {i+1}: No new content ({no_new_comments_count}/{max_no_new_comments}, empty: {consecutive_empty_scrolls}/{max_consecutive_empty})")
                
                # Stop conditions
                if no_new_comments_count >= max_no_new_comments:
                    print(f"🏁 Stopping scroll: No new comments for {max_no_new_comments} attempts")
                    break
                
                if consecutive_empty_scrolls >= max_consecutive_empty:
                    print(f"🏁 Stopping scroll: {max_consecutive_empty} consecutive empty scrolls")
                    break
                
                # Progress update with more frequent reporting
                if i % 10 == 0:  # Progress updates every 10 scrolls for 275 scrolls
                    print(f"🔄 Scrolling progress: {i+1}/{max_scroll_attempts} (Target: 3k comments)")
                    
                    # Save progress periodically (every 25 scrolls for 275 scrolls)
                    if i % 25 == 0:
                        self._save_scroll_progress(i, self.current_comments_data)
                    
                    # Update progress callback if available
                    if self.progress_callback:
                        self.progress_callback(i+1, f"Đang scroll để lấy comments... ({i+1}/{max_scroll_attempts})")
                
                # Adaptive wait time based on scroll count for 275 scrolls - OPTIMIZED FOR 3K COMMENTS
                if i > 50:  # After 50 scrolls, slight increase
                    time.sleep(0.8)
                elif i > 100:  # After 100 scrolls, increase wait time
                    time.sleep(1.0)
                elif i > 150:  # After 150 scrolls, increase wait time more
                    time.sleep(1.2)
                elif i > 200:  # After 200 scrolls, even more wait time
                    time.sleep(1.5)
                elif i > 250:  # After 250 scrolls, maximum wait time
                    time.sleep(2.0)
        
        except Exception as e:
            print(f"⚠️ Ultra fast loading error: {e}")

    def _switch_to_all_comments(self):
        """Switch to 'All comments' view to get more comments - from focused code"""
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

    def extract_comments_ultra_fast(self):
        """Ultra fast comment extraction"""
        print(f"⚡ ULTRA FAST EXTRACTION STARTING")
        
        all_comment_elements = []
        
        # Enhanced selectors based on layout (from working code)
        if self.current_layout == "www":
            selectors = [
                "//div[@role='article']",
                "//div[contains(@aria-label, 'Comment by')]",
                "//div[contains(@aria-label, 'Bình luận của')]",
                "//div[.//a[contains(@href, '/user/') or contains(@href, '/profile/')]]",
                "//div[.//h3//a[contains(@href, 'facebook.com')]]"
            ]
        elif self.current_layout == "mobile":
            selectors = [
                "//div[@data-sigil='comment']",
                "//div[contains(@data-ft, 'comment')]",
                "//div[contains(@id, 'comment_')]",
                "//div[.//a[contains(@href, 'profile.php') or contains(@href, 'user.php')]]"
            ]
        else:  # mbasic
            selectors = [
                "//div[@data-ft and contains(@data-ft, 'comment')]",
                "//div[contains(@id, 'comment_')]",
                "//table//div[.//a[contains(@href, 'profile.php')]]",
                "//div[.//a[contains(@href, 'profile.php?id=')]]"
            ]
        
        # Apply selectors (from working code)
        for i, selector in enumerate(selectors):
            try:
                # Add timeout handling for element finding with retry mechanism
                elements = []
                retry_count = 0
                max_retries = 2
                
                while retry_count < max_retries:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        break  # Success, exit retry loop
                    except Exception as retry_e:
                        retry_count += 1
                        print(f"⚠️ Selector {i+1} retry {retry_count}/{max_retries}: {retry_e}")
                        
                        # Check if it's a timeout error
                        if "HTTPConnectionPool" in str(retry_e) or "timeout" in str(retry_e).lower():
                            self.timeout_count += 1
                            print(f"⚠️ Timeout count: {self.timeout_count}/{self.max_timeouts}")
                            
                            # Restart browser if too many timeouts
                            if self.timeout_count >= self.max_timeouts:
                                # Extract current comments before restart to preserve data
                                print("🚨 CRITICAL: Extracting comments before browser restart to preserve data...")
                                try:
                                    current_extracted_comments = self.extract_comments_ultra_fast()
                                    print(f"💾 Extracted {len(current_extracted_comments)} comments before restart")
                                except Exception as extract_e:
                                    print(f"⚠️ Could not extract comments before restart: {extract_e}")
                                    current_extracted_comments = self.current_comments_data if hasattr(self, 'current_comments_data') else []
                                
                                # Save current extraction progress with actual data
                                self._save_scroll_progress(0, current_extracted_comments)
                                
                                if self._restart_browser_on_timeout():
                                    print("🔄 Browser restarted, continuing extraction...")
                                    # Restore progress if possible
                                    if self._restore_scroll_progress():
                                        print("✅ Extraction progress preserved")
                                    time.sleep(3)
                                else:
                                    print("❌ Browser restart failed")
                                    break
                        
                        if retry_count < max_retries:
                            time.sleep(2)  # Wait before retry
                        continue
                
                print(f"📊 Selector {i+1}: Found {len(elements)} elements")
                
                for elem in elements:
                    if elem not in all_comment_elements:
                        all_comment_elements.append(elem)
                        
            except Exception as e:
                print(f"📊 Selector {i+1} failed: {e}")
                continue
        
        # Fallback selectors (from working code)
        if len(all_comment_elements) == 0:
            print("⚠️ No comments with standard selectors, trying fallback...")
            
            fallback_selectors = [
                "//div[.//a[contains(@href, 'facebook.com/')] and string-length(normalize-space(text())) > 20]",
                "//div[string-length(normalize-space(text())) > 30]",
                "//div[@role='article' and string-length(normalize-space(text())) > 20]",
                "//*[.//a[contains(@href, 'profile')] and string-length(normalize-space(text())) > 15]"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    print(f"📊 Fallback selector: Found {len(elements)} elements")
                    for elem in elements:
                        if elem not in all_comment_elements:
                            all_comment_elements.append(elem)
                    
                    if len(all_comment_elements) > 20:
                        break
                except:
                    continue
        
        # Remove duplicates quickly
        all_comment_elements = list(set(all_comment_elements))
        
        # Sort by position (from working code)
        try:
            all_comment_elements.sort(key=lambda x: (x.location['y'], x.location['x']))
        except:
            pass
        
        # Set total for progress tracking
        self.total_estimated = len(all_comment_elements)
        print(f"📊 Found {self.total_estimated} potential comments")
        
        # Ultra fast processing with debug
        comments = []
        seen_content = set()
        rejected_count = 0
        
        print(f"🔍 Processing {len(all_comment_elements)} elements...")
        
        for i, element in enumerate(all_comment_elements):
            if self._stop_flag:
                break
                
            # Check limit
            if self.comment_limit > 0 and len(comments) >= self.comment_limit:
                break
                
            try:
                # Debug first 10 elements
                if i < 10:
                    element_text = element.text.strip()[:100] if element.text else "No text"
                    print(f"🔍 Element {i}: '{element_text}...'")
                
                comment_data = self._extract_comment_ultra_fast(element, i)
                
                if not comment_data:
                    # Only reject if element has no text at all (very short)
                    element_text = element.text.strip() if element.text else ""
                    if len(element_text) < 5:  # Use same threshold as focused code
                        rejected_count += 1
                        if i < 10:
                            print(f"  ❌ Rejected element {i}: Too short '{element_text}...'")
                        continue
                    else:
                        # Create comment data with extracted name even if main extraction failed
                        # Try to extract name from element even if main extraction failed
                        extracted_name = "Unknown"
                        try:
                            # Try to find first link that might be a name
                            links = element.find_elements(By.XPATH, ".//a")
                            for link in links[:3]:  # Check first 3 links
                                link_text = link.text.strip()
                                link_href = link.get_attribute("href") or ""
                                
                                # Check if this looks like a profile link
                                if ('facebook.com' in link_href and 
                                    ('profile.php' in link_href or '/user/' in link_href or 'user.php' in link_href or
                                     re.search(r'facebook\.com/[^/?&]+/?$', link_href))):
                                    
                                    # Check if link text looks like a name
                                    if (link_text and len(link_text) >= 2 and len(link_text) <= 100 and
                                        not link_text.isdigit() and not link_text.startswith('http') and
                                        not any(ui in link_text.lower() for ui in [
                                            'like', 'reply', 'share', 'comment', 'thích', 'trả lời', 
                                            'chia sẻ', 'bình luận', 'ago', 'trước', 'min', 'hour', 
                                            'day', 'phút', 'giờ', 'ngày', 'view', 'xem', 'show'
                                        ])):
                                        extracted_name = link_text
                                        break
                            
                            # Fallback: try to get first line of text as name
                            if extracted_name == "Unknown":
                                lines = element_text.splitlines()
                                if lines:
                                    first_line = lines[0].strip()
                                    if (first_line and 2 <= len(first_line) <= 100 and 
                                        not first_line.startswith("http") and
                                        not any(keyword in first_line.lower() for keyword in ['anonymous', 'ẩn danh'])):
                                        extracted_name = first_line
                        except:
                            pass
                        
                        # Tìm comment link cho fallback data
                        fallback_comment_link = ""
                        try:
                            # Tìm tất cả link trong element để lấy comment link
                            fallback_links = element.find_elements(By.XPATH, ".//a")
                            print(f"    Fallback: Found {len(fallback_links)} links in element")
                            
                            for fallback_link in fallback_links:
                                try:
                                    fallback_link_text = fallback_link.text.strip()
                                    fallback_link_href = fallback_link.get_attribute("href") or ""
                                    
                                    # Tìm link có comment_id
                                    if ('facebook.com' in fallback_link_href and 
                                        'comment_id=' in fallback_link_href and 
                                        '/groups/' in fallback_link_href and 
                                        '/posts/' in fallback_link_href):
                                        
                                        # Kiểm tra text của link có phải là thời gian không
                                        time_patterns = [
                                            r'\d+\s*(phút|giờ|ngày|tuần|tháng|năm|trước)',  # Vietnamese time
                                            r'\d+\s*(min|hour|day|week|month|year|ago)',     # English time
                                            r'\d+[hmsdwy]',                                 # Short format: 1h, 2d, 3m, etc.
                                            r'(vừa xong|just now|bây giờ|now)'              # "Just now" patterns
                                        ]
                                        
                                        is_time_link = any(re.search(pattern, fallback_link_text.lower()) for pattern in time_patterns)
                                        
                                        # Nếu text ngắn cũng coi là time link
                                        if not is_time_link and fallback_link_text and len(fallback_link_text) <= 20:
                                            time_indicators = ['ago', 'trước', 'giờ', 'ngày', 'phút', 'h', 'm', 'd', 'w', 'y']
                                            is_time_link = any(indicator in fallback_link_text.lower() for indicator in time_indicators)
                                        
                                        # LẤY LINK CHO FALLBACK DATA
                                        if is_time_link:
                                            fallback_comment_link = fallback_link_href.replace('&amp;', '&')
                                            print(f"      🔗 Fallback: Found TIME comment link: '{fallback_link_text}' -> {fallback_comment_link[:80]}...")
                                            break
                                        elif not fallback_comment_link:  # Nếu chưa có link nào, lấy link này
                                            fallback_comment_link = fallback_link_href.replace('&amp;', '&')
                                            print(f"      🔗 Fallback: Found ANY comment link: '{fallback_link_text}' -> {fallback_comment_link[:80]}...")
                                            
                                except Exception as e:
                                    print(f"      Error processing fallback link: {e}")
                                    continue
                                    
                        except Exception as e:
                            print(f"    Error finding fallback comment link: {e}")
                        
                        # Create comment data with extracted name and comment link
                        comment_data = {
                            "UID": "Unknown",
                            "Name": extracted_name,
                            "ProfileLink": "",
                            "CommentLink": fallback_comment_link,  # Thêm comment link cho fallback
                            "ElementIndex": i,
                            "TextPreview": element_text[:100] + "..." if len(element_text) > 100 else element_text,
                            "ContainerHeight": "Ultra Fast - Name Extracted + Time Click Links"
                        }
                
                # MINIMAL DEDUPLICATION - Only skip exact duplicates
                # Use text content for deduplication instead of user info
                text_signature = comment_data['TextPreview'][:50]  # First 50 chars of text
                
                if text_signature in seen_content:
                    if i < 10:
                        print(f"  🔄 Duplicate text element {i}: '{text_signature}...'")
                    continue
                seen_content.add(text_signature)
                
                comment_data['Type'] = 'Comment'
                comment_data['Layout'] = self.current_layout
                comment_data['Source'] = 'Ultra Fast'
                
                comments.append(comment_data)
                self.extracted_count = len(comments)
                self.current_comments_data = comments  # Store for save on stop
                
                # Enhanced progress saving every 50 comments during extraction
                if len(comments) % 50 == 0:
                    print(f"💾 Auto-saving progress: {len(comments)} comments extracted")
                    # This ensures current_comments_data is always up to date
                
                if i < 10:  # Debug first 10 successful extractions
                    name_status = "✅" if comment_data['Name'] != "Unknown" else "⚠️"
                    print(f"  {name_status} Extracted element {i}: {comment_data['Name']} - '{comment_data['TextPreview'][:50]}...'")
                
                # Enhanced progress update for 8k comments - MORE FREQUENT UPDATES
                if self.progress_callback:
                    if len(comments) % 10 == 0 or len(comments) <= 50:  # Update every 10 comments or first 50
                        progress_text = f"Đã lấy {self.extracted_count} comments"
                        if self.comment_limit > 0:
                            progress_text += f" / {self.comment_limit}"
                        else:
                            progress_text += f" / {self.total_estimated} (Target: 3k)"
                        self.progress_callback(self.extracted_count, progress_text)
                
            except Exception as e:
                rejected_count += 1
                if i < 10:
                    print(f"  ⚠️ Exception element {i}: {e}")
                continue
        
        # Calculate name extraction statistics
        named_comments = len([c for c in comments if c['Name'] != "Unknown"])
        name_success_rate = (named_comments / len(comments) * 100) if comments else 0
        
        print(f"📊 Processing complete: {len(comments)} extracted, {rejected_count} rejected (only empty elements)")
        print(f"🎯 ACCEPT ALL + NAME EXTRACTION: Extracted {len(comments)}/{len(all_comment_elements)} elements ({len(comments)/len(all_comment_elements)*100:.1f}% success rate)")
        print(f"👤 Name extraction: {named_comments}/{len(comments)} comments with names ({name_success_rate:.1f}% name success rate)")
        
        # Final progress update
        if self.progress_callback:
            final_progress_text = f"Đã lấy {len(comments)} comments"
            if self.comment_limit > 0:
                final_progress_text += f" / {self.comment_limit}"
            else:
                final_progress_text += f" / {self.total_estimated}"
            self.progress_callback(len(comments), final_progress_text)
        
        print(f"⚡ ULTRA FAST EXTRACTION COMPLETE: {len(comments)} comments")
        return comments

    def _extract_comment_ultra_fast(self, element, index):
        """Ultra fast comment data extraction with time click links"""
        try:
            full_text = element.text.strip()
            if len(full_text) < 5:
                print(f"  ❌ Text too short: '{full_text}'")
                return None
            
            print(f"  Processing: '{full_text[:60]}...'")
            
            username = "Unknown"
            profile_href = ""
            uid = "Unknown"
            comment_link = ""  # Link khi click vào thời gian comment
            
            # Kiểm tra người dùng ẩn danh
            is_anonymous = any(keyword in full_text.lower() for keyword in [
                'ẩn danh', 
                'người tham gia ẩn danh', 
                'anonymous participant',
                'anonymous user',
                'anonymous member'
            ])
            
            if is_anonymous:
                print(f"      🔍 Detected anonymous user, setting name to 'Unknown'")
                username = "Unknown"
                uid = "Anonymous"
            
            # Tìm tất cả các link trong comment để lấy link thời gian - CHO TẤT CẢ NGƯỜI DÙNG
            try:
                all_links = element.find_elements(By.XPATH, ".//a")
                print(f"    Found {len(all_links)} links in comment")
                
                # BƯỚC 1: Tìm comment link TRƯỚC (cho tất cả người dùng) - TÌM KIẾM MẠNH MẼ
                for link_index, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip()
                        link_href = link.get_attribute("href") or ""
                        
                        print(f"      Link {link_index+1}: Text='{link_text}' | Href={link_href[:60]}...")
                        
                        # TÌM KIẾM MẠNH MẼ: BẤT KỲ link nào có comment_id và thuộc Facebook Groups
                        if ('facebook.com' in link_href and 
                            'comment_id=' in link_href and 
                            '/groups/' in link_href and 
                            '/posts/' in link_href):
                            
                            # Kiểm tra text của link có phải là thời gian không
                            time_patterns = [
                                r'\d+\s*(phút|giờ|ngày|tuần|tháng|năm|trước)',  # Vietnamese time
                                r'\d+\s*(min|hour|day|week|month|year|ago)',     # English time
                                r'\d+[hmsdwy]',                                 # Short format: 1h, 2d, 3m, etc.
                                r'(vừa xong|just now|bây giờ|now)'              # "Just now" patterns
                            ]
                            
                            is_time_link = any(re.search(pattern, link_text.lower()) for pattern in time_patterns)
                            
                            # Nếu text ngắn cũng coi là time link
                            if not is_time_link and link_text and len(link_text) <= 20:
                                time_indicators = ['ago', 'trước', 'giờ', 'ngày', 'phút', 'h', 'm', 'd', 'w', 'y']
                                is_time_link = any(indicator in link_text.lower() for indicator in time_indicators)
                            
                            # LẤY LINK CHO TẤT CẢ NGƯỜI DÙNG - ƯU TIÊN TIME LINK NHƯNG LẤY BẤT KỲ LINK NÀO
                            if is_time_link:
                                # Clean the URL
                                comment_link = link_href.replace('&amp;', '&')
                                print(f"      🔗 Found TIME comment link for ALL users: '{link_text}' -> {comment_link[:80]}...")
                                break  # Ưu tiên time link, break ngay
                            elif not comment_link:  # Nếu chưa có link nào, lấy link này
                                # Clean the URL
                                comment_link = link_href.replace('&amp;', '&')
                                print(f"      🔗 Found ANY comment link for ALL users: '{link_text}' -> {comment_link[:80]}...")
                                # KHÔNG break để có thể tìm time link tốt hơn
                                
                    except Exception as e:
                        print(f"      Error processing link {link_index+1}: {e}")
                        continue
                
                # BƯỚC 2: Tìm profile link (chỉ cho người dùng không ẩn danh)
                if not is_anonymous:
                    for link_index, link in enumerate(all_links):
                        try:
                            link_text = link.text.strip()
                            link_href = link.get_attribute("href") or ""
                            
                            # Kiểm tra profile link
                            if (link_href and 
                                  (('facebook.com' in link_href and 
                                    ('profile.php' in link_href or '/user/' in link_href or 'user.php' in link_href or
                                     re.search(r'facebook\.com/[^/?&]+/?$', link_href))) or
                                    (link_href.startswith('/groups/') and '/user/' in link_href) or
                                    ('/user/' in link_href and link_href != ''))):
                                
                                # Kiểm tra tên hợp lệ
                                is_valid_name = (link_text and 
                                    len(link_text) >= 2 and 
                                    len(link_text) <= 100 and
                                    not link_text.isdigit() and
                                    not link_text.startswith('http') and
                                    not any(ui in link_text.lower() for ui in [
                                        'like', 'reply', 'share', 'comment', 'thích', 'trả lời', 
                                        'chia sẻ', 'bình luận', 'ago', 'trước', 'min', 'hour', 
                                        'day', 'phút', 'giờ', 'ngày', 'ẩn danh', 'anonymous',
                                        'view', 'xem', 'show', 'hiển thị', 'see more', 'view more'
                                    ]))
                                
                                if is_valid_name:
                                    # Trích xuất UID từ link
                                    extracted_uid = "Unknown"
                                    uid_patterns = [
                                        r'/groups/\d+/user/(\d+)/',
                                        r'/groups/\d+/user/(\d+)\?',
                                        r'/groups/\d+/user/(\d+)$',
                                        r'/groups/[^/]+/user/(\d+)/',
                                        r'/groups/[^/]+/user/(\d+)\?',
                                        r'/groups/[^/]+/user/(\d+)$',
                                        r'/user/(\d+)/',
                                        r'/user/(\d+)\?',
                                        r'/user/(\d+)$',
                                        r'profile\.php\?id=(\d+)',
                                        r'user\.php\?id=(\d+)',
                                        r'[?&]id=(\d+)',
                                        r'facebook\.com/([^/?&]+)/?$',
                                        r'(\d{10,})'
                                    ]
                                    
                                    for pattern in uid_patterns:
                                        try:
                                            uid_match = re.search(pattern, link_href)
                                            if uid_match:
                                                potential_uid = uid_match.group(1)
                                                if potential_uid.isdigit() and len(potential_uid) >= 8:
                                                    extracted_uid = potential_uid
                                                    break
                                                elif not potential_uid.isdigit() and len(potential_uid) >= 3:
                                                    extracted_uid = f"username:{potential_uid}"
                                                    break
                                        except:
                                            continue
                                    
                                    # Cập nhật thông tin user nếu có UID
                                    if extracted_uid != "Unknown":
                                        username = link_text
                                        uid = extracted_uid
                                        
                                        if link_href.startswith('/'):
                                            profile_href = f"https://www.facebook.com{link_href}"
                                        else:
                                            profile_href = link_href
                                        
                                        print(f"      ✅ Updated profile: {username} -> UID: {uid}")
                                        break  # Đã tìm thấy profile, break
                                        
                        except Exception as e:
                            print(f"      Error processing profile link {link_index+1}: {e}")
                            continue
                        
            except Exception as e:
                print(f"    Error finding links: {e}")
            
            # FALLBACK: Nếu chưa có comment link, tìm BẤT KỲ link nào có comment_id
            if not comment_link:
                print(f"    ⚠️ No comment link found, trying AGGRESSIVE fallback method...")
                try:
                    # Phương pháp 1: Tìm tất cả link có comment_id trong toàn bộ element
                    fallback_links = element.find_elements(By.XPATH, ".//a[contains(@href, 'comment_id=')]")
                    print(f"    Found {len(fallback_links)} fallback links with comment_id")
                    
                    for fallback_link in fallback_links:
                        try:
                            fallback_href = fallback_link.get_attribute("href") or ""
                            if ('facebook.com' in fallback_href and 
                                'comment_id=' in fallback_href and 
                                '/groups/' in fallback_href and 
                                '/posts/' in fallback_href):
                                comment_link = fallback_href.replace('&amp;', '&')
                                print(f"    🔗 Fallback Method 1: Found comment link -> {comment_link[:80]}...")
                                break
                        except:
                            continue
                    
                    # Phương pháp 2: Nếu vẫn chưa có, tìm trong toàn bộ trang
                    if not comment_link:
                        print(f"    ⚠️ Still no comment link, trying page-wide search...")
                        page_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'comment_id=')]")
                        print(f"    Found {len(page_links)} page-wide links with comment_id")
                        
                        for page_link in page_links[:10]:  # Chỉ kiểm tra 10 link đầu
                            try:
                                page_href = page_link.get_attribute("href") or ""
                                if ('facebook.com' in page_href and 
                                    'comment_id=' in page_href and 
                                    '/groups/' in page_href and 
                                    '/posts/' in page_href):
                                    comment_link = page_href.replace('&amp;', '&')
                                    print(f"    🔗 Fallback Method 2: Found comment link -> {comment_link[:80]}...")
                                    break
                            except:
                                continue
                                
                except Exception as e:
                    print(f"    Error in fallback method: {e}")
            
            # Fallback cho username nếu chưa có
            if username == "Unknown" and not is_anonymous:
                try:
                    children = element.find_elements(By.XPATH, "./*")
                    if children:
                        first_child_text = (children[0].text or "").strip()
                        if first_child_text:
                            first_line = first_child_text.splitlines()[0].strip()
                            if (first_line and 2 <= len(first_line) <= 120 and 
                                not first_line.startswith("http") and
                                not any(keyword in first_line.lower() for keyword in ['anonymous', 'ẩn danh'])):
                                username = first_line
                                print(f"      ✅ Fallback name: {username}")
                except Exception as e:
                    print(f"      ⚠️ Fallback name extraction error: {e}")

            # Kiểm tra cuối cùng - cho phép anonymous users
            if username == "Unknown" and not is_anonymous:
                print("  ❌ Extraction failed for this element (not anonymous, no username found)")
                return None
            elif is_anonymous:
                print("  ✅ Keeping anonymous user with name 'Unknown'")
                
            print(f"  ✅ Successfully extracted username: {username}")
            if comment_link:
                print(f"  🔗 TIME CLICK COMMENT LINK found for ALL users: {comment_link[:80]}...")
            else:
                print(f"  ❌ CRITICAL ERROR: No comment link found for user: {username}")
                print(f"  ⚠️ This should NEVER happen - all users MUST have comment links!")
                print(f"  🔍 Debug info: Element text preview: {full_text[:100]}...")
            
            return {
                "UID": uid,
                "Name": username,
                "ProfileLink": profile_href,
                "CommentLink": comment_link,  # Link khi click vào thời gian comment
                "ElementIndex": index,
                "TextPreview": full_text[:100] + "..." if len(full_text) > 100 else full_text,
                "ContainerHeight": "Ultra Fast - Time Click Links"
            }
            
        except Exception as e:
            print(f"Error in ultra fast extraction: {e}")
            return None

    def scrape_all_comments_ultra_fast(self, limit=0, resolve_uid=True, progress_callback=None):
        """Ultra fast main scraping orchestrator"""
        print(f"⚡ ULTRA FAST SCRAPING STARTING")
        
        if self._stop_flag:
            return []
        
        # Setup
        self.comment_limit = limit
        self.progress_callback = progress_callback
        self.extracted_count = 0
        
        # Extract comments ultra fast
        comments = self.extract_comments_ultra_fast()
        
        # Apply limit
        if limit > 0 and len(comments) > limit:
            comments = comments[:limit]
        
        # Final progress
        if progress_callback:
            final_text = f"Hoàn thành: {len(comments)} comments"
            if limit > 0:
                final_text += f" / {limit}"
            progress_callback(len(comments), final_text)
        
        print(f"⚡ ULTRA FAST SCRAPING COMPLETE: {len(comments)} comments")
        return comments

    def close(self):
        try: 
            self.driver.quit()
        except: 
            pass

# ----------------------------
# Ultra Fast GUI
# ----------------------------

class UltraFastFBGroupsAppGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        self.initialize_variables()
        
    def setup_window(self):
        """Setup ultra fast window"""
        self.root.title("⚡ Facebook Groups Ultra Fast Scraper - ULTRA PERFORMANCE + SAVE ON STOP")
        self.root.geometry("1000x800")
        self.root.configure(bg="#0a0a0a")
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1000x800+{x}+{y}")
        
    def create_widgets(self):
        """Create ultra fast widgets - SINGLE URL MODE"""
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#0a0a0a")
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, text="⚡ Facebook Groups Ultra Fast Scraper", 
                              font=("Arial", 18, "bold"), bg="#0a0a0a", fg="#00ff00")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="🚀 TIME CLICK COMMENT LINKS + CONTINUE FROM COMMENT: Paste comment link để chạy tiếp từ comment cụ thể!", 
                                 font=("Arial", 10), bg="#0a0a0a", fg="#888888")
        subtitle_label.pack(pady=(5,0))
        
        # Input section - SINGLE URL
        input_frame = tk.LabelFrame(main_frame, text="📝 Thông tin", font=("Arial", 12, "bold"), 
                                   bg="#0a0a0a", fg="#00ff00", relief="groove", bd=2)
        input_frame.pack(fill="x", pady=(0,15))
        
        tk.Label(input_frame, text="🔗 Link bài viết Groups:", bg="#0a0a0a", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15,5))
        self.entry_url = tk.Entry(input_frame, width=80, font=("Arial", 9))
        self.entry_url.pack(fill="x", padx=15, pady=(0,10))
        
        tk.Label(input_frame, text="🍪 Cookie Facebook:", bg="#0a0a0a", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5,5))
        self.txt_cookie = tk.Text(input_frame, height=4, font=("Arial", 9))
        self.txt_cookie.pack(fill="x", padx=15, pady=(0,10))
        
        tk.Label(input_frame, text="🔢 Giới hạn comments (0 = không giới hạn):", bg="#0a0a0a", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5,5))
        self.entry_limit = tk.Entry(input_frame, font=("Arial", 9))
        self.entry_limit.insert(0, "0")
        self.entry_limit.pack(fill="x", padx=15, pady=(0,10))
        
        # Comment Link section
        tk.Label(input_frame, text="🔗 Comment Link (tùy chọn - để chạy tiếp từ comment cụ thể):", bg="#0a0a0a", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5,5))
        self.entry_comment_link = tk.Entry(input_frame, width=80, font=("Arial", 9))
        self.entry_comment_link.pack(fill="x", padx=15, pady=(0,10))
        tk.Label(input_frame, text="💡 Tip: Paste comment link từ Excel để chạy tiếp từ comment đó", bg="#0a0a0a", font=("Arial", 8), fg="#888888").pack(anchor="w", padx=15, pady=(0,5))
        
        # File output section with choose button
        file_frame = tk.Frame(input_frame, bg="#0a0a0a")
        file_frame.pack(fill="x", padx=15, pady=(5,10))
        
        tk.Label(file_frame, text="💾 File output:", bg="#0a0a0a", font=("Arial", 10)).pack(anchor="w")
        
        file_input_frame = tk.Frame(file_frame, bg="#0a0a0a")
        file_input_frame.pack(fill="x", pady=(5,0))
        
        self.entry_file = tk.Entry(file_input_frame, font=("Arial", 9))
        self.entry_file.insert(0, "ultra_fast_comments.xlsx")
        self.entry_file.pack(side="left", fill="x", expand=True)
        
        self.btn_choose_file = tk.Button(file_input_frame, text="📁 Chọn", command=self.choose_file, 
                                        bg="#17a2b8", fg="white", font=("Arial", 9), bd=0, padx=10, pady=2)
        self.btn_choose_file.pack(side="right", padx=(10,0))
        
        # Checkboxes
        checkbox_frame = tk.Frame(input_frame, bg="#0a0a0a")
        checkbox_frame.pack(fill="x", padx=15, pady=(10,0))
        
        self.headless_var = tk.BooleanVar(value=True)
        self.headless_check = tk.Checkbutton(checkbox_frame, text="Headless Browser", variable=self.headless_var, 
                                            bg="#0a0a0a", fg="#ffffff", selectcolor="#0a0a0a", 
                                            activebackground="#0a0a0a", activeforeground="#ffffff")
        self.headless_check.pack(side="left", padx=(0,20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#0a0a0a")
        button_frame.pack(fill="x", pady=(10,0))
        
        self.btn_start = tk.Button(button_frame, text="⚡ Bắt đầu Ultra Fast", command=self.start_scrape_thread, 
                                  bg="#0066cc", fg="white", font=("Arial", 10, "bold"), bd=0, padx=20, pady=5)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = tk.Button(button_frame, text="⏹ Dừng và Lưu", command=self.stop_scrape, 
                                 bg="#cc0000", fg="white", font=("Arial", 10, "bold"), bd=0, padx=20, pady=5, state=tk.DISABLED)
        self.btn_stop.pack(side="left", padx=5)
        
        # Status
        status_frame = tk.LabelFrame(main_frame, text="📊 Trạng thái", font=("Arial", 12, "bold"), 
                                    bg="#0a0a0a", fg="#00ff00", relief="groove", bd=2)
        status_frame.pack(fill="both", expand=True, pady=(10,0))
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(15,10))
        
        self.lbl_status = tk.Label(status_frame, text="⚡ Ultra Fast Scraper sẵn sàng - CONTINUE FROM COMMENT!", fg="#00ff00", 
                                  wraplength=800, justify="left", font=("Arial", 11), bg="#0a0a0a")
        self.lbl_status.pack(anchor="w", padx=15, pady=(15,5))
        
        self.lbl_progress_detail = tk.Label(status_frame, text="🚀 CONTINUE FROM COMMENT: Paste comment link để chạy tiếp từ comment cụ thể. Features: Comment link detection, Auto-scroll to comment, Time-based comment links, All Comments view, Groups UID patterns",
                                          fg="#888888", wraplength=800, justify="left", font=("Arial", 9), bg="#0a0a0a")
        self.lbl_progress_detail.pack(anchor="w", padx=15, pady=(0,10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=15, pady=(0,15))
        
    def initialize_variables(self):
        """Initialize variables"""
        self._scrape_thread = None
        self._stop_flag = False
        self.scraper = None
        self.current_comments = []
        
    def choose_file(self):
        """Choose output file"""
        f = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
            title="Chọn file để lưu Ultra Fast comments"
        )
        if f:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, f)
    
    def start_scrape_thread(self):
        """Start ultra fast scraping"""
        url = self.entry_url.get().strip()
        cookie_str = self.txt_cookie.get("1.0", tk.END).strip()
        file_out = self.entry_file.get().strip() or "ultra_fast_comments.xlsx"
        comment_link = self.entry_comment_link.get().strip()
        
        if not url:
            messagebox.showerror("❌ Lỗi", "Vui lòng nhập link bài viết Groups.")
            return
        
        try: 
            limit = int(self.entry_limit.get().strip())
            if limit < 0:
                messagebox.showerror("❌ Lỗi", "Giới hạn comments phải là số không âm")
                return
            if limit > 100000:
                result = messagebox.askyesno("⚠️ Cảnh báo", 
                    f"Giới hạn {limit} comments rất lớn và có thể mất nhiều thời gian.\n"
                    f"Bạn có chắc chắn muốn tiếp tục không?")
                if not result:
                    return
        except ValueError:
            messagebox.showerror("❌ Lỗi", "Giới hạn comments không hợp lệ")
            return
        
        self._stop_flag = False
        self.progress_var.set(0)
        self.progress_bar.start()
        self.lbl_status.config(text="⚡ Đang khởi động Ultra Fast Scraper...", fg="#00ff00")
        self.lbl_progress_detail.config(text="🚀 Initializing ultra fast extraction...")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        self._scrape_thread = threading.Thread(target=self._scrape_worker, 
                                             args=(url, cookie_str, file_out, limit, 
                                                   self.headless_var.get(), comment_link))
        self._scrape_thread.daemon = True
        self._scrape_thread.start()
    
    def stop_scrape(self):
        """Stop scraping and save data"""
        self._stop_flag = True
        if self.scraper:
            self.scraper._stop_flag = True
        
        self.lbl_status.config(text="⏹️ Đang dừng và lưu dữ liệu...", fg="#ff0000")
        self.lbl_progress_detail.config(text="💾 Saving current data...")
        self.btn_stop.config(state=tk.DISABLED)
        
        # Save current data - ENHANCED with multiple fallback methods
        try:
            # Method 1: Try to get data from scraper's current_comments_data
            current_data = []
            if hasattr(self, 'scraper') and self.scraper and hasattr(self.scraper, 'current_comments_data'):
                current_data = self.scraper.current_comments_data
                print(f"💾 Found {len(current_data)} comments from scraper.current_comments_data")
            
            # Method 2: Fallback to GUI's current_comments
            if not current_data and hasattr(self, 'current_comments') and self.current_comments:
                current_data = self.current_comments
                print(f"💾 Found {len(current_data)} comments from GUI current_comments")
            
            # Method 3: Try to get from progress callback data
            if not current_data and hasattr(self, '_last_progress_data'):
                current_data = self._last_progress_data
                print(f"💾 Found {len(current_data)} comments from last progress data")
            
            if current_data:
                file_out = self.entry_file.get().strip()
                if not file_out:
                    file_out = f"ultra_fast_stopped_{datetime.now().strftime('%d_%m_%Y_%H_%M')}.xlsx"
                
                success = save_to_excel_fast(current_data, file_out)
                if success:
                    self.lbl_status.config(text=f"✅ Đã dừng và lưu {len(current_data)} comments", fg="#00ff00")
                    self.lbl_progress_detail.config(text=f"💾 Dữ liệu đã lưu vào: {file_out}")
                    
                    messagebox.showinfo("Đã dừng và lưu", 
                        f"Ultra Fast Scraping đã được dừng!\n\n"
                        f"📊 Đã lưu: {len(current_data)} comments\n"
                        f"💾 File: {file_out}")
                else:
                    self.lbl_status.config(text="⚠️ Đã dừng nhưng không thể lưu", fg="#ffaa00")
            else:
                self.lbl_status.config(text="⚠️ Đã dừng nhưng không có dữ liệu để lưu", fg="#ffaa00")
                print("⚠️ No data found to save when stopping")
        except Exception as e:
            self.lbl_status.config(text=f"❌ Lỗi khi lưu: {str(e)[:50]}...", fg="#ff0000")
            print(f"❌ Error saving data when stopping: {e}")
        else:
            self.lbl_status.config(text="⏹️ Đã dừng (chưa có dữ liệu)", fg="#ffaa00")
    
    def _progress_callback(self, count, detail=""):
        """Enhanced progress callback with detailed tracking and data saving"""
        self.progress_var.set(count)
        
        if detail:
            self.lbl_status.config(text=f"⚡ {detail}", fg="#00ff00")
        else:
            self.lbl_status.config(text=f"⚡ Ultra Fast: {count} comments", fg="#00ff00")
        
        # Store current data for save on stop
        if hasattr(self, 'scraper') and self.scraper and hasattr(self.scraper, 'current_comments_data'):
            self.current_comments = self.scraper.current_comments_data
            self._last_progress_data = self.scraper.current_comments_data
            print(f"💾 Progress callback: Stored {len(self.scraper.current_comments_data)} comments for save on stop")
        
        # Enhanced progress detail
        if detail:
            self.lbl_progress_detail.config(text=f"🚀 Ultra fast extraction in progress...")
        else:
            self.lbl_progress_detail.config(text=f"📊 Đang trích xuất dữ liệu từ Facebook Groups...")
    
    def _scrape_worker(self, url, cookie_str, file_out, limit, headless, comment_link):
        """Ultra fast worker thread"""
        scraper = None
        try:
            self.root.after(0, lambda: self.lbl_status.config(text="⚡ Khởi tạo Ultra Fast Browser...", fg="#00ff00"))
            self.root.after(0, lambda: self.lbl_progress_detail.config(text="🚀 Setting up ultra optimized Chrome..."))
            
            # Initialize ultra fast scraper
            scraper = UltraFastFacebookGroupsScraper(cookie_str, headless=headless)
            self.scraper = scraper
            
            # Check if comment link is provided
            if comment_link:
                self.root.after(0, lambda: self.lbl_progress_detail.config(text=f"🔗 Loading from comment link: {comment_link[:50]}..."))
                
                # Load from comment link first
                if not scraper.load_post_ultra_fast(comment_link):
                    self.root.after(0, lambda: self.lbl_progress_detail.config(text="⚠️ Comment link failed, trying main post URL..."))
                    # Fallback to main post URL
                    if not scraper.load_post_ultra_fast(url):
                        raise Exception("Không thể tải bài viết từ cả comment link và main URL")
                else:
                    self.root.after(0, lambda: self.lbl_progress_detail.config(text="✅ Loaded from comment link successfully"))
            else:
                self.root.after(0, lambda: self.lbl_progress_detail.config(text="⚡ Loading post ultra fast..."))
                
                # Load post ultra fast
                if not scraper.load_post_ultra_fast(url):
                    raise Exception("Không thể tải bài viết")
            
            self.root.after(0, lambda: self.lbl_progress_detail.config(text="🚀 Ultra fast comment extraction..."))
            
            # Define enhanced progress callback
            def progress_callback(count, detail=""):
                # Store current comments for save on stop
                if hasattr(scraper, 'current_comments_data'):
                    self.current_comments = scraper.current_comments_data
                else:
                    self.current_comments = []
                self.root.after(0, self._progress_callback, count, detail)
            
            # Extract comments ultra fast
            comments_data = scraper.scrape_all_comments_ultra_fast(
                limit=limit, 
                resolve_uid=True, 
                progress_callback=progress_callback
            )
            
            # Store final comments for potential save on stop
            self.current_comments = comments_data
            
            if self._stop_flag:
                self.root.after(0, lambda: self.lbl_status.config(text="⏹️ Đã dừng theo yêu cầu", fg="#ffaa00"))
                return
            
            if not comments_data:
                raise Exception("Không tìm thấy comments")
            
            # Ultra fast save
            self.root.after(0, lambda: self.lbl_progress_detail.config(text="⚡ Ultra fast saving..."))
            
            success = save_to_excel_fast(comments_data, file_out)
            
            if not success:
                raise Exception("Không thể lưu file")
            
            # Success
            self.root.after(0, lambda: self.lbl_status.config(text="🎉 ULTRA FAST HOÀN THÀNH!", fg="#00ff00"))
            self.root.after(0, lambda: self.lbl_progress_detail.config(text=f"⚡ {len(comments_data)} comments saved ultra fast!"))
            
            # Show success
            def show_success():
                messagebox.showinfo("Ultra Fast Success", 
                    f"Ultra Fast Scraping hoàn thành!\n\n"
                    f"⚡ Extracted: {len(comments_data)} comments\n"
                    f"💾 Saved to: {file_out}\n"
                    f"🚀 Ultra fast mode enabled!")
            
            self.root.after(0, show_success)
            
        except Exception as e:
            error_msg = f"❌ Ultra Fast Error: {str(e)}"
            error_detail = str(e)  # Capture error detail
            self.root.after(0, lambda: self.lbl_status.config(text=error_msg, fg="#ff0000"))
            self.root.after(0, lambda: self.lbl_progress_detail.config(text="Check inputs and try again"))
            
            def show_error():
                messagebox.showerror("Ultra Fast Error", f"Scraping failed:\n{error_detail}")
            
            self.root.after(0, show_error)
            
        finally:
            # Cleanup
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
            
            # Reset UI
            self.root.after(0, self._reset_ui_after_scraping)
    
    def _reset_ui_after_scraping(self):
        """Reset UI after scraping"""
        self.progress_bar.stop()
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self._scrape_thread = None
        self.scraper = None

# ----------------------------
# Run Ultra Fast App
# ----------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = UltraFastFBGroupsAppGUI(root)
    root.mainloop()
