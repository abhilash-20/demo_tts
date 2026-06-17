import json
import re

def parse_conll_to_generative_jsonl(input_path, output_path):
    dataset = []
    current_tokens = []
    current_clusters = {} # stack to track open spans
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                if current_tokens:
                    # Finalize the sentence markup
                    text = " ".join([t['word'] for t in current_tokens])
                    
                    # Create tagged version
                    tagged_text = ""
                    for i, t in enumerate(current_tokens):
                        # Logic to add [ and ]{ID:x} based on span markers
                        word = t['word']
                        if t['starts']:
                            for cluster_id in t['starts']:
                                tagged_text += f"[{cluster_id}] "
                        tagged_text += word + " "
                    
                    # For SFT, we want Input -> Output mapping
                    dataset.append({
                        "instruction": "Identify coreference clusters in the text by tagging mentions.",
                        "input": text.strip(),
                        "output": tagged_text.strip()
                    })
                    current_tokens = []
                continue

            parts = line.split()
            word = parts[3] # Usually index 3 in CoNLL-2012
            coref_info = parts[-1]
            
            token_data = {"word": word, "starts": [], "ends": []}
            
            # Simple regex to find cluster IDs like (7, 7), or (7|8
            if coref_info != "-":
                starts = re.findall(r'\((\d+)', coref_info)
                ends = re.findall(r'(\d+)\)', coref_info)
                token_data["starts"] = starts
                token_data["ends"] = ends
                
            current_tokens.append(token_data)

    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in dataset:
            f.write(json.dumps(entry) + '\n')

# Usage
parse_conll_to_generative_jsonl("E:/Final Year Project/train-test-split/dev.conll", "E:/Final Year Project/train-test-split/litbank_generative_dev.jsonl")
print("Conversion complete!")