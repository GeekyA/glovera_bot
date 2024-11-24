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
    "english_requirements": Minimum language scores,
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
    "name": "query_mongo_db",
    "description": """this function queries a MongoDB collection with a MongoDB query. The collection contains documents with fields such as:
    "course_name": Name of the course,
    "degree_type": Type of degree (e.g., M.Sc.),
    "tuition_fee": Course fee,
    "duration": Course length (e.g., '1 year'),
    "university_name": University name,
    "university_location": University location,
    "global_rank": University ranking,
    "english_requirements": Minimum language scores,
    "min_gpa": Required GPA,
    "work_experience": Relevant work experience,
    "start_date": Course start date,
    "apply_date": Application deadline.""",
    "parameters": {
        "type": "object",
        "properties": {
            "mongo_query": {
                "type": "object",
                "description": """A MongoDB query as a Python dictionary used to filter documents in the collection.
                The query should be case-insensitive and should handle naming variations. Examples:
                
                1. Tell me about some good universities in the USA that teach sociology:
                   {"university_location": {"$regex": "usa|united states|us", "$options": "i"}, 
                    "course_name": {"$regex": "sociology", "$options": "i"}}
                
                2. Tell me good universities in the USA for MBA:
                   {"university_location": {"$regex": "usa|united states|us", "$options": "i"}, 
                    "course_name": {"$regex": "business|administration|mba", "$options": "i"}}
                
                3. Recommend computer science programs in the USA:
                   {"university_location": {"$regex": "usa|united states|us", "$options": "i"}, 
                    "course_name": {"$regex": "computer", "$options": "i"}}
                
                4. Find data science programs in Canada:
                   {"university_location": {"$regex": "canada", "$options": "i"}, 
                    "course_name": {"$regex": "data|science", "$options": "i"}}
                
                5. Engineering courses in the UK:
                   {"university_location": {"$regex": "uk|united kingdom|england", "$options": "i"}, 
                    "course_name": {"$regex": "engineering", "$options": "i"}}
                
                Use `$regex` for flexible, case-insensitive matching and include relevant fields for filtering.
                """
            }
        },
        "required": ["mongo_query"],
        "additionalProperties": False
    },
}

