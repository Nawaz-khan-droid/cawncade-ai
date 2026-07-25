from PIL import Image

def trim_black(im_path, out_path):
    img = Image.open(im_path).convert("RGB")
    pixels = img.load()
    width, height = img.size
    
    min_x = width
    min_y = height
    max_x = 0
    max_y = 0
    
    # Threshold for "black" (Midjourney/DALL-E might have very dark gray pixels)
    threshold = 15
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if r > threshold or g > threshold or b > threshold:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                
    if min_x > max_x:
        print("Image is entirely black")
        return
        
    print(f"Bounding box: ({min_x}, {min_y}, {max_x}, {max_y})")
    
    cropped = img.crop((min_x, min_y, max_x, max_y))
    
    # Ensure it's a perfect square
    w, h = cropped.size
    size = max(w, h)
    square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0)) # transparent padding
    square_img.paste(cropped.convert("RGBA"), ((size - w) // 2, (size - h) // 2))
    
    # Resize to 512x512
    final = square_img.resize((512, 512), Image.Resampling.LANCZOS)
    final.save(out_path, "PNG")
    print("Saved successfully!")

if __name__ == "__main__":
    trim_black(r"C:\Users\ks919\Downloads\CAWNCADE AI\frontend\public\logo-raw.png", 
               r"C:\Users\ks919\Downloads\CAWNCADE AI\frontend\public\logo.png")
