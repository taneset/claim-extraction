# #%%
import json
from typing import List, Dict, Any, Optional

def prepare_claim_extraction_message(
    title: str,
    abstract: str,
    body: str,
    response: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Prepares a message structure for claim extraction from a paper.
    
    Args:
        title (str): The title of the paper.
        abstract (str): The abstract of the paper.
        body (str): The body content of the paper.
        response (List[Dict[str, Any]], optional): The assistant's response, if available.

    Returns:
        Dict[str, Any]: The structured message ready for JSON serialization or processing.
    """
    # System instructions
    system_instruction = """
Your main task is to extract the novel main findings of the paper. Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.

IMPORTANT: Note that a claim is described in the following ways:
- A statement that declares something is better;
- A statement that proposes something new;
- A statement that describes a new finding or a new cause-effect relationship.

1. Novelty Claims
Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
Examples:
- Proposing a new algorithm for data compression.
- Introducing a novel framework for distributed computing.
Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

2. Performance Claims
Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
Examples:
- Demonstrating that an algorithm runs faster than existing alternatives.
- Showing that a model achieves higher accuracy on benchmark datasets.
Validation: Supported by empirical results, benchmarks, or performance comparisons.

3. Applicability Claims
Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
Examples:
- Asserting that a security protocol is effective for IoT devices.
- Demonstrating that a machine learning model can be applied to healthcare diagnostics.
Validation: Validated through case studies, domain-specific applications, or practical implementations.

4. Background Claims
Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
Examples:
- Referencing a well-known algorithm to explain the foundation of the current approach.
- Citing previous studies to justify the need for new research in a particular area.
- Discussing existing theories or models that the current study builds upon or challenges.
Validation: Typically validated by citing credible sources, existing literature, or previous research findings.

Please extract the claims from the provided paper's content and present them in the following JSON format:

[
  {
    "claim": "...",  // The core finding; self-contained, atomic, verifiable
    "section_name": "...",  // Section name from which the claim was extracted
    "context": "...",  // Brief context or explanation for the claim
    "theme": "..."     // The category of the claim: 'Novelty', 'Performance', 'Applicability', or 'Background'
  },
  {
    "claim": "...",
    "section_name": "...",
    "context": "...",
    "theme": "..."
  },
  ...
]

Notes:
- Do not assign "content" as the section name. Find the actual section name from the paper.
- The "theme" field should be one of the following values: 'Novelty', 'Performance', 'Applicability', or 'Background', corresponding to the claim categories defined above.
- Ensure that each claim is clear and understandable on its own.
- You can even generate claims from the title even it is not a sentence!
- DO NOT generate more than 15 claims, but feel free to generate fewer!
"""

    # Construct the messages
    messages = [
        {
            "role": "system",
            "content": system_instruction.strip()
        },
        {
            "role": "user",
            "content": json.dumps({
                "title": title,
                "abstract": abstract,
                "content": body
            }, ensure_ascii=False)
        }
    ]

    # Add the assistant's response if provided
    if response is not None:
        messages.append({
            "role": "assistant",
            "content": json.dumps(response, ensure_ascii=False)
        })

    # Prepare the full message structure
    message = {"messages": messages}

    # Return the message as a Python dictionary
    return message

# #%%
# def make_claim_extraction_from_paper_query(title: str,abstract:str, body:str) -> str:
   
  
#     instruction="""Can you extract claims from the following computer science paper? Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.
    
#     You do NOT have to fill in all of these categories. Your main task is to extract the novel main findings of the paper (focus primarily on this).

#     IMPORTANT: Give your main focus to the follwing sections:
#      - title, (Even it is not sentence you infrence the main findings from the title)
#      - abstract,
#      - introducton, 
#     these are well-known for providing the main findings of the paper.

#     Note that a claim is described in the following ways:
#     - A statement that declares something is better;
#     - A statement that proposes something new;
#     - A statement that describes a new finding or a new cause-effect relationship.

# 1. Novelty Claims
# Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
# Examples:
# Proposing a new algorithm for data compression.
# Introducing a novel framework for distributed computing.
# Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

# 2. Performance Claims
# Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
# Examples:
# Demonstrating that an algorithm runs faster than existing alternatives.
# Showing that a model achieves higher accuracy on benchmark datasets.
# Validation: Supported by empirical results, benchmarks, or performance comparisons.

# 3. Applicability Claims
# Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
# Examples:
# Asserting that a security protocol is effective for IoT devices.
# Demonstrating that a machine learning model can be applied to healthcare diagnostics.
# Validation: Validated through case studies, domain-specific applications, or practical implementations.

# 4. Background Claims
# Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
# Examples:
# Referencing a well-known algorithm to explain the foundation of the current approach.
# Citing previous studies to justify the need for new research in a particular area.
# Discussing existing theories or models that the current study builds upon or challenges.
# Validation: Typically validated by citing credible sources, existing literature, or previous research findings.




# {
# "Novelty Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# },

# "Performance Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# },

# "Applicability Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" findthe paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# },


# "Background Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# }
# ]
# },

# }


# """

#     prompt= instruction+ f'/n title: {title} /n abstract: {abstract} /n body: {body}'


#     return prompt


# #%% alternative version
# # def make_claim_extraction_from_paper_query(title: str,abstract:str, body:str) -> str:
   
  
# #     instruction="""Can you extract claims from the following computer science paper? Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.
    
# #     You do NOT have to fill in all of these categories. Your main task is to extract the novel main findings of the paper (focus primarily on this).

# #     IMPORTANT: Give your main focus to the follwing sections:
# #      - title (Even it is not sentence you infrence the main claim from the title), 
# #      - abstract,
# #      - introducton, 
# #     these are well-known for providing the main findings of the paper. Generate 5-10 claims from each of these sections. If you can not find any claims from these sections, you can look at the rest of the paper.

# #     Note that a claim is described in the following ways:
# #     - A statement that declares something is better;
# #     - A statement that proposes something new;
# #     - A statement that describes a new finding or a new cause-effect relationship.

# # 1. Novelty Claims
# # Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
# # Examples:
# # Proposing a new algorithm for data compression.
# # Introducing a novel framework for distributed computing.
# # Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

# # 2. Performance Claims
# # Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
# # Examples:
# # Demonstrating that an algorithm runs faster than existing alternatives.
# # Showing that a model achieves higher accuracy on benchmark datasets.
# # Validation: Supported by empirical results, benchmarks, or performance comparisons.

# # 3. Applicability Claims
# # Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
# # Examples:
# # Asserting that a security protocol is effective for IoT devices.
# # Demonstrating that a machine learning model can be applied to healthcare diagnostics.
# # Validation: Validated through case studies, domain-specific applications, or practical implementations.

# # 4. Background Claims
# # Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
# # Examples:
# # Referencing a well-known algorithm to explain the foundation of the current approach.
# # Citing previous studies to justify the need for new research in a particular area.
# # Discussing existing theories or models that the current study builds upon or challenges.
# # Validation: Typically validated by citing credible sources, existing literature, or previous research findings.




# # {
# # "Novelty Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name)
# # },
# # {"claim":"...",
# # "section":"..."}
# # ]
# # },

# # "Performance Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# # "context of the claim":"..."(provide a brief context or explanation for the claim, if needed)
# # },
# # {"claim":"...",
# # "section":"..."
# # }
# # ]
# # },

# # "Applicability Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" findthe paper's section name),
# # },
# # {"claim":"...",
# # "section":"..."
# # }
# # ]
# # },


# # "Background Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name)

# # },
# # {"claim":"...",
# # "section":"..."
# # }
# # ]
# # }
# # ]
# # },

# # }


# # """

# #     prompt= instruction+ f'/n title: {title} /n abstract: {abstract} /n body: {body}'


# #     return prompt
# #%%

# #%%
# def make_claim_extraction_from_paper_query(title: str,abstract:str, body:str) -> str:
   
  
#     instruction="""Can you extract claims from the following computer science paper? Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.
    
#     You do NOT have to fill in all of these categories. Your main task is to extract the novel main findings of the paper (focus primarily on this).

#     IMPORTANT: Give your main focus to the follwing sections:
#      - title, (Even it is not sentence you infrence the main findings from the title)
#      - abstract,
#      - introducton, 
#     these are well-known for providing the main findings of the paper.

#     Note that a claim is described in the following ways:
#     - A statement that declares something is better;
#     - A statement that proposes something new;
#     - A statement that describes a new finding or a new cause-effect relationship.

# 1. Novelty Claims
# Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
# Examples:
# Proposing a new algorithm for data compression.
# Introducing a novel framework for distributed computing.
# Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

# 2. Performance Claims
# Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
# Examples:
# Demonstrating that an algorithm runs faster than existing alternatives.
# Showing that a model achieves higher accuracy on benchmark datasets.
# Validation: Supported by empirical results, benchmarks, or performance comparisons.

# 3. Applicability Claims
# Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
# Examples:
# Asserting that a security protocol is effective for IoT devices.
# Demonstrating that a machine learning model can be applied to healthcare diagnostics.
# Validation: Validated through case studies, domain-specific applications, or practical implementations.

# 4. Background Claims
# Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
# Examples:
# Referencing a well-known algorithm to explain the foundation of the current approach.
# Citing previous studies to justify the need for new research in a particular area.
# Discussing existing theories or models that the current study builds upon or challenges.
# Validation: Typically validated by citing credible sources, existing literature, or previous research findings.




# {
# "Novelty Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# },

# "Performance Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# },

# "Applicability Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" findthe paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# },


# "Background Claims":
# [
# {
# "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# "context":"..."(provide a brief context or explanation for the claim, if needed)
# },
# {"claim":"...",
# "section":"...",
# "context":"..."}
# ]
# }
# ]
# },

# }


# """

#     prompt= instruction+ f'/n title: {title} /n abstract: {abstract} /n body: {body}'


#     return prompt


# #%% alternative version
# # def make_claim_extraction_from_paper_query(title: str,abstract:str, body:str) -> str:
   
  
# #     instruction="""Can you extract claims from the following computer science paper? Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.
    
# #     You do NOT have to fill in all of these categories. Your main task is to extract the novel main findings of the paper (focus primarily on this).

# #     IMPORTANT: Give your main focus to the follwing sections:
# #      - title (Even it is not sentence you infrence the main claim from the title), 
# #      - abstract,
# #      - introducton, 
# #     these are well-known for providing the main findings of the paper. Generate 5-10 claims from each of these sections. If you can not find any claims from these sections, you can look at the rest of the paper.

# #     Note that a claim is described in the following ways:
# #     - A statement that declares something is better;
# #     - A statement that proposes something new;
# #     - A statement that describes a new finding or a new cause-effect relationship.

# # 1. Novelty Claims
# # Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
# # Examples:
# # Proposing a new algorithm for data compression.
# # Introducing a novel framework for distributed computing.
# # Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

# # 2. Performance Claims
# # Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
# # Examples:
# # Demonstrating that an algorithm runs faster than existing alternatives.
# # Showing that a model achieves higher accuracy on benchmark datasets.
# # Validation: Supported by empirical results, benchmarks, or performance comparisons.

# # 3. Applicability Claims
# # Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
# # Examples:
# # Asserting that a security protocol is effective for IoT devices.
# # Demonstrating that a machine learning model can be applied to healthcare diagnostics.
# # Validation: Validated through case studies, domain-specific applications, or practical implementations.

# # 4. Background Claims
# # Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
# # Examples:
# # Referencing a well-known algorithm to explain the foundation of the current approach.
# # Citing previous studies to justify the need for new research in a particular area.
# # Discussing existing theories or models that the current study builds upon or challenges.
# # Validation: Typically validated by citing credible sources, existing literature, or previous research findings.




# # {
# # "Novelty Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name)
# # },
# # {"claim":"...",
# # "section":"..."}
# # ]
# # },

# # "Performance Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name),
# # "context of the claim":"..."(provide a brief context or explanation for the claim, if needed)
# # },
# # {"claim":"...",
# # "section":"..."
# # }
# # ]
# # },

# # "Applicability Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" findthe paper's section name),
# # },
# # {"claim":"...",
# # "section":"..."
# # }
# # ]
# # },


# # "Background Claims":
# # [
# # {
# # "claim":"..."(it should be core finding, self-contained (the reader should understand without reading the article), atomic(short), and it can be verifiable against external sources),
# # "section":"..."(section name of extraction, do NOT assign "contents" find the paper's section name)

# # },
# # {"claim":"...",
# # "section":"..."
# # }
# # ]
# # }
# # ]
# # },

# # }


# # """

# #     prompt= instruction+ f'/n title: {title} /n abstract: {abstract} /n body: {body}'


# #     return prompt
# #%%
# import json

# def make_claim_extraction_from_paper_query_fine_tune(title: str, abstract: str, body: str, response: list) -> str:
#     # Define the system message with your instructions
#     system_instruction = """
# Your main task is to extract the novel main findings of the paper. Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.

# IMPORTANT: Note that a claim is described in the following ways:
# - A statement that declares something is better;
# - A statement that proposes something new;
# - A statement that describes a new finding or a new cause-effect relationship.

# 1. Novelty Claims
# Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
# Examples:
# Proposing a new algorithm for data compression.
# Introducing a novel framework for distributed computing.
# Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

# 2. Performance Claims
# Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
# Examples:
# Demonstrating that an algorithm runs faster than existing alternatives.
# Showing that a model achieves higher accuracy on benchmark datasets.
# Validation: Supported by empirical results, benchmarks, or performance comparisons.

# 3. Applicability Claims
# Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
# Examples:
# Asserting that a security protocol is effective for IoT devices.
# Demonstrating that a machine learning model can be applied to healthcare diagnostics.
# Validation: Validated through case studies, domain-specific applications, or practical implementations.

# 4. Background Claims
# Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
# Examples:
# Referencing a well-known algorithm to explain the foundation of the current approach.
# Citing previous studies to justify the need for new research in a particular area.
# Discussing existing theories or models that the current study builds upon or challenges.
# Validation: Typically validated by citing credible sources, existing literature, or previous research findings.

# Please extract the claims from the provided paper's content and present them in the following JSON format:

# [
#   {
#     "claim": "...",  // The core finding; self-contained, atomic, verifiable
#     "section": "...",  // Section name from which the claim was extracted
#     "context": "...",  // Brief context or explanation for the claim
#     "theme": "..."     // The category of the claim: 'Novelty', 'Performance', 'Applicability', or 'Background'
#   },
#   {
#     "claim": "...",
#     "section": "...",
#     "context": "...",
#     "theme": "..."
#   },
#   ...
# ]

# Notes:
# - Do not assign "contents" as the section name. Find the actual section name from the paper.
# - The "theme" field should be one of the following values: 'Novelty', 'Performance', 'Applicability', or 'Background', corresponding to the claim categories defined above.
# - Ensure that each claim is clear and understandable on its own.
# - DO NOT generate more than 15 claims, but feel free to generate fewer.
# """

#     # Construct the system message
#     system_message = {
#         "role": "system",
#         "content": [
#             {
#                 "text": system_instruction.strip(),
#                 "type": "text"
#             }
#         ]
#     }

#     # Prepare the user message with title, abstract, and body
#     user_content = {
#         "title": title,
#         "abstract": abstract,
#         "content": body
#     }

#     user_message = {
#         "role": "user",
#         "content": [
#             {
#                 "text": json.dumps(user_content),
#                 "type": "text"
#             }
#         ]
#     }

#     # Prepare the assistant message with the response
#     assistant_message = {
#         "role": "assistant",
#         "content": [
#             {
#                 "text": json.dumps(response),
#                 "type": "text"
#             }
#         ]
#     }
        
#     # Construct the message list
#     messages = [system_message, user_message, assistant_message]

#     # Construct the full message structure
#     message = {"messages": messages}

#     # Return the message as a JSON string
#     return json.dumps(message, ensure_ascii=False, separators=(',', ':'))


# # response=[
# #   {
# #     "claim": "New algorithm improves data compression efficiency by 20%",
# #     "section": "Abstract",
# #     "context": "The study introduces a novel algorithm for data compression.",
# #     "theme": "Novelty"
# #   },
# #   {
# #     "claim": "Algorithm achieves higher accuracy on benchmark datasets",
# #     "section": "Results",
# #     "context": "Comparison with existing methods shows improvement.",
# #     "theme": "Performance"
# #   }
# # ]


# # %%
# import json
# def make_claim_extraction_from_paper_query_new(title: str, abstract: str, body: str) -> str:
#     # Define the system message with your instructions
#     system_instruction = """
# Your main task is to extract the novel main findings of the paper. Each 'claim' should be concise and may be broken down if necessary. Avoid using determiners, and present the claims as generic statements that are searchable. Imagine you are going to cite these claims in your paper, so ensure they are clear, concise, and highlight the main findings.


# IMPORTANT: Note that a claim is described in the following ways:
# - A statement that declares something is better;
# - A statement that proposes something new;
# - A statement that describes a new finding or a new cause-effect relationship.


# 1. Novelty Claims
# Definition: Claims that introduce something new or original, such as a new theory, algorithm, model, or approach.
# Examples:
# Proposing a new algorithm for data compression.
# Introducing a novel framework for distributed computing.
# Validation: Often validated through theoretical proofs or by demonstrating that the new contribution is different from and improves upon existing work.

# 2. Performance Claims
# Definition: Claims that focus on the efficiency, speed, accuracy, or scalability of a method, system, or algorithm.
# Examples:
# Demonstrating that an algorithm runs faster than existing alternatives.
# Showing that a model achieves higher accuracy on benchmark datasets.
# Validation: Supported by empirical results, benchmarks, or performance comparisons.

# 3. Applicability Claims
# Definition: Claims that emphasize the practical use, relevance, or impact of the research in real-world scenarios or specific domains.
# Examples:
# Asserting that a security protocol is effective for IoT devices.
# Demonstrating that a machine learning model can be applied to healthcare diagnostics.
# Validation: Validated through case studies, domain-specific applications, or practical implementations.

# 4. Background Claims
# Definition: Claims that are imported from previous work or existing literature to provide context, justification, or support for the current study. These claims are often found in the related work section or when framing the problem.
# Examples:
# Referencing a well-known algorithm to explain the foundation of the current approach.
# Citing previous studies to justify the need for new research in a particular area.
# Discussing existing theories or models that the current study builds upon or challenges.
# Validation: Typically validated by citing credible sources, existing literature, or previous research findings.

# Please extract the claims from the provided paper's content and present them in the following JSON format:


# [
#   {
#     "claim": "...",  // The core finding; self-contained, atomic, verifiable
#     "section": "...",  // Section name from which the claim was extracted
#     "context": "...",  // Brief context or explanation for the claim
#     "theme": "..."     // The category of the claim: 'Novelty', 'Performance', 'Applicability', or 'Background'
#   },
#   {
#     "claim": "...",
#     "section": "...",
#     "context": "...",
#     "theme": "..."
#   },
#   ...
# ]

# Notes:
# - Do not assign "contents" as the section name. Find the actual section name from the paper.
# - The "theme" field should be one of the following values: 'Novelty', 'Performance', 'Applicability', or 'Background', corresponding to the claim categories defined above.
# - Ensure that each claim is clear and understandable on its own.

# """

#     # Construct the system message
#     system_message = {
#         "role": "system",
#         "content": [
#             {
#                 "text": system_instruction.strip(),
#                 "type": "text"
#             }
#         ]
#     }

#     # Prepare the user message with title, abstract, and body
#     user_content = {
#         "title": title,
#         "abstract": abstract,
#         "main_content": body,
#     }

#     user_message = {
#         "role": "user",
#         "content": [
#             {
#                 "text": json.dumps(user_content),
#                 "type": "text"
#             }
#         ]
#     }

#     # Construct the message list
#     messages = [system_message, user_message]

#     # Construct the full message structure
#     message = {"messages": messages}

#     # Return the message as a JSON string
#     return json.dumps(message, ensure_ascii=False, separators=(',', ':'))
