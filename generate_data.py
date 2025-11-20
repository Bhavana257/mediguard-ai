import os
from faker import Faker
import pandas as pd
import random

# Initialize Faker and set seeds for reproducibility
fake = Faker()
random.seed(42)
Faker.seed(42)

def generate_data(n=10000, output_dir="data"):
    """
    Generate synthetic patient data for MediGuard fraud detection system
    
    Args:
        n: Number of patient records to generate (default: 10000)
        output_dir: Directory to save the CSV file (default: "data")
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    data = []
    for i in range(1, n + 1):
        data.append({
            "patient_id": f"P{i:07d}",
            "name": fake.name(),
            "dob": fake.date_of_birth(minimum_age=18, maximum_age=90),
            "phone": fake.phone_number()[:12],
            "email": fake.email(),
            "diagnosis": random.choice(["I10", "E11.9", "J44.9", "M54.5"]),
            "procedure": random.choice(["99214", "93000", "36415", "81001"]),
            "amount": round(random.uniform(100, 8000), 2),
            "task": random.choice([
                "Pending Lab", 
                "Missing Consult", 
                "None", 
                "Pending Imaging"
            ])
        })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(data)
    output_path = os.path.join(output_dir, "patients.csv")
    df.to_csv(output_path, index=False)
    
    print(f"✅ Generated {n:,} synthetic patient records")
    print(f"📁 Saved to: {output_path}")
    print(f"📊 File size: {os.path.getsize(output_path) / 1024:.2f} KB")
    
    # Display sample data
    print("\n📋 Sample records:")
    print(df.head().to_string())
    
    return df

if __name__ == "__main__":
    # Generate 10,000 patient records
    generate_data(10000)