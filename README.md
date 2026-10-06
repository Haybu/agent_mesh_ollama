# agent_mesh — AI agents collaborating over RSocket

One broker, three single-task agents (Sales, Supply Chain, Finance).

```bash
pip install -r requirements.txt
python demo.py                      # everything in one process
```

`run_agent.py <name>` starts a single agent as its own process against a
running broker (`python -m mesh.broker`), which is how you would deploy them.

Set `OLLAMA_API_KEY` (and optionally `OLLAMA_MODEL`, default `gpt-oss:120b`)
to have agents explain decisions with an Ollama Cloud model; optionally you can use a local Ollama model.
otherwise a rule-based reasoner is used.
