#!/bin/bash

# Seed sample data for testing
# Creates test documents in MinIO

set -e

echo "Seeding sample data..."

# Create minimal test PDF
echo "Creating test PDF..."
python3 << 'EOF'
# Create a minimal valid PDF
pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Sample Test Document) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000323 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
417
%%EOF
"""

with open("sample.pdf", "wb") as f:
    f.write(pdf_content)
print("✓ Created sample.pdf")
EOF

# Upload via the API
echo "Uploading sample document..."
curl -s -F "file=@sample.pdf" http://localhost:8080/documents/upload | jq '.' || echo "Note: API may not be running yet"

echo "✓ Sample data seeded"
echo ""
echo "Sample document created. Run 'make up' to start services."
