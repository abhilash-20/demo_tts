import re
from collections import defaultdict
from unsloth import FastLanguageModel
import torch

# 1. Load Model with 4-bit Quantization (Essential for 4GB VRAM)
model_path = "C:\Users\chinm\c tutorials\Final Year Project\backend\gender_detection\models\llama3_coref_model_200_steps\checkpoint-200" 

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_path,
    max_seq_length = 1024,
    dtype = None,           
    load_in_4bit = True,    
)

# 2. Optimized for Inference
FastLanguageModel.for_inference(model)

character_memory = {}
implicit_counter = 1 

MALE_PRONOUNS = {"he", "him", "his", "himself"}
FEMALE_PRONOUNS = {"she", "her", "hers", "herself"}

def assign_gender_from_pronouns(mentions):
    male_count = 0
    female_count = 0
    
    for m in mentions:
        # Split into words and strip punctuation like commas or quotes
        words = [w.strip('.,“"”!? ') for w in m.lower().split()]
        
        for word in words:
            if word in MALE_PRONOUNS:
                male_count += 1
            elif word in FEMALE_PRONOUNS:
                female_count += 1
                
    if male_count > female_count: return "male", 1.0
    if female_count > male_count: return "female", 1.0
    return "unknown", 0.0

def is_character_mention(mention_text: str, character: str):
    # This ensures "Sarah" is found even if the model outputs "[0] Sarah went to"
    clean_mention = mention_text.lower()
    clean_char = character.lower()
    return clean_char in clean_mention

def get_llama_coref_clusters(text):
    prompt = f"### Instruction:\nIdentify coreference clusters in the text by tagging mentions.\n\n### Input:\n{text}\n\n### Response:\n"
    inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
    
    # Use 'do_sample=False' for consistent results
    outputs = model.generate(**inputs, max_new_tokens=1024, use_cache=True, do_sample=False)
    response = tokenizer.batch_decode(outputs)[0]
    
    response_text = response.split("### Response:\n")[-1].replace(tokenizer.eos_token, "").strip()
    print(f"DEBUG - Raw Model Output: {response_text}")

    clusters = defaultdict(list)
    
    # Split by '[' to get: ['', '0] Sarah went...', '0] She bought...']
    parts = response_text.split('[')
    for part in parts:
        if ']' in part:
            tag_split = part.split(']', 1)
            cluster_id = tag_split[0].strip() # "0"
            content = tag_split[1].strip()    # "Sarah went to the market."
            clusters[cluster_id].append(content)
            
    return list(clusters.values())

def generative_pronoun_gender_score(text: str, character: str):
    clusters = get_llama_coref_clusters(text)
    
    # Clean the target character name
    target = character.lower().strip()
    
    for cluster_mentions in clusters:
        # Check if ANY mention in this cluster contains the character's name
        # We use a 'fuzzy' check: is "jim" inside "jim was in"?
        is_this_cluster_for_character = False
        for m in cluster_mentions:
            if target in m.lower():
                is_this_cluster_for_character = True
                break
        
        if is_this_cluster_for_character:
            # Once we find the right cluster, count pronouns in ALL mentions of that cluster
            gender, conf = assign_gender_from_pronouns(cluster_mentions)
            if gender != "unknown":
                return gender, conf
                
    return "unknown", 0.0
# TEST CALL
# print("sample test:", generative_pronoun_gender_score(
#     text="Sarah went to the market. She bought some apples.", 
#     character="Sarah"
# ))

print("sample test:", generative_pronoun_gender_score(
    text="Their house is by the sea, you know. It might be just the thing for the children. Fanny is very nice—she would look after them well.’ ‘Yes—and she has a child of her own too, hasn’t she?’ said the children’s mother. ‘Let me see—what’s her name—something funny—yes, Georgina! How old would she be? About eleven, I should think.’ ‘Same age as me,’ said Dick.", 
    character="Fanny"
))

# print("sample test:", generative_pronoun_gender_score(
#     text="Tom Sawyer lived with his aunt because his mother and father were dead. Tom didn’t like going to school, and he didn’t like working. He liked playing and having adventures. One Friday, he didn’t go to school—he went to the river. Aunt Polly was angry. “You’re a bad boy!” she said. “Tomorrow you can’t play with your friends because you didn’t go to school today. Tomorrow you’re going to work for me. You can paint the fence.” Saturday morning, Tom was not happy, but he started to paint the fence. His friend Jim was in the street. Tom asked him, “Do you want to paint?” Jim said, “No, I can’t. I’m going to get water.” Then Ben came to Tom’s house. He watched Tom and said, “I’m going to swim today. You can’t swim because you’re working.” Tom said, “This isn’t work. I like painting.” “Can I paint, too?” Ben asked. “No, you can’t,” Tom answered. “Aunt Polly asked me because I’m a very good painter.” Ben said, “I’m a good painter, too. Please, can I paint? I have some fruit. Do you want it?” OK,” Tom said. “Give me the fruit. Then you can paint.” Ben started to paint the fence. Later, many boys came to Tom’s house. They watched Ben, and they wanted to paint, too. Tom said, “Give me some food and you can paint.” 1 Tom stayed in the yard, and the boys painted. Tom stayed in the yard, and the boys painted. They painted the fence three times. It was beautiful and white. Tom went into the house. “Aunt Polly, can I play now?” he asked. Aunt Polly was surprised. “Did you paint the fence?” she asked. “Yes, I did,” Tom answered. Aunt Polly went to the yard and looked at the fence. She was very surprised and very happy. “It’s beautiful!” she said. “Yes, you can play now.” Tom walked to his friend Joe Harper’s house and played with his friends there. Then he walked home again. There was a new girl in one yard. She had yellow hair and blue eyes. She was beautiful. Tom wanted to talk to her, but she didn’t see him. She went into her house. Tom waited, but she didn’t come out again.", 
#     character="Jim"
# ))

# print("sample test:", generative_pronoun_gender_score(
#     text="One morning before school, Tom’s friend Huck Finn waited for him in the street. Huck didn’t have a home, and he never went to school. People in the town didn’t like him. But Tom liked Huck. Huck said, “Let’s have an adventure.” “What can we do on our adventure?” Tom asked. “Let’s go to the graveyard at night—at twelve o’clock!” Huck answered. ‘That’s a good adventure,” Tom said. “Let’s meet at eleven o’clock.” Then Tom went to school, but he was late. The teacher was angry. He asked, “Why are you late again?” 3 “I’m late because I talked to Huck Finn,” Tom said. Then the teacher was very angry. “Sit with the girls,” he said to Tom. Tom sat near the beautiful new girl. He was happy. He looked at her. “What’s your name?” he asked. “Becky,” she answered. Tom smiled and said, “My name’s Tom.” The teacher was angry again. “Tom Sawyer, stop talking! Go to your place now,” he said. Tom went to his place. At twelve o’clock Tom and Becky didn’t go home. They stayed in the school yard and talked. Tom said, “I love you. Do you love me?” “Yes,” Becky answered. “Good,” Tom said. “Then you’re going to walk to school with me every day. Amy always walked with me.” “Amy!” Becky said angrily. “Do you love her?” “No,” Tom answered. “I love you now. Do you want to walk with me?” But Becky was angry with Tom. She walked away and didn’t answer. Tom was unhappy. He didn’t go to school in the afternoon. That night Tom went to bed at nine o’clock, but he didn’t sleep. At eleven o’clock he went out his bedroom window to the yard. Huck was there. They walked to the graveyard. They stopped behind some big trees and talked quietly. Suddenly, there was a noise. Three men came into the graveyard—the doctor, Muff Potter, and Injun Joe. Injun Joe and the doctor talked angrily. Then Injun Joe 4 Then Injun Joe killed the doctor with a knife. killed the doctor with a knife. Tom and Huck watched. Then they went away quickly because they were afraid. They went to Tom’s yard. Huck said, “We can’t talk about this. Injun Joe can find us and kill us, too.” “That’s right,” Tom said. “We can’t talk about it.” Tom went in his bedroom window. He went to bed, but he didn’t sleep well. Tom and Huck didn’t talk to their friends or Aunt Polly about that night because they were afraid of Injun Joe. Later, some men went to Muff Potter and said, “You’re a bad man. You killed the doctor.”", 
#     character="Huck Finn"
# ))
