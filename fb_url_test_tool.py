# fb_url_test_tool.py - Tool để test Facebook URL parsing và PostLink generation

import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from urllib.parse import urlparse, parse_qs
import pandas as pd
from datetime import datetime

def parse_fb_url(url: str):
    """
    Phân tích URL Facebook thành group/page slug, post_id, comment_id
    Trả về dict chứa các giá trị cần thiết
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    query = parse_qs(parsed.query)

    group = None
    post_id = None
    comment_id = None

    # Ví dụ: /groups/chaohanhmienphi/posts/31258488570464523/
    if "groups" in path_parts:
        idx = path_parts.index("groups")
        if len(path_parts) > idx + 1:
            group = path_parts[idx + 1]

        if "posts" in path_parts:
            idx_post = path_parts.index("posts")
            if len(path_parts) > idx_post + 1:
                post_id = path_parts[idx_post + 1]

    # Trường hợp post trong profile/page: /username/posts/123456789/
    elif "posts" in path_parts:
        idx_post = path_parts.index("posts")
        if len(path_parts) > idx_post + 1:
            post_id = path_parts[idx_post + 1]

    # Trường hợp share link trực tiếp dạng /permalink/POST_ID/
    elif "permalink" in path_parts:
        idx_post = path_parts.index("permalink")
        if len(path_parts) > idx_post + 1:
            post_id = path_parts[idx_post + 1]

    # Lấy comment_id nếu có
    if "comment_id" in query:
        comment_id = query["comment_id"][0]

    return {
        "group": group,
        "post_id": post_id,
        "comment_id": comment_id
    }

def generate_post_link_with_comment(group_id, post_id, comment_id=None):
    """
    Tạo PostLink với comment_id như ví dụ của bạn
    """
    if not group_id or not post_id:
        return ""
    
    # Base post URL
    post_link = f"https://www.facebook.com/groups/{group_id}/posts/{post_id}/"
    
    # Add comment_id if available
    if comment_id:
        post_link += f"?comment_id={comment_id}"
    
    return post_link

class FBURLTestTool:
    def __init__(self, root):
        self.root = root
        root.title("🔗 Facebook URL Test Tool - PostLink Generator")
        root.geometry("1000x800")
        root.configure(bg="#f0f8ff")

        # Main frame
        main_frame = tk.Frame(root, bg="#f0f8ff")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Header
        header_label = tk.Label(main_frame, text="🔗 Facebook URL Test Tool", 
                              font=("Arial", 18, "bold"), bg="#f0f8ff", fg="#2d5a2d")
        header_label.pack(pady=(0,20))

        # Input section
        input_frame = tk.LabelFrame(main_frame, text="📝 Nhập URL Facebook để test", 
                                   font=("Arial", 12, "bold"), bg="#f0f8ff", fg="#2d5a2d")
        input_frame.pack(fill="x", pady=(0,15))

        tk.Label(input_frame, text="🔗 Facebook URL:", bg="#f0f8ff", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15,5))
        
        self.entry_url = tk.Entry(input_frame, width=100, font=("Arial", 9))
        self.entry_url.pack(fill="x", padx=15, pady=(0,10))
        
        # Set default example
        example_url = "https://www.facebook.com/groups/chaohanhmienphi/posts/31258488570464523/?comment_id=31294138870232826"
        self.entry_url.insert(0, example_url)

        # Buttons
        button_frame = tk.Frame(input_frame, bg="#f0f8ff")
        button_frame.pack(fill="x", padx=15, pady=(10,15))
        
        tk.Button(button_frame, text="🔍 Parse URL", command=self.parse_url, 
                 bg="#007bff", fg="white", font=("Arial", 10, "bold")).pack(side="left")
        
        tk.Button(button_frame, text="🧪 Test Multiple URLs", command=self.test_multiple_urls, 
                 bg="#28a745", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=(10,0))
        
        tk.Button(button_frame, text="💾 Export to Excel", command=self.export_to_excel, 
                 bg="#ffc107", fg="black", font=("Arial", 10, "bold")).pack(side="right")

        # Results section
        results_frame = tk.LabelFrame(main_frame, text="📊 Kết quả phân tích URL", 
                                     font=("Arial", 12, "bold"), bg="#f0f8ff", fg="#2d5a2d")
        results_frame.pack(fill="both", expand=True, pady=(0,15))

        self.results_text = scrolledtext.ScrolledText(results_frame, height=25, font=("Consolas", 9))
        self.results_text.pack(fill="both", expand=True, padx=15, pady=15)

        # Test data storage
        self.test_results = []

        # Show initial example
        self.parse_url()

    def parse_url(self):
        url = self.entry_url.get().strip()
        if not url:
            self.results_text.insert(tk.END, "❌ Vui lòng nhập URL!\n\n")
            return

        self.results_text.insert(tk.END, f"🔍 PARSING URL: {url}\n")
        self.results_text.insert(tk.END, "=" * 80 + "\n")

        try:
            # Parse URL
            parsed = parse_fb_url(url)
            
            self.results_text.insert(tk.END, f"📊 PARSED RESULTS:\n")
            self.results_text.insert(tk.END, f"   Group ID: {parsed['group']}\n")
            self.results_text.insert(tk.END, f"   Post ID: {parsed['post_id']}\n")
            self.results_text.insert(tk.END, f"   Comment ID: {parsed['comment_id']}\n\n")

            # Generate PostLink
            if parsed['group'] and parsed['post_id']:
                # Without comment_id
                post_link_basic = generate_post_link_with_comment(parsed['group'], parsed['post_id'])
                self.results_text.insert(tk.END, f"🔗 PostLink (Basic): {post_link_basic}\n")
                
                # With comment_id
                post_link_with_comment = generate_post_link_with_comment(parsed['group'], parsed['post_id'], parsed['comment_id'])
                self.results_text.insert(tk.END, f"🔗 PostLink (With Comment): {post_link_with_comment}\n")
                
                # Store result
                result = {
                    'Original_URL': url,
                    'Group_ID': parsed['group'],
                    'Post_ID': parsed['post_id'], 
                    'Comment_ID': parsed['comment_id'],
                    'PostLink_Basic': post_link_basic,
                    'PostLink_With_Comment': post_link_with_comment,
                    'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.test_results.append(result)
                
                self.results_text.insert(tk.END, f"\n✅ RESULT SAVED TO EXPORT LIST\n")
            else:
                self.results_text.insert(tk.END, f"❌ Không thể tạo PostLink - thiếu Group ID hoặc Post ID\n")

        except Exception as e:
            self.results_text.insert(tk.END, f"❌ Error: {e}\n")

        self.results_text.insert(tk.END, "\n" + "=" * 80 + "\n\n")
        self.results_text.see(tk.END)

    def test_multiple_urls(self):
        """Test với nhiều URL mẫu"""
        sample_urls = [
            "https://www.facebook.com/groups/chaohanhmienphi/posts/31258488570464523/?comment_id=31294138870232826",
            "https://www.facebook.com/groups/chaohanhmienphi/posts/31258488570464523/",
            "https://www.facebook.com/groups/testgroup/posts/123456789/?comment_id=987654321",
            "https://m.facebook.com/groups/mobilegroup/posts/555666777/",
            "https://mbasic.facebook.com/groups/basicgroup/posts/111222333/?comment_id=444555666"
        ]
        
        self.results_text.insert(tk.END, "🧪 TESTING MULTIPLE URLs:\n")
        self.results_text.insert(tk.END, "=" * 80 + "\n\n")
        
        for i, url in enumerate(sample_urls, 1):
            self.results_text.insert(tk.END, f"Test {i}: {url}\n")
            
            parsed = parse_fb_url(url)
            self.results_text.insert(tk.END, f"   Group: {parsed['group']}\n")
            self.results_text.insert(tk.END, f"   Post: {parsed['post_id']}\n") 
            self.results_text.insert(tk.END, f"   Comment: {parsed['comment_id']}\n")
            
            if parsed['group'] and parsed['post_id']:
                post_link = generate_post_link_with_comment(parsed['group'], parsed['post_id'], parsed['comment_id'])
                self.results_text.insert(tk.END, f"   ✅ PostLink: {post_link}\n")
                
                # Store result
                result = {
                    'Original_URL': url,
                    'Group_ID': parsed['group'],
                    'Post_ID': parsed['post_id'],
                    'Comment_ID': parsed['comment_id'],
                    'PostLink_Basic': generate_post_link_with_comment(parsed['group'], parsed['post_id']),
                    'PostLink_With_Comment': post_link,
                    'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.test_results.append(result)
            else:
                self.results_text.insert(tk.END, f"   ❌ Không thể tạo PostLink\n")
            
            self.results_text.insert(tk.END, "\n")
        
        self.results_text.insert(tk.END, f"📊 Total tested: {len(sample_urls)} URLs\n")
        self.results_text.insert(tk.END, f"📊 Total results stored: {len(self.test_results)} entries\n\n")
        self.results_text.see(tk.END)

    def export_to_excel(self):
        """Export test results to Excel"""
        if not self.test_results:
            self.results_text.insert(tk.END, "❌ Không có dữ liệu để export!\n\n")
            return
        
        try:
            # Create DataFrame
            df = pd.DataFrame(self.test_results)
            
            # Add index
            df.insert(0, 'STT', range(1, len(df) + 1))
            
            # Export to Excel
            filename = f"fb_url_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False, engine="openpyxl")
            
            self.results_text.insert(tk.END, f"💾 EXPORTED TO: {filename}\n")
            self.results_text.insert(tk.END, f"📊 Total entries: {len(df)} rows\n")
            self.results_text.insert(tk.END, f"📝 Columns: {', '.join(df.columns)}\n\n")
            
            print(f"✅ Exported {len(df)} test results to {filename}")
            
        except Exception as e:
            self.results_text.insert(tk.END, f"❌ Export error: {e}\n\n")
        
        self.results_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FBURLTestTool(root)
    root.mainloop()