import os
from pathlib import Path

train_file = Path(r"E:\Final Year Project\train-test-split\train.conll")
dev_file = Path(r"E:\Final Year Project\train-test-split\dev.conll")

def final_conll_standardization(file_path):
    print(f"Standardizing {file_path} to CoNLL-2012 format...")
    temp_file = file_path.with_suffix('.tmp')
    
    with open(file_path, 'r', encoding='utf-8') as f_in, \
         open(temp_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            if line.startswith("#") or not line.strip():
                f_out.write(line)
                continue
            
            parts = line.strip().split('\t')
            raw_coref = parts[-1]
            
            if raw_coref == "-":
                coref_fixed = "-"
            else:
                # Remove all asterisks. The reader expects (ID) or (ID or ID)
                # and it will associate them with the * in the penultimate column.
                coref_fixed = raw_coref.replace('*', '')
            
            # Construct the row. 
            # Columns 3 is word, Column 11 is Coref.
            # We set column 10 (index 10) to '*' because that is the 'token' placeholder.
            new_row = [
                parts[0], "0", parts[2], parts[3], 
                "XX", "*", "-", "-", "-", "-", "*", coref_fixed
            ]
            f_out.write("\t".join(new_row) + "\n")

    os.remove(file_path)
    os.rename(temp_file, file_path)
    print("Standardization Complete.")

final_conll_standardization(train_file)
final_conll_standardization(dev_file)