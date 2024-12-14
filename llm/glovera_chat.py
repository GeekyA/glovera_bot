from dotenv import load_dotenv
from openai import OpenAI
from enum import Enum
import json
from utils.database import get_programs_collection
import pandas as pd
import os
from utils.agent_tools import query_df_desc, query_mongo_db_desc  # Assuming this is a function descriptor
from llm.agents import ask_db_agent

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

load_dotenv()
client = OpenAI()

    
def ask_database(natural_language_query, user_data):
    natural2mongo = ask_db_agent(natural_language_query, user_data)
    natural2mongo = json.loads(natural2mongo)
    print("query: ",natural2mongo)
    try:
        # Connect to MongoDB
        collection = get_programs_collection()

        # Execute the query
        filtered_docs = list(collection.find(natural2mongo))
        tot = len(filtered_docs)

        return f"Found {tot} documents, data: {filtered_docs}"
    
    except Exception as e:
        return f"Error in query_mongo_db: {e}"

def say_bye():
    return "bye_bye_message_dont_show_to_user"

ask_db_tool = {
    "name": "ask_database",
    "description": "Queries a database of universities in natural language, this should be called when data is needed to get an accurate response",
    "parameters": {
        "type": "object",
        "properties": {
            "natural_language_query": {
                "type": "string",
                "description": "User's query"
            }
        },
        "required": ["natural_language_query"],
        "additionalProperties": False
    }
}

say_bye_tool = {
    "name": "say_bye",
    "description": "This function should be called when the conversation ends",
}
class OpenAIConversation:
    def __init__(self, model, system_prompt, user_data=None):
        self.system_prompt = system_prompt
        self.model = model
        self.system_prompt = system_prompt
        self.user_data = user_data
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
                        "function": ask_db_tool
                    },
                    {
                        "type": "function",
                        "function": say_bye_tool
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
            if tool_call.function.name == "ask_database":
                try:
                    print(tool_call)
                    arguments = json.loads(tool_call.function.arguments)
                    query = eval(str(arguments))['natural_language_query']

                    last_query = self.messages[-1]['content']
                    # Call the function and retrieve the result
                 
                    function_response = ask_database(query, user_data=self.user_data)

                    

                    # Update query with function response and get new response
                    
                    updated_query = f"""Answer the user query {last_query} based on this data: {function_response}. 
                    Dont bombard the user with information, just tell them like a consultant about their available options. Create your response concise and well formatted.\n
                    Your response will be listened by users after going through a TTS model so it's important you keep it short and engaging. 
                    You don't have to use all the program data in the conversation.
                    Don't add the curriculum link in the response or 
                    """

                    self.messages.append({"role": Role.USER.value, "content": updated_query})
                    return self.get_response_no_tools()

                except Exception as e:
                    return f"Error processing function call: {e}"

            if tool_call.function.name == 'say_bye':
                self.messages.append({"role": Role.USER.value, "content": say_bye()})
                return self.messages[-1]['content']



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
