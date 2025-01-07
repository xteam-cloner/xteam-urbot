import os
from collections import deque
from io import BytesIO

import requests

from . import (
    ultroid_cmd,
    check_filename,
    udB,
    LOGS,
    download_file,
    run_async,
)

# Gemini API configuration
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"

# Initialize chat history with a maximum of 30 messages
GEMINI_CHAT_HISTORY = deque(maxlen=30)


@run_async
def get_medical_advice(query, api_key):
    """
    Sends a request to the Gemini API to generate content based on the provided query.

    Args:
        query (str): The user's query or prompt.
        api_key (str): The API key for authenticating with the Gemini API.

    Returns:
        dict: The JSON response from the Gemini API.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip"
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": query
            }]
        }],
        "safetySettings": [],
        "generationConfig": None
    }
    response = requests.post(f"{API_URL}?key={api_key}", headers=headers, json=payload)
    response.raise_for_status()  # Raises HTTPError, if one occurred.
    return response.json()


@ultroid_cmd(
    pattern=r"gemini( ([\s\S]*)|$)",
)
async def google_gemini(e):
    """
    Handles the `.gemini` command to interact with the Gemini API.

    Usage:
        .gemini <your query>
        .gemini -c  # To clear the chat history
    """
    # Retrieve the Gemini API key from the database
    api_key = udB.get_key("GEMINI_API")
    if not api_key:
        return await e.eor("`GEMINI_API` key missing..", time=8)

    # Extract the query from the command or replied message
    query = e.pattern_match.group(2)
    if not query:
        reply = await e.get_reply_message()
        if reply and reply.text:
            query = reply.message
    if not query:
        return await e.eor("`Please provide a question for Gemini..`", time=5)

    # Clear chat history if the user sends '-c'
    if query.strip().lower() == "-c":
        GEMINI_CHAT_HISTORY.clear()
        return await e.eor("__Cleared Gemini Chat History!__", time=6)

    # Inform the user that the answer is being generated
    eris = await e.eor(f"__Generating answer for:__\n`{query[:128]} ...`")
    
    # Append the user's query to the chat history
    GEMINI_CHAT_HISTORY.append({"role": "user", "content": query})

    try:
        # Call the get_medical_advice function to interact with Gemini API
        response = await get_medical_advice(query, api_key)
        
        # Parse the response to extract the assistant's reply
        # The exact parsing depends on the Gemini API's response structure
        # Here, we assume a similar structure to OpenAI's API for demonstration
        assistant_reply = response.get("candidates", [{}])[0].get("content", "No response generated.")

        # Append the assistant's reply to the chat history
        GEMINI_CHAT_HISTORY.append({"role": "assistant", "content": assistant_reply})
        
    except requests.HTTPError as http_err:
        # Handle HTTP-specific errors
        LOGS.warning(f"HTTP error occurred: {http_err}", exc_info=True)
        GEMINI_CHAT_HISTORY.pop()  # Remove the last user message if there was an error
        return await eris.edit(
            f"**HTTP Error while requesting data from Gemini:** \n> `{http_err}`"
        )
    except Exception as exc:
        # Log any other exceptions and notify the user
        LOGS.warning(f"Unexpected error: {exc}", exc_info=True)
        GEMINI_CHAT_HISTORY.pop()  # Remove the last user message if there was an error
        return await eris.edit(
            f"**Error while requesting data from Gemini:** \n> `{exc}`"
        )

    
    # Optionally log token usage if available in the response
    # Adjust this section based on the actual response structure
    if "usage" in response and "completion_tokens" in response["usage"]:
        LOGS.debug(f'Tokens used for query "{query}": {response["usage"]["completion_tokens"]}')

    # Check if the response length is manageable for a single message
    if len(assistant_reply + query) < 4050:
        formatted_reply = f"**Query:**\n~ __{query}__\n\n**Gemini:**\n~ {assistant_reply}"
        return await eris.edit(formatted_reply)

    # If the response is too long, send it as a file
    with BytesIO(assistant_reply.encode()) as file:
        file.name = "gemini-output.txt"
        await eris.respond(
            f"__{query[:360]} ...__",
            file=file,
            reply_to=e.reply_to_msg_id or e.id,
        )
    await eris.try_delete()
