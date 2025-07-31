#!/usr/bin/env node
/**
 * Lean-Deep 3.1 Marker Validator
 * Checks if a marker structure complies with Lean-Deep 3.1 schema
 */

function validateLeanDeep31(marker) {
  const errors = [];
  const warnings = [];

  // 1. Check required top-level fields
  if (!marker._id || typeof marker._id !== 'string') {
    errors.push("Missing or invalid '_id' field (must be string)");
  }

  if (!marker.frame || typeof marker.frame !== 'object') {
    errors.push("Missing or invalid 'frame' field (must be object)");
  }

  if (!marker.examples || !Array.isArray(marker.examples)) {
    errors.push("Missing or invalid 'examples' field (must be array)");
  } else if (marker.examples.length === 0) {
    errors.push("'examples' array cannot be empty (minimum 1 example required)");
  } else if (marker.examples.length < 5) {
    warnings.push(`Only ${marker.examples.length} examples provided (5+ recommended for better coverage)`);
  }

  // 2. Check frame structure
  if (marker.frame) {
    const requiredFrameFields = ['signal', 'concept', 'pragmatics', 'narrative'];
    const missingFrameFields = requiredFrameFields.filter(field => !marker.frame[field]);
    
    if (missingFrameFields.length > 0) {
      errors.push(`Frame missing required fields: ${missingFrameFields.join(', ')}`);
    }

    // Check signal type
    if (marker.frame.signal && 
        typeof marker.frame.signal !== 'string' && 
        (!Array.isArray(marker.frame.signal) || !marker.frame.signal.every(s => typeof s === 'string'))) {
      errors.push("Frame 'signal' must be string or array of strings");
    }

    // Check other frame fields are strings
    ['concept', 'pragmatics', 'narrative'].forEach(field => {
      if (marker.frame[field] && typeof marker.frame[field] !== 'string') {
        errors.push(`Frame '${field}' must be a string`);
      }
    });
  }

  // 3. Check XOR constraint (exactly one of pattern, composed_of, detect_class)
  const detectionMethods = [];
  if (marker.pattern !== null && marker.pattern !== undefined) detectionMethods.push('pattern');
  if (marker.composed_of !== null && marker.composed_of !== undefined) detectionMethods.push('composed_of');
  if (marker.detect_class !== null && marker.detect_class !== undefined) detectionMethods.push('detect_class');

  if (detectionMethods.length === 0) {
    errors.push("Must have exactly ONE of: pattern, composed_of, or detect_class");
  } else if (detectionMethods.length > 1) {
    errors.push(`Cannot have multiple detection methods. Found: ${detectionMethods.join(', ')}`);
  }

  // 4. Validate detection method types
  if (marker.pattern !== null && marker.pattern !== undefined) {
    if (typeof marker.pattern !== 'string' && 
        (!Array.isArray(marker.pattern) || !marker.pattern.every(p => typeof p === 'string'))) {
      errors.push("'pattern' must be string or array of strings");
    }
  }

  if (marker.composed_of !== null && marker.composed_of !== undefined) {
    if (!Array.isArray(marker.composed_of) || !marker.composed_of.every(c => typeof c === 'string')) {
      errors.push("'composed_of' must be array of strings (marker IDs)");
    }
  }

  if (marker.detect_class !== null && marker.detect_class !== undefined) {
    if (typeof marker.detect_class !== 'string') {
      errors.push("'detect_class' must be a string");
    }
  }

  // 5. Check optional fields
  if (marker.activation !== null && marker.activation !== undefined && typeof marker.activation !== 'object') {
    errors.push("'activation' must be an object when present");
  }

  if (marker.scoring !== null && marker.scoring !== undefined && typeof marker.scoring !== 'object') {
    errors.push("'scoring' must be an object when present");
  }

  if (marker.tags !== null && marker.tags !== undefined) {
    if (!Array.isArray(marker.tags) || !marker.tags.every(t => typeof t === 'string')) {
      errors.push("'tags' must be array of strings when present");
    }
  }

  // 6. Check for unexpected fields (warnings)
  const validFields = ['_id', 'frame', 'examples', 'pattern', 'composed_of', 'detect_class', 
                       'activation', 'scoring', 'tags'];
  const unexpectedFields = Object.keys(marker).filter(field => !validFields.includes(field));
  
  if (unexpectedFields.length > 0) {
    warnings.push(`Unexpected fields found: ${unexpectedFields.join(', ')}`);
  }

  return { 
    valid: errors.length === 0, 
    errors, 
    warnings,
    detectionMethod: detectionMethods[0] || 'none'
  };
}

// Example usage and tests
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('Lean-Deep 3.1 Marker Validator\n');

  // Test with example markers
  const testMarkers = [
    {
      name: "Valid Pattern Marker",
      marker: {
        _id: "A_VALID_PATTERN",
        frame: {
          signal: ["test", "pattern"],
          concept: "Testing",
          pragmatics: "Validation",
          narrative: "Example"
        },
        pattern: ["test.*pattern"],
        examples: ["This is a test pattern", "Another test pattern here"]
      }
    },
    {
      name: "Invalid - Missing Frame Fields",
      marker: {
        _id: "INVALID_FRAME",
        frame: {
          concept: "Testing"
        },
        pattern: ["test"],
        examples: ["test"]
      }
    },
    {
      name: "Invalid - Multiple Detection Methods",
      marker: {
        _id: "INVALID_MULTIPLE",
        frame: {
          signal: "test",
          concept: "Test",
          pragmatics: "Test",
          narrative: "Test"
        },
        pattern: ["test"],
        composed_of: ["OTHER_MARKER"],
        examples: ["test"]
      }
    },
    {
      name: "Invalid - No Detection Method",
      marker: {
        _id: "INVALID_NO_METHOD",
        frame: {
          signal: "test",
          concept: "Test",
          pragmatics: "Test",
          narrative: "Test"
        },
        examples: ["test"]
      }
    },
    {
      name: "Invalid - Empty Examples",
      marker: {
        _id: "INVALID_EXAMPLES",
        frame: {
          signal: "test",
          concept: "Test",
          pragmatics: "Test",
          narrative: "Test"
        },
        pattern: ["test"],
        examples: []
      }
    }
  ];

  testMarkers.forEach(test => {
    console.log(`\nTesting: ${test.name}`);
    console.log('-'.repeat(50));
    
    const result = validateLeanDeep31(test.marker);
    
    console.log(`Valid: ${result.valid ? '✅' : '❌'}`);
    if (result.detectionMethod !== 'none') {
      console.log(`Detection Method: ${result.detectionMethod}`);
    }
    
    if (result.errors.length > 0) {
      console.log('\nErrors:');
      result.errors.forEach(error => console.log(`  ❌ ${error}`));
    }
    
    if (result.warnings.length > 0) {
      console.log('\nWarnings:');
      result.warnings.forEach(warning => console.log(`  ⚠️  ${warning}`));
    }
  });

  // CLI usage
  const args = process.argv.slice(2);
  if (args.length > 0 && args[0] === '--file') {
    import('fs').then(fs => {
    const filePath = args[1];
    
    if (!filePath) {
      console.error('\nError: Please provide a file path with --file');
      process.exit(1);
    }

    try {
      const fileContent = fs.readFileSync(filePath, 'utf8');
      const marker = JSON.parse(fileContent);
      
      console.log(`\n\nValidating marker from file: ${filePath}`);
      console.log('='.repeat(60));
      
      const result = validateLeanDeep31(marker);
      
      console.log(`\nMarker ID: ${marker._id || 'MISSING'}`);
      console.log(`Valid: ${result.valid ? '✅ YES' : '❌ NO'}`);
      
      if (result.valid) {
        console.log(`Detection Method: ${result.detectionMethod}`);
        console.log('\n✅ This marker is Lean-Deep 3.1 compliant!');
      }
      
      if (result.errors.length > 0) {
        console.log('\n❌ ERRORS (must fix):');
        result.errors.forEach((error, i) => console.log(`  ${i + 1}. ${error}`));
      }
      
      if (result.warnings.length > 0) {
        console.log('\n⚠️  WARNINGS (recommended fixes):');
        result.warnings.forEach((warning, i) => console.log(`  ${i + 1}. ${warning}`));
      }
      
      process.exit(result.valid ? 0 : 1);
    } catch (error) {
      console.error(`\nError reading/parsing file: ${error.message}`);
      process.exit(1);
    }
  }
}

export { validateLeanDeep31 };