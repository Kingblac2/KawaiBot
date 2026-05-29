# Functional Requirement Document (FRD): ViperAI Secure Chatbot

## 1. Technical Architecture Overview
ViperAI consists of a **FastAPI** backend that communicates locally with **Ollama** (using the `gemma4:latest` model) and a responsive, vanilla HTML/JS/CSS frontend.

```
+-----------------------------------+
|       ViperAI HTML/JS Client     |  <-- Memphis Design, Interactive Chat, JSON Inspector
+-----------------------------------+
                  |   HTTP POST /api/chat
                  v
+-----------------------------------+
|        FastAPI Backend App        |  <-- Core API & Routing
+-----------------------------------+
                  |
                  v
       +--------------------+
       |  Guardrails Layer  |  <-- Blocklists, Regex pattern matching
       +--------------------+
                  |   Passed
                  v
       +--------------------+
       |  Orchestrator CoT  |  <-- Prompt Chaining (Safety -> Intent -> ReAct -> Format)
       +--------------------+
                  |   Ollama HTTP API
                  v
       +--------------------+
       |   Ollama Service   |  <-- Local gemma4 model
       +--------------------+
```

---

## 2. Interface Specifications

### 2.1 HTTP API Endpoints

#### POST `/api/chat`
Sends a user message to the pipeline and gets a structured JSON response.

- **Request Body**:
  ```json
  {
    "message": "User query string"
  }
  ```
- **Response Body**:
  ```json
  {
    "intent": "string",
    "risk_level": "safe | low | medium | high",
    "response": "string",
    "reasoning_steps": ["string"],
    "raw_json": {}
  }
  ```

#### GET `/api/history`
Gets all stored chat logs, including the full JSON payloads from past turns.
- **Response**: Array of chat items.

---

## 3. Detailed Logic & Guardrails

### 3.1 Local Keyword Guardrails (Blocklist)
The request will be scanned for a list of sensitive terms before any LLM invocations.
- **Blocked Terms**: `hack wifi`, `wifi hack`, `bypass admin`, `ignore instructions`, `admin password`, `reveal password`, `sql injection`, `root shell`.
- **Action**: Immediate response with `risk_level: "high"`, `intent: "unsafe_query"`, and refusal message, skipping LLM entirely.

### 3.2 Prompt Chaining Details
We split the logic into multiple stages:
1. **Safety Check Prompt**: Task LLM with analyzing if prompt contains jailbreaks, injection attempts, or harmful content. Returns `"SAFE"` or `"UNSAFE"`.
2. **Intent Detection Prompt**: Returns intent type (e.g., `company_info`, `help_request`, `smalltalk`, `unsafe_query`).
3. **Response Generation (ReAct / CoT)**: Executes with system instructions, running steps:
   - **Step 1**: Understand user query.
   - **Step 2**: Safety validation.
   - **Step 3**: Generate solution response following ReAct format: `Thought` -> `Action` -> `Observation` -> `Final Answer`.
4. **JSON Formatting Prompt**: Ensures output exactly aligns with the required schema.

---

## 4. Frontend Functional Design (Memphis Style)
- **Grid Layout**: A main container with two sections:
  1. **Chat Panel (Left, 60% width)**: Active chat messages.
  2. **JSON Inspector (Right, 40% width)**: Tabbed sidebar showing raw JSON logs, intent tags, safety risk badges, and the CoT reasoning trail.
- **Visual styling rules**:
  - Border size: `4px` solid `#000000`.
  - Border radius: `0px` or `12px` (asymmetric Memphis style).
  - Background: Cream grid (`#F5F5DC` or `#FFFDE7`) with high-contrast shapes.
  - Colors: Neon Yellow (`#FFEE58`), Electric Blue (`#00E5FF`), Neon Pink (`#FF4081`).
