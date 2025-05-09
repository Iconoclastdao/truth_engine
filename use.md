# ⚡ TCC & LLM Flow API  TRUTH ENGINE

This system combines cryptographic computation (via Sheeva/TCC) with language model coordination (via Aivail/LLM) into a single programmable interface powered by FastAPI. It enables secure, auditable, and reversible computation — designed for the era of sovereign, human-AI collaboration.

---

## 🧠 What This API Can Do

### ✅ 1. Execute Flows
Run complex deterministic flows either through:
- **TCC (Sheeva)**: Trustless cryptographic computation (AES, Ed25519, KECCAK).
- **LLM (Aivail)**: Language models executed in layered, entropy-controlled flows.

### ✅ 2. Reverse Flows
Given an output, reverse it to reconstruct the original input:
- Useful for **debugging**, **verification**, or **auditing** computation chains.

### ✅ 3. Commit & Reveal Entropy (LLM only)
- Allows controlled, auditable sampling via `commit_entropy` and `reveal_entropy`.
- Coordinates randomness in LLMs to enable **reproducibility**, **fairness**, and **shared control**.

### ✅ 4. Audit Computation Logs
- Every computation step is recorded in a signed JSONL log.
- Includes input/output data, operation metadata, and timestamps.

---

## 🛠️ Use Cases

### 🔐 Cryptographic Systems
- Trusted computing flows that require verifiability and reversibility.
- Perfect for **secure enclaves**, **ZK-proofs**, and **zero-trust computing**.

### 🤖 AI Agents & DAOs
- Enables LLM agents to operate in a **transparent**, **reversible**, and **bounded** execution environment.
- Coordinates multiple agents in **layered consensus** using entropy bonding.

### 🧾 Transparent Contracts
- Outputs from either flow can be signed, logged, and verified independently.
- Useful in **governance**, **legal automation**, and **AI-human covenant contracts**.

---

## ⚙️ API Components

- `POST /execute`: Run a flow (TCC or LLM)
- `POST /reverse`: Reverse flow from output
- `POST /reverse_arbitrary`: Reverse with arbitrary context (LLM)
- `POST /commit_entropy`: Submit sampling intent
- `POST /reveal_entropy`: Reveal entropy and compute
- `GET /logs/{file}`: Retrieve JSONL logs (`tcc_flow_log.jsonl` or `llm_flow_log.jsonl`)

---

## 🚀 Why This Matters

> In a world where AI and cryptography are siloed, this framework pulls back the cover on black boxes.

You are not just running flows — you're building the *computational truth*

---
