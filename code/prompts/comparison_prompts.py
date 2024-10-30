def citance_to_claims_prompt(citances_claims_batch):
    instruction = """For each citance provided (citation sentences in other papers), evaluate how accurately each claim represents the citance by assigning a degree of match (0-10).

 Respond **only** in JSON format without any additional text or code fences:

{
    "citance_to_claims": [
        {
            "citance": "...",
            "matches": [
                {"claim": "...", "dm": ...},
                ...
            ]
        },
        ...
    ]
}
"""

    batch_text = "\n".join([
        f"Citance {idx+1}:\nCitance: {item['citance']}\nClaims: {item['claims']}\n"
        for idx, item in enumerate(citances_claims_batch)
    ])

    prompt = instruction + "\n\n" + batch_text
    return prompt






def claim_to_citances_prompt(claims_citances_batch):
    instruction = """For each claim provided, evaluate how accurately each citance (citation sentences in other papers) represents the claim by assigning a degree of match (0-10).

 Respond **only** in JSON format without any additional text or code fences:

{
    "claim_to_citances": [
        {
            "claim": "...",
            "matches": [
                {"citance": "...", "dm": ...},
                ...
            ]
        },
        ...
    ]
}
"""

    batch_text = "\n".join([
        f"Claim {idx+1}:\nClaim: {item['claim']}\nCitances: {item['citances']}\n"
        for idx, item in enumerate(claims_citances_batch)
    ])

    prompt = instruction + "\n\n" + batch_text
    return prompt