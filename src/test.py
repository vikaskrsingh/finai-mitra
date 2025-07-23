from google.cloud import vision

def test_ocr(gcs_uri):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(source=vision.ImageSource(image_uri=gcs_uri))
    response = client.document_text_detection(image=image)
    print("OCR Response:", response.full_text_annotation.text)

# Replace with your GCS URI
test_ocr("gs://finai-mitra-docs-bucket/finai-mitra-uploads/1753109776_Loan-Agreement(secured-against-Bank-Guarantee).pdf")