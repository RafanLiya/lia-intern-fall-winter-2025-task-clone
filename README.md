# RFC – Timeout Handling and Retry in LLM API Calls

## Background
We recently got this error in our logs:

```bash
LLM API call failed: 504 Server Error: Gateway Time-out for url: https://api.xyz.com/chat/completions
```

This happened in our summarization service – the micro service responsible for summarizing transcripts.

We found additional logs related to the error:

```bash
Got transcript text from database for transcript with ID: xyz.
Calling LLM API with 194 seconds timeout...
```

The transcript with id `xyz`  was a large piece of text, and the LLM API call took longer than 194 seconds, resulting in a timeout.

But timing out and losing the transcript is not ideal because it wastes expensive GPU resources and the user doesn't get a summary. 

We should handle this case more gracefully.

Improve the code with a retry mechanism using tenacity and an improved estimation mechanism for the number of seconds to timeout.

## Steps
1. Clone the repository (if you fork, other applicants will see your code)
2. Create a new branch for your changes
3. Make the necessary changes to the codebase in the branch
4. Commit your changes with a clear message and create a well-documented (description of your changes and reasoning) pull request in your clone
5. Send us the link to your pull request