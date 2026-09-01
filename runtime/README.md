# Local Runtime

The Docker Compose file starts a local, read-only portal at `http://localhost:8080`. It mounts this repository into an Nginx container. The portal home page links to the Markdown guides.

The scanner stays disabled during normal startup. Lab 2 runs it with:

```text
docker compose run --rm scanner
```

The scanner reads only the supplied synthetic assets. It does not execute `loader.py` or `model.bin`.

No service calls an LLM API. Students use their own ChatGPT or Claude browser session.
