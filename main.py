import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from sheeva import define_default_flow as define_crypto_flow, TCCFlow
from aivail import define_default_flow as define_llm_flow, LLMFlow, LLMCoordinator, LLMEntropyEngine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
try:
    app = FastAPI(title="TCC Flow API", description="API for executing Sheeva and Aivail flows", version="1.0.0")
    logger.info("FastAPI app initialized successfully")

    # Mount static directory for index.html
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted at /static")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured")

except Exception as e:
    logger.error(f"Failed to initialize FastAPI app: {str(e)}")
    raise

# Pydantic models
class ExecuteInput(BaseModel):
    script: str
    input_data: str
    arbitrary_input: Optional[str] = None
    target_output: Optional[str] = None
    aes_key: Optional[str] = None
    ed25519_key: Optional[str] = None
    model_name: Optional[str] = "distilgpt2"
    num_layers: Optional[int] = 2
    include_keccak: Optional[bool] = False
    commit_entropy: Optional[str] = None
    reveal_entropy: Optional[str] = None
    commit_sampling: Optional[str] = None
    reveal_sampling: Optional[str] = None
    user_id: Optional[str] = "user1"
    fee: Optional[int] = 1000
    deploy_shard: Optional[bool] = False

class LogEntry(BaseModel):
    step: int
    operation: str
    input_data: str
    output_data: str
    metadata: Dict[str, Any]
    log_level: str
    error_code: str
    prev_hash: str
    operation_id: str
    timestamp: int
    execution_time_ns: int

class ExecuteResponse(BaseModel):
    output: str
    logs: List[LogEntry]

class LogsResponse(BaseModel):
    logs: List[LogEntry]

# Utility function
def read_logs(log_file: str) -> List[LogEntry]:
    logs = []
    try:
        if not os.path.exists(log_file):
            logger.info(f"Log file {log_file} not found, creating empty file")
            with open(log_file, "w") as f:
                pass
        with open(log_file, "r") as f:
            for line in f:
                try:
                    log = json.loads(line.strip())
                    logs.append(LogEntry(**log))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in log file {log_file}: {line.strip()}")
                    continue
    except Exception as e:
        logger.error(f"Failed to read log file {log_file}: {str(e)}")
    return logs

# Route handlers
@app.get("/", response_class=HTMLResponse)
async def root():
    logger.debug("Serving root endpoint")
    try:
        with open("static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        logger.error("index.html not found in static/")
        raise HTTPException(status_code=404, detail="index.html not found")

@app.post("/execute", response_model=ExecuteResponse)
async def execute(data: ExecuteInput):
    logger.debug(f"Executing script: {data.script}, payload: {data.dict()}")
    logs = []
    output = ""

    try:
        # Validate input_data
        if not data.input_data or len(data.input_data) > 1024:
            raise ValueError("Input data must be non-empty and at most 1024 characters")

        if data.script == "sheeva":
            # Validate AES key
            if not data.aes_key or len(data.aes_key) != 32:
                raise ValueError("AES key must be 32 hex characters")
            try:
                aes_key = bytes.fromhex(data.aes_key)
            except ValueError:
                raise ValueError("AES key must be valid hex")

            # Validate Ed25519 key
            if not data.ed25519_key or len(data.ed25519_key) != 64:
                raise ValueError("Ed25519 key must be 64 hex characters")
            try:
                ed25519_key = bytes.fromhex(data.ed25519_key)
            except ValueError:
                raise ValueError("Ed25519 key must be valid hex")

            # Validate fee
            if data.fee < 1000:
                raise ValueError("Fee must be at least 1000")

            logger.debug(f"Initializing TCCFlow with include_keccak={data.include_keccak}")
            flow = define_crypto_flow(aes_key, ed25519_key, include_keccak=data.include_keccak)

            if data.commit_entropy or data.reveal_entropy:
                output += "Warning: Entropy commit/reveal not supported in sheeva.py\n"

            if data.deploy_shard:
                output += "Warning: Shard deployment not supported in sheeva.py\n"

            logger.debug(f"Executing flow with input: {data.input_data}")
            # --- THIS IS THE KEY LINE: ---
            result = flow.execute(data.input_data.encode())
            output = result.hex()

            # Optionally reverse
            if data.target_output:
                try:
                    logger.debug(f"Reversing flow with target_output: {data.target_output}")
                    reconstructed = flow.reverse(bytes.fromhex(data.target_output))
                    output += f"\nReconstructed input: {reconstructed.decode(errors='replace')}"
                except ValueError as e:
                    output += f"\nReverse error: {str(e)}"

            logger.debug("Saving flow log")
            flow.save_log("tcc_flow_log.jsonl")
            # Use the flow's log attribute directly, if available
            logs = flow.flow_log  # This is step-by-step, as in your class

        # ... (rest of your code for "aivail" etc. unchanged) ...

        return ExecuteResponse(output=output, logs=logs)

    except ValueError as e:
        logger.error(f"ValueError in execute: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in execute: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/reverse", response_model=ExecuteResponse)
async def reverse(data: ExecuteInput):
    logger.debug(f"Reversing script: {data.script}, payload: {data.dict()}")
    if not data.target_output:
        raise HTTPException(status_code=400, detail="Target output is required")
    try:
        if data.script == "sheeva":
            if not data.aes_key or not data.ed25519_key:
                raise ValueError("AES and Ed25519 keys are required")
            flow = define_crypto_flow(bytes.fromhex(data.aes_key), bytes.fromhex(data.ed25519_key), data.include_keccak)
            result = flow.reverse(bytes.fromhex(data.target_output))
            flow.save_log("tcc_flow_log.jsonl")
            return ExecuteResponse(output=result.decode(), logs=read_logs("tcc_flow_log.jsonl"))
        elif data.script == "aivail":
            flow = define_llm_flow(data.model_name, data.num_layers)
            result = flow.reverse(data.target_output)
            flow.save_flow_log("llm_flow_log.jsonl")
            return ExecuteResponse(output=result, logs=read_logs("llm_flow_log.jsonl"))
        raise HTTPException(status_code=400, detail="Invalid script")
    except ValueError as e:
        logger.error(f"ValueError in reverse: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in reverse: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/reverse_arbitrary", response_model=ExecuteResponse)
async def reverse_arbitrary(data: ExecuteInput):
    logger.debug(f"Reverse arbitrary for script: {data.script}, payload: {data.dict()}")
    if not data.target_output or not data.arbitrary_input:
        raise HTTPException(status_code=400, detail="Target output and arbitrary input are required")
    try:
        if data.script == "aivail":
            flow = define_llm_flow(data.model_name, data.num_layers)
            result = flow.reverse_arbitrary(data.target_output, data.arbitrary_input)
            flow.save_flow_log("llm_flow_log.jsonl")
            return ExecuteResponse(output=result, logs=read_logs("llm_flow_log.jsonl"))
        raise HTTPException(status_code=400, detail="Only aivail supports reverse_arbitrary")
    except ValueError as e:
        logger.error(f"ValueError in reverse_arbitrary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in reverse_arbitrary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/commit_entropy", response_model=ExecuteResponse)
async def commit_entropy(data: ExecuteInput):
    logger.debug(f"Committing entropy for script: {data.script}, payload: {data.dict()}")
    if not data.commit_entropy:
        raise HTTPException(status_code=400, detail="Commit entropy is required")
    try:
        if data.script == "aivail":
            coordinator = LLMCoordinator(LLMEntropyEngine(), LLMEntropyEngine(), LLMEntropyEngine())
            seed, temp = map(float, data.commit_entropy.split(":"))
            coordinator.commit_sampling_all(data.user_id, int(seed), temp, int(seed), temp, int(seed), temp)
            coordinator.save_log("llm_flow_log.jsonl")
            return ExecuteResponse(
                output=f"Committed sampling for {data.user_id}: seed={seed}, temp={temp}",
                logs=read_logs("llm_flow_log.jsonl")
            )
        raise HTTPException(status_code=400, detail="Only aivail supports commit_entropy")
    except ValueError as e:
        logger.error(f"ValueError in commit_entropy: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in commit_entropy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/reveal_entropy", response_model=ExecuteResponse)
async def reveal_entropy(data: ExecuteInput):
    logger.debug(f"Revealing entropy for script: {data.script}, payload: {data.dict()}")
    if not data.reveal_entropy:
        raise HTTPException(status_code=400, detail="Reveal entropy is required")
    try:
        if data.script == "aivail":
            coordinator = LLMCoordinator(LLMEntropyEngine(), LLMEntropyEngine(), LLMEntropyEngine())
            seed, temp = map(float, data.reveal_entropy.split(":"))
            coordinator.reveal_sampling_all(data.user_id, int(seed), temp, int(seed), temp, int(seed), temp, data.fee)
            coordinator.save_log("llm_flow_log.jsonl")
            return ExecuteResponse(
                output=f"Revealed sampling for {data.user_id}: seed={seed}, temp={temp}",
                logs=read_logs("llm_flow_log.jsonl")
            )
        raise HTTPException(status_code=400, detail="Only aivail supports reveal_entropy")
    except ValueError as e:
        logger.error(f"ValueError in reveal_entropy: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in reveal_entropy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/deploy_shard", response_model=ExecuteResponse)
async def deploy_shard(data: ExecuteInput):
    logger.debug(f"Deploying shard for script: {data.script}, payload: {data.dict()}")
    try:
        if data.script == "sheeva":
            return ExecuteResponse(
                output="Shard deployment not supported in sheeva.py",
                logs=read_logs("tcc_flow_log.jsonl")
            )
        raise HTTPException(status_code=400, detail="Only sheeva supports deploy_shard")
    except Exception as e:
        logger.error(f"Unexpected error in deploy_shard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/logs/{log_file}", response_model=LogsResponse)
async def get_logs(log_file: str):
    logger.debug(f"Fetching logs for file: {log_file}")
    if log_file not in ["tcc_flow_log.jsonl", "llm_flow_log.jsonl"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid log file. Use 'tcc_flow_log.jsonl' or 'llm_flow_log.jsonl'."
        )
    logs = read_logs(log_file)
    if not logs and not os.path.exists(log_file):
        return LogsResponse(logs=[])
    return LogsResponse(logs=logs)