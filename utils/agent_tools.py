query_df_desc = {
    "name": "query_df",
   "description": """query_df queries a pandas dataframe with a lambda function. The dataframe includes columns such as:
    "course_name": Name of the course,
    "degree_type": Type of degree (e.g., M.Sc.),
    "tuition_fee": Course fee,
    "duration": Course length (e.g., '1 year'),
    "university_name": University name,
    "university_location": University location,
    "global_rank": University ranking,
    "english_requirments": Minimum language scores,
    "min_gpa": Required GPA,
    "work_experience": Relevant work experience,
    "start_date": Course start date,
    "apply_date": Application deadline.""",
    "parameters": {
        "type": "object",
        "properties": {
            "lambda_exp": {
                "type": "string",
                "description": """A string representation of a lambda function used to query the dataframe. Query should case insensitive and should handle naming variations  for example:\n
                Make sure the function is a complete lambda function i.e lambda row: expression
                Examples:
                1. Tell me about some good universities in the USA that teach sociology => lambda row: any(x in row['university_location'].lower() for x in ['united states', 'usa', 'us']) and 'sociology' in row['course_name'].lower();
                2. Tell me good universities in the USA for MBA => lambda row: any(x in row['university_location'].lower() for x in ['united states', 'usa', 'us']) and any(x in row['course_name'].lower() for x in ['business', 'administration', 'mba']);
                3. Recommend computer science programs in the USA => lambda row: any(x in row['university_location'].lower() for x in ['united states', 'usa', 'us']) and 'computer' in row['course_name'].lower();
                4. Find data science programs in Canada => lambda row: 'canada' in row['university_location'].lower() and any(x in row['course_name'].lower() for x in ['data', 'science']);
                5. Engineering courses in the UK => lambda row: any(x in row['university_location'].lower() for x in ['united kingdom', 'uk', 'england']) and 'engineering' in row['course_name'].lower();
                                
                be creative and try to find relevant keywords to search for in relevant columns in case insensitive manner, finding exact info is not important\n
                but finding relevant info is important.

                """
            }
        },
        "required": ["lambda_exp"],
        "additionalProperties": False
    },
}

query_mongo_db_desc = {
    "name": "query_mongodb",
    "description": """query_mongodb searches a MongoDB collection containing educational program information. The collection documents include fields such as:
    "course_name": Name of the course,
    "degree_type": Type of degree (e.g., M.Sc.),
    "tuition_fee": Course fee,
    "duration": Course length (e.g., '1 year'),
    "university_name": University name,
    "university_location": University location,
    "global_rank": University ranking,
    "english_requirments": Minimum language scores, contains three more fields ( {"ielts": ielts_score, "toefl": toefl_score, "pte"pte_score})
    "min_gpa": Required GPA,
    "work_experience": Relevant work experience,
    "start_date": Course start date,
    "apply_date": Application deadline.""",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "description": """A MongoDB query object to search the collection. Queries should be case-insensitive and handle naming variations.
                Examples:
                1. Tell me about some good universities in the USA that teach sociology =>
                {
                    "$and": [
                        { "university_location": { "$regex": "united states|usa|us", "$options": "i" } },
                        { "course_name": { "$regex": "sociology", "$options": "i" } }
                    ]
                }

                2. Tell me good universities in the USA for MBA =>
                {
                    "$and": [
                        { "university_location": { "$regex": "united states|usa|us", "$options": "i" } },
                        { "course_name": { "$regex": "business|administration|mba", "$options": "i" } }
                    ]
                }

                3. Recommend computer science programs in the USA =>
                {
                    "$and": [
                        { "university_location": { "$regex": "united states|usa|us", "$options": "i" } },
                        { "course_name": { "$regex": "computer", "$options": "i" } }
                    ]
                }

                4. Find data science programs in Canada =>
                {
                    "$and": [
                        { "university_location": { "$regex": "canada", "$options": "i" } },
                        { "course_name": { "$regex": "data.*science|science.*data", "$options": "i" } }
                    ]
                }

                5. Engineering courses in the UK =>
                {
                    "$and": [
                        { "university_location": { "$regex": "united kingdom|uk|england", "$options": "i" } },
                        { "course_name": { "$regex": "engineering", "$options": "i" } }
                    ]
                }

                Additional Features:
                - Use "$options": "i" for case-insensitive matching
                - Use "$regex" for pattern matching and handling variations
                - Use "$or" for alternative matches
                - Use "$and" to combine multiple conditions
                - Use "$gte", "$lte" for numeric comparisons
                - Use "$in" for matching multiple possible values
                
                Focus on creating flexible queries that can match relevant information even with variations in naming or formatting.
                """
            },
            "projection": {
                "type": "object",
                "description": "Optional field selection object to specify which fields to return in the results",
                "default": {}
            },
            "sort": {
                "type": "object",
                "description": "Optional sorting criteria for the results",
                "default": {}
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}


