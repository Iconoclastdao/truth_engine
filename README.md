# LLM Flow Demonstrator
# TRUTH ENGINE

*A transparent, cryptographically-logged computation and tracing framework for Large Language Models (LLMs) and cryptographic primitives.*

This project enables full traceability, reproducibility, and auditability of AI and cryptographic computation flows.

---

## License

**Open Source for Individuals & Non-Commercial Use:**  
Licensed under the MIT License.

**Commercial/Corporate Use:**  
Requires a separate commercial license.  
Contact [iconoclastdao@gmail.com](mailto:iconoclastdao@gmail.com) to inquire.

**By using this software, you agree to these terms.**

---

## What is This System?

This project provides a transparent, step-by-step logging and tracing system for both cryptographic and AI computation pipelines.  
It is designed for researchers, auditors, and developers who need to:

- Understand and audit model behavior at every layer (tokenization, embedding, transformer, decoding)
- Trace cryptographic operations (SHA256, Ed25519, AES, Keccak, etc.)
- Reproduce and verify computations with cryptographically signed logs
- Coordinate entropy and randomness in a verifiable way (for cryptography and AI sampling)

---

## How Does It Work?

### 1. Modular Computation Flows

**AI/LLM Flow:**

- Input text is tokenized, embedded, passed through transformer layers, and decoded.
- Each step is logged with input/output, metadata, and cryptographic hashes.
- Supports Hugging Face models (e.g., GPT-2).

**Cryptographic Flow:**

- Data passes through hash, signature, encryption, and other crypto primitives.
- Each operation is logged and can be reversed or mimicked for audit purposes.

### 2. Transparent Logging

- Every step in the pipeline is recorded as a signed log entry.
- Logs include operation type, input/output (base64), metadata, and cryptographic hashes.
- Logs can be exported for external audit or reproducibility.

### 3. Entropy Coordination

- Commitment and reveal mechanisms for entropy/sampling (for both crypto and AI).
- Ensures that randomness and sampling are auditable and not manipulated.

### 4. Reversibility and Mimicry

- Many operations can be reversed or mimicked, enabling input reconstruction and what-if analysis.

---

## Example Usage

**Run an LLM flow:**

```bash
python llm_flow.py --input "Hello, world!" --model-name distilgpt2 --num-layers 2
```
Run a cryptographic flow:
```bash

python tcc_flow.py --input "test" --aes-key <32 hex chars> --ed25519-key <64 hex chars>
```
See all options:
```bash
python llm_flow.py --help
python tcc_flow.py --help
```

Typical Applications

AI/ML Research:
Trace and audit every step of LLM inference for transparency and debugging.

Security & Compliance:
Provide cryptographic proof of computation steps for audits or regulatory requirements.

Reproducible Science:
Guarantee that results can be independently verified with full logs.

⸻
# 🌐 API Usage (FastAPI Server)

A full-featured FastAPI server is included to execute **Sheeva** (TCC) and **Aivail** (LLM) flows via HTTP.

## 🔧 Running the API Server

```bash
uvicorn main:app --reload
```

Note:
Ensure main.py contains your FastAPI app and the correct import paths for Sheeva and Aivail.

📡 Endpoints Overview

POST /execute
Run a cryptographic (Sheeva) or language model (Aivail) flow.

<details> <summary>Example: Sheeva (TCC Crypto)</summary>
{
  "script": "sheeva",
  "input_data": "hello world",
  "aes_key": "00112233445566778899aabbccddeeff",
  "ed25519_key": "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
  "include_keccak": true
}
</details> <details> <summary>Example: Aivail (LLM)</summary>
{
  "script": "aivail",
  "input_data": "The quick brown fox",
  "model_name": "distilgpt2",
  "num_layers": 2,
  "entropy": "42:0.8"
}
</details>
🔁 POST /reverse
Reverse a flow to get the original input:

{
  "script": "sheeva",
  "target_output": "<hex_output>",
  "aes_key": "00112233445566778899aabbccddeeff",
  "ed25519_key": "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899"
}
🔐 POST /commit_entropy and /reveal_entropy
Coordinate entropy values in a verifiable way for sampling control in LLM flows.

Commit:

{
  "script": "aivail",
  "user_id": "user1",
  "commit_entropy": "42:0.8"
}
Reveal:

{
  "script": "aivail",
  "user_id": "user1",
  "reveal_entropy": "42:0.8",
  "fee": 1000
}
📜 GET /logs/tcc_flow_log.jsonl or /logs/llm_flow_log.jsonl
Retrieve the computation log as structured JSON.


Commercial Licensing

If you are a company or wish to use this software for commercial purposes,
you must obtain a commercial license.
Contact iconoclastdao@gmail.com for details.

⸻

Disclaimer

This software is provided as-is, without warranty of any kind.
See the LICENSE file for details.
