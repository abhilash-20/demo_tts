import os
import random
from pathlib import Path

# 1. Update this to the actual path where LitBank's conll files are stored
source_dir = Path(r"E:\\Final Year Project\\dbamman litbank master coref-conll") 

# 2. This is your target folder
target_dir = Path(r"E:\\Final Year Project\\train-test-split")

# Create target directory if it doesn't exist
target_dir.mkdir(parents=True, exist_ok=True)

# Get all .conll files
all_files = [f for f in os.listdir(source_dir) if f.endswith(".conll")]

# Shuffle to ensure a random mix of books in train/dev
random.seed(42) # Fixed seed for reproducibility
random.shuffle(all_files)

# Define 80/20 split
split_point = int(len(all_files) * 0.8)
train_files = all_files[:split_point]
dev_files = all_files[split_point:]

def combine_files(file_list, output_filename):
    output_path = target_dir / output_filename
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for fname in file_list:
            file_path = source_dir / fname
            with open(file_path, 'r', encoding='utf-8') as infile:
                # Write the content of the individual book
                outfile.write(infile.read())
                # Ensure there is a newline between documents
                outfile.write("\n\n")
    return output_path

train_path = combine_files(train_files, "train.conll")
dev_path = combine_files(dev_files, "dev.conll")

print(f"Successfully created:")
print(f" - Train set: {train_path} ({len(train_files)} books)")
print(f" - Dev set:   {dev_path} ({len(dev_files)} books)")