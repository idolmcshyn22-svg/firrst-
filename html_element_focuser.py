#!/usr/bin/env python3
"""
HTML Element Focuser

A Python utility to focus on specific HTML elements based on their height values.
This tool is particularly useful for working with dynamically generated HTML content
where you need to target specific elements by their styling properties.

Author: HTML Element Focuser Team
Version: 1.0.0
"""

import re
import json
import argparse
from typing import List, Dict, Optional, Union
from dataclasses import dataclass


@dataclass
class HTMLElement:
    """Represents an HTML element with its properties."""
    tag: str
    classes: List[str]
    attributes: Dict[str, str]
    style: Dict[str, str]
    height: Optional[str]
    raw_html: str


class HTMLElementFocuser:
    """Main class for focusing on HTML elements based on height values."""
    
    def __init__(self, html_content: str):
        """
        Initialize the focuser with HTML content.
        
        Args:
            html_content (str): The HTML content to work with
        """
        self.html_content = html_content
        self.elements = self._parse_elements()
    
    def _parse_style_string(self, style_str: str) -> Dict[str, str]:
        """
        Parse CSS style string into a dictionary.
        
        Args:
            style_str (str): CSS style string
            
        Returns:
            Dict[str, str]: Parsed style properties
        """
        style_dict = {}
        if not style_str:
            return style_dict
            
        # Split by semicolon and parse each property
        for prop in style_str.split(';'):
            prop = prop.strip()
            if ':' in prop:
                key, value = prop.split(':', 1)
                style_dict[key.strip()] = value.strip()
        
        return style_dict
    
    def _parse_elements(self) -> List[HTMLElement]:
        """
        Parse HTML content and extract elements with the target class pattern.
        
        Returns:
            List[HTMLElement]: List of parsed HTML elements
        """
        elements = []
        
        # Enhanced pattern to match div elements with the specific class pattern
        pattern = r'<div[^>]*class="[^"]*x14nfmen[^"]*x1sd63oq[^"]*"[^>]*>'
        matches = re.finditer(pattern, self.html_content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            raw_html = match.group(0)
            
            # Extract classes
            class_match = re.search(r'class="([^"]*)"', raw_html)
            classes = class_match.group(1).split() if class_match else []
            
            # Extract all attributes
            attr_pattern = r'(\w+(?:-\w+)*)="([^"]*)"'
            attributes = dict(re.findall(attr_pattern, raw_html))
            
            # Extract and parse style
            style_str = attributes.get('style', '')
            style_dict = self._parse_style_string(style_str)
            
            # Extract height
            height = style_dict.get('height')
            
            element = HTMLElement(
                tag='div',
                classes=classes,
                attributes=attributes,
                style=style_dict,
                height=height,
                raw_html=raw_html
            )
            
            elements.append(element)
        
        return elements
    
    def focus_on_height(self, target_height: str) -> Optional[HTMLElement]:
        """
        Focus on an element with the specified height.
        
        Args:
            target_height (str): Target height value (e.g., "3161px")
            
        Returns:
            Optional[HTMLElement]: The matching element or None if not found
        """
        for element in self.elements:
            if element.height == target_height:
                return element
        return None
    
    def get_all_heights(self) -> List[str]:
        """
        Get all unique height values from parsed elements.
        
        Returns:
            List[str]: List of unique height values
        """
        heights = []
        for element in self.elements:
            if element.height and element.height not in heights:
                heights.append(element.height)
        return sorted(heights, key=lambda x: int(x.replace('px', '')) if 'px' in x else 0)
    
    def filter_by_height_range(self, min_height: int, max_height: int) -> List[HTMLElement]:
        """
        Filter elements by height range.
        
        Args:
            min_height (int): Minimum height in pixels
            max_height (int): Maximum height in pixels
            
        Returns:
            List[HTMLElement]: Filtered elements
        """
        filtered = []
        for element in self.elements:
            if element.height and 'px' in element.height:
                height_value = int(element.height.replace('px', ''))
                if min_height <= height_value <= max_height:
                    filtered.append(element)
        return filtered
    
    def update_element_height(self, old_height: str, new_height: str) -> str:
        """
        Update HTML content by changing height values.
        
        Args:
            old_height (str): Current height value
            new_height (str): New height value
            
        Returns:
            str: Updated HTML content
        """
        return self.html_content.replace(f'height: {old_height}', f'height: {new_height}')
    
    def get_element_info(self, element: HTMLElement) -> Dict[str, Union[str, List[str], Dict[str, str]]]:
        """
        Get detailed information about an element.
        
        Args:
            element (HTMLElement): The element to analyze
            
        Returns:
            Dict: Element information
        """
        return {
            'tag': element.tag,
            'classes': element.classes,
            'height': element.height,
            'style_properties': element.style,
            'data_attributes': {k: v for k, v in element.attributes.items() if k.startswith('data-')},
            'all_attributes': element.attributes,
            'raw_html': element.raw_html
        }
    
    def export_to_json(self, filename: str) -> None:
        """
        Export parsed elements to JSON file.
        
        Args:
            filename (str): Output filename
        """
        data = []
        for element in self.elements:
            data.append(self.get_element_info(element))
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive report of all elements.
        
        Returns:
            str: Formatted report
        """
        report = []
        report.append("HTML Element Analysis Report")
        report.append("=" * 50)
        report.append(f"Total elements found: {len(self.elements)}")
        report.append(f"Unique heights: {', '.join(self.get_all_heights())}")
        report.append("")
        
        for i, element in enumerate(self.elements, 1):
            report.append(f"Element {i}:")
            report.append(f"  Height: {element.height}")
            report.append(f"  Classes: {len(element.classes)} classes")
            report.append(f"  Data attributes: {len([k for k in element.attributes.keys() if k.startswith('data-')])}")
            report.append(f"  Style properties: {len(element.style)}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='HTML Element Focuser')
    parser.add_argument('--target-height', '-t', default='3161px', 
                       help='Target height to focus on (default: 3161px)')
    parser.add_argument('--input-file', '-i', 
                       help='Input HTML file to process')
    parser.add_argument('--export-json', '-e', 
                       help='Export results to JSON file')
    parser.add_argument('--report', '-r', action='store_true',
                       help='Generate detailed report')
    
    args = parser.parse_args()
    
    # Sample HTML content (can be replaced with file input)
    html_sample = '''
    <div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" 
         data-visualcompletion="ignore" 
         data-thumb="1" 
         style="display: block; height: 924px; right: 0px;"></div>

    <div class="x14nfmen x1s85apg x5yr21d xtijo5x xg01cxk x10l6tqk x13vifvy x1wsgiic x19991ni xwji4o3 x1kky2od x1sd63oq" 
         data-visualcompletion="ignore" 
         data-thumb="1" 
         style="display: block; height: 3161px; right: 0px;"></div>
    '''
    
    # Use input file if provided
    html_content = html_sample
    if args.input_file:
        try:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.input_file}' not found.")
            return
    
    # Initialize focuser
    focuser = HTMLElementFocuser(html_content)
    
    # Generate report if requested
    if args.report:
        print(focuser.generate_report())
        print()
    
    # Focus on target height
    target_element = focuser.focus_on_height(args.target_height)
    
    if target_element:
        print(f"✅ Successfully focused on element with height {args.target_height}")
        print("\nElement Details:")
        print("-" * 30)
        
        info = focuser.get_element_info(target_element)
        print(f"Height: {info['height']}")
        print(f"Classes: {len(info['classes'])} total")
        print(f"Data attributes: {len(info['data_attributes'])}")
        print(f"Style properties: {len(info['style_properties'])}")
        
        print(f"\nRaw HTML:")
        print(info['raw_html'])
        
    else:
        print(f"❌ No element found with height {args.target_height}")
        available_heights = focuser.get_all_heights()
        if available_heights:
            print(f"Available heights: {', '.join(available_heights)}")
    
    # Export to JSON if requested
    if args.export_json:
        focuser.export_to_json(args.export_json)
        print(f"\n📄 Results exported to {args.export_json}")


if __name__ == "__main__":
    main()
