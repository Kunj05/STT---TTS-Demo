from paddleocr import PaddleOCR
import cv2

# Initialize OCR
ocr = PaddleOCR(use_textline_orientation=True, lang='en')

# Read image
image_path = "/app/images/menu1.png"

# Run OCR
result = ocr.predict(image_path)

print("\n--- OCR RESULT ---\n")

extracted_text = []

for line in result[0]:
    text = line[1][0]
    extracted_text.append(text)

print("Detected Text:")
print(" ".join(extracted_text))