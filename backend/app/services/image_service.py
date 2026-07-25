import logging
import io
from typing import Dict, Any

try:
    from PIL import Image, ExifTags
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

log = logging.getLogger("api")

def extract_image_evidence(image_bytes: bytes) -> Dict[str, Any]:
    """
    Phase 4: Local Image OCR & Metadata Tampering Pre-Processor.
    Optimized for CPU Hugging Face Spaces.
    
    1. Loads the image and extracts raw EXIF data.
    2. Resizes (max 1024px) and converts to Grayscale to save memory/CPU.
    3. Extracts visible text via Tesseract OCR.
    4. Evaluates metadata for tampering flags or social media scrubbing.
    """
    if Image is None or pytesseract is None:
        log.warning("[ImageService] Pillow or pytesseract is not installed. Skipping image pre-processing.")
        return {"ocr_text": "", "metadata_context": "[WARNING: Image processing dependencies missing on server]"}

    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        
        # ── Step 1: Metadata Extraction & Tamper Evaluation ──
        metadata_context = _evaluate_tampering(img)
        
        # ── Step 2: CPU Optimization Pre-Processing ──
        # Convert to grayscale to speed up OCR and reduce RAM
        img = img.convert('L')
        
        # Resize to max width 1024px to prevent massive 4K images from hanging the event loop
        max_width = 1024
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * float(ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        # ── Step 3: Tesseract OCR Extraction ──
        ocr_text = ""
        try:
            ocr_text = pytesseract.image_to_string(img).strip()
        except pytesseract.TesseractNotFoundError:
            log.warning("[ImageService] Tesseract binary not found! (Normal for local dev without Tesseract installed).")
            ocr_text = "[WARNING: OCR failed due to missing Tesseract binary on the host system.]"
            
        if not ocr_text:
            ocr_text = "[No readable text found in image]"
            
        return {
            "ocr_text": ocr_text,
            "metadata_context": metadata_context
        }
        
    except Exception as e:
        log.error(f"[ImageService] Failed to process image: {e}")
        return {
            "ocr_text": "",
            "metadata_context": f"[ERROR: Failed to process image file: {e}]"
        }

def _evaluate_tampering(img) -> str:
    """
    Analyzes EXIF data for signs of manipulation (Photoshop, AI generators).
    Handles the 'Social Media Strip-Out' edge case securely.
    """
    raw_exif = img.getexif()
    
    # 🚨 The Web-Upload EXIF Clearing Trap: 
    # Blank metadata on social media is extremely common.
    if not raw_exif:
        return "[METADATA ANALYSIS: EXIF data is completely blank. Note: Social media platforms (X, Facebook, WhatsApp) routinely strip metadata. Treat this image as neutral but unverified.]"
        
    # Extract readable tags
    exif_data = {}
    for tag_id, value in raw_exif.items():
        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
        exif_data[tag_name] = str(value).lower()
        
    suspicious_flags = []
    
    # Check "Software", "ProcessingSoftware", or "Artist" tags
    software_tag = exif_data.get("Software", "") + " " + exif_data.get("ProcessingSoftware", "")
    
    # AI Generators
    if any(ai in software_tag for ai in ["midjourney", "dall-e", "stable diffusion", "comfyui"]):
        suspicious_flags.append("🚨 HIGH RISK: Metadata contains AI-Generation signatures.")
        
    # Photo Editors
    if any(editor in software_tag for editor in ["photoshop", "canva", "illustrator", "lightroom"]):
        suspicious_flags.append("⚠️ MODERATE RISK: Metadata indicates the image was processed in photo-editing software.")

    if suspicious_flags:
        flags_str = " | ".join(suspicious_flags)
        return f"[METADATA ANALYSIS: {flags_str} | Raw Software Tag: {software_tag}]"
        
    return "[METADATA ANALYSIS: EXIF data present. No overt manipulation software detected.]"
