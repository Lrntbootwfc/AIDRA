from fpdf import FPDF

def create_pdf(report_text, filename="AIDRA_Report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AIDRA Pharmaceutical Intelligence Report", ln=True, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=11)
    # Cleaning special characters for PDF safety
    clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    
    pdf.output(filename)
    print(f"PDF Saved as {filename}")

# Ise app.py mein import karke use kar sakte hain