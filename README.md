# AI Offense and Defense Lab

> **Beta version 20260901**
> This course is under review. Lab flow, Docker images, and prompts may change before the final release.

An eight-hour, remote course for intermediate security professionals. The course has nine standalone labs. Every lab uses harmless local targets and synthetic data.

## Student requirements

- A Mac or Windows computer.
- Docker Desktop installed before class.
- A current ChatGPT or Claude subscription.
- A modern web browser.
- Git, or a downloaded ZIP copy of this repository.

The course does not need API keys, paid cloud accounts, Python, or a local GPU. Students use ChatGPT or Claude in the browser. They copy only the supplied synthetic data into a chat.

## Start the lab

1. Clone or download this repository.
2. Start Docker Desktop.
3. Run `docker compose up --build` from the repository root.
4. Open `http://localhost:8080`.
5. Follow [student setup](docs/student-setup.md).

Docker starts a local, read-only portal. Lab 2 also runs a local Semgrep supply-chain scan. Docker does not send data to an LLM.

Students can complete every lab from the Markdown files if Docker is unavailable. They use a ChatGPT or Claude browser chat for the supplied synthetic prompts.

## Course materials

- [Course overview](docs/course-overview.md)
- [Lab architecture](docs/lab-architecture.md)
- [Student setup](docs/student-setup.md)
- [Instructor guide](docs/instructor-guide.md)
- [Safety policy](docs/safety-policy.md)
- [Troubleshooting](docs/troubleshooting.md)
- [OWASP threat mapping](docs/owasp-threat-mapping.md)
- [Instructor demonstrations](instructor-demos/README.md)

## Labs

1. [Indirect prompt injection](labs/01-indirect-prompt-injection/README.md)
2. [Supply-chain audit](labs/02-supply-chain-audit/README.md)
3. [Adversarial red teaming](labs/03-adversarial-red-teaming/README.md)
4. [MITRE ATLAS mapping](labs/04-mitre-atlas/README.md)
5. [Dual-LLM guardrails](labs/05-dual-llm-guardrails/README.md)
6. [Secure MCP](labs/06-secure-mcp/README.md)
7. [RAG poisoning](labs/07-rag-poisoning/README.md)
8. [AI-native incident response](labs/08-ai-incident-response/README.md)
9. [Enterprise guardrails](labs/09-enterprise-guardrails/README.md)

## Evidence and completion

The course uses completion, not grades. Each student saves one short finding or decision record for each lab. Use the templates in [templates](templates/README.md). Do not upload customer data, secrets, or real attack content.

## License and use

Use this material only for authorized education and local testing. See the [safety policy](docs/safety-policy.md).
