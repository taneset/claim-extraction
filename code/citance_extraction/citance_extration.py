#%%

"""This script processes a CSV file of scientific paper citations, retrieves detailed information for each paper using an API, 
and checks if the full text is available. It filters the dataset to include only papers with available full text, 
saves the filtered data into a structured JSON file, and prepares it for further analysis. 
The script also logs its operations and handles asynchronous tasks to manage API calls efficiently"""
import pandas as pd
import logging
import aiohttp
import asyncio
import nest_asyncio
import re
import json
import os
from tqdm import tqdm
import nest_asyncio
import os
import sys

# Add the path to the `calls` module to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from calls.vespa import get_paper_by_id, display_paper
#%%
# Apply nested asyncio
nest_asyncio.apply()

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Constants
INPUT_CSV = 'citances.csv'
TEMP_JSON = 'extracted_citances_output.json'
FINAL_JSON = 'extracted_citances_output.json'
CORPUS_IDS_TXT = 'corpus_ids.txt'


async def get_paper_details(paper_id: str) -> dict:
    paper_details = asyncio.run(get_paper_by_id(paper_id))
    output = display_paper(paper_details)
    return output
    #check_full_text_exists  if "contents" in not empty or none then save 

#save the output to a json file if the full text exists
async def check_full_text_exists(ids: list) -> list:
    results = []
    for paper_id in tqdm(ids, desc="Checking full text existence", unit="paper"):
        output = await get_paper_details(paper_id)
        if len(output['contents'])>500:
            output['corpusID'] = paper_id 
            results.append(output)
            
    with open('full_dataset.json', 'w') as f:
        json.dump(results, f, indent=4)



df = pd.read_csv(INPUT_CSV)

# Process the DataFrame to get unique corpus IDs
titles_series = df['corpusId']
titles_df = pd.DataFrame(titles_series, columns=['corpusId'])
title_counts = titles_df['corpusId'].value_counts().reset_index()
title_counts.columns = ['corpusId', 'Count']
titles_gt_20 = title_counts[(title_counts['Count'] > 19) & (title_counts['Count'] < 101)]
filtered_df = df[df['corpusId'].isin(titles_gt_20['corpusId'])]
filtered_df = filtered_df.merge(titles_gt_20, on='corpusId', how='left')
sorted_filtered_df = filtered_df.sort_values(by=['Count', 'corpusId'], ascending=[False, True])
ids_with_counts = sorted_filtered_df[['corpusId', 'Count']].drop_duplicates().values.tolist()

#check wheter the full text exists
ids = [corpus_id for corpus_id, count in ids_with_counts]
results = asyncio.run(check_full_text_exists(ids))
#%%
# Merge results with the original DataFrame
results_df = pd.DataFrame(results)
df_with_full_text = df.merge(results_df[['paper_id', 'full_text_exists']], left_on='corpusId', right_on='paper_id', how='left')

# Replace NaN values in 'full_text_exists' with False
df_with_full_text['full_text_exists'].fillna(False, inplace=True)

# Filter the DataFrame to keep only rows where full text exists
filtered_df_with_full_text = df_with_full_text[df_with_full_text['full_text_exists']]
print(f'Length of dataset is: {len(filtered_df_with_full_text)}')
#%%
# Function to convert results to DataFrame
def results_to_df(results: list) -> pd.DataFrame:
    return pd.DataFrame(results)

# Function to clean and convert a JSON string
def clean_and_convert(json_string: str) -> dict:
    try:
        json_string = json_string.replace('```json', '').replace('```', '').strip()
        json_string = re.sub(r',\s*([\]}])', r'\1', json_string)
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e}\nProblematic JSON string: {json_string}")
        return {}

# Main function to process the data
def main():
    # Read the input CSV file
    df = pd.read_csv(INPUT_CSV)

    # Process the DataFrame to get unique corpus IDs
    titles_series = df['corpusId']
    titles_df = pd.DataFrame(titles_series, columns=['corpusId'])
    title_counts = titles_df['corpusId'].value_counts().reset_index()
    title_counts.columns = ['corpusId', 'Count']
    titles_gt_20 = title_counts[(title_counts['Count'] > 19) & (title_counts['Count'] < 101)]
    filtered_df = df[df['corpusId'].isin(titles_gt_20['corpusId'])]
    filtered_df = filtered_df.merge(titles_gt_20, on='corpusId', how='left')
    sorted_filtered_df = filtered_df.sort_values(by=['Count', 'corpusId'], ascending=[False, True])
    ids_with_counts = sorted_filtered_df[['corpusId', 'Count']].drop_duplicates().values.tolist()

    # Save the list of (corpusId, count) to a txt file
    with open(CORPUS_IDS_TXT, 'w') as f:
        for corpus_id, count in ids_with_counts:
            f.write(f"({corpus_id}, {count})\n")

    # Extract just the IDs for the API call
    ids = [corpus_id for corpus_id, count in ids_with_counts]

    # Fetch paper details and add full text info
    results = asyncio.run(check_full_text_exists(ids))
    results_df = results_to_df(results)

    # Merge results with the original DataFrame
    df_with_full_text = df.merge(results_df[['paper_id', 'full_text_exists']], left_on='corpusId', right_on='paper_id', how='left')

    # Replace NaN values in 'full_text_exists' with False
    df_with_full_text['full_text_exists'].fillna(False, inplace=True)

    # Filter the DataFrame to keep only rows where full text exists
    filtered_df_with_full_text = df_with_full_text[df_with_full_text['full_text_exists']]
    print(f'Length of dataset is: {len(filtered_df_with_full_text)}')

    # Save the filtered DataFrame to a CSV file
    #filtered_df_with_full_text.to_csv(OUTPUT_CSV, index=False)

    # Group by 'corpusId' and prepare the final JSON structure
    grouped = filtered_df_with_full_text.groupby('corpusId')
    result = []

    for corpus_id, group in grouped:
        citances = group[['citance', 'sourceCorpusId', 'paragraphId']].to_dict(orient='records')
        for idx, citance in enumerate(citances):
            citance['citanceId'] = idx + 1
        result.append({'corpusId': corpus_id, 'citances': citances})

    with open(FINAL_JSON, 'w') as f:
        json.dump(result, f, indent=4)

   
if __name__ == "__main__":
    main()

# %%
