# 🎯 LLM Competitor Analysis

![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Budget Guard](https://img.shields.io/badge/%F0%9F%92%B8-cost%20logged-blue)


**Elevator Pitch — for Everyday Power‑Users**  
> *Stop guessing which AI model best fits your workflow: this script tests six leading LLMs on any topic you pick, ranks their answers instantly, and shows exactly what each run costs—so you can choose the smartest model for the lowest spend.*

Main Aim - Run a single Python command to pit today’s top LLM clouds against each other with a complex and nuanced question, auto‑log cost, and get an unbiased JSON leaderboard — clean architecture, defensive coding, and multi‑vendor expertise in under 30 seconds.

---

## ⚡ Skills demonstrated

| Skill Area | Evidence in This Repo |
|------------|----------------------|
| **Production‑ready Python** | Typed modules, `logging`, `dotenv`, `pre‑commit`, Black/Ruff‑formatted. |
| **Cost‑aware AI engineering** | `openai_guard.py` logs tokens → CSV, enforces monthly £ cap, model‑specific shims. |
| **Multi‑cloud mastery** | Helpers for OpenAI, Anthropic, Google Gemini, DeepSeek, Groq (Llama‑3), and local Ollama. |
| **Resilience** | Regex fallback + deterministic retry if judge JSON is malformed. |
| **Clean API design** | Provider registry → drop‑in new vendors in one line. |
| **Testing culture** | Pytest mocks guard cost & judge parse (green badge above). |
| **Dev UX polish** | One‑liner Quick Start, `.env.example`, animated GIF demo. |

Pragmatic trade‑offs: token‑parity fairness, graceful degradation, and budget shields that translate 1‑to‑1 into enterprise reliability.

---

## 🗺️ Architecture Diagram

%% LLM‑Competitor‑Analysis — high‑level flow
flowchart LR
    subgraph CostGuard[Cost Guard 🔒]
        style CostGuard stroke-dasharray: 4 4
        A[gpt_call()] --> CSV[usage_log.csv]
    end

    Q["Prompt Gen<br/>(gpt‑4o‑mini)"] -->|question| Fan[Provider Fan‑out]

    %% Competitor calls
    Fan --> OA[gpt‑4o‑mini]
    Fan --> CL[claude‑3]
    Fan --> GM[gemini‑flash]
    Fan --> DS[deepseek]
    Fan --> GR[llama‑3 (Groq)]
    Fan --> OL[llama‑3 (Ollama)]

    %% Collect answers
    OA --> Coll[Answer Collector]
    CL --> Coll
    GM --> Coll
    DS --> Coll
    GR --> Coll
    OL --> Coll

    %% Judge path
    Coll --> JP[Judge Prompt]
    JP --> J[o3‑mini judge]
    J -->|JSON rank| LB[Leaderboard]

    %% Log arrow
    A -. logs .-> LB
---

## 🚀 Quick Start

```bash
# 1 Clone & enter
$ git clone https://github.com/your‑user/llm‑competitor‑analysis.git && cd llm‑competitor‑analysis

# 2 Create env & install
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt

# 3 Add keys (see .env.example for all options)
$ cp .env.example .env && $EDITOR .env  # paste your secrets

# 4 Run the showdown
$ python llm_competitor_analysis.py
```

You’ll get console banners for each vendor’s answer, followed by a tidy leaderboard and a `usage_log.csv` showing you spent pennies.

---

## 🛠️ Tech Stack

- **Python 3.11**  •  **OpenAI Python SDK ≥ 1.23**  •  **Anthropic SDK**  •  `python‑dotenv`  •  **Black/Ruff**  •  **pytest**

---

## 🔍 What to Look for in the Code

* `openai_guard.py` — model‑aware param shims, FX conversion, CSV logger.
* `providers.py` — feather‑weight wrappers with identical signatures.
* `llm_competitor_analysis.py` — main flow, retry logic, regex JSON rescue.
* `tests/` — unit tests mocking provider responses and cost‑guard maths.

Each commit message follows Conventional Commits for clean history.



## 📄 License

Released under the MIT License — fork, iterate, and impress.
