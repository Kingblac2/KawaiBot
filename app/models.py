from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user query or prompt to be answered.")

class ChatResponse(BaseModel):
    intent: str = Field(..., description="The detected intent of the user query.")
    risk_level: str = Field(..., description="The calculated security risk level (safe, low, medium, high).")
    response: str = Field(..., description="The professional text response from the chatbot.")
    reasoning_steps: List[str] = Field(default=[], description="Chain-of-thought steps taken to construct response.")
    react_thought: Optional[str] = Field(None, description="The internal thought step from the ReAct flow.")
    react_action: Optional[str] = Field(None, description="The internal action step from the ReAct flow.")
    react_observation: Optional[str] = Field(None, description="The internal observation step from the ReAct flow.")
