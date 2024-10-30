
import json
import os
import argparse
import asyncio
import time
from tqdm import tqdm
import sys
import re
import aiohttp


# Append the parent directory to the system path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


from prompts.comparison_prompts import claim_to_citances_prompt, citance_to_claims_prompt

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def parse_args():
    parser = argparse.ArgumentParser(description="Collect matches between claims and citances using OpenAI API.")
    parser.add_argument('--citances', type=str, default="test_citances.json", help="Path to the citances JSON file.")
    parser.add_argument('--claims', type=str, default="extarcted_claims", help="Path to the claims JSON file.")
    parser.add_argument('--output_dir', type=str, default=".", help="Directory to save the output JSON files.")
    parser.add_argument('--openai_api_key', type=str, default=OPENAI_API_KEY, help="OpenAI API key.")
    parser.add_argument('--batch_size', type=int, default=5, help="Number of items per batch to send to OpenAI API.")
    parser.add_argument('--max_concurrent_requests', type=int, default=200, help="Maximum number of concurrent API requests.")
    return parser.parse_args()




async def get_one_completion_async(prompt, session, api_key, model, temperature=0.0):
    start_time = time.perf_counter()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    async with session.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
    ) as resp:
        if resp.status != 200:
            response_text = await resp.text()
            raise Exception(f"API call failed with status {resp.status}: {response_text}")
        response_json = await resp.json()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Request took {elapsed_time:.2f} seconds.")
    return response_json["choices"][0]['message']["content"]


def sanitize_response(response_text):
    # Remove code fences and language specifiers
    response_text = response_text.strip()
    response_text = re.sub(r'^```[a-zA-Z]*\n', '', response_text)
    response_text = re.sub(r'\n```$', '', response_text)
    return response_text

def extract_claims_citances(data_citances, data_claims):
    """
    Extract claims and citances grouped by corpusId.
    """
    claims_citances = {}
    # Create a mapping from corpusId to claims
    claims_dict = {}
    for item in data_claims:
        corpusId = str(item.get('corpusId') or item.get('corpusid'))
        claims = item.get('claims', [])
        claims_dict[corpusId] = claims

    # Iterate over citances and associate with claims
    for item in data_citances:
        corpusId = str(item.get('corpusId') or item.get('paper_id'))
        citances = item.get('citances', [])
        claims = claims_dict.get(corpusId, [])
        if claims and citances:
            claims_citances[corpusId] = {'claims': claims, 'citances': citances}

    return claims_citances


async def limited_get_one_completion(prompt, session, sem, api_key, model, temperature=0.0):
    async with sem:
        return await get_one_completion_async(prompt, session, api_key, model, temperature)

async def collect_citance_to_claims_matches(
    corpusId,
    list_citances,
    list_claims,
    batch_size,
    session,
    sem,
    api_key,
    model
):
    """
    Collect matches from citances to claims.
    """
    all_matches = []
    claim_text_to_data = {claim_data['claim']: claim_data for claim_data in list_claims}
    list_claim_texts = [claim_data['claim'] for claim_data in list_claims]

    tasks = []
    citance_scores = {}  # To hold citance and their scores for mapping later
    for citance in list_citances:
        citance_text = citance['citance']
        citance_scores[citance_text] = citance['score']

    for i in range(0, len(list_citances), batch_size):
        batch_citances = list_citances[i:i + batch_size]
        citances_claims_batch = [{'citance': citance['citance'], 'claims': list_claim_texts} for citance in batch_citances]
        prompt = citance_to_claims_prompt(citances_claims_batch)
        task = limited_get_one_completion(prompt, session, sem, api_key, model)
        tasks.append(task)

    # Process tasks concurrently
    responses = await asyncio.gather(*tasks)

    # Process responses
    for response_text in responses:
        if response_text is None:
            continue
        sanitized_response = sanitize_response(response_text)
        try:
            response_data = json.loads(sanitized_response)
            citance_matches_list = response_data.get('citance_to_claims', [])

            for citance_match in citance_matches_list:
                citance_text = citance_match.get('citance')
                # We get citance_score from our pre-stored dictionary
                citance_score = citance_scores.get(citance_text)

                matches = citance_match.get('matches', [])
                for match in matches:
                    claim_text = match.get('claim')
                    dm = float(match.get('dm', 0))
                    claim_data = claim_text_to_data.get(claim_text, {'claim': claim_text})
                    all_matches.append({
                        'citance': citance_text,
                        'claim': claim_data,
                        'c_score': citance_score,
                        'dm_score': dm
                    })
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {e}")
            continue
    return all_matches

async def collect_claim_to_citances_matches(
    corpusId,
    list_citances,
    list_claims,
    batch_size,
    session,
    sem,
    api_key,
    model
):
    """
    Collect matches from claims to citances.
    """
    all_matches = []
    claim_text_to_data = {claim_data['claim']: claim_data for claim_data in list_claims}
    list_citance_texts = [citance['citance'] for citance in list_citances]
    citance_scores = {citance['citance']: citance['score'] for citance in list_citances}

    tasks = []
    for i in range(0, len(list_claims), batch_size):
        batch_claims_data = list_claims[i:i + batch_size]
        batch_claims_texts = [claim_data['claim'] for claim_data in batch_claims_data]
        claims_citances_batch = [{'claim': claim_text, 'citances': list_citance_texts} for claim_text in batch_claims_texts]
        prompt = claim_to_citances_prompt(claims_citances_batch)
        task = limited_get_one_completion(prompt, session, sem, api_key, model)
        tasks.append(task)

    # Process tasks concurrently
    responses = await asyncio.gather(*tasks)

    # Process responses
    for response_text in responses:
        if response_text is None:
            continue
        sanitized_response = sanitize_response(response_text)
        try:
            response_data = json.loads(sanitized_response)
            claim_matches_list = response_data.get('claim_to_citances', [])

            for claim_match in claim_matches_list:
                claim_text = claim_match.get('claim')
                matches = claim_match.get('matches', [])
                for match in matches:
                    citance_text = match.get('citance')
                    citance_score = citance_scores.get(citance_text)
                    dm = float(match.get('dm', 0))
                    claim_data = claim_text_to_data.get(claim_text, {'claim': claim_text})
                    all_matches.append({
                        'claim': claim_data,
                        'citance': citance_text,
                        'c_score': citance_score,
                        'dm_score': dm
                    })
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {e}")
            continue
    return all_matches

async def process_corpus(corpusId, list_citances, list_claims, args, session, sem, api_key, model):
    """
    Process a single corpus: collect matches from citances to claims and from claims to citances.
    """
    # Create tasks for both functions
    task1 = collect_citance_to_claims_matches(
        corpusId,
        list_citances,
        list_claims,
        batch_size=args.batch_size,
        session=session,
        sem=sem,
        api_key=api_key,
        model=model
    )

    task2 = collect_claim_to_citances_matches(
        corpusId,
        list_citances,
        list_claims,
        batch_size=args.batch_size,
        session=session,
        sem=sem,
        api_key=api_key,
        model=model
    )

    # Run tasks concurrently
    citance_to_claims_matches, claim_to_citances_matches = await asyncio.gather(task1, task2)

    corpus_data = {
        'citances': list_citances,
        'claims': list_claims,
        'matches': {
            'citance_to_claims': citance_to_claims_matches,
            'claim_to_citances': claim_to_citances_matches
        }
    }

    return corpusId, corpus_data

async def main():
    args = parse_args()
    api_key = args.openai_api_key
    model =  "gpt-4o"
    if not api_key:
        print("OpenAI API key not provided.")
        return

    # Load citances and claims data
    try:
        with open(args.citances, 'r') as f1, open(args.claims, 'r') as f2:
            data_citances = json.load(f1)
            data_claims = json.load(f2)
    except Exception as e:
        print(f"Error loading JSON files: {e}")
        return

    # Extract claims and citances grouped by corpusId
    claims_citances = extract_claims_citances(data_citances, data_claims)

    if not claims_citances:
        print("No valid claims and citances found for evaluation.")
        return

    cache_data = {}

    # Initialize semaphore and session
    sem = asyncio.Semaphore(args.max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        # Create tasks for each corpusId
        tasks = []
        for corpusId, data in claims_citances.items():
            list_citances = data['citances']
            list_claims = data['claims']

            if not list_citances or not list_claims:
                print(f"Skipping corpus ID {corpusId} due to empty claims or citances.\n")
                continue

            task = process_corpus(corpusId, list_citances, list_claims, args, session, sem, api_key, model)
            tasks.append(task)

        # Process tasks concurrently with a progress bar
        total_tasks = len(tasks)

        # Create an iterator over futures
        futures_iterator = asyncio.as_completed(tasks)

        # Wrap the iterator with tqdm for progress bar
        for future in tqdm(futures_iterator, total=total_tasks, desc="Processing paper IDs"):
            try:
                corpusId, corpus_data = await future
                cache_data[corpusId] = corpus_data
            except Exception as e:
                print(f"Error processing corpus: {e}")

        # Save combined results
        output_dir = args.output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        cache_filename = os.path.join(output_dir, 'eval_cache_filtered.json')
        try:
            with open(cache_filename, 'w') as f:
                json.dump(cache_data, f, indent=4)
            print(f"\nCombined cache data saved to {cache_filename}")
        except Exception as e:
            print(f"Error saving combined cache data: {e}")

if __name__ == "__main__":
    asyncio.run(main())