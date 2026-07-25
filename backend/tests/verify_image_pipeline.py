import os
import sys
import asyncio
from PIL import Image

# Ensure the backend directory is in the path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.image_service import extract_image_evidence

def create_mock_tampered_image(test_path="tests/mock_fake_news.jpg"):
    """Generates a temporary image seeded with known photo-editing software signatures."""
    os.makedirs("tests", exist_ok=True)
    
    # 1. Create a basic 200x200 placeholder canvas
    img = Image.new('RGB', (200, 200), color='red')
    
    # 2. Inject an explicit 'Software' tag inside the image's EXIF directory
    exif_data = img.getexif()
    
    # The standard EXIF ID for 'Software' is 305
    exif_data[305] = "Adobe Photoshop 2026 (Windows)"
    
    # Save the file with the embedded metadata
    img.save(test_path, exif=exif_data)
    print(f"Generated mock tampered image asset at: {test_path}")
    return test_path

async def run_pipeline_test():
    test_file = create_mock_tampered_image()
    
    print("\nExecuting local image pipeline analysis loop...")
    try:
        # Read the raw file bytes to simulate an API multipart upload payload
        with open(test_file, "rb") as f:
            image_bytes = f.read()
            
        # Run the extraction pass natively on the CPU container
        analysis_report = extract_image_evidence(image_bytes)
        
        print("\n==================================================")
        print("PIPELINE OUTPUT ANALYSIS REPORT:")
        print("==================================================")
        print(str(analysis_report).encode('ascii', 'ignore').decode('ascii'))
        print("==================================================")
        
        # Verify that our security warning string was successfully triggered
        metadata_context = analysis_report.get("metadata_context", "")
        if "Photoshop" in metadata_context or "photoshop" in metadata_context:
            print("TEST PASSED: Image pre-processor successfully flagged the digital alteration signature!")
        else:
            print("TEST FAILED: Pipeline failed to extract the target software metadata metadata.")
            
    except Exception as e:
        print(f"Test script runtime exception encountered: {str(e)}")
    finally:
        # Clean up the test file asset from the workspace
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
