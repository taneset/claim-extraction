def rubric_query(citances: str) -> str:
   
     """
    The following citation sentences are extracted from research papers in computer science. 
    You are tasked with assessing the quality of the conclusion of each citation sentence.

    A good quality citances usually contains one of the following:
         - a statement that declares something is better;
         - a statement that proposes something new;
         - a statement that describes a new finding or a new cause-effect relationship  

        Assess each statement and give over all score between (0-10), your answer in this json format. 
        {
            "citance": "The statement",
            "score": 0-10
        }      
    """
 
    
     
    prompt= instruction + f'/n {citances}'


    return prompt

