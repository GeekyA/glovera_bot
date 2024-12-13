from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI()

examples = """Examples of queries:\n
1. Tell me about some good universities in the USA that teach sociology =>
                {
                    "$and": [
                        { "location": { "$regex": "united states|usa|us", "$options": "i" } },
                        { "program_name": { "$regex": "sociology", "$options": "i" } }
                    ]
                }

2. Tell me good universities in the USA for MBA =>
{
    "$and": [
        { "location": { "$regex": "united states|usa|us", "$options": "i" } },
        { "program_name": { "$regex": "business|administration|mba", "$options": "i" } }
    ]
}

3. Recommend computer science programs in the USA =>
{
    "$and": [
        { "location": { "$regex": "united states|usa|us", "$options": "i" } },
        { "program_name": { "$regex": "computer", "$options": "i" } }
    ]
}
Focus on creating flexible queries that can match relevant information even with variations in naming or formatting."""

def ask_db_agent(query, user_data = None):
    prompt = (f"""You are a helpful AI agent/assistant.
You will be provided with a natural language query and\n
and you have to generate a mongodb query that is relevant to the natural language one, use the examples below to learn\n{examples}.
Here's the schema of the database:
<schema>
ranking (integer): Rank of the university or program.
program_name (string): The name of the program (e.g., MBA, MS in Information Technology).
location (string): The city and state of the institution. 
glovera_pricing (float): Discounted pricing for the program in USD.
original_pricing (float): Original pricing for the program in USD.
savings_percent (float): Percentage saved through discounts.
public_private (string): Indicates whether the institution is public or private.
key_job_roles (string): Key job roles associated with the program.
type_of_program (string): Type of program (e.g., MBA, MS).
quant_or_qualitative (string): Indicates if the program is quantitative or qualitative.
min_gpa (float): Minimum GPA requirement for admission.
<schema/>
Here's the user's natural language query: <natural_language_query>{str(query)}</natural_language_query>
Return your query within the following tags <query></query>
Important instructions\n: 
1. All programs are based in the US so don't ever filter by country.
2. Don't add comments in the generated query ever, never fucking ever
3. Use all possible keywords or phrases for string match, for example:
keywords associated with masters in program_name are ms | masters etc
4. If you're filtering by budget, don't add a lower bound, just make sure that you're finding unis below max budget
""")
    
    if user_data:
        user_data['max_budet'] = user_data['budget_range'].split('-')[-1]
        del user_data['budget_range']
        '''print(user_data)
        user_data = [(i,user_data[i]) for i in user_data.keys() if i != '_id' and i != 'userId']
        print(user_data['budget_range'])
        #user_data['budget'] = float(user_data['budget_range'].split('-')[-1])
        #user_data = [(i,user_data[i]) for i in user_data.keys() if i != 'budget_range']
        user_data = dict(user_data)'''
        prompt += f"Here's some info about the user as well to help you augment your response in a better way\n<user_info>\n{user_data}\n</user_info>"

    #print(prompt)


    response = client.chat.completions.create(
                model='gpt-4o',
            
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=2000,
            )

    choice = response.choices[-1]
    reply = choice.message.content
    reply = reply.split('</query>')[0].split('<query>')[-1]
    #print(f"Reply: {reply}")

    return reply



