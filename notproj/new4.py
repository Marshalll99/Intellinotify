from ai_helper import query_ai  # Import the function

# Get user input dynamically (or fetch from web scraping later)
user_prompt = input("Enter your question: ")

# Query AI and get the response
ai_response = query_ai(user_prompt)

# Display AI response
print("🤖 AI Response:", ai_response)
