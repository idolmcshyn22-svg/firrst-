# 🎯 Facebook Groups Scraper - Enhanced UID + Anonymous Filter

## 🚫 **Anonymous Filter Features**

### Tự động bỏ qua các loại người dùng ẩn danh:

#### **🇻🇳 Tiếng Việt:**
- `Ẩn danh`, `An danh`
- `Người dùng ẩn danh`
- `Thành viên ẩn danh`, `TV ẩn danh`
- `Người tham gia ẩn danh`

#### **🇺🇸 Tiếng Anh:**
- `Anonymous`, `Anon`
- `Anonymous user/member/participant`
- `Hidden user/member/participant` 
- `Private user/member/participant`
- `Facebook user`, `FB user`
- `Deleted user/account`
- `Deactivated user/account`

#### **🔢 Pattern nghi ngờ:**
- `User 123`, `Member 456`, `Participant 789`
- `Guest`, `Guest123`
- Chỉ là số: `12345678`
- Hash string dài: `a1b2c3d4e5f6g7h8`
- Username quá ngắn: `X`, `AB`
- Chỉ ký tự đặc biệt: `@#$%`, `***`
- Có nhiều số liên tiếp (6+ digits): `User123456789`

## 🚀 **Cách sử dụng:**

1. **Chạy ứng dụng:**
   ```bash
   python3 fb_groups_scraper_focused.py
   ```

2. **Nhập thông tin:**
   - Link bài viết Groups
   - Cookie Facebook
   - Tên file output

3. **Kết quả:**
   - ✅ Chỉ lấy real users
   - 🆔 Extract UID cho real users
   - 🚫 Tự động bỏ qua anonymous users
   - 📊 Statistics đầy đủ

## 📊 **Sample Output:**

```
🚫 Filtering anonymous users from 10 comments...
  🚫 Filtered anonymous: Anonymous participant 505
  🚫 Filtered anonymous: Ẩn danh
  🚫 Filtered anonymous: User 123
  📊 Filtered out 3 anonymous users
  ✅ Remaining: 7 real users

🔄 Resolving UIDs for 7 real users...
  🔍 Resolving UID for: Nguyễn Văn A
    ✅ Resolved UID: 100012345678901
  🔍 Resolving UID for: John Smith  
    ✅ Resolved UID: 100098765432109

✅ FOCUSED scraping completed: 7 real user comments | 5 UIDs resolved | 3 anonymous users filtered
```

## 🎯 **Benefits:**

- **Higher data quality**: Chỉ real users
- **Better performance**: Không waste time cho anonymous
- **Accurate analytics**: Statistics chính xác
- **Multi-language support**: Việt + Anh + patterns
- **Smart detection**: Nhiều pattern recognition methods

## ⚙️ **Technical Details:**

- **Filter timing**: Trước khi resolve UID (tiết kiệm thời gian)
- **Comprehensive patterns**: 15+ regex patterns
- **Validation layers**: Length, special chars, number patterns
- **Logging**: Chi tiết từng case được filter
- **Statistics tracking**: Count anonymous users filtered