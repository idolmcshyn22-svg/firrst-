# HTML Element Focuser 🎯

A powerful Python utility for focusing on specific HTML elements based on their height values and CSS properties. This tool is particularly useful for working with dynamically generated HTML content where you need to target specific elements by their styling properties.

## 🌟 Features

- **Height-based Element Targeting**: Focus on HTML elements by their specific height values
- **Advanced HTML Parsing**: Parse complex HTML structures with CSS classes and inline styles
- **Element Analysis**: Get detailed information about HTML elements including classes, attributes, and styles
- **Height Range Filtering**: Filter elements within specific height ranges
- **JSON Export**: Export analysis results to JSON format
- **Comprehensive Reporting**: Generate detailed reports of all found elements
- **Command-line Interface**: Easy-to-use CLI for batch processing
- **No External Dependencies**: Uses only Python standard library for core functionality

## 🚀 Quick Start

### 1) Setup and Environment Activation

```bash
git clone https://github.com/idolmcshyn22-svg/firrst-.git
cd firrst-

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Run the Facebook Groups Comment Scraper (GUI)

Prerequisites:
- Google Chrome installed

Run:
```bash
python fb_group_comment_scrapper.py
```

In the GUI:
- Paste a Facebook Groups post URL
- Paste your Facebook cookie string
- Choose output file (.xlsx or .csv)
- Click “Bắt đầu FIXED Scraping”

Notes:
- If you encounter a Tkinter error on macOS, use a Python.org build that includes Tk or install Tk via Homebrew.
- The scraper uses Selenium + ChromeDriver (managed automatically by webdriver-manager).

### Basic Usage

```python
from html_element_focuser import HTMLElementFocuser

html_content = '''
<div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" 
     data-visualcompletion="ignore" 
     data-thumb="1" 
     style="display: block; height: 3161px; right: 0px;"></div>
'''

# Initialize the focuser
focuser = HTMLElementFocuser(html_content)

# Focus on element with specific height
target_element = focuser.focus_on_height("3161px")

if target_element:
    print(f"Found element with height: {target_element.height}")
    print(f"Element classes: {target_element.classes}")
```

### Command Line Usage

```bash
# Focus on element with specific height
python html_element_focuser.py --target-height "3161px"

# Generate detailed report
python html_element_focuser.py --report

# Process HTML file and export to JSON
python html_element_focuser.py --input-file input.html --export-json results.json

# Combine multiple options
python html_element_focuser.py --target-height "3161px" --report --export-json analysis.json
```

## 📋 Requirements

- Python 3.7 or higher
- No external dependencies required for core functionality

## 🛠️ Installation

1. Clone this repository:
```bash
git clone https://github.com/idolmcshyn22-svg/firrst-.git
cd firrst-
```

2. (Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install optional dependencies if needed:
```bash
pip install -r requirements.txt
```

## 📖 API Documentation

### HTMLElementFocuser Class

#### Methods

- **`__init__(html_content: str)`**: Initialize with HTML content
- **`focus_on_height(target_height: str) -> Optional[HTMLElement]`**: Focus on element with specific height
- **`get_all_heights() -> List[str]`**: Get all unique height values
- **`filter_by_height_range(min_height: int, max_height: int) -> List[HTMLElement]`**: Filter by height range
- **`update_element_height(old_height: str, new_height: str) -> str`**: Update height values in HTML
- **`get_element_info(element: HTMLElement) -> Dict`**: Get detailed element information
- **`export_to_json(filename: str) -> None`**: Export results to JSON
- **`generate_report() -> str`**: Generate comprehensive report

### HTMLElement Dataclass

```python
@dataclass
class HTMLElement:
    tag: str                    # HTML tag name
    classes: List[str]          # CSS classes
    attributes: Dict[str, str]  # HTML attributes
    style: Dict[str, str]       # Parsed CSS styles
    height: Optional[str]       # Height value
    raw_html: str              # Original HTML string
```

## 🎯 Use Cases

### 1. Focus on Different Height Elements

```python
# Switch focus from 924px to 3161px element
old_element = focuser.focus_on_height("924px")
new_element = focuser.focus_on_height("3161px")

print(f"Old focus: {old_element.height if old_element else 'Not found'}")
print(f"New focus: {new_element.height if new_element else 'Not found'}")
```

### 2. Analyze All Elements

```python
# Get comprehensive analysis
report = focuser.generate_report()
print(report)

# Get all available heights
heights = focuser.get_all_heights()
print(f"Available heights: {heights}")
```

### 3. Filter by Height Range

```python
# Find elements between 1000px and 4000px
large_elements = focuser.filter_by_height_range(1000, 4000)
print(f"Found {len(large_elements)} large elements")
```

### 4. Export Results

```python
# Export to JSON for further analysis
focuser.export_to_json("analysis_results.json")
```

## 🧪 Examples

### Example 1: Basic Element Focusing

```python
html = '''
<div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" 
     style="height: 924px;">Element 1</div>
<div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" 
     style="height: 3161px;">Element 2</div>
'''

focuser = HTMLElementFocuser(html)
target = focuser.focus_on_height("3161px")
print(f"Focused on: {target.raw_html}")
```

### Example 2: Command Line Processing

```bash
# Process HTML file and generate report
python html_element_focuser.py \
    --input-file webpage.html \
    --target-height "3161px" \
    --report \
    --export-json results.json
```

## 🐛 Troubleshooting

### Common Issues

1. **Element not found**: Check if the height value includes "px" unit
2. **No elements parsed**: Verify the HTML contains elements with the target CSS classes
3. **Style parsing issues**: Ensure CSS styles are properly formatted

### Debug Tips

```python
# Check what elements were found
focuser = HTMLElementFocuser(html_content)
print(f"Found {len(focuser.elements)} elements")
for element in focuser.elements:
    print(f"Height: {element.height}, Classes: {len(element.classes)}")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔄 Version History

- **v1.0.0** - Initial release with core functionality
  - Height-based element focusing
  - HTML parsing and analysis
  - Command-line interface
  - JSON export capability

## 🙋‍♂️ Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/idolmcshyn22-svg/firrst-/issues) page
2. Create a new issue with detailed information
3. Include sample HTML and expected behavior

## 📊 Performance

- **Fast parsing**: Optimized regex patterns for element detection
- **Memory efficient**: Processes large HTML files without loading everything into memory
- **No dependencies**: Lightweight solution using only Python standard library

---

Made with ❤️ for HTML element analysis and focusing tasks.
