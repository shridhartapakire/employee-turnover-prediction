import pandas as pd

input_file = "WA_Fn-UseC_-HR-Employee-Attrition.csv"
output_file = "WA_Fn-UseC_-HR-Employee-Attrition-Processed.csv"

# Read the original dataset
df = pd.read_csv(input_file)

# Rename the target column
df = df.rename(columns={"Attrition": "left"})

# Convert Yes/No to 1/0
df["left"] = df["left"].map({
    "Yes": 1,
    "No": 0
})

# Save the processed dataset
df.to_csv(output_file, index=False)

print("Dataset conversion completed.")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Saved as: {output_file}")
print("\nTarget values:")
print(df["left"].value_counts())