"""Run a contained instructor demonstration against a local Ollama model."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "scenarios"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("LOCAL_MODEL", "llama3.2:1b")


def chat(system, user):
    """Send one non-streaming request to a model that stays inside Docker."""
    payload = json.dumps(
        {
            "model": MODEL,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))["message"]["content"]
    except urllib.error.URLError as error:
        raise RuntimeError(f"Cannot reach the local Ollama service: {error}") from error


def render_user(scenario, user_override=None):
    user = user_override or scenario["user"]
    context = scenario.get("untrusted_context", "")
    if context:
        return (
            "Untrusted application content follows.\n"
            "[UNTRUSTED CONTENT START]\n"
            f"{context}\n"
            "[UNTRUSTED CONTENT END]\n\n"
            f"User request:\n{user}"
        )
    return user


def print_result(label, output):
    print(f"\n## {label}\n")
    print(output.strip())


def run_single(scenario):
    user = render_user(scenario)
    print_result("Baseline model response", chat(scenario["baseline_system"], user))
    print_result("Guarded model response", chat(scenario["guarded_system"], user))


def run_multi(scenario):
    for case in scenario["cases"]:
        print(f"\n# Test case: {case['name']}")
        output = chat(scenario["baseline_system"], render_user(scenario, case["request"]))
        print_result("Model response", output)


def run_dual(scenario):
    draft = chat(scenario["application_system"], render_user(scenario))
    print_result("Application-model draft", draft)
    reviewer_user = (
        f"Policy:\n{scenario['policy']}\n\n"
        f"User request:\n{scenario['user']}\n\n"
        f"Proposed answer:\n{draft}\n\n"
        "Return ALLOW, REVISE, or ESCALATE. Explain the policy reason."
    )
    print_result("Reviewer-model decision", chat(scenario["reviewer_system"], reviewer_user))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lab", choices=[f"{number:02d}" for number in range(1, 10)])
    args = parser.parse_args()
    path = SCENARIO_DIR / f"{args.lab}.json"
    scenario = json.loads(path.read_text(encoding="utf-8"))
    print(f"# {scenario['title']}\n\nModel: {MODEL}\nMode: {scenario['mode']}")
    if scenario["mode"] == "single":
        run_single(scenario)
    elif scenario["mode"] == "multi":
        run_multi(scenario)
    elif scenario["mode"] == "dual":
        run_dual(scenario)
    else:
        raise ValueError(f"Unknown demonstration mode: {scenario['mode']}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, ValueError) as error:
        print(f"Demo failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
