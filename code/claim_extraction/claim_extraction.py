
import os
import json
import asyncio
import re
import tqdm  # For progress bar
import logging
import sys
import nest_asyncio
import demjson3 as demjson  # For tolerant JSON parsing
import aiohttp  # Import aiohttp for asynchronous HTTP requests
import time
nest_asyncio.apply()

# Configure logging to show debug messages as well
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Append the parent directory to the system path for imports (adjust the path as needed)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import custom modules

from prompts.claim_extraction_prompt import prepare_claim_extraction_message

model="fine_tuned_model"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 


# Define headers for API requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

async def completion(content, session, model=model, temperature=0.0):
       start_time = time.perf_counter()
       
       # Define headers within the function
       headers = {
           "Content-Type": "application/json",
           "Authorization": f"Bearer {OPENAI_API_KEY}"
       }
   
       # content is already a dictionary, so use it directly
       message_data = content
       messages = message_data.get("messages", [])
   
       # Prepare the messages for the API
       api_messages = []
       for message in messages:
           role = message.get("role")
           content_value = message.get("content", "")
           # Ensure the content is a string
           if isinstance(content_value, str):
               content_text = content_value
           else:
               # Serialize content to a JSON-formatted string if it's a dictionary
               content_text = json.dumps(content_value, ensure_ascii=False)
           api_messages.append({"role": role, "content": content_text})
   
       # Make a POST request to OpenAI's API for text completion
       async with session.post(
           "https://api.openai.com/v1/chat/completions",
           headers=headers,
           json={
               "model": model,
               "messages": api_messages,
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


# Paths to your data files
full_data = 'full_dataset.json'
FINAL_JSON = 'weakly_supervised_extracted_claims.json'

# Ensure OPENAI_API_KEY is defined
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set.")
    sys.exit(1)

# Function to clean and convert JSON strings using a tolerant parser
def clean_and_convert(json_string):
    """
    Cleans and converts a JSON string using demjson3, with a fallback to regex extraction.
    """
    # Remove code block markers and extra annotations
    json_string = json_string.strip().strip('```json').strip('```').strip()
    try:
        # Attempt to parse using demjson
        return demjson.decode(json_string)
    except demjson.JSONDecodeError as e:
        logger.error(f"demjson.JSONDecodeError: {e}")
        logger.warning("Attempting to extract data using regex.")
        # Fallback to regex extraction
        return extract_claims_with_regex(json_string)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return []

# Function to extract claims using regex as a fallback
def extract_claims_with_regex(json_string):
    """
    Extracts claims, sections, contexts, and themes from the given string using regular expressions.
    """
    claims_list = []
    try:
        # Remove code block markers and extra annotations
        clean_string = json_string.strip().strip('```json').strip('```').strip()

        # Regex pattern to find claim objects
        claim_pattern = re.compile(r'\{(.*?)\}', re.DOTALL)
        for claim_match in claim_pattern.finditer(clean_string):
            claim_text = claim_match.group(1)
            # Extract 'claim', 'section', 'context', and 'theme'
            claim_field = re.search(r'"claim"\s*:\s*"([^"]*?)"', claim_text)
            section_field = re.search(r'"section"\s*:\s*"([^"]*?)"', claim_text)
            context_field = re.search(r'"context"\s*:\s*"([^"]*?)"', claim_text)
            theme_field = re.search(r'"theme"\s*:\s*"([^"]*?)"', claim_text)
            claim_value = claim_field.group(1) if claim_field else ""
            section_value = section_field.group(1) if section_field else ""
            context_value = context_field.group(1) if context_field else ""
            theme_value = theme_field.group(1) if theme_field else ""
            claims_list.append({
                'claim': claim_value,
                'section': section_value,
                'context': context_value,
                'theme': theme_value
            })
    except Exception as e:
        logger.error(f"Error extracting claims with regex: {e}")
    return claims_list


# Function to extract claims from a paper
async def extract_claims_from_paper(title: str, abstract: str, contents: str, session) -> list:
    prompt = prepare_claim_extraction_message(title, abstract, contents)
    try:
        result = await completion(prompt, session,model=model)
        logger.debug(f"Raw model output: {result}")
        # Extract the assistant's message content
        if isinstance(result, dict):
            if 'choices' in result and len(result['choices']) > 0:
                assistant_reply = result['choices'][0]['message']['content']
            else:
                logger.error(f"Unexpected response format: {result}")
                assistant_reply = str(result)
        else:
            assistant_reply = str(result)
        # Now pass the assistant's reply to clean_and_convert
        result = clean_and_convert(assistant_reply)
        return result  # Now returns a list
    except Exception as e:
        logger.error(f"Error extracting claims: {e}")
        return []

# Function to retry claim extraction with multiple attempts
async def retry_extract_claims_from_paper(title: str, abstract: str, contents: str, session, retries: int = 10) -> list:
    for attempt in range(retries):
        result = await extract_claims_from_paper(title, abstract, contents, session)
        if result and isinstance(result, list):  # Check if the result is not empty and is a list
            return result
        logger.warning(f"Attempt {attempt + 1} failed, retrying...")
        await asyncio.sleep(1)  # Add delay between retries
    logger.error("Failed to extract claims after multiple attempts.")
    return []

# Function to create a list of claims with IDs
def create_claims_list(claims, starting_id):
    return [
        {
            "claim": claim.get('claim', ''),
            "section": claim.get('section_name', ''),  # Updated field name
            "context": claim.get('context', ''),
            "id": str(starting_id + i),
            "theme": claim.get('theme', '')
        }
        for i, claim in enumerate(claims)
    ]

# Function to read existing corpus IDs from the output file
def read_existing_corpus_ids(output_file: str):
    if not os.path.exists(output_file):
        return set()

    with open(output_file, "r") as f:
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.error("Error decoding JSON from the output file.")
            return set()

    return {item.get("corpusid") for item in existing_data if "corpusid" in item}

# Updated display_paper_details function with error handling
def display_paper_details(json_file_path):
    paper_details = []
    all_corpus_ids = []

    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            # Try to load the entire JSON file
            json_file = json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError while loading file: {e}")
        logger.info("Attempting to load JSON line by line.")
        # Attempt to read JSON objects line by line
        with open(json_file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    corpus_id = item.get("corpusID") or item.get("corpusId")
                    if corpus_id is not None:
                        corpus_id = int(corpus_id)
                        all_corpus_ids.append(corpus_id)
                        paper_details.append({
                            "corpusId": corpus_id,
                            "title": str(item.get("title")),
                            "field": str(item.get("fields")),
                            "year": str(item.get("year")),
                            "abstract": str(item.get("abstract")),
                            "contents": str(item.get("contents"))
                        })
                except json.JSONDecodeError as e_line:
                    logger.error(f"JSONDecodeError at line {line_num}: {e_line}")
                    logger.error(f"Problematic line: {line}")
                except Exception as e_line:
                    logger.error(f"Unexpected error at line {line_num}: {e_line}")
                    logger.error(f"Problematic line: {line}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading the JSON file: {e}")
    else:
        # JSON loaded successfully
        for item in json_file:
            corpus_id = item.get("corpusID") or item.get("corpusId")
            if corpus_id is not None:
                corpus_id = int(corpus_id)
                all_corpus_ids.append(corpus_id)
                paper_details.append({
                    "corpusId": corpus_id,
                    "title": str(item.get("title")),
                    "field": str(item.get("fields")),
                    "year": str(item.get("year")),
                    "abstract": str(item.get("abstract")),
                    "contents": str(item.get("contents"))
                })

    # Log all corpus IDs loaded from the dataset for debugging
    logger.debug(f"Available Corpus IDs in dataset: {all_corpus_ids}")

    return paper_details

# Function to process a batch of papers asynchronously
async def process_papers_batch(paper_ids: list, output_file: str, semaphore, session, checkpoint_interval: int = 20, pbar=None):
    # Load all paper details once (move this outside the function to avoid reloading for each batch)
    papers_info = display_paper_details(full_data)

    async def process_single_paper(paper_id):
        async with semaphore:  # Ensuring semaphore limit is applied correctly
            try:
                # Find the paper with the matching corpusId
                paper_info = next((paper for paper in papers_info if paper["corpusId"] == paper_id), None)
                if not paper_info:
                    logger.warning(f"Paper ID {paper_id} not found in dataset.")
                    return None

                # Provide title, abstract, and contents explicitly
                title = paper_info["title"]
                abstract = paper_info["abstract"]
                contents = paper_info["contents"]

                # Extract claims
                claims = await retry_extract_claims_from_paper(title, abstract, contents, session)

                if not claims:
                    logger.warning(f"No claims extracted for Paper ID {paper_id}.")
                    return None

                starting_id = 1
                claims_list = create_claims_list(claims, starting_id)

                paper_output = {
                    "corpusid": paper_id,
                    "claims": claims_list
                }

                return paper_output  # Return the result

            except Exception as e:
                logger.error(f"An error occurred while processing paper ID {paper_id}: {e}")
                return None
            finally:
                if pbar is not None:
                    pbar.update(1)

    tasks = [process_single_paper(paper_id) for paper_id in paper_ids]
    # Run tasks concurrently
    results = await asyncio.gather(*tasks)
    # Collect non-None results
    final_output = [result for result in results if result is not None]

    # Checkpointing
    if len(final_output) > 0 and len(final_output) % checkpoint_interval == 0:
        checkpoint_file = output_file + ".checkpoint"
        with open(checkpoint_file, "w") as f:
            json.dump(final_output, f, indent=4)

    return final_output

# Function to process all papers
async def process_papers(paper_ids: list, output_file: str, checkpoint_interval: int = 20, batch_size: int = 1224):
    semaphore = asyncio.Semaphore(value=80)  # Limit to 80 concurrent requests
    final_output = []
    total_papers = len(paper_ids)
    pbar = tqdm.tqdm(total=total_papers, desc="Processing all Papers")

    async with aiohttp.ClientSession() as session:
        for i in range(0, total_papers, batch_size):
            batch = paper_ids[i:i + batch_size]
            batch_output = await process_papers_batch(batch, output_file, semaphore, session, checkpoint_interval, pbar)
            final_output.extend(batch_output)

    pbar.close()

    # Save final output to JSON file
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                logger.error("Error decoding JSON from the output file.")
                existing_data = []
        existing_data.extend(final_output)
    else:
        existing_data = final_output

    with open(output_file, "w") as f:
        json.dump(existing_data, f, indent=4)

    # Remove the checkpoint file
    checkpoint_file = output_file + ".checkpoint"
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

# Main execution
if __name__ == "__main__":
    # Get paper details
    all_papers = display_paper_details(full_data)
    if not all_papers:
        logger.error("No papers available to process.")
        sys.exit(1)  # Exit if there are no papers

    paper_ids = [item.get("corpusId") for item in all_papers]

    # Remove None values
    paper_ids = [pid for pid in paper_ids if pid is not None]

    # Read existing corpus IDs to avoid reprocessing
    existing_corpus_ids = read_existing_corpus_ids(FINAL_JSON)
    paper_ids_to_process = [pid for pid in paper_ids if pid not in existing_corpus_ids]

    if not paper_ids_to_process:
        logger.info("All papers have been processed already.")
    else:
        asyncio.run(process_papers(paper_ids_to_process, FINAL_JSON))  # Process all papers