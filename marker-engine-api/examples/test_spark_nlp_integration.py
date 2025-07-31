#!/usr/bin/env python3
"""
Example script to test the Spark NLP integration with MarkerEngine v1.0
"""
import asyncio
import httpx
import json
from typing import Dict, Any


async def test_analyze_v2(base_url: str = "http://localhost:8000"):
    """Test the new analyze/v2 endpoint with NLP features"""
    
    # Test texts with different complexity levels
    test_cases = [
        {
            "name": "Simple emotion",
            "text": "Ich vermisse dich.",
            "schema_id": "relationship_markers"
        },
        {
            "name": "Complex ambivalence",
            "text": "Ich liebe dich, aber ich brauche Zeit für mich allein.",
            "schema_id": "relationship_markers"
        },
        {
            "name": "Temporal sequence",
            "text": "Zuerst war ich glücklich, dann wurde ich traurig, aber jetzt bin ich wieder hoffnungsvoll.",
            "schema_id": "emotion_markers"
        },
        {
            "name": "Negation context",
            "text": "Ich bin nicht mehr wütend, aber ich kann dir noch nicht verzeihen.",
            "schema_id": "relationship_markers"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Testing MarkerEngine v1.0 with Spark NLP Integration")
        print("=" * 80)
        
        # First, check service status
        print("\n1. Checking service status...")
        try:
            response = await client.get(f"{base_url}/analyze/v2/status")
            status = response.json()
            print(f"   - Orchestration Service: {status['orchestration_service']}")
            print(f"   - NLP Service Type: {status['nlp_service']['type']}")
            print(f"   - NLP Available: {status['nlp_service']['available']}")
            print(f"   - Spark NLP Enabled: {status['nlp_service']['spark_nlp_enabled']}")
        except Exception as e:
            print(f"   ERROR: Could not check status - {e}")
            return
        
        # Test each case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            print(f"   Text: \"{test_case['text']}\"")
            
            try:
                # Make request
                response = await client.post(
                    f"{base_url}/analyze/v2",
                    json={
                        "text": test_case["text"],
                        "schema_id": test_case.get("schema_id")
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display results
                    print(f"   ✓ Analysis successful!")
                    print(f"   - Request ID: {result['request_id']}")
                    print(f"   - Markers found: {result['marker_count']}")
                    print(f"   - Total score: {result['total_score']:.2f}")
                    print(f"   - NLP enriched: {result['nlp_enriched']}")
                    
                    # Show phase breakdown
                    print("   - Phase breakdown:")
                    for phase, metrics in result['phases'].items():
                        time_ms = metrics.get('processing_time', 0) * 1000
                        if phase == 'phase1_initial_scan':
                            print(f"     • Phase 1 (Initial): {metrics.get('markers_found', 0)} markers in {time_ms:.1f}ms")
                        elif phase == 'phase2_nlp_enrichment':
                            enrichment = metrics.get('enrichment', {})
                            if enrichment:
                                print(f"     • Phase 2 (NLP): {enrichment.get('tokens', 0)} tokens in {time_ms:.1f}ms")
                            else:
                                print(f"     • Phase 2 (NLP): Skipped")
                        elif phase == 'phase3_contextual_rescan':
                            added = metrics.get('markers_found', 0)
                            if added:
                                print(f"     • Phase 3 (Context): +{added} markers in {time_ms:.1f}ms")
                            else:
                                print(f"     • Phase 3 (Context): No additional markers")
                    
                    # Show detected markers
                    if result['markers']:
                        print("   - Detected markers:")
                        for marker in result['markers'][:5]:  # Show first 5
                            conf = marker.get('confidence', 0)
                            phase = marker.get('detection_phase', 'unknown')
                            print(f"     • {marker['marker_id']} (confidence: {conf:.2f}, phase: {phase})")
                        if len(result['markers']) > 5:
                            print(f"     ... and {len(result['markers']) - 5} more")
                    
                    # Show interpretation snippet
                    if result.get('interpretation'):
                        interp = result['interpretation'][:150] + "..." if len(result['interpretation']) > 150 else result['interpretation']
                        print(f"   - Interpretation: {interp}")
                        print(f"   - Model used: {result.get('model_used', 'none')}")
                    
                else:
                    print(f"   ✗ Error: HTTP {response.status_code}")
                    print(f"   - Details: {response.text}")
                    
            except Exception as e:
                print(f"   ✗ Exception: {e}")
        
        # Test batch processing
        print("\n" + "=" * 80)
        print("Testing batch processing...")
        
        try:
            batch_texts = [tc["text"] for tc in test_cases[:3]]
            response = await client.post(
                f"{base_url}/analyze/v2/batch",
                json={
                    "texts": batch_texts,
                    "schema_id": "relationship_markers"
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✓ Batch analysis successful! Processed {len(results)} texts")
                
                total_markers = sum(r['marker_count'] for r in results)
                total_time = sum(r['total_processing_time'] for r in results)
                avg_time = total_time / len(results) if results else 0
                
                print(f"  - Total markers found: {total_markers}")
                print(f"  - Average processing time: {avg_time:.3f}s per text")
                
            else:
                print(f"✗ Batch processing failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ Batch processing exception: {e}")


async def compare_v1_vs_v2(base_url: str = "http://localhost:8000"):
    """Compare results between v1 and v2 endpoints"""
    
    test_text = "Ich liebe dich, aber ich kann dir nicht mehr vertrauen."
    schema_id = "relationship_markers"
    
    print("\n" + "=" * 80)
    print("Comparing v1 vs v2 endpoints")
    print("=" * 80)
    print(f"Test text: \"{test_text}\"")
    
    async with httpx.AsyncClient() as client:
        # Test v1
        print("\nTesting v1 endpoint...")
        try:
            response = await client.post(
                f"{base_url}/analyze",
                json={"text": test_text, "schema_id": schema_id}
            )
            v1_result = response.json()
            print(f"  - Markers found: {v1_result.get('marker_count', 0)}")
            print(f"  - Processing time: Not tracked in v1")
        except Exception as e:
            print(f"  - Error: {e}")
            v1_result = None
        
        # Test v2
        print("\nTesting v2 endpoint...")
        try:
            response = await client.post(
                f"{base_url}/analyze/v2",
                json={"text": test_text, "schema_id": schema_id}
            )
            v2_result = response.json()
            print(f"  - Markers found: {v2_result['marker_count']}")
            print(f"  - Total processing time: {v2_result['total_processing_time']:.3f}s")
            print(f"  - NLP enriched: {v2_result['nlp_enriched']}")
            
            # Show phase contributions
            phase1_markers = v2_result['phases']['phase1_initial_scan'].get('markers_found', 0)
            phase3_added = v2_result['phases']['phase3_contextual_rescan'].get('markers_found', 0)
            
            print(f"  - Phase 1 markers: {phase1_markers}")
            print(f"  - Phase 3 additions: +{phase3_added}")
            
        except Exception as e:
            print(f"  - Error: {e}")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_analyze_v2())
    asyncio.run(compare_v1_vs_v2())
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)