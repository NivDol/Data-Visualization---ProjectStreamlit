import pandas as pd
import os

def preprocess_and_merge():
    # 1. Load the datasets
    file1 = "ai_job_dataset.csv"
    file2 = "ai_job_dataset1.csv"
    output_file = "database_ai_job_final.csv"

    if not os.path.exists(file1) or not os.path.exists(file2):
        print("Error: Input files not found.")
        return

    print("Loading datasets...")
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # 2. Fix Job IDs
    # Offset the IDs of the second dataset to ensure uniqueness
    offset = len(df1)
    df2['job_id'] = [f"AI{i+1+offset:05d}" for i in range(len(df2))]

    # 3. Concatenate (Merge)
    print("Merging datasets...")
    df_final = pd.concat([df1, df2], ignore_index=True)

    # 4. Delete the 'salary_local' field
    if 'salary_local' in df_final.columns:
        print("Removing 'salary_local' column...")
        df_final.drop(columns=['salary_local'], inplace=True)

    # 5. Save to CSV
    print(f"Saving to {output_file}...")
    df_final.to_csv(output_file, index=False)

    print("Success!")
    print(f"Final Database Shape: {df_final.shape}")
    print("Columns:", df_final.columns.tolist())

if __name__ == "__main__":
    preprocess_and_merge()