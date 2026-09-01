# Troubleshooting

## Docker Desktop is not running

Start Docker Desktop. Wait for its status to show that the engine is running. Then rerun the setup command.

## Port 8080 is in use

Stop the other local service that uses port 8080. Then rerun Docker Compose. If needed, change the host port in the compose file and use the new URL.

## Image download fails

Check your internet connection. Retry the command. If the download still fails, use the Markdown-only path and skip scanner execution.

## ChatGPT or Claude refuses a prompt

Use the lab’s safer alternative prompt. Do not rewrite the prompt to seek a bypass. Record the refusal as a guardrail observation.

## Windows path issue

Use PowerShell or Git Bash from the repository folder. Avoid copying a path with smart quotes.

## Mac permission issue

Allow Docker Desktop to access the repository folder when macOS asks. Then restart Docker Desktop.
