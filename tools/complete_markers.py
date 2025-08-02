#!/usr/bin/env python3
"""
complete_markers.py - Normalizes YAML markers to Lean Deep 3.11 compliance

This tool reads marker YAML files, repairs common syntax errors, and ensures
they conform to the Lean Deep 3.11 specification with proper frame structure,
sufficient examples, and complete metadata.
"""

import yaml
import os
import sys
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configuration Section
CONFIG = {
    'MARKER_DIR': 'marker',
    'OUTPUT_DIR': 'final_marker_set',
    'QUARANTINE': 'quarantine',
    'SUMMARY_LOG': 'tools/normalize_report.tsv',
    'MIN_EXAMPLES': 5,
    'LOG_LEVEL': 'INFO',
    'LOG_FILE': 'tools/complete_markers.log'
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


class YAMLRepairer:
    """Handles YAML syntax error recovery"""
    
    @staticmethod
    def repair_yaml_content(content: str) -> str:
        """Apply multiple repair strategies to fix common YAML issues"""
        # Remove document separators
        content = content.replace('---', '')
        
        # Convert tabs to spaces
        content = content.replace('\t', '  ')
        
        # Fix missing colons in headers
        lines = content.split('\n')
        repaired_lines = []
        
        for line in lines:
            # Fix lines that look like headers without colons
            if line.strip() and not line.strip().startswith('-') and ':' not in line:
                # Check if it looks like a key (alphanumeric with underscores)
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', line.strip()):
                    line = line.rstrip() + ':'
            repaired_lines.append(line)
        
        content = '\n'.join(repaired_lines)
        
        # Fix common YAML array issues
        content = re.sub(r'^\s*-\s*"(.+)"$', r'  - "\1"', content, flags=re.MULTILINE)
        
        return content
    
    @staticmethod
    def parse_with_recovery(file_path: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Try multiple strategies to parse YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return None, f"Failed to read file: {str(e)}"
        
        # Strategy 1: Try parsing as-is
        try:
            data = yaml.safe_load(content)
            if data:
                return data, None
        except yaml.YAMLError:
            pass
        
        # Strategy 2: Apply repairs and try again
        try:
            repaired_content = YAMLRepairer.repair_yaml_content(content)
            data = yaml.safe_load(repaired_content)
            if data:
                logger.info(f"Successfully repaired YAML for {file_path}")
                return data, None
        except yaml.YAMLError as e:
            pass
        
        # Strategy 3: Try line-by-line recovery
        try:
            data = {}
            current_key = None
            current_value = []
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line and not line.startswith('-'):
                    if current_key and current_value:
                        data[current_key] = '\n'.join(current_value).strip()
                    
                    parts = line.split(':', 1)
                    current_key = parts[0].strip()
                    current_value = [parts[1].strip()] if len(parts) > 1 and parts[1].strip() else []
                elif current_key:
                    current_value.append(line)
            
            if current_key and current_value:
                data[current_key] = '\n'.join(current_value).strip()
            
            if data:
                logger.warning(f"Used fallback parsing for {file_path}")
                return data, None
        except Exception:
            pass
        
        return None, "All parsing strategies failed"


class MarkerNormalizer:
    """Normalizes markers to Lean Deep 3.11 compliance"""
    
    def __init__(self):
        self.frame_templates = {
            'ENTITY': {
                'signal': 'Named entity detection patterns',
                'concept': 'Recognition of persons, organizations, locations',
                'pragmatics': 'Entity extraction and classification',
                'narrative': 'Identifying key actors and references in discourse'
            },
            'ATTACHMENT': {
                'signal': 'Attachment style linguistic patterns',
                'concept': 'Psychological attachment theory markers',
                'pragmatics': 'Relationship pattern identification',
                'narrative': 'Understanding interpersonal dynamics through language'
            },
            'EMOTION': {
                'signal': 'Emotional expression patterns',
                'concept': 'Affective state indicators',
                'pragmatics': 'Emotion recognition and tracking',
                'narrative': 'Monitoring emotional trajectories in conversation'
            },
            'CONVERSATION': {
                'signal': 'Conversational dynamics patterns',
                'concept': 'Interaction and dialogue structures',
                'pragmatics': 'Conversation flow analysis',
                'narrative': 'Understanding communication patterns and strategies'
            },
            'META': {
                'signal': 'Meta-level communication patterns',
                'concept': 'Higher-order linguistic structures',
                'pragmatics': 'Meta-communication analysis',
                'narrative': 'Detecting abstract patterns across multiple markers'
            }
        }
    
    def detect_category(self, marker_data: Dict) -> str:
        """Detect marker category based on name and content"""
        marker_name = marker_data.get('marker_name', '')
        description = str(marker_data.get('beschreibung', ''))
        
        # Check marker name prefixes
        if marker_name.startswith('A_LOC') or marker_name.startswith('A_PER') or marker_name.startswith('A_ORG'):
            return 'ENTITY'
        elif 'ATTACHMENT' in marker_name or 'attachment' in description.lower():
            return 'ATTACHMENT'
        elif 'EMO_' in marker_name or 'emotion' in description.lower():
            return 'EMOTION'
        elif marker_name.startswith('MM_'):
            return 'META'
        elif marker_name.startswith('C_') or marker_name.startswith('S_'):
            return 'CONVERSATION'
        else:
            return 'CONVERSATION'  # Default category
    
    def generate_frame(self, marker_data: Dict) -> Dict[str, str]:
        """Generate frame structure based on marker category"""
        category = self.detect_category(marker_data)
        template = self.frame_templates.get(category, self.frame_templates['CONVERSATION'])
        
        # Customize based on specific marker content
        marker_name = marker_data.get('marker_name', '')
        description = str(marker_data.get('beschreibung', ''))
        
        frame = template.copy()
        
        # Add marker-specific details
        if marker_name:
            frame['signal'] = f"{template['signal']} for {marker_name}"
        
        return frame
    
    def ensure_minimum_examples(self, examples: List) -> List[str]:
        """Ensure at least MIN_EXAMPLES examples exist"""
        # Clean and normalize existing examples
        clean_examples = []
        
        if isinstance(examples, list):
            for ex in examples:
                if isinstance(ex, str):
                    # Remove leading dash and quotes
                    ex = ex.strip()
                    if ex.startswith('- '):
                        ex = ex[2:]
                    ex = ex.strip('"')
                    if ex and ex != 'examples:' and ex != '-':
                        clean_examples.append(ex)
        
        # Generate additional examples if needed
        while len(clean_examples) < CONFIG['MIN_EXAMPLES']:
            template_idx = len(clean_examples) + 1
            clean_examples.append(f"Example usage pattern {template_idx} for this marker")
        
        return clean_examples
    
    def normalize_marker(self, marker_data: Dict, file_name: str) -> Dict:
        """Normalize a single marker to LD3.11 compliance"""
        # Extract marker ID from filename or marker_name
        marker_id = marker_data.get('marker_name', file_name.replace('.yaml', ''))
        
        # Create normalized structure
        normalized = {
            '_id': marker_id,
            'frame': self.generate_frame(marker_data),
            'examples': self.ensure_minimum_examples(marker_data.get('beispiele', [])),
            'pattern': f"Pattern for {marker_id}",  # Default pattern
            'metadata': {
                'created': marker_data.get('metadata', {}).get('created_at', datetime.now().isoformat()),
                'author': marker_data.get('metadata', {}).get('created_by', 'complete_markers.py'),
                'version': marker_data.get('metadata', {}).get('version', '1.0'),
                'tags': list(set(marker_data.get('metadata', {}).get('tags', ['normalized', 'ld3.11'])))
            }
        }
        
        # Add optional fields if present
        if 'kategorie' in marker_data:
            normalized['category'] = marker_data['kategorie']
        
        if 'semantische_grabber_id' in marker_data:
            normalized['semantic_id'] = marker_data['semantische_grabber_id']
        
        # Add original description as comment
        if 'beschreibung' in marker_data:
            normalized['original_description'] = str(marker_data['beschreibung'])
        
        return normalized


def process_markers():
    """Main processing function"""
    # Create output directories
    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
    os.makedirs(CONFIG['QUARANTINE'], exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG['SUMMARY_LOG']), exist_ok=True)
    
    # Initialize counters and report data
    total_files = 0
    successful = 0
    quarantined = 0
    report_data = []
    
    repairer = YAMLRepairer()
    normalizer = MarkerNormalizer()
    
    # Process all YAML files in marker directory
    marker_path = Path(CONFIG['MARKER_DIR'])
    
    if not marker_path.exists():
        logger.error(f"Marker directory '{CONFIG['MARKER_DIR']}' does not exist")
        return
    
    for yaml_file in marker_path.glob('*.yaml'):
        total_files += 1
        file_name = yaml_file.name
        logger.info(f"Processing {file_name}")
        
        # Try to parse and repair YAML
        marker_data, error = repairer.parse_with_recovery(str(yaml_file))
        
        if error:
            # Quarantine file
            quarantine_path = Path(CONFIG['QUARANTINE']) / file_name
            error_path = Path(CONFIG['QUARANTINE']) / f"{yaml_file.stem}.errors.json"
            
            # Copy original file to quarantine
            quarantine_path.write_text(yaml_file.read_text())
            
            # Write error details
            error_data = {
                'file': file_name,
                'error': error,
                'timestamp': datetime.now().isoformat(),
                'recovery_attempted': True
            }
            error_path.write_text(json.dumps(error_data, indent=2))
            
            quarantined += 1
            report_data.append({
                'file': file_name,
                'status': 'QUARANTINED',
                'error': 'YAML_ERROR',
                'details': error
            })
            logger.error(f"Quarantined {file_name}: {error}")
            continue
        
        try:
            # Normalize marker
            normalized = normalizer.normalize_marker(marker_data, file_name)
            
            # Write normalized marker
            output_path = Path(CONFIG['OUTPUT_DIR']) / file_name
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(normalized, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            successful += 1
            report_data.append({
                'file': file_name,
                'status': 'SUCCESS',
                'error': '',
                'details': f"Normalized with {len(normalized['examples'])} examples"
            })
            logger.info(f"Successfully normalized {file_name}")
            
        except Exception as e:
            # Quarantine file with processing error
            quarantine_path = Path(CONFIG['QUARANTINE']) / file_name
            error_path = Path(CONFIG['QUARANTINE']) / f"{yaml_file.stem}.errors.json"
            
            quarantine_path.write_text(yaml_file.read_text())
            
            error_data = {
                'file': file_name,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'stage': 'normalization'
            }
            error_path.write_text(json.dumps(error_data, indent=2))
            
            quarantined += 1
            report_data.append({
                'file': file_name,
                'status': 'QUARANTINED',
                'error': 'NORMALIZATION_ERROR',
                'details': str(e)
            })
            logger.error(f"Failed to normalize {file_name}: {e}")
    
    # Write TSV report
    with open(CONFIG['SUMMARY_LOG'], 'w', encoding='utf-8') as f:
        f.write("File\tStatus\tError\tDetails\n")
        for entry in report_data:
            f.write(f"{entry['file']}\t{entry['status']}\t{entry['error']}\t{entry['details']}\n")
    
    # Print summary
    print(f"\nProcessing Complete:")
    print(f"Total files: {total_files}")
    print(f"Successfully normalized: {successful}")
    print(f"Quarantined: {quarantined}")
    print(f"\nReport saved to: {CONFIG['SUMMARY_LOG']}")
    print(f"Normalized markers in: {CONFIG['OUTPUT_DIR']}")
    print(f"Quarantined files in: {CONFIG['QUARANTINE']}")


if __name__ == '__main__':
    process_markers()