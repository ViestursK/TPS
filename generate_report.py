#!/usr/bin/env python3
"""
Trustpilot HTML Report Generator
Generates a modern dark-themed HTML report with embedded data
"""

import json
import sys
from pathlib import Path


def generate_html_report(json_data_path, output_path="trustpilot_report.html"):
    """
    Generate an HTML report with embedded JSON data
    
    Args:
        json_data_path: Path to the JSON data file (trustpilot_raw_data.json)
        output_path: Output HTML file path
    """
    
    # Read the JSON data
    try:
        with open(json_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[!] Error: JSON file not found: {json_data_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[!] Error: Invalid JSON file: {e}")
        sys.exit(1)
    
    # Read the HTML template
    template_path = Path(__file__).parent / "trustpilot_report.html"
    
    if not template_path.exists():
        print(f"[!] Error: HTML template not found: {template_path}")
        print("    Make sure 'trustpilot_report_v2.html' is in the same directory")
        sys.exit(1)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()
    
    # Embed the data in the HTML
    # Convert Python dict to JSON string
    json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    # Replace the EMBEDDED_DATA placeholder
    html_output = html_template.replace(
        'const EMBEDDED_DATA = null;',
        f'const EMBEDDED_DATA = {json_str};'
    )
    
    # Write the output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"\n[✓] HTML report generated: {output_path}")
    print(f"    Open this file in your browser to view the report")
    print(f"    Data source: {json_data_path}")
    print(f"    Total reviews in dataset: {len(data.get('reviews', []))}")
    print(f"    Company: {data.get('company', {}).get('brand_name', 'N/A')}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate Trustpilot HTML Report from JSON data'
    )
    parser.add_argument(
        'json_file',
        nargs='?',
        default='trustpilot_raw_data.json',
        help='Path to the JSON data file (default: trustpilot_raw_data.json)'
    )
    parser.add_argument(
        '-o', '--output',
        default='trustpilot_report.html',
        help='Output HTML file path (default: trustpilot_report.html)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("TRUSTPILOT HTML REPORT GENERATOR")
    print("="*70 + "\n")
    
    generate_html_report(args.json_file, args.output)
    
    print("\n" + "="*70)
    print("REPORT GENERATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()