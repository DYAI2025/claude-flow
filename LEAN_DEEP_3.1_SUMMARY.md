# Lean-Deep 3.1 Schema Summary

## Key Points to Remember

### 🔴 Required Fields (3)
1. **`_id`** - Unique string identifier
2. **`frame`** - Object with 4 required subfields
3. **`examples`** - Array with at least 1 example

### 🟡 Frame Structure (4 required fields)
1. **`signal`** - What you observe (string or array)
2. **`concept`** - Abstract meaning (string)
3. **`pragmatics`** - Functional purpose (string)
4. **`narrative`** - Contextual role (string)

### 🟢 XOR Detection Method (choose exactly ONE)
- **`pattern`** - For keyword/regex matching
- **`composed_of`** - For complex markers from simpler ones
- **`detect_class`** - For programmatic detection

### 🔵 Optional Fields
- **`activation`** - Object with activation rules
- **`scoring`** - Object with scoring config
- **`tags`** - Array of categorization strings

## Quick Validation Checklist

```bash
# Validate a single marker file
node scripts/validate-lean-deep-marker.js --file path/to/marker.json

# Check in code
const { validateLeanDeep31 } = require('./scripts/validate-lean-deep-marker.js');
const result = validateLeanDeep31(markerObject);
if (!result.valid) {
  console.error('Validation errors:', result.errors);
}
```

## Common Issues

1. **Missing frame fields** - All 4 frame fields are required
2. **Empty examples** - Must have at least 1 example
3. **Multiple detection methods** - Can only have one of pattern/composed_of/detect_class
4. **No detection method** - Must have exactly one detection method
5. **Wrong field types** - Check that arrays and strings are used correctly

## Non-Compliant Marker Examples

### ❌ Old format (not Lean-Deep 3.1)
```yaml
marker_name: A_CONTRAST_CONJUNCTION
id: "A_CONTRAST_CONJUNCTION"
atomic_pattern:
  - "aber"
  - "jedoch"
```

### ✅ Lean-Deep 3.1 format
```json
{
  "_id": "A_CONTRAST_CONJUNCTION",
  "frame": {
    "signal": ["aber", "jedoch"],
    "concept": "Contrast",
    "pragmatics": "Opposition marking",
    "narrative": "Perspective shift"
  },
  "pattern": ["aber", "jedoch"],
  "examples": ["Ich mag es, aber..."]
}
```