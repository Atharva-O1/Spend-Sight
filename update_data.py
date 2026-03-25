import requests
import pdfplumber
import pandas as pd
import re
import io
import urllib3

# Hide SSL warnings (common when scraping government websites)
urllib3.disable_warnings()

# An official public PDF URL from the Nagpur Municipal Corporation website
PDF_URL = "https://nmcnagpur.gov.in/assets/300/2024/05/mediafiles/Tranport_Budget_Expense_24-25.pdf"

# 1. The Categorization Engine
# We map specific keywords found in the PDF text to your dashboard's sectors
CATEGORIES = {
    "Public Transport": ["bus", "transport", "metro", "vehicle", "ticket", "depot", "passenger"],
    "Water Supply": ["water", "pipe", "tanker", "river", "drain", "sewage", "drinking"],
    "Education": ["school", "library", "student", "study", "education", "college"],
    "Infrastructure & Roads": ["road", "repair", "construction", "bridge", "pothole", "asphalt"],
    "Urban Development": ["planning", "street", "smart city", "zone", "ward", "afforestation"],
    "Public Safety & Fire": ["fire", "police", "security", "guard", "emergency"],
    "Administration": ["salary", "pension", "office", "expense", "tax", "audit", "computer"]
}

def categorize_line(text):
    text_lower = text.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    return "Other Municipal Operations"

def extract_amount(text):
    # Regex formula to locate financial numbers in the text (e.g., 5000000.00)
    matches = re.findall(r'\b\d+\.\d{2}\b', text)
    if matches:
        # Convert the string to a float and pick the largest number on the line
        amounts = [float(m) for m in matches]
        # Divide by 10,000,000 to convert raw Rupee figures into Crores for the dashboard
        return max(amounts) / 10000000 
    return 0.0

def fetch_and_process_pdf():
    print(f"Connecting to NMC Server and downloading PDF...")
    
    # 2. Fetch the Official PDF
    try:
        # verify=False bypasses strict SSL checks which often block government site scraping
        response = requests.get(PDF_URL, verify=False) 
        response.raise_for_status()
        pdf_file = io.BytesIO(response.content)
        print("Download successful! Analyzing document using AI keyword mapping...")
    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return

    extracted_data = []

    # 3. Read and Analyze the Document
    with pdfplumber.open(pdf_file) as pdf:
        # We loop through pages (limiting to first 5 for speed during the hackathon demo)
        for i, page in enumerate(pdf.pages[:5]):
            text = page.extract_text()
            if not text:
                continue
                
            # Process the page line by line
            for line in text.split('\n'):
                # Ignore short headers or blank lines
                if len(line) < 10:
                    continue
                    
                amount_cr = extract_amount(line)
                
                # If we successfully extracted a financial amount, save this data point
                if amount_cr > 0:
                    sector = categorize_line(line)
                    
                    # Clean up the project name (remove the raw numbers and symbols from the text)
                    project_name = re.sub(r'[\d\.\-\_]', '', line).strip()
                    
                    # Prevent empty names
                    if len(project_name) < 5: 
                        project_name = "General Civic Expenditure"

                    extracted_data.append({
                        "Sector": sector,
                        "Project_Name": project_name,
                        "Allocated_Amount_Cr": round(amount_cr, 2),
                        "Status": "Proposed"
                    })

    # 4. Save to CSV for Streamlit
    if extracted_data:
        df = pd.DataFrame(extracted_data)
        
        # Consolidate duplicate items to make the chart look cleaner
        df = df.groupby(['Sector', 'Project_Name', 'Status'], as_index=False)['Allocated_Amount_Cr'].sum()
        
        # Sort so the highest funded projects appear at the top
        df = df.sort_values(by="Allocated_Amount_Cr", ascending=False)
        
        # Overwrite the old csv file with the live data
        df.to_csv("nagpur_budget.csv", index=False)
        
        print(f"\nSuccess! Successfully extracted {len(df)} financial records.")
        print("The data has been categorized and saved to 'nagpur_budget.csv'.")
        print("Refresh your Streamlit website to see the live updates!")
    else:
        print("Error: Could not extract any meaningful financial data from the document.")

# Trigger the script
if __name__ == "__main__":
    fetch_and_process_pdf()