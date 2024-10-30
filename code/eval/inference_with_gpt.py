
import json
import os
import argparse
from tqdm import tqdm
#E:\claim_extraction_project\scripts\eval\gpt\turbo_eval_cache_filtered.json E:\claim_extraction_project\scripts\eval\gpt\eval_cache_new_filtered.json" E:\claim_extraction_project\scripts\eval\gpt\weakly_last_eval_cache_filtered.json
#C:\Users\neset\OneDrive\Desktop\claim_extraction\scripts\eval\gpt\new_weakly_eval_cache_filtered.json
def parse_args():
    parser = argparse.ArgumentParser(description="Calculate coverage and precision metrics from cached data with filtering options.")
    parser.add_argument('--cache_file', type=str, default="eval_cache_filtered.json", help="Path to the cache JSON file.")
    parser.add_argument('--output_dir', type=str, default=r"", help="Directory to save the output JSON files.")
    parser.add_argument('--threshold', type=float, default=6, help="Threshold for degree of match (dm_score).")
    parser.add_argument('--c_score_threshold', type=float, default=8, help="Threshold for c_score.")
    # Add arguments for filtering by theme and section
    parser.add_argument('--theme', type=str, nargs='*',help="Themes to include (case-insensitive, e.g., 'Novelty Claims').")
    # Removed default=["abstract"] to prevent unintended filtering
    parser.add_argument('--section', type=str, nargs='*' , help="Sections to include (case-insensitive, e.g., 'Abstract', 'Introduction').")
    return parser.parse_args()


def calculate_metrics_from_cache(
    corpusId,
    data,
    dm_threshold,
    c_score_threshold,
    metric,
    filter_themes=None,
    filter_sections=None
):
    """
    Calculate coverage or precision metrics from cached data with filtering.
    Case-insensitive matching for themes and sections.
    """
    # Convert filter criteria to lowercase
    if filter_themes is not None:
        filter_themes = [theme.lower() for theme in filter_themes]
    if filter_sections is not None:
        filter_sections = [section.lower() for section in filter_sections]

    # Get lists of citances and claims
    list_citances = data['citances']
    list_claims = data['claims']
    list_claim_texts = []

    # Filter claims based on theme and section
    filtered_claims = []
    for idx, claim_data in enumerate(list_claims):
        include_claim = True

        # Convert data strings to lowercase for comparison
        claim_theme = claim_data.get('theme', '').lower()
        claim_section = claim_data.get('section_name', '').lower()

        if filter_themes is not None and claim_theme not in filter_themes:
            include_claim = False

        if filter_sections is not None and claim_section not in filter_sections:
            include_claim = False

        if include_claim:
            filtered_claims.append(claim_data)
            list_claim_texts.append(claim_data['claim'])

    # Update list_claims after filtering
    list_claims = filtered_claims

    if not list_claims:
        print(f"No claims left after filtering for corpus ID {corpusId}. Skipping.")
        return None, 0.0

    # Create a mapping from claim text to index
    claim_text_to_index = {claim['claim']: idx for idx, claim in enumerate(list_claims)}

    # Retrieve the appropriate matches from the cache
    if metric == 'coverage':
        # Use 'citance_to_claims' matches
        matches_data = data['matches']['citance_to_claims']
    elif metric == 'precision':
        # Use 'claim_to_citances' matches
        matches_data = data['matches']['claim_to_citances']
    else:
        raise ValueError(f"Unsupported metric: {metric}")

    matches = []
    matched_indices_citances = set()
    matched_indices_claims = set()

    # To keep track of unique matches based on metric
    unique_matches_set = set()

    # **New Step: Collect citances with potential matches above threshold**
    potential_citances = set()
    for match in matches_data:
        citance_text = match.get('citance')
        claim_data_match = match.get('claim')  # This is a dictionary
        claim_text_match = claim_data_match.get('claim')

        dm_score = match.get('dm_score', 0.0)
        c_score = match.get('c_score', 0.0)

        # Check if claim is in our filtered list
        if claim_text_match not in claim_text_to_index:
            continue  # Skip this match as the claim does not meet the filter criteria

        # **Consider potential matches based on c_score_threshold only**
        if c_score >= c_score_threshold:
            potential_citances.add(citance_text)

    # **Filter list_citances to only include those with potential matches**
    filtered_citances = [cit for cit in list_citances if cit.get('citance') in potential_citances]

    if not filtered_citances:
        print(f"No citances left after filtering for corpus ID {corpusId}. Skipping.")
        return None, 0.0

    # Continue with the matching process, but only with filtered citances
    for match in matches_data:
        citance_text = match.get('citance')
        claim_data_match = match.get('claim')  # This is a dictionary
        claim_text_match = claim_data_match.get('claim')

        dm_score = match.get('dm_score', 0.0)
        c_score = match.get('c_score', 0.0)

        # Check if claim is in our filtered list
        if claim_text_match not in claim_text_to_index:
            continue  # Skip this match as the claim does not meet the filter criteria

        # **Only consider matches where the citance is in filtered_citances**
        if citance_text not in potential_citances:
            continue

        # Apply c_score and dm_score thresholds
        if c_score >= c_score_threshold and dm_score >= dm_threshold:
            # Create a unique identifier for the match
            if metric == 'precision':
                # For precision, ensure each claim is added only once
                match_identifier = claim_text_match  # Unique per claim
            elif metric == 'coverage':
                # For coverage, ensure each citance is added only once
                match_identifier = citance_text  # Unique per citance
            else:
                match_identifier = (citance_text, claim_text_match)  # Include both for safety

            if match_identifier not in unique_matches_set:
                unique_matches_set.add(match_identifier)
                matches.append(match)

                # Find indices in citances and claims lists
                # For citances, match 'citance_text' to the 'citance' field in the citance data
                citance_indices = [idx for idx, cit in enumerate(filtered_citances) if cit.get('citance') == citance_text]
                if citance_indices:
                    idx_citance = citance_indices[0]
                    matched_indices_citances.add(idx_citance)

                idx_claim = claim_text_to_index[claim_text_match]
                matched_indices_claims.add(idx_claim)

    number_of_matches = len(matches)

    # **Update the number of citances after filtering**
    num_citances_after_filtering = len(filtered_citances)

    # Calculate metric based on the metric type
    if metric == 'coverage':
        # Coverage: Proportion of citances that have at least one matching claim
        metric_value = len(matched_indices_citances) / num_citances_after_filtering if num_citances_after_filtering > 0 else 0
    elif metric == 'precision':
        # Precision: Proportion of claims that have at least one matching citance
        metric_value = len(matched_indices_claims) / len(list_claims) if len(list_claims) > 0 else 0

    print(f"Corpus ID {corpusId}")
    print(f"Number of matches: {number_of_matches}")
    print(f"Number of citances after filtering: {num_citances_after_filtering}")
    print(f"{metric.capitalize()}: {metric_value}\n")

    return {
        'number_of_matches': number_of_matches,
        'number_of_citances': num_citances_after_filtering,
        'number_of_claims': len(list_claims),
        'matched_pairs': matches,
        'coverage': len(matched_indices_citances) / num_citances_after_filtering if metric == 'coverage' else 0,
        'precision': len(matched_indices_claims) / len(list_claims) if metric == 'precision' else 0,
    }, metric_value


def main():
    args = parse_args()
    dm_threshold = args.threshold
    c_score_threshold = args.c_score_threshold

    # Retrieve filtering options
    filter_themes = args.theme  # This will be None or a list
    filter_sections = args.section  # This will be None or a list

    # Convert filter criteria to lowercase for case-insensitive matching
    if filter_themes is not None:
        filter_themes = [theme.lower() for theme in filter_themes]
    if filter_sections is not None:
        filter_sections = [section.lower() for section in filter_sections]

    print(f"Filtering by themes: {filter_themes}")
    print(f"Filtering by sections: {filter_sections}")

    # Load cache data
    try:
        with open(args.cache_file, 'r') as f:
            cache_data = json.load(f)
    except Exception as e:
        print(f"Error loading cache JSON file: {e}")
        return

    coverage_outcomes = {}
    precision_outcomes = {}
    coverage_sum = 0.0
    precision_sum = 0.0
    count_coverage = 0
    count_precision = 0

    # Initialize total counts for claims and citances after filtering
    total_claims = 0
    total_citances = 0
    count_corpusIds = 0

    for corpusId, data in tqdm(cache_data.items(), desc="Processing cached corpora"):
        list_citances = data.get('citances', [])
        list_claims = data.get('claims', [])

        if not list_citances or not list_claims:
            print(f"Skipping corpus ID {corpusId} due to empty claims or citances.\n")
            continue

        # We cannot update total_claims and total_citances here because filtering hasn't been applied yet

        # Calculate coverage
        coverage_result = None
        try:
            coverage_result = calculate_metrics_from_cache(
                corpusId,
                data,
                dm_threshold=dm_threshold,
                c_score_threshold=c_score_threshold,
                metric='coverage',
                filter_themes=filter_themes,
                filter_sections=filter_sections
            )
            if coverage_result[0] is not None:
                coverage_data, coverage_value = coverage_result
                coverage_outcomes[corpusId] = coverage_data
                coverage_sum += coverage_value
                count_coverage += 1

                # Update total citances after filtering (citances are not filtered in this script)
                total_citances += coverage_data['number_of_citances']
        except Exception as e:
            print(f"Error calculating coverage for corpus ID {corpusId}: {e}\n")

        # Calculate precision
        precision_result = None
        try:
            precision_result = calculate_metrics_from_cache(
                corpusId,
                data,
                dm_threshold=dm_threshold,
                c_score_threshold=c_score_threshold,
                metric='precision',
                filter_themes=filter_themes,
                filter_sections=filter_sections
            )
            if precision_result[0] is not None:
                precision_data, precision_value = precision_result
                precision_outcomes[corpusId] = precision_data
                precision_sum += precision_value
                count_precision += 1

                # Update total claims after filtering
                total_claims += precision_data['number_of_claims']
                count_corpusIds += 1  # Increment corpus ID count only when precision calculation is successful
        except Exception as e:
            print(f"Error calculating precision for corpus ID {corpusId}: {e}\n")

    # Calculate average claims and citances per corpus ID after filtering
    average_claims_per_corpusId = total_claims / count_corpusIds if count_corpusIds > 0 else 0
    average_citances_per_corpusId = total_citances / count_corpusIds if count_corpusIds > 0 else 0

    # Save coverage outcomes
    base_filename = os.path.splitext(os.path.basename(args.cache_file))[0]
    # Include filtering info in filenames
    filter_info = ''
    if filter_themes:
        filter_info += "_themes_" + "_".join(filter_themes)
    if filter_sections:
        filter_info += "_sections_" + "_".join(filter_sections)
    coverage_detailed_filename = os.path.join(args.output_dir, f'{base_filename}_detailed_coverage_dm_{dm_threshold}_cscore_{c_score_threshold}{filter_info}.json')
    average_coverage = coverage_sum / count_coverage if count_coverage > 0 else 0

    try:
        with open(coverage_detailed_filename, 'w') as f:
            json.dump(coverage_outcomes, f, indent=4)
            print(f"\nCoverage outcomes saved to {coverage_detailed_filename}")
    except Exception as e:
        print(f"Error saving coverage outcomes: {e}")

    # Save precision outcomes
    precision_detailed_filename = os.path.join(args.output_dir, f'{base_filename}_detailed_precision_dm_{dm_threshold}_cscore_{c_score_threshold}{filter_info}.json')
    scores_filename = os.path.join(args.output_dir, f'{base_filename}_scores_dm_{dm_threshold}_cscore_{c_score_threshold}{filter_info}.json')
    average_precision = precision_sum / count_precision if count_precision > 0 else 0

    try:
        with open(precision_detailed_filename, 'w') as f:
            json.dump(precision_outcomes, f, indent=4)
            print(f"Precision outcomes saved to {precision_detailed_filename}")
    except Exception as e:
        print(f"Error saving precision outcomes: {e}")

    # Save average scores including the new average claims and citances per corpus ID
    try:
        with open(scores_filename, 'w') as f:
            json.dump({
                'average_precision': average_precision,
                'average_coverage': average_coverage,
                'average_claims_per_corpusId': average_claims_per_corpusId,
                'average_citances_per_corpusId': average_citances_per_corpusId
            }, f, indent=4)
            print(f"\nAverage scores saved to {scores_filename}\n")
    except Exception as e:
        print(f"Error saving scores: {e}")

if __name__ == "__main__":
    main()