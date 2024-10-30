#%%

import json
import os
import random
import logging
from typing import List, Dict, Any, Optional
import time

import sys

import openai
import json

# List fine-tuning jobs
try:
    fine_tuning_jobs = openai.FineTune.list()
    print(json.dumps(fine_tuning_jobs['data'], indent=1))
except Exception as e:
    print(f"An error occurred: {e}")

#%%
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from prompts.claim_extraction_prompt import prepare_claim_extraction_message


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Loads data from the given JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return []

def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Processes raw data into the required format."""
    new_data = []
    for item in data:
        new_item = {
            "title": item.get('title', ''),
            "abstract": item.get('abstract', ''),
            "contents": item.get('contents', ''),
            "citances": [
                {
                    "claim": citance.get('citance', ''),
                    "section": citance.get('section', ''),
                    "theme": citance.get('theme', ''),
                    "contents": citance.get('context', '')
                }
                for citance in item.get('citances', [])
            ]
        }
        new_data.append(new_item)
    return new_data

def print_citance_info(new_data: List[Dict[str, Any]]):
    """Prints the number of citances for each paper."""
    for item in new_data:
        logging.info(f"Title: {item['title']}, Contents Length: {len(item['contents'])}, Number of Claims: {len(item['claims'])}")

def prepare_message(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Prepares a single message for fine-tuning."""
    message = prepare_claim_extraction_message(
        title=entry['title'],
        abstract=entry['abstract'],
        body=entry['contents'],
        response=entry['claims']
    )
    return message

def generate_message_set(new_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generates a message set for fine-tuning."""
    message_set = []
    for entry in new_data:
        try:
            message = prepare_message(entry)
            message_set.append(message)
        except Exception as e:
            logging.error(f"Error processing entry '{entry['title']}': {e}")
    return message_set

def split_data(dataset: List[Dict[str, Any]], train_ratio: float = 0.99) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
    """Splits the dataset into training and testing sets."""
    total_items = len(dataset)
    train_size = int(train_ratio * total_items)
    random.seed(42)  # For reproducibility
    train_set = random.sample(dataset, train_size)
    test_set = [item for item in dataset if item not in train_set]
    return train_set, test_set

def write_jsonl(filename: str, data: List[Dict[str, Any]]):
    """Writes data to a JSONL file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

def main():
    logging.basicConfig(level=logging.INFO)

    # Adjust the data file path as needed
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_filepath = os.path.join(script_dir, 'data', 'processed_data', 'fine/tune_data.json')

    data = load_data(data_filepath)
    if not data:
        logging.error("No data loaded. Exiting.")
        return

    #new_data = process_data(data)
    new_data = data
    print_citance_info(new_data)
    message_set = generate_message_set(new_data)
    train_set, test_set = split_data(message_set)

    # Write the train and test sets to JSONL files
    write_jsonl('train_set_for_ext.jsonl', train_set)
    write_jsonl('test_set_for_ext.jsonl', test_set)

    # Set your OpenAI API key as an environment variable or replace 'your-api-key' with your actual key
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')  # Ensure your API key is set

    # Upload files using the new API methods (compatible with openai>=1.0.0)
    try:
        logging.info("Uploading training file...")
        training_response = openai.File.create(
            file=open('train_set_for_ext.jsonl', 'rb'),
            purpose='fine-tune'
        )
        training_file_id = training_response['id']
        logging.info(f"Training file uploaded: {training_file_id}")

        logging.info("Uploading validation file...")
        validation_response = openai.File.create(
            file=open('test_set_for_ext.jsonl', 'rb'),
            purpose='fine-tune'
        )
        validation_file_id = validation_response['id']
        logging.info(f"Validation file uploaded: {validation_file_id}")
    except Exception as e:
        logging.error(f"Failed to upload files: {e}")
        return

    # Create fine-tuning job using the new API
    try:
        logging.info("Creating fine-tuning job...")
        fine_tune_response = openai.FineTuningJob.create(
            training_file=training_file_id,
            validation_file=validation_file_id,
            model='gpt-4o-2024-08-06',  # Replace with the model you want to fine-tune
            suffix='claim-extraction-v3'
        )
        job_id = fine_tune_response['id']
        logging.info(f"Fine-tuning job created: {job_id}")
    except Exception as e:
        logging.error(f"Failed to create fine-tuning job: {e}")
        return

    # Monitor the fine-tuning job
    try:
        logging.info(f"Monitoring fine-tuning job {job_id}...")
        while True:
            status_response = openai.FineTuningJob.retrieve(job_id)
            status = status_response['status']
            logging.info(f"Job status: {status}")
            if status in ['succeeded', 'failed', 'cancelled']:
                break
            time.sleep(30)  # Wait before checking again

        if status == 'succeeded':
            fine_tuned_model = status_response['fine_tuned_model']
            logging.info(f"Fine-tuning job {job_id} succeeded. Fine-tuned model: {fine_tuned_model}")
        else:
            logging.error(f"Fine-tuning job {job_id} ended with status: {status}")
    except Exception as e:
        logging.error(f"Error while monitoring the fine-tuning job: {e}")

if __name__ == '__main__':
    main()
# %%

