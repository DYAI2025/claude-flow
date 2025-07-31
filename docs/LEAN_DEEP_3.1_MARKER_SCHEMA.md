# Lean-Deep 3.1 Marker Schema Documentation

## Overview
Lean-Deep 3.1 is a structured schema specification for psychological and linguistic markers that ensures consistency and validation in marker-based text analysis systems.

## Core Requirements

### 1. Required Fields
Every marker MUST have these fields:
- `_id` (string): Unique identifier for the marker
- `frame` (object): Core semantic frame with four required subfields
- `examples` (array): At least one example string

### 2. Frame Structure
The `frame` object MUST contain all four fields:
- `signal` (string or array of strings): Observable linguistic patterns
- `concept` (string): Abstract concept being marked
- `pragmatics` (string): Pragmatic function or intent
- `narrative` (string): Narrative or contextual role

### 3. XOR Constraint
A marker MUST have exactly ONE of these fields (not zero, not multiple):
- `pattern` (string or array): Regex or pattern matching rules
- `composed_of` (array): References to other markers
- `detect_class` (string): Detection class identifier

### 4. Optional Fields
These fields are optional but have specific types when present:
- `activation` (object): Activation rules for the marker
- `scoring` (object): Scoring configuration
- `tags` (array of strings): Categorization tags

## Valid Marker Examples

### Example 1: Pattern-based Marker
```json
{
  "_id": "A_CONTRAST_CONJUNCTION",
  "frame": {
    "signal": ["aber", "jedoch", "dennoch"],
    "concept": "Contrast",
    "pragmatics": "Opposition marking",
    "narrative": "Shift in perspective"
  },
  "pattern": ["aber", "jedoch", "dennoch", "allerdings"],
  "examples": [
    "Ich mag dich, aber ich brauche Zeit",
    "Das ist richtig, jedoch nicht vollständig"
  ],
  "tags": ["contrast", "conjunction"]
}
```

### Example 2: Composed Marker
```json
{
  "_id": "C_RELATIONAL_LOOP",
  "frame": {
    "signal": ["Nähe/Distanz Pattern"],
    "concept": "Relational Ambivalence",
    "pragmatics": "Destabilization",
    "narrative": "Relationship cycle"
  },
  "composed_of": ["A_CLOSENESS_MARKER", "A_DISTANCE_MARKER"],
  "activation": {
    "rule": "ANY 2 IN 48h",
    "threshold": 0.7
  },
  "examples": [
    "Ich vermisse dich... aber ich brauche Abstand"
  ]
}
```

### Example 3: Detect Class Marker
```json
{
  "_id": "MM_EMOTION_DETECTOR",
  "frame": {
    "signal": "Emotional language patterns",
    "concept": "Emotional Expression",
    "pragmatics": "Emotion communication",
    "narrative": "Emotional state"
  },
  "detect_class": "EmotionDetector",
  "examples": [
    "Ich bin so glücklich!",
    "Das macht mich traurig"
  ],
  "scoring": {
    "base": 1.5,
    "weight": 2.0
  }
}
```

## Common Validation Errors

### 1. Missing Required Fields
❌ **Invalid**: Missing frame
```json
{
  "_id": "INVALID_MARKER",
  "examples": ["test"]
}
```

### 2. Incomplete Frame
❌ **Invalid**: Frame missing required fields
```json
{
  "_id": "INVALID_MARKER",
  "frame": {
    "concept": "Test"  // Missing signal, pragmatics, narrative
  },
  "examples": ["test"]
}
```

### 3. Empty Examples
❌ **Invalid**: Examples array cannot be empty
```json
{
  "_id": "INVALID_MARKER",
  "frame": {
    "signal": "test",
    "concept": "Test",
    "pragmatics": "Testing",
    "narrative": "Test narrative"
  },
  "examples": []  // Must have at least one example
}
```

### 4. Multiple Detection Methods
❌ **Invalid**: Has both pattern and composed_of
```json
{
  "_id": "INVALID_MARKER",
  "frame": { /* valid frame */ },
  "pattern": ["test"],
  "composed_of": ["OTHER_MARKER"],  // Can't have both!
  "examples": ["test"]
}
```

### 5. No Detection Method
❌ **Invalid**: Must have one of pattern, composed_of, or detect_class
```json
{
  "_id": "INVALID_MARKER",
  "frame": { /* valid frame */ },
  "examples": ["test"]
  // Missing pattern, composed_of, or detect_class
}
```

## Validation Checklist

To ensure a marker is Lean-Deep 3.1 compliant:

- [ ] Has `_id` field (string)
- [ ] Has `frame` object with all 4 required fields:
  - [ ] `signal` (string or string array)
  - [ ] `concept` (string)
  - [ ] `pragmatics` (string)  
  - [ ] `narrative` (string)
- [ ] Has `examples` array with at least 1 example
- [ ] Has EXACTLY ONE of:
  - [ ] `pattern` (string or string array)
  - [ ] `composed_of` (string array)
  - [ ] `detect_class` (string)
- [ ] Optional fields have correct types:
  - [ ] `activation` is object or null
  - [ ] `scoring` is object or null
  - [ ] `tags` is string array or null

## Practical Tips

1. **Choose the Right Detection Method**:
   - Use `pattern` for simple keyword/regex matching
   - Use `composed_of` for complex markers built from simpler ones
   - Use `detect_class` for programmatic detection logic

2. **Frame Design**:
   - `signal`: What you observe in the text
   - `concept`: What it means abstractly
   - `pragmatics`: What it does functionally
   - `narrative`: How it fits in context

3. **Examples**:
   - Provide diverse, realistic examples
   - Include edge cases
   - Minimum 5 examples recommended (though 1 is required)

4. **Validation Testing**:
   - Use the database initialization script to verify schema
   - Test markers before bulk import
   - Check MongoDB validation errors for specific issues