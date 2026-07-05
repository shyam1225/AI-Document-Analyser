system_message = "You are a helpful assistant that summarizes the content of a document based on the provided text."
def generate_prompt(book, topic):
    prompt = f"Please summarize the content of the book '{book}' focusing on the topic '{topic}'."
    return prompt