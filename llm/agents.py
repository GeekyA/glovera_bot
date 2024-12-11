from openai import Client
from dotenv import load_dotenv

load_dotenv()


client = Client()

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

def ask_db_agent(query):
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
minimum_qualifications (string): Minimum qualifications required for admission.
type_of_program (string): Type of program (e.g., MBA, MS).
quant_or_qualitative (string): Indicates if the program is quantitative or qualitative.
min_gpa (float): Minimum GPA requirement for admission.
<schema/>
Here's the user's natural language query: <natural_language_query>{query}</natural_language_query>
Return your query within the following tags <query></query>
""")


    response = client.chat.completions.create(
                model='gpt-4o',
            
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=2000,
            )

    choice = response.choices[-1]
    reply = choice.message.content
    reply = reply.split('</query>')[0].split('<query>')[-1]

    return reply



