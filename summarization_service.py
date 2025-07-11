import json
import logging
import os
import requests

from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log
import requests.exceptions

logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv(".env.dev")

def fake_get_transcript(transcript_id: str):
    """
    Fake function to get a transcript by its ID.
    :param transcript_id: ID of the transcript to retrieve
    :return: The transcript text
    """
    return "This is a sample transcript text for testing purposes."

def fake_detect_language(text: str) -> str:
    """
    Fake function to detect the language of a given text.
    :param text: The text to analyze
    :return: Detected language code (e.g., 'en', 'fr', 'de', 'it')
    """
    return "en"

def fake_get_prompt_for_language(lang_code: str) -> str:
    """
    Fake function to get a prompt for a specific language.
    :param lang_code:
    :return: The prompt text for the specified language
    """
    prompts = {
        "en": "Please summarize the following text in English.",
        "fr": "Veuillez résumer le texte suivant en français.",
        "de": "Bitte fassen Sie den folgenden Text auf Deutsch zusammen.",
        "it": "Per favore, riassumi il seguente testo in italiano.",
    }
    return prompts.get(lang_code,)

def fake_save_summary(transcript_id: str, summary: str):
    """
    Fake function to save a summary.
    :param transcript_id: ID of the transcript
    :param summary: The summary text
    """
    logger.info(f"Saved summary for transcript with ID: {transcript_id}.")


def summarize_transcript(transcript_id: str):
    """
    Summarize a transcript by its ID.
    :param transcript_id: ID of the transcript to summarize
    """
    logger.info("Summarization started.")
    try:
        transcript_text = fake_get_transcript(transcript_id)
        logger.info(
            f"Got transcript text from database for transcript with ID: {transcript_id}."
        )
    except Exception as e:
        logger.error(f"Error retrieving transcript text from the database: {e}")
        raise FileNotFoundError(
            f"Error retrieving transcript text from the database: {e}"
        )

    try:
        detected_language = fake_detect_language(transcript_text)
        logger.info(f"Detected language: {detected_language}")
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        logger.warning("Falling back to English for summarization...")
        detected_language = "en"

    base_prompt = fake_get_prompt_for_language(detected_language)
    prompt = f"{base_prompt}\n\n[INST]\n{transcript_text}\n[/INST]"

    try:
        summary = call_llm_api(prompt)
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        raise

    logger.info("Generated summary.")
    fake_save_summary(transcript_id, summary)
    logger.info("Summary saved.")

# Automatically retry the function up to 3 times if a requests-related exception occurs.
# Retries happen with exponential backoff: 10s → 20s → 40s (capped at 60s).
# Only retries on network-related errors (timeouts, 5xx, connection issues).
# Final failure will still raise the original exception (reraise=True).
@retry(
    wait=wait_exponential(multiplier=1, min=5, max=60),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)

def call_llm_api(prompt: str) -> str:
    """
    Call the LLM API to generate a summary, with retries on network errors or timeouts.
    :param prompt: The prompt to send to the LLM API
    :return: The generated summary
    """
    # Estimate token count from prompt length, assuming ~1.3 tokens per word
    estimated_tokens = len(prompt.split()) * 1.3

    # Dynamically calculate a timeout based on size (defaults to at least 60s).
    # Assumes LLM can process ~25 tokens per second.
    timeout = max(60, int(estimated_tokens * 0.04))


    logger.info(f"Calling LLM API with {timeout} seconds timeout...")

    try:
        # Make the POST request to the LLM API with the generated prompt
        response = requests.post(
            url=os.getenv("LLM_API_URL"),
            data=json.dumps(
                {"model": "mixtral", "messages": [{"role": "user", "content": prompt}]}
            ),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}",
            },
            timeout=timeout,  # Dynamic timeout applied here
        )

        # Raise HTTPError if status is 4xx/5xx
        response.raise_for_status()

        # Return the LLM's summarized response
        return response.json()["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        # Log retryable exceptions (network, timeout, 5xx)
        logger.warning(f"Retryable LLM API call error: {e}")
        raise



