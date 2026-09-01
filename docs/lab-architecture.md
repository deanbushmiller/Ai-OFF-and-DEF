# Lab Architecture

## Design goals

The lab starts in under 15 minutes. It works on macOS and Windows. It needs no API key and no cloud account. It limits all targets to the student computer.

## Components

```text
Browser
├── ChatGPT or Claude tab
│   ├── analyst prompts
│   └── reviewer prompts
└── localhost lab portal
    ├── scenario briefs and synthetic data
    ├── local mock services
    ├── scanner containers
    ├── MITRE ATLAS mapping assets
    └── evidence templates
```

Docker runs only local services. The browser LLM acts as an analysis assistant. A student copies small, approved scenario excerpts into a chat. The lab never makes a browser LLM call through an API.

## Runtime design

`docker compose up --build` starts the local portal and mock services. The portal serves the lab files. A scanner container runs local rules against the included sample artifacts. The RAG and MCP labs use static requests and log files, not network-accessible production systems.

## Tool choices

| Need | Core tool | Reason |
| --- | --- | --- |
| Local runtime | Docker Compose | One command works on both operating systems. |
| Supply-chain scan | Semgrep or Trivy | Students run a real scanner on harmless files. |
| Data review | Markdown and CSV | Students can inspect files without a local IDE. |
| LLM analysis | ChatGPT or Claude browser chat | Meets the single subscription requirement. |
| ATLAS map | Included matrix worksheet | Avoids an account or an API dependency. |
| Evidence | Markdown templates | Portable and easy to review. |

Jupyter is optional. The core course does not require it because browser-based steps reduce setup risk. An instructor may add a notebook after the course review.

## Dual-LLM pattern

Students use two isolated browser chats, even when both chats use one provider. The application-model chat drafts a response. The reviewer-model chat checks policy, sensitive data, tool scope, and escalation needs. The student compares both outputs before making a decision.

This pattern teaches separation of duties. It does not claim that two chats form an automated production control.

## Cloud options

No cloud account is required. Advanced students may map their guardrail design to a free developer tier after class. They must not upload lab files to any service unless the file contains only the supplied synthetic content.
