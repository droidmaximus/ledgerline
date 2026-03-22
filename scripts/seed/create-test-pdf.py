#!/usr/bin/env python3
"""
Create minimal test PDF files for PageIndex system testing.
Useful when you don't have sample documents but want to test the system.
"""

import os
import sys
from pathlib import Path

# Try to create PDFs with reportlab (lightweight approach)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    print("⚠ reportlab not installed. Installing...")
    os.system(f"{sys.executable} -m pip install reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    HAS_REPORTLAB = True

def create_nvidia_10k_sample():
    """Create a sample NVIDIA 10-K report"""
    output_path = Path("sample-data/nvidia-10k-sample.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#000080',
        spaceAfter=30,
    )
    story.append(Paragraph("NVIDIA CORPORATION", title_style))
    story.append(Paragraph("Form 10-K", styles['Heading2']))
    story.append(Paragraph("Fiscal Year Ended January 28, 2025", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Forward-looking statement
    story.append(Paragraph("<b>Forward-Looking Statements</b>", styles['Heading3']))
    story.append(Paragraph(
        "This 10-K contains forward-looking statements regarding our future financial performance "
        "and operational results. Actual results may differ materially due to various risks and uncertainties.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Business Overview
    story.append(PageBreak())
    story.append(Paragraph("<b>Item 1. Business</b>", styles['Heading3']))
    story.append(Paragraph(
        "NVIDIA designs and manufactures graphics processing units (GPUs) and system-on-chip units. "
        "Our GPUs are used in gaming, professional visualization, data centers, and AI applications. "
        "We serve customers worldwide through our product lines including GeForce for gaming, "
        "Quadro for professional workstations, and Tesla for AI and data center applications.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Financial Data
    story.append(Paragraph("<b>Item 6. Selected Financial Data</b>", styles['Heading3']))
    story.append(Paragraph(
        "<b>Consolidated Statements of Income</b><br/>"
        "Revenue (in millions): $60,922<br/>"
        "Gross Profit: $44,050<br/>"
        "Operating Income: $27,747<br/>"
        "Net Income: $26,904<br/>"
        "<br/>"
        "<b>Gross Margin:</b> 72.3%<br/>"
        "<b>Operating Margin:</b> 45.5%<br/>"
        "<b>Net Margin:</b> 44.2%",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Risk Factors
    story.append(Paragraph("<b>Item 1A. Risk Factors</b>", styles['Heading3']))
    story.append(Paragraph(
        "• <b>Market Competition:</b> We face intense competition in the GPU market from AMD, Intel, and others.<br/>"
        "• <b>China Export Controls:</b> Restrictions on AI chip exports to China could impact revenue.<br/>"
        "• <b>Supply Chain:</b> Our manufacturing depends on third-party foundries, particularly TSMC.<br/>"
        "• <b>Currency Fluctuation:</b> International sales may be affected by exchange rate changes.<br/>"
        "• <b>Technology Transition:</b> Rapid advances require continuous R&D investment.",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    return output_path

def create_apple_10q_sample():
    """Create a sample Apple quarterly report"""
    output_path = Path("sample-data/apple-10q-sample.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#555555',
        spaceAfter=30,
    )
    story.append(Paragraph("APPLE INC.", title_style))
    story.append(Paragraph("Form 10-Q", styles['Heading2']))
    story.append(Paragraph("Quarterly Report for Q4 FY2024", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    story.append(Paragraph("<b>Item 1. Financial Statements</b>", styles['Heading3']))
    story.append(Paragraph(
        "<b>Condensed Consolidated Statements of Operations</b><br/>"
        "(In millions, except per share amounts)<br/>"
        "For the three months ended September 28, 2024:<br/>"
        "<br/>"
        "Net Sales: $94,736<br/>"
        "Cost of Sales: $46,342<br/>"
        "Gross Margin: $48,394 (51.1%)<br/>"
        "Operating Expenses: $11,562<br/>"
        "Operating Income: $36,832<br/>"
        "Net Income: $29,388<br/>",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Product Segment Data
    story.append(PageBreak())
    story.append(Paragraph("<b>Net Sales by Product Category</b>", styles['Heading3']))
    story.append(Paragraph(
        "<b>iPhone:</b> $46,221 million (48.8%)<br/>"
        "<b>Services:</b> $23,125 million (24.4%)<br/>"
        "<b>Mac:</b> $7,816 million (8.3%)<br/>"
        "<b>iPad:</b> $6,947 million (7.3%)<br/>"
        "<b>Wearables, Home, and Accessories:</b> $10,627 million (11.2%)",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Management Discussion
    story.append(Paragraph("<b>Item 2. Management's Discussion and Analysis</b>", styles['Heading3']))
    story.append(Paragraph(
        "Apple's Q4 FY2024 results reflect strong performance driven by robust iPhone sales and "
        "continued growth in Services. Despite macroeconomic challenges, we maintained momentum in our "
        "installed base and services revenue. Capital allocation priorities include ongoing investment "
        "in R&D, return of capital to shareholders through dividends and buybacks, and strategic acquisitions.",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    return output_path

def create_tesla_annual_sample():
    """Create a sample Tesla annual report"""
    output_path = Path("sample-data/tesla-annual-sample.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#CC0000',
        spaceAfter=30,
    )
    story.append(Paragraph("TESLA, INC.", title_style))
    story.append(Paragraph("Form 10-K", styles['Heading2']))
    story.append(Paragraph("Annual Report for Fiscal Year 2024", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Business Summary
    story.append(Paragraph("<b>Item 1. Business</b>", styles['Heading3']))
    story.append(Paragraph(
        "Tesla designs, manufactures, and sells electric vehicles, energy storage systems, and solar products. "
        "Our primary focus is accelerating the world's transition to sustainable energy. "
        "Our business segments include Automotive (vehicle sales), Energy Storage & Solar, and Services.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Financials
    story.append(PageBreak())
    story.append(Paragraph("<b>Financial Highlights</b>", styles['Heading3']))
    story.append(Paragraph(
        "<b>Total Revenues:</b> $81.4 billion<br/>"
        "<b>Cost of Revenues:</b> $54.3 billion<br/>"
        "<b>Gross Profit:</b> $27.1 billion (33.3%)<br/>"
        "<b>Operating Income:</b> $6.3 billion<br/>"
        "<b>Net Income:</b> $7.2 billion<br/>"
        "<br/>"
        "<b>Automotive Revenue:</b> $75.2 billion (92.4% of total)<br/>"
        "<b>Energy Storage Revenue:</b> $4.1 billion<br/>"
        "<b>Services & Other:</b> $2.1 billion",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Risks
    story.append(Paragraph("<b>Risk Factors</b>", styles['Heading3']))
    story.append(Paragraph(
        "• <b>Competition:</b> Increasing EV competition from traditional automakers and new entrants<br/>"
        "• <b>Supply Chain:</b> Dependence on critical materials and battery suppliers<br/>"
        "• <b>Regulatory:</b> Changes in EV incentives and emissions regulations<br/>"
        "• <b>Geopolitical:</b> Trade tensions and tariffs affecting operations<br/>"
        "• <b>Technology:</b> Rapid pace of EV technology advancement",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    return output_path

def main():
    """Create all sample PDFs"""
    print("\n" + "="*70)
    print("Creating Sample Financial Document PDFs for Testing")
    print("="*70 + "\n")
    
    samples = [
        ("NVIDIA 10-K", create_nvidia_10k_sample),
        ("Apple 10-Q", create_apple_10q_sample),
        ("Tesla Annual", create_tesla_annual_sample),
    ]
    
    created_files = []
    
    for name, creator_func in samples:
        try:
            print(f"Creating {name}...", end=" ")
            path = creator_func()
            size_kb = path.stat().st_size / 1024
            print(f"✓ ({size_kb:.1f} KB)")
            created_files.append(path)
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "-"*70)
    if created_files:
        print(f"✓ Successfully created {len(created_files)} sample PDF(s):")
        for pdf in created_files:
            print(f"  • {pdf}")
        print("\nYou can now use these PDFs with:")
        print("  .\scripts\seed\ingest-documents.ps1")
    else:
        print("✗ No PDFs were created. Check errors above.")
    
    print("-"*70 + "\n")

if __name__ == "__main__":
    main()
