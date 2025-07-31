#!/usr/bin/env python3
"""
Count markers that don't comply with Lean-Deep 3.1 schema
"""

import json
import os
import yaml
from pathlib import Path

def check_lean_deep_compliance(marker_data):
    """Check if a marker complies with Lean-Deep 3.1 schema"""
    # Required fields
    if not isinstance(marker_data, dict):
        return False, ["Not a valid dictionary"]
    
    errors = []
    
    # Check _id
    if '_id' not in marker_data or not isinstance(marker_data.get('_id'), str):
        errors.append("Missing or invalid '_id' field")
    
    # Check frame
    if 'frame' not in marker_data or not isinstance(marker_data.get('frame'), dict):
        errors.append("Missing or invalid 'frame' field")
    else:
        frame = marker_data['frame']
        required_frame_fields = ['signal', 'concept', 'pragmatics', 'narrative']
        for field in required_frame_fields:
            if field not in frame:
                errors.append(f"Frame missing required field: {field}")
    
    # Check examples
    if 'examples' not in marker_data or not isinstance(marker_data.get('examples'), list):
        errors.append("Missing or invalid 'examples' field")
    elif len(marker_data['examples']) == 0:
        errors.append("Examples array cannot be empty")
    
    # Check XOR constraint
    detection_methods = []
    if marker_data.get('pattern') is not None:
        detection_methods.append('pattern')
    if marker_data.get('composed_of') is not None:
        detection_methods.append('composed_of')
    if marker_data.get('detect_class') is not None:
        detection_methods.append('detect_class')
    
    if len(detection_methods) != 1:
        errors.append(f"Must have exactly ONE of pattern, composed_of, or detect_class (found {len(detection_methods)})")
    
    return len(errors) == 0, errors

def is_old_format(marker_data):
    """Check if marker is in old (non Lean-Deep) format"""
    if not isinstance(marker_data, dict):
        return False
    
    old_format_indicators = [
        'marker_name' in marker_data,
        'id' in marker_data and '_id' not in marker_data,
        'atomic_pattern' in marker_data,
        'level' in marker_data and 'frame' not in marker_data,
        'kategorie' in marker_data
    ]
    
    return any(old_format_indicators)

def analyze_file(file_path):
    """Analyze a single marker file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() == '.json':
                data = json.load(f)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                return None, "Unknown file type"
        
        is_compliant, errors = check_lean_deep_compliance(data)
        is_old = is_old_format(data)
        
        return {
            'path': str(file_path),
            'filename': file_path.name,
            'compliant': is_compliant,
            'old_format': is_old,
            'errors': errors
        }, None
        
    except Exception as e:
        return None, str(e)

def find_marker_files(directory):
    """Find all potential marker files"""
    marker_files = []
    
    for ext in ['*.json', '*.yaml', '*.yml']:
        marker_files.extend(Path(directory).rglob(ext))
    
    # Filter to likely marker files
    filtered = []
    for file in marker_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if any(keyword in content for keyword in ['marker', '_id', 'frame', 'pattern', 'examples']):
                    filtered.append(file)
        except:
            pass
    
    return filtered

def main():
    print("🔍 Analyzing markers for Lean-Deep 3.1 compliance...\n")
    
    # Search directories
    base_dir = Path(__file__).parent.parent
    markers_dir = base_dir / 'resources' / 'markers'
    repair_dir = base_dir / 'marker-repair'
    
    all_files = []
    
    if markers_dir.exists():
        all_files.extend(find_marker_files(markers_dir))
        print(f"Found {len(all_files)} marker files in resources/markers")
    
    repair_files = []
    if repair_dir.exists():
        repair_files = find_marker_files(repair_dir)
        all_files.extend(repair_files)
        print(f"Found {len(repair_files)} marker files in marker-repair")
    
    print(f"\nTotal marker files found: {len(all_files)}\n")
    
    # Analyze files
    compliant = []
    old_format = []
    invalid = []
    errors = []
    
    for file in all_files:
        result, error = analyze_file(file)
        if error:
            errors.append({'file': str(file), 'error': error})
        elif result:
            if result['compliant']:
                compliant.append(result)
            elif result['old_format']:
                old_format.append(result)
            else:
                invalid.append(result)
    
    # Summary
    print("📊 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total marker files analyzed: {len(all_files)}")
    print(f"✅ Lean-Deep 3.1 compliant: {len(compliant)}")
    print(f"📜 Old format (non-compliant): {len(old_format)}")
    print(f"❌ Invalid format: {len(invalid)}")
    print(f"⚠️  Parse errors: {len(errors)}")
    print()
    
    # Non-compliant total
    non_compliant_total = len(old_format) + len(invalid)
    print(f"🔴 TOTAL NON-COMPLIANT MARKERS: {non_compliant_total}")
    print()
    
    # Compliance rate
    if len(all_files) > 0:
        compliance_rate = (len(compliant) / len(all_files)) * 100
        print(f"📈 Compliance Rate: {compliance_rate:.1f}%")
        print(f"📉 Non-compliance Rate: {100 - compliance_rate:.1f}%")
    print()
    
    # Show examples
    if old_format:
        print("📜 Examples of OLD FORMAT markers:")
        print("-" * 60)
        for marker in old_format[:5]:
            print(f"  - {marker['filename']}")
        if len(old_format) > 5:
            print(f"  ... and {len(old_format) - 5} more")
        print()
    
    if compliant:
        print("✅ Examples of COMPLIANT markers:")
        print("-" * 60)
        for marker in compliant[:5]:
            print(f"  - {marker['filename']}")
        if len(compliant) > 5:
            print(f"  ... and {len(compliant) - 5} more")
        print()
    
    # Save detailed report
    report = {
        'summary': {
            'total': len(all_files),
            'compliant': len(compliant),
            'old_format': len(old_format),
            'invalid': len(invalid),
            'errors': len(errors),
            'non_compliant_total': non_compliant_total
        },
        'compliant_files': [m['filename'] for m in compliant],
        'old_format_files': [m['filename'] for m in old_format],
        'invalid_files': [m['filename'] for m in invalid],
        'error_files': errors
    }
    
    report_path = base_dir / 'marker-compliance-analysis.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    main()