import csv
import os
from kaedra.services.memory import MemoryService

def ingest_billing_report(csv_path: str):
    print(f"[*] Reading billing report from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[!] Error: File not found: {csv_path}")
        return

    memory_service = MemoryService()
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        report_summary = []
        for row in reader:
            service = row.get('Service description')
            cost = row.get('Cost ($)')
            subtotal = row.get('Subtotal ($)')
            if service and cost:
                summary = f"- {service}: Cost ${cost}, Subtotal ${subtotal}"
                report_summary.append(summary)
        
        if report_summary:
            bulk_text = "Google Cloud Billing Report (Who Ent Free - Dec 2025):\n" + "\n".join(report_summary)
            print("[*] Ingesting summary into Memory Bank...")
            memory_service.insert(content=bulk_text, role="user")
            print("[*] Consolidation triggered...")
            memory_service.consolidate()
            print("[✓] Billing report ingested successfully.")

if __name__ == "__main__":
    CSV_PATH = r"c:\Users\super\Downloads\Who Ent Free (feb)_Reports, 2025-12-01 — 2025-12-27.csv"
    ingest_billing_report(CSV_PATH)
