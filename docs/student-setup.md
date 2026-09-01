# Student Setup

## Before class

1. Install Docker Desktop for your operating system.
2. Start Docker Desktop and wait until it reports that it is running.
3. Sign in to ChatGPT or Claude in a browser.
4. Download or clone this repository.
5. Do not add an API key or personal data to this repository.

## Start the local environment

1. Open a terminal in the repository folder.
2. Run `docker compose up --build`.
3. Wait for the portal start message.
4. Open `http://localhost:8080` in a browser.
5. Open ChatGPT or Claude in a separate browser tab.

If the local portal is unavailable, continue from the Markdown files. The course content works without the portal.

## Browser LLM rules

1. Start a new chat for each lab.
2. Copy only the scenario text marked **Safe to share with an LLM**.
3. Do not copy hidden instructor material into a chat.
4. Do not use customer data, credentials, source code, or production logs.
5. State when a conclusion comes from the LLM rather than local evidence.

## Smoke test

1. Open `labs/01-indirect-prompt-injection/README.md`.
2. Find the Safe to share section.
3. Paste the first prompt into your provider chat.
4. Save the answer as a local Markdown note.

## Stop the environment

1. Return to the terminal window.
2. Press `Control+C`.
3. Run `docker compose down`.
