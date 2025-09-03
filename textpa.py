import re

def focus_on_element(html_content, target_height):
    """
    Focus on a specific HTML element based on its height value
    
    Args:
        html_content (str): The HTML content to parse
        target_height (str): The target height to focus on (e.g., "3161px")
    
    Returns:
        str: The matching HTML element or None if not found
    """
    # Pattern to match div elements with the specific class and style
    pattern = r'<div[^>]*class="x14nfmen[^"]*x1sd63oq"[^>]*style="[^"]*height:\s*' + re.escape(target_height) + r'[^"]*"[^>]*>[^<]*</div>'
    
    match = re.search(pattern, html_content, re.IGNORECASE)
    if match:
        return match.group(0)
    
    # Try a more flexible pattern
    pattern2 = r'<div[^>]*x14nfmen[^>]*height:\s*' + re.escape(target_height) + r'[^>]*>'
    match2 = re.search(pattern2, html_content, re.IGNORECASE)
    if match2:
        return match2.group(0)
    
    return None

def extract_height_from_element(html_element):
    """
    Extract height value from HTML element
    
    Args:
        html_element (str): HTML element string
    
    Returns:
        str: Height value or None if not found
    """
    height_match = re.search(r'height:\s*(\d+px)', html_element)
    if height_match:
        return height_match.group(1)
    return None

def update_focus_element(html_content, old_height, new_height):
    """
    Update the HTML to focus on a different element by changing height references
    
    Args:
        html_content (str): The HTML content
        old_height (str): The current height being focused on
        new_height (str): The new height to focus on
    
    Returns:
        str: Updated HTML content
    """
    # Replace the height value in the HTML
    updated_html = html_content.replace(f'height: {old_height}', f'height: {new_height}')
    return updated_html

def analyze_elements(html_content):
    """
    Analyze all div elements with the target class pattern
    
    Args:
        html_content (str): The HTML content
    
    Returns:
        list: List of found elements with their heights
    """
    # Find all div elements with the class pattern
    pattern = r'<div[^>]*class="[^"]*x14nfmen[^"]*x1sd63oq[^"]*"[^>]*style="[^"]*height:\s*(\d+px)[^"]*"[^>]*>'
    matches = re.finditer(pattern, html_content, re.IGNORECASE)
    
    elements = []
    for match in matches:
        height = match.group(1)
        element = match.group(0)
        elements.append({
            'height': height,
            'element': element,
            'full_match': match.group(0)
        })
    
    return elements

# Example usage with your HTML elements
html_example = '''
<div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" data-visualcompletion="ignore" data-thumb="1" style="display: block; height: 924px; right: 0px;"></div>

<div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" data-visualcompletion="ignore" data-thumb="1" style="display: block; height: 3161px; right: 0px;"></div>
'''

def main():
    print("Analyzing HTML elements...")
    print("="*60)
    
    # Analyze all elements
    elements = analyze_elements(html_example)
    
    print(f"Found {len(elements)} elements:")
    for i, elem in enumerate(elements, 1):
        print(f"\nElement {i}:")
        print(f"  Height: {elem['height']}")
        print(f"  Element: {elem['element']}")
    
    print("\n" + "="*60)
    
    # Focus on the element with height 3161px
    target_element = focus_on_element(html_example, "3161px")
    
    if target_element:
        print("✅ Successfully focused on element with height 3161px:")
        print(f"Target element: {target_element}")
        
        height = extract_height_from_element(target_element)
        print(f"Extracted height: {height}")
        
    else:
        print("❌ Target element with height 3161px not found")
    
    print("\n" + "="*60)
    print("Switching focus from 924px to 3161px:")
    
    # Show the difference
    old_focus = focus_on_element(html_example, "924px")
    new_focus = focus_on_element(html_example, "3161px")
    
    print(f"\nOld focus (924px): {old_focus is not None}")
    print(f"New focus (3161px): {new_focus is not None}")
    
    if old_focus and new_focus:
        print(f"\nOld element height: {extract_height_from_element(old_focus)}")
        print(f"New element height: {extract_height_from_element(new_focus)}")

if __name__ == "__main__":
    main()