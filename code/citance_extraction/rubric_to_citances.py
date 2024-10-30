#%%
import os
import sys
import json
import re
import asyncio
import logging
from tqdm.asyncio import tqdm
from difflib import get_close_matches
import nest_asyncio
import aiohttp
import time
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
model ="gpt-4o"
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

nest_asyncio.apply()

# Adjust the project root and add it to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Import custom modules
from prompts.rubric_prompt import rubric_query


headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

async def get_one_completion(content,model=model,temperature=0.0):
    start_time = time.perf_counter()  # Record the start time for this request
    async with aiohttp.ClientSession() as session:
        # Make a POST request to OpenAI's API for text completion
        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": temperature
        }) as resp:
            response_json = await resp.json()
            end_time = time.perf_counter()  # Record the end time for this request
            elapsed_time = end_time - start_time
            print(f"Request for content '{content}' took {elapsed_time:.2f} seconds.")
            return response_json["choices"][0]['message']["content"]




# Load JSON data from citances file
with open(r'sample.json', 'r') as f:
    citances_data = json.load(f)

# Function to replace phrases in the 'citance' texts
def replace_phrases_in_citances(data, phrases_to_replace):
    for entry in data:
        for citance_dict in entry.get('citances', []):
            citance_text = citance_dict.get('citance', '')
            if isinstance(citance_text, str):
                for old_phrase, new_phrase in phrases_to_replace:
                    citance_text = citance_text.replace(old_phrase, new_phrase)
                citance_dict['citance'] = citance_text

# Phrases to replace
phrases_to_replace = [
    ("A prior work that", "Our work"),
    ("Prior works that", "Our work"),
    ("A group of prior works", "Our work"),
    ("A set of prior works", "Our work"),
    ("Three prior works", "Our work")
]

# Replace phrases in the citances
replace_phrases_in_citances(citances_data, phrases_to_replace)

# Function to clean and convert the AI's answer to a list of strings
def clean_and_convert(answer):
    # Remove unnecessary formatting or characters and filter out unwanted lines
    clean_lines = re.sub(r'[`\[\]\{\}]', '', answer).strip()
    # Split the answer into lines and strip whitespace
    clean_list = [line.strip() for line in clean_lines.split('\n') if line.strip() and line.lower() != "json"]
    return clean_list

# Asynchronous function to process each entry
async def process_entry(entry):
    corpus_id = entry.get('corpusId')
    citances_list = [citance_dict.get('citance', '') for citance_dict in entry.get('citances', [])]

    logging.info(f"Processing corpusId {corpus_id} with citances: {citances_list}")

    citances_formatted = " ".join([f"{i + 1}. {citance}\r\n\r\n" for i, citance in enumerate(citances_list)])
    query = rubric_query(citances_formatted)
    answer = await get_one_completion(query)
    clean = clean_and_convert(answer)
    logging.info(f"Processed data for corpusId {corpus_id}: {clean}")

    # Store the filtered citances in the entry
    entry['filtered_citances'] = clean

# Asynchronous function to process all entries
async def process_all_entries(data):
    tasks = [process_entry(entry) for entry in data]
    for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing citances"):
        await f

# Run the processing and save the results
asyncio.run(process_all_entries(citances_data))

# Save the processed data to a JSON file
output_file_path = "filtered_citances_all_data.json"
with open(output_file_path, "w") as f:
    json.dump(citances_data, f, indent=4)

# Function to parse the 'filtered_citances' and extract citance-score pairs
def parse_filtered_citances(filtered_citances):
    entries = [item.strip() for item in filtered_citances if item.strip() and item.strip() != ',']
    citance_scores = []
    i = 0
    while i < len(entries):
        citance_line = entries[i]
        if citance_line.lower().startswith('citance:'):
            # Extract the citance text
            citance = citance_line[len('citance:'):].strip().rstrip(',')
            # Assume the next line is the score
            i += 1
            if i < len(entries):
                score_line = entries[i]
                if score_line.lower().startswith('score:'):
                    score_str = score_line[len('score:'):].strip().rstrip(',')
                    try:
                        score = int(score_str)
                    except ValueError:
                        print(f"Invalid score value at index {i}: {score_str}")
                        score = None
                    citance_scores.append({'citance': citance, 'score': score})
                else:
                    print(f"Expected score after citance at index {i-1}, but got: {score_line}")
                    citance_scores.append({'citance': citance, 'score': None})
            else:
                print(f"No score found after citance at index {i-1}")
                citance_scores.append({'citance': citance, 'score': None})
        else:
            print(f"Unexpected format at index {i}: {citance_line}")
        i += 1
    return citance_scores

# Map the scores back to the original citances
for entry in citances_data:
    # Parse the filtered_citances to get citance-score pairs
    filtered_citances = entry.get('filtered_citances', [])
    citance_scores = parse_filtered_citances(filtered_citances)

    # Build a mapping from citance text to score
    citance_to_score = {item['citance']: item['score'] for item in citance_scores}

    # Add the score to each citance in 'citances' using fuzzy matching
    for citance_dict in entry.get('citances', []):
        citance_text = citance_dict.get('citance', '')
        if not isinstance(citance_text, str):
            print(f"citanceId {citance_dict.get('citanceId')}: citance_text is not a string, it is {type(citance_text)}")
            continue

        # Find the closest match in citance_to_score.keys()
        matches = get_close_matches(citance_text, citance_to_score.keys(), n=1, cutoff=0.9)
        if matches:
            matched_text = matches[0]
            score = citance_to_score.get(matched_text)
            citance_dict['score'] = score
        else:
            # No close match found
            citance_dict['score'] = None
            print(f"No close match found for citanceId {citance_dict.get('citanceId')}")

    # Optionally, remove 'filtered_citances' from the entry if no longer needed
    del entry['filtered_citances']


# %%
