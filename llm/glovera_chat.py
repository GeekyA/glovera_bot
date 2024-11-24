from dotenv import load_dotenv
from openai import OpenAI
from enum import Enum
import json
from utils.database import get_conversations_collection
import pandas as pd
from utils.agent_tools import query_df_desc, query_mongo_db_desc  # Assuming this is a function descriptor

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

load_dotenv()
client = OpenAI()

def query_mongo_db(mongo_query: dict):
    """
    Function to query a MongoDB collection using a MongoDB query.
    
    Args:
    - mongo_query (dict): MongoDB query as a Python dictionary.
    
    Returns:
    - str: Results of the query or an error message.
    """
    print("Executing query_mongo_db with MongoDB query:")
    
    try:
        # Connect to MongoDB
        collection = get_conversations_collection()

        # Execute the query
        filtered_docs = list(collection.find(mongo_query))
        tot = len(filtered_docs)

        return f"Found {tot} documents, data: {filtered_docs}"
    
    except Exception as e:
        return f"Error in query_mongo_db: {e}"

class OpenAIConversation:
    def __init__(self, model, system_prompt=None):
        self.model = model
        self.system_prompt = system_prompt
        self.memory = []
        self.messages = [{"role": Role.SYSTEM.value, "content": system_prompt}] if system_prompt else []

    def add_user_message(self, message):
        self.messages.append({"role": Role.USER.value, "content": message})
        return self.get_response()

    def get_response(self):
        try:
            response = client.chat.completions.create(
                model=self.model,
                tools=[
                    {
                        "type": "function",
                        "function": query_mongo_db_desc
                    }
                ],
                messages=self.messages,
                temperature=0,
                max_tokens=2000,
            )

            choice = response.choices[-1]
            if choice.message.content:
                # Direct response from the assistant
                reply = choice.message.content
                self.messages.append({"role": Role.ASSISTANT.value, "content": reply})
                return reply
            elif choice.message.tool_calls:
                # Handle function call
                return self.handle_function_call(choice.message.tool_calls)

        except Exception as e:
            return f"Error: {str(e)}"
        
    def get_response_no_tools(self):
        try:
            response = client.chat.completions.create(
                model=self.model,
            
                messages=self.messages,
                temperature=0,
                max_tokens=2000,
            )

            choice = response.choices[-1]
            reply = choice.message.content
            self.messages.append({"role": Role.ASSISTANT.value, "content": reply})
            return reply
        except Exception as e:
            return f"Error: {str(e)}"

    def handle_function_call(self, tool_calls):
        """
        Process function calls made by the assistant and generate an appropriate response.
        """
        print(tool_calls)
        for tool_call in tool_calls:
            if tool_call.function.name == "query_mongo_db":
                try:
                    print(tool_call)
                    arguments = json.loads(tool_call.function.arguments)
                    print(arguments)
                    lambda_exp = arguments.get("lambda_exp", "")
                    print(lambda_exp)

                    last_query = self.messages[-1]['content']
                    # Call the function and retrieve the result
                    function_response = query_mongo_db(lambda_exp)

                    # Update query with function response and get new response
                    updated_query = f"Answer the user query {last_query} based on this data: {function_response}. Dont bombard the user with information, just tell them like a consultant about their available options. Try avoiding bullet points"
                    self.messages.append({"role": Role.USER.value, "content": updated_query})
                    return self.get_response()

                except Exception as e:
                    return f"Error processing function call: {e}"

    def start_conversation(self, initial_message):
        self.messages.append({"role": Role.ASSISTANT.value, "content": initial_message})

    def reset_conversation(self):
        self.messages = [{"role": Role.SYSTEM.value, "content": self.system_prompt}]

    def set_conversation(self, conversation):
        self.messages = conversation

    def get_conversation(self):
        return self.messages

if __name__ == "__main__":
    system_prompt = (
        "You are an AI consultant to help users who want to study abroad.\n"
        "Answer all their questions regarding courses, universities, eligibility, etc.\n"
        "Tailor your responses keeping in mind that they'll be parsed by a Text-to-speech model\n"
        "In a natural human-like conversation"
    )

    initial_message = (
        "Hi, I am an AI consultant who'll help you find the best universities abroad. "
        "Ask me anything about where you want to study, what you want to study, your budget, "
        "or any other questions you might have."
    )

    conv = OpenAIConversation(model="gpt-4o", system_prompt=system_prompt)
    print("Agent:", initial_message)
    conv.start_conversation(initial_message=initial_message)

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit_chat":
            break
        agent_response = conv.add_user_message(user_input)
        print("Agent:", agent_response)

    print("Conversation Log:", conv.get_conversation())
