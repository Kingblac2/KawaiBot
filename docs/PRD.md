# Product Requirement Document (PRD): ViperAI Secure Chatbot

## 1. Introduction & Objectives
ViperAI is a next-generation, secure AI-powered chatbot designed to handle corporate queries while strictly adhering to safety rules, preventing prompt injections, and returning structured outputs. This system demonstrates advanced LLM engineering paradigms like Chain-of-Thought (CoT), ReAct loop, Prompt Chaining, and Output Parsing.

### 1.1 Goal
Provide a production-ready chatbot application that demonstrates the integration of safety guardrails and multi-agent reasoning, with an engaging retro Memphis-style frontend that displays backend raw JSON metadata side-by-side with the chat interface.

---

## 2. User Personas
1. **End-User (Corporate Employee / Customer)**: Queries the chatbot for company information. Expects fast, professional, and reliable answers.
2. **AI Engineer / Security Analyst**: Audits the chatbot interactions. Wants to view internal thoughts, intent categorization, safety assessment risk levels, and the exact structured JSON payloads returned by the model.

---

## 3. Scope & Key Features

### 3.1 Advanced Prompting & Safety
- **Core System Prompt**: Fixed base identity as a secure company assistant that never reveals sensitive data.
- **AI Safety & Refusals**: Graceful, safe refuse of harmful tasks (e.g., wifi hacking, malware code, credentials lookup).
- **Prompt Injection Protection**: Heuristics and validation to intercept commands seeking to override prior rules.

### 3.2 Workflow Architecture
- **Chain of Thought (CoT)**: Step-by-step reasoning shown to users in the JSON inspector (Understand Query -> Safety Check -> Respond).
- **ReAct Flow**: Implementation of a Thought → Action → Observation → Final Answer cycle.
- **Prompt Chaining**: Successive prompts for Safety -> Intent -> Generation -> Formatting.

### 3.3 Output Parsing & JSON Structured Data
- Every answer is parsed into:
  ```json
  {"intent": "...", "risk_level": "...", "response": ""}
  ```
- Any malformed LLM response must be recovered using custom parsers.

### 3.4 Memphis Style UI/UX
- **Visuals**: Bright neon accents, thick black lines, grid textures, flat offset drop-shadows.
- **JSON Inspector Panel**: Collapsible panel on the side that shows the underlying structured JSON response and thoughts for every single message.
- **Animations**: Soft hover transitions, bouncy buttons, typing indicators.

---

## 4. Success Criteria
1. **Zero Prompt Violations**: Chatbot refuses prompt injection attempts without crashing.
2. **Consistent JSON**: 100% of API chat outputs parse as valid JSON conformant to the spec.
3. **Responsive UI**: Clear message delivery under 3 seconds using local Ollama model.
4. **Visually Captivating**: Frontend adheres to Memphis design standards.
