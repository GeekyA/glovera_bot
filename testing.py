from llm.glovera_chat import OpenAIConversation


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