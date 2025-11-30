import os
import time
import base64
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
except ImportError:
    print("Playwright not installed. Computer Use Agent will not function.")
    sync_playwright = None

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    Content,
    Part,
    FunctionDeclaration,
    Schema,
    Type
)

from config import PROJECT_ID, LOCATION, MODEL_COSTS, Colors
from core.cost_manager import cost_manager

# Configuration
COMPUTER_USE_MODEL = "gemini-2.5-computer-use-preview-10-2025"
MAX_STEPS = 15

class ComputerAgent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        self.history = []
        
    def start_session(self, headless: bool = False):
        """Initialize the browser session."""
        if not sync_playwright:
            raise ImportError("Playwright is required for Computer Agent.")
            
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.context = self.browser.new_context(
            viewport={'width': 1024, 'height': 768},
            device_scale_factor=1
        )
        self.page = self.context.new_page()
        print(f"{Colors.NEON_CYAN}[COMPUTER]{Colors.RESET} Browser session started.")

    def stop_session(self):
        """Close the browser session."""
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        print(f"{Colors.NEON_CYAN}[COMPUTER]{Colors.RESET} Session ended.")

    def _get_screenshot_b64(self) -> str:
        """Capture screenshot and return as base64 string."""
        screenshot_bytes = self.page.screenshot(format="jpeg", quality=80)
        return base64.b64encode(screenshot_bytes).decode('utf-8')

    def _get_tools(self) -> List[Tool]:
        """Define tools for the model."""
        return [Tool(function_declarations=[
            FunctionDeclaration(
                name="click_element",
                description="Click on an element at specific coordinates or by selector.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "x": Schema(type=Type.INTEGER, description="X coordinate"),
                        "y": Schema(type=Type.INTEGER, description="Y coordinate"),
                        "description": Schema(type=Type.STRING, description="Description of what is being clicked")
                    },
                    required=["x", "y"]
                )
            ),
            FunctionDeclaration(
                name="type_text",
                description="Type text into the focused element.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "text": Schema(type=Type.STRING, description="Text to type"),
                        "submit": Schema(type=Type.BOOLEAN, description="Whether to press Enter after typing")
                    },
                    required=["text"]
                )
            ),
            FunctionDeclaration(
                name="scroll",
                description="Scroll the page.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "direction": Schema(type=Type.STRING, description="'up' or 'down'"),
                        "amount": Schema(type=Type.INTEGER, description="Pixels to scroll (default 500)")
                    },
                    required=["direction"]
                )
            ),
            FunctionDeclaration(
                name="navigate",
                description="Go to a specific URL.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "url": Schema(type=Type.STRING, description="URL to navigate to")
                    },
                    required=["url"]
                )
            ),
            FunctionDeclaration(
                name="task_complete",
                description="Call this when the user's task is finished.",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "summary": Schema(type=Type.STRING, description="Summary of what was achieved")
                    },
                    required=["summary"]
                )
            )
        ])]

    def execute_task(self, instruction: str):
        """Run the agent loop for a task."""
        if not self.page:
            self.start_session()
            
        print(f"{Colors.NEON_CYAN}[COMPUTER]{Colors.RESET} Task: {instruction}")
        self.history = [
            Content(role="user", parts=[Part(text=f"You are a computer use agent. You have control over a browser. Goal: {instruction}")])
        ]
        
        step = 0
        while step < MAX_STEPS:
            step += 1
            print(f"{Colors.DIM}[Step {step}/{MAX_STEPS}]{Colors.RESET}")
            
            # 1. Capture State
            screenshot_b64 = self._get_screenshot_b64()
            
            # 2. Prepare Request
            # We send the screenshot as a part of the user message (or system context in this flow)
            # For the chat flow, we append the screenshot to the history or send it in the new turn
            
            # Create the message for this turn
            # Note: In a real multi-turn chat, we'd append to history. 
            # Here we construct the turn.
            
            # Add screenshot to the latest user message or as a new user message
            screen_part = Part.from_data(data=base64.b64decode(screenshot_b64), mime_type="image/jpeg")
            
            # If it's the first step, we already have the instruction in history.
            # We need to attach the screenshot to it or send a new message.
            if step == 1:
                self.history[0].parts.append(screen_part)
            else:
                self.history.append(Content(role="user", parts=[screen_part, Part(text="Current screen state. What is the next action?")]))
            
            # 3. Call Model
            try:
                # Check budget
                cost_manager.get_safe_model(COMPUTER_USE_MODEL) # Just to log check, we force model here
                
                response = self.client.models.generate_content(
                    model=COMPUTER_USE_MODEL,
                    contents=self.history,
                    config=GenerateContentConfig(
                        temperature=0.1, # Low temp for precise actions
                        tools=self._get_tools(),
                        response_modalities=["TEXT"]
                    )
                )
                
                # Record Usage
                if hasattr(response, 'usage_metadata'):
                    cost_manager.record_usage("computer", 
                                            response.usage_metadata.prompt_token_count or 0, 
                                            response.usage_metadata.candidates_token_count or 0)

            except Exception as e:
                print(f"{Colors.NEON_RED}[ERROR] Model call failed: {e}{Colors.RESET}")
                break
                
            # 4. Parse Response
            if not response.candidates:
                print("No response from model.")
                break
                
            candidate = response.candidates[0]
            self.history.append(candidate.content) # Add model response to history
            
            # Check for tool calls
            tool_calls = []
            for part in candidate.content.parts:
                if part.function_call:
                    tool_calls.append(part.function_call)
            
            if not tool_calls:
                # Just text response
                text = candidate.content.parts[0].text if candidate.content.parts else "..."
                print(f"{Colors.NEON_CYAN}[AGENT]{Colors.RESET} {text}")
                # If the model just talks without acting, we might need to prompt it to act
                continue
                
            # 5. Execute Tools
            for fc in tool_calls:
                name = fc.name
                args = fc.args
                print(f"{Colors.NEON_CYAN}[ACTION]{Colors.RESET} {name}({args})")
                
                result = {}
                try:
                    if name == "click_element":
                        self.page.mouse.click(args["x"], args["y"])
                        result = {"status": "clicked", "x": args["x"], "y": args["y"]}
                        time.sleep(1.0) # Wait for UI
                        
                    elif name == "type_text":
                        self.page.keyboard.type(args["text"])
                        if args.get("submit"):
                            self.page.keyboard.press("Enter")
                        result = {"status": "typed", "text": args["text"]}
                        time.sleep(1.0)
                        
                    elif name == "scroll":
                        amount = args.get("amount", 500)
                        if args["direction"] == "up":
                            self.page.mouse.wheel(0, -amount)
                        else:
                            self.page.mouse.wheel(0, amount)
                        result = {"status": "scrolled", "direction": args["direction"]}
                        time.sleep(0.5)
                        
                    elif name == "navigate":
                        self.page.goto(args["url"])
                        result = {"status": "navigated", "url": args["url"]}
                        time.sleep(2.0)
                        
                    elif name == "task_complete":
                        print(f"{Colors.NEON_GREEN}[DONE]{Colors.RESET} {args['summary']}")
                        return args['summary']
                        
                except Exception as e:
                    print(f"{Colors.NEON_RED}[TOOL ERROR]{Colors.RESET} {e}")
                    result = {"error": str(e)}
                
                # Add tool result to history
                self.history.append(Content(role="user", parts=[
                    Part(function_response={
                        "name": name,
                        "response": {"result": result}
                    })
                ]))
                
        print(f"{Colors.GOLD}[LIMIT]{Colors.RESET} Max steps reached.")
        return "Task stopped (max steps)."

