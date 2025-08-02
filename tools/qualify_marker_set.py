#!/usr/bin/env python3
"""
qualify_marker_set.py - Validates normalized markers against Lean Deep 3.11 specification

This tool reads normalized marker files, validates them against LD3.11 rules,
and outputs qualified markers to final_marker_set/ or quarantine/ with detailed
error reporting.
"""

import yaml
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Configuration Section
CONFIG = {
    'MARKER_DIR': 'final_marker_set',  # Input from complete_markers.py
    'OUTPUT_DIR': 'final_marker_set',  # Qualified markers stay here
    'QUARANTINE': 'quarantine',
    'SUMMARY_LOG': 'tools/normalize_report.tsv',
    'MIN_EXAMPLES': 5,
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'tools/qualify_marker_set.log',
    'APPEND_TO_REPORT': True  # Append to existing report
}

# Set up logging
logging.basicConfig(
    level=getattr(logging, CONFIG['LOG_LEVEL']),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['LOG_FILE']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LeanDeep31Validator:
    """Validates markers against Lean Deep 3.11 specification"""
    
    def __init__(self):
        self.required_fields = {'_id', 'frame', 'examples'}
        self.frame_fields = {'signal', 'concept', 'pragmatics', 'narrative'}
        self.optional_fields = {'metadata', 'category', 'semantic_id', 'original_description',
                               'pattern', 'composed_of', 'detect_class'}
        self.errors = []
        self.warnings = []
    
    def validate_xor_constraint(self, marker: Dict) -> bool:
        """Validate XOR constraint: exactly one of pattern, composed_of, or detect_class"""
        xor_fields = ['pattern', 'composed_of', 'detect_class']
        present_fields = [f for f in xor_fields if f in marker]
        
        if len(present_fields) != 1:
            self.errors.append(f"XOR constraint violated: exactly one of {xor_fields} must be present, found {present_fields}")
            return False
        return True
    
    def validate_frame_structure(self, frame: Any) -> bool:
        """Validate frame object structure"""
        if not isinstance(frame, dict):
            self.errors.append(f"Frame must be a dictionary, got {type(frame).__name__}")
            return False
        
        missing_fields = self.frame_fields - set(frame.keys())
        if missing_fields:
            self.errors.append(f"Frame missing required fields: {missing_fields}")
            return False
        
        # Validate each frame field is a string
        for field in self.frame_fields:
            if not isinstance(frame[field], str):
                self.errors.append(f"Frame field '{field}' must be a string, got {type(frame[field]).__name__}")
                return False
            if not frame[field].strip():
                self.warnings.append(f"Frame field '{field}' is empty")
        
        return True
    
    def validate_examples(self, examples: Any) -> bool:
        """Validate examples array"""
        if not isinstance(examples, list):
            self.errors.append(f"Examples must be a list, got {type(examples).__name__}")
            return False
        
        if len(examples) < CONFIG['MIN_EXAMPLES']:
            self.errors.append(f"Insufficient examples: found {len(examples)}, minimum {CONFIG['MIN_EXAMPLES']} required")
            return False
        
        # Check for duplicates
        unique_examples = set()
        for i, example in enumerate(examples):
            if not isinstance(example, str):
                self.errors.append(f"Example {i} must be a string, got {type(example).__name__}")
                return False
            
            if example in unique_examples:
                self.warnings.append(f"Duplicate example found: '{example[:50]}...'")
            unique_examples.add(example)
        
        return True
    
    def validate_metadata(self, metadata: Any) -> bool:
        """Validate metadata structure if present"""
        if metadata is None:
            return True
        
        if not isinstance(metadata, dict):
            self.errors.append(f"Metadata must be a dictionary, got {type(metadata).__name__}")
            return False
        
        # Check recommended metadata fields
        recommended = {'created', 'author', 'version', 'tags'}
        present = set(metadata.keys())
        missing = recommended - present
        
        if missing:
            self.warnings.append(f"Metadata missing recommended fields: {missing}")
        
        # Validate tags if present
        if 'tags' in metadata:
            if not isinstance(metadata['tags'], list):
                self.errors.append("Metadata 'tags' must be a list")
                return False
            
            # Check for duplicate tags
            tags = metadata['tags']
            if len(tags) != len(set(tags)):
                self.warnings.append("Duplicate tags found in metadata")
        
        return True
    
    def validate_pattern(self, pattern: Any) -> bool:
        """Validate pattern field if present"""
        if not isinstance(pattern, str):
            self.errors.append(f"Pattern must be a string, got {type(pattern).__name__}")
            return False
        
        if not pattern.strip():
            self.warnings.append("Pattern is empty")
        
        return True
    
    def validate_composed_of(self, composed_of: Any) -> bool:
        """Validate composed_of structure if present"""
        if not isinstance(composed_of, list):
            self.errors.append(f"composed_of must be a list, got {type(composed_of).__name__}")
            return False
        
        for i, component in enumerate(composed_of):
            if not isinstance(component, dict):
                self.errors.append(f"composed_of[{i}] must be a dictionary")
                return False
            
            if 'type' not in component or 'marker_ids' not in component:
                self.errors.append(f"composed_of[{i}] must have 'type' and 'marker_ids' fields")
                return False
        
        return True
    
    def validate_marker(self, marker: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate a complete marker. Returns (is_valid, errors, warnings)"""
        self.errors = []
        self.warnings = []
        
        # Check required fields
        missing_required = self.required_fields - set(marker.keys())
        if missing_required:
            self.errors.append(f"Missing required fields: {missing_required}")
            return False, self.errors, self.warnings
        
        # Validate _id
        if not isinstance(marker['_id'], str) or not marker['_id'].strip():
            self.errors.append("_id must be a non-empty string")
        
        # Validate frame
        if not self.validate_frame_structure(marker.get('frame')):
            return False, self.errors, self.warnings
        
        # Validate examples
        if not self.validate_examples(marker.get('examples')):
            return False, self.errors, self.warnings
        
        # Validate XOR constraint
        if not self.validate_xor_constraint(marker):
            return False, self.errors, self.warnings
        
        # Validate optional fields if present
        if 'pattern' in marker:
            self.validate_pattern(marker['pattern'])
        
        if 'composed_of' in marker:
            self.validate_composed_of(marker['composed_of'])
        
        if 'metadata' in marker:
            self.validate_metadata(marker['metadata'])
        
        # Check for unknown fields
        all_allowed_fields = self.required_fields | self.optional_fields | {'pattern', 'composed_of', 'detect_class'}
        unknown_fields = set(marker.keys()) - all_allowed_fields
        if unknown_fields:
            self.warnings.append(f"Unknown fields will be preserved: {unknown_fields}")
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings


class MarkerQualifier:
    """Qualifies markers based on validation results"""
    
    def __init__(self):
        self.validator = LeanDeep31Validator()
    
    def calculate_quality_score(self, marker: Dict, warnings: List[str]) -> Tuple[float, str]:
        """Calculate quality score and rating"""
        score = 100.0
        
        # Deduct points for warnings
        score -= len(warnings) * 5
        
        # Bonus for complete metadata
        if 'metadata' in marker:
            metadata = marker['metadata']
            if all(field in metadata for field in ['created', 'author', 'version', 'tags']):
                score += 10
        
        # Bonus for rich examples
        if len(marker.get('examples', [])) > CONFIG['MIN_EXAMPLES']:
            score += 5
        
        # Bonus for detailed frame descriptions
        if 'frame' in marker:
            frame = marker['frame']
            avg_length = sum(len(frame.get(f, '')) for f in frame) / 4
            if avg_length > 50:
                score += 5
        
        # Determine rating
        if score >= 90:
            rating = "Excellent"
        elif score >= 80:
            rating = "Good"
        elif score >= 70:
            rating = "Acceptable"
        elif score >= 60:
            rating = "Needs Improvement"
        else:
            rating = "Poor"
        
        return max(0, min(100, score)), rating
    
    def qualify_marker(self, marker_path: Path) -> Dict[str, Any]:
        """Qualify a single marker file"""
        result = {
            'file': marker_path.name,
            'status': 'UNKNOWN',
            'errors': [],
            'warnings': [],
            'quality_score': 0,
            'quality_rating': 'N/A'
        }
        
        try:
            # Load marker
            with open(marker_path, 'r', encoding='utf-8') as f:
                marker = yaml.safe_load(f)
            
            if not marker:
                result['status'] = 'FAILED'
                result['errors'] = ['Empty or invalid YAML file']
                return result
            
            # Validate marker
            is_valid, errors, warnings = self.validator.validate_marker(marker)
            result['errors'] = errors
            result['warnings'] = warnings
            
            if is_valid:
                # Calculate quality score
                score, rating = self.calculate_quality_score(marker, warnings)
                result['quality_score'] = score
                result['quality_rating'] = rating
                result['status'] = 'QUALIFIED'
                
                # Marker stays in final_marker_set/
                logger.info(f"Qualified {marker_path.name} - Score: {score:.1f} ({rating})")
            else:
                result['status'] = 'FAILED'
                # Move to quarantine
                self._quarantine_marker(marker_path, errors)
                logger.error(f"Failed qualification for {marker_path.name}: {errors[0]}")
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['errors'] = [f"Processing error: {str(e)}"]
            self._quarantine_marker(marker_path, [str(e)])
            logger.error(f"Error processing {marker_path.name}: {e}")
        
        return result
    
    def _quarantine_marker(self, marker_path: Path, errors: List[str]):
        """Move failed marker to quarantine with error report"""
        quarantine_path = Path(CONFIG['QUARANTINE']) / marker_path.name
        error_path = Path(CONFIG['QUARANTINE']) / f"{marker_path.stem}.errors.json"
        
        # Move file to quarantine
        if marker_path.exists():
            quarantine_path.write_text(marker_path.read_text())
            marker_path.unlink()  # Remove from final_marker_set
        
        # Write error report
        error_data = {
            'file': marker_path.name,
            'validation_errors': errors,
            'timestamp': datetime.now().isoformat(),
            'stage': 'qualification'
        }
        error_path.write_text(json.dumps(error_data, indent=2))


def qualify_marker_set():
    """Main qualification function"""
    # Create output directories
    os.makedirs(CONFIG['QUARANTINE'], exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG['SUMMARY_LOG']), exist_ok=True)
    
    # Initialize counters
    total_files = 0
    qualified = 0
    failed = 0
    report_data = []
    
    qualifier = MarkerQualifier()
    
    # Process all YAML files in marker directory
    marker_path = Path(CONFIG['MARKER_DIR'])
    
    if not marker_path.exists():
        logger.error(f"Marker directory '{CONFIG["MARKER_DIR"]}' does not exist")
        print(f"Error: Marker directory '{CONFIG["MARKER_DIR"]}' does not exist")
        print("Please run complete_markers.py first to normalize markers.")
        return
    
    yaml_files = list(marker_path.glob('*.yaml'))
    if not yaml_files:
        logger.warning(f"No YAML files found in '{CONFIG['MARKER_DIR']}'")
        print(f"No YAML files found in '{CONFIG['MARKER_DIR']}'")
        return
    
    print(f"Qualifying {len(yaml_files)} markers...")
    
    for yaml_file in yaml_files:
        total_files += 1
        result = qualifier.qualify_marker(yaml_file)
        
        if result['status'] == 'QUALIFIED':
            qualified += 1
        else:
            failed += 1
        
        # Add to report
        report_entry = {
            'file': result['file'],
            'status': result['status'],
            'error': 'VALIDATION_ERROR' if result['errors'] else '',
            'details': f"Score: {result['quality_score']:.1f} ({result['quality_rating']})" 
                      if result['status'] == 'QUALIFIED' 
                      else '; '.join(result['errors'][:2])  # First 2 errors
        }
        report_data.append(report_entry)
        
        # Print progress
        if total_files % 10 == 0:
            print(f"Processed {total_files} files...")
    
    # Write or append to TSV report
    mode = 'a' if CONFIG['APPEND_TO_REPORT'] and os.path.exists(CONFIG['SUMMARY_LOG']) else 'w'
    with open(CONFIG['SUMMARY_LOG'], mode, encoding='utf-8') as f:
        if mode == 'w':
            f.write("File\tStatus\tError\tDetails\n")
        for entry in report_data:
            f.write(f"{entry['file']}\t{entry['status']}\t{entry['error']}\t{entry['details']}\n")
    
    # Calculate success rate
    success_rate = (qualified / total_files * 100) if total_files > 0 else 0
    
    # Print summary
    print(f"\nQualification Complete:")
    print(f"Total files: {total_files}")
    print(f"Successfully qualified: {qualified} ({success_rate:.1f}%)")
    print(f"Failed qualification: {failed}")
    print(f"\nReport saved to: {CONFIG['SUMMARY_LOG']}")
    print(f"Qualified markers remain in: {CONFIG['OUTPUT_DIR']}")
    print(f"Failed markers moved to: {CONFIG['QUARANTINE']}")
    
    # Check if all markers were qualified (acceptance criteria)
    if qualified == total_files:
        print("\n✅ SUCCESS: All markers successfully qualified!")
    else:
        print(f"\n⚠️  WARNING: {failed} markers failed qualification")


if __name__ == '__main__':
    qualify_marker_set()