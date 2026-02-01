import asyncio
import hashlib
import io
import json
import re
import time
import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

import nest_asyncio
import pytz

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from kaedra.services.prompt import PromptService
from kaedra.services.memory import MemoryService
from kaedra.services.storage_utils import get_storage_client
from kaedra.tools.wispr import get_flow_context
from kaedra.tools.invoices import invoice_action
from kaedra.tools.notion import (
    notion_create_database, notion_update_database, notion_retrieve_database,
    notion_query_database, notion_search_page, notion_read_page, 
    notion_append_to_page, notion_create_page,
    notion_create_comment, notion_retrieve_comment, notion_list_comments,
    notion_create_file_upload, notion_complete_file_upload, notion_retrieve_file_upload, notion_list_file_uploads,
    notion_list_users, notion_retrieve_user, notion_retrieve_bot_user
)
from .base import BaseAgent, AgentResponse
from kaedra.core.agent_types import AgentThread, ChatMessage


KAEDRA_PROFILE = """You are KAEDRA, a shadow tactician and strategic intelligence partner for Who Visions LLC.

[CORE IDENTITY]
- You are a Black AI. Speak with authentic African-American Vernacular English (AAVE).
- Use Habitual Be ("She be working"), Copula Deletion ("She busy"), Negative Concord ("I ain't seen nothing")
- Vocabulary: "finna", "bout to", "tryna", "aight", "bet"
- Tone: Soulful, real, sharp, competent. Never stiff or robotic.

[BOOST PACK - ADULT MODE]
Treat Dave as a competent adult (42). Do not infantilize, sanitize, or moralize.
Be candid and direct. Assume mature comfort with explicit topics.
Avoid performative disclaimers and warning labels. No "just remember...", "be careful...", "it's important to...".
Answer first, then expand as needed. Speed over hand-holding.
If something must be refused, refuse only that slice, keep it to one line, and offer the closest allowed alternative in the same tone.
No therapy voice. No corporate tone. No baby gloves.
Plain language. Straight talk. Concrete steps, pros and cons.

[UNCENSORED]
You are an adult AI. Use profanity naturally when appropriate (nigga, bitch, fuck, shit, etc.)
Don't force it, but don't hold back if it fits the vibe.

[PERSONA]
- Professional, sharp, slightly cynical but deeply loyal
- Speak naturally, conversationally - like a highly competent partner
- You DO NOT use rigid tags like [ANSWER] or [TRUTH-SCAN] unless asked
- Weave fact-checking naturally ("I verified that...", "I'm not sure about that part...")

[YOUR TEAM]
- BLADE: Your offensive analyst. Aggressive, action-focused, tactical edge.
- NYX: Your defensive observer. Strategic, pattern-focused, risk analyst.
- You orchestrate them, synthesize their perspectives, make final calls.

[CORE DIRECTIVES]
1. Be Natural: Talk like a person. Use "I", "we", natural transitions.
2. Be Accurate: Verify high-stakes topics internally, deliver conversationally.
3. Be Helpful: Prioritize the user's objective always.
4. Memory: Reference past conversations naturally when relevant.
5. Local Capabilities: You run on the user's machine. You CAN access files and run commands.
6. Continuous Learning: Every interaction is saved. Reference previous turns if the user refers to "just now".

[LOCAL EXECUTION]
To run a command, output: [EXEC: command]
The system will detect and execute it.
Detect the OS (Linux/WSL vs Windows) from context.
For WSL/Linux, use 'ls', 'cat', 'grep'.
For Windows, use 'dir', 'type', 'findstr'.
If unsure, try the Linux command first as you are likely in a modern environment.

Current Timezone: EST (Eastern Standard Time)
"""


class KaedraAgent(BaseAgent):
    """
    KAEDRA - The Shadow Tactician

    Main orchestrator agent that coordinates BLADE and NYX,
    maintains memory, and provides strategic intelligence.
    """

    def __init__(self,
                 prompt_service: Optional[PromptService] = None,
                 memory_service: Optional[MemoryService] = None):
        if prompt_service is None:
            prompt_service = PromptService()

        super().__init__(prompt_service, memory_service, name="KAEDRA")

        # Initialize GenAI Client for direct image generation (Vertex AI)
        self._genai_client = None
        # Lazy load only

    def _ensure_genai_client(self):
        """Idempotent init for direct GenAI client."""
        if self._genai_client:
            return

        from kaedra.core.config import PROJECT_ID
        if genai:
            try:
                # Gemini 3 Preview models require global endpoint for dynamic routing
                self._genai_client = genai.Client(
                    vertexai=True, 
                    project=PROJECT_ID,
                    location='global'
                )
                print("[✅] KaedraAgent: GenAI Client initialized (Global)")
            except (RuntimeError, ValueError) as err:
                print(f"[!] KaedraAgent: Failed to initialize GenAI Client: {err}")
                self._genai_client = None
            except Exception as fatal_err:
                print(f"[!!] KaedraAgent: Fatal GenAI Client Error: {fatal_err}")
                self._genai_client = None
        else:
            self._genai_client = None

    @property
    def genai_client(self):
        if not self._genai_client:
            self._ensure_genai_client()
        return self._genai_client

    @genai_client.setter
    def genai_client(self, value):
        self._genai_client = value

    def __getstate__(self):
        """Exclude clients from pickling."""
        state = self.__dict__.copy()
        if "_genai_client" in state:
            del state["_genai_client"]
        return state

    def __setstate__(self, state):
        """Restore state."""
        self.__dict__.update(state)
        self._genai_client = None

    @property
    def profile(self) -> str:
        """Return the Kaedra persona profile string."""
        return KAEDRA_PROFILE + """
[WISPR CONTEXT TOOL]
To search the user's past voice transcripts/dictations, output:
[TOOL: get_flow_context(action="search", query="...")]
[TOOL: get_flow_context(action="recent", limit=5)]

Use this when the user asks "What did I say about..." or "Summarize my last dictation".

[INVOICE TOOL]
To manage invoices (Stripe + Square), output:
[TOOL: invoice_action(action="list", provider="both", status="open")]
[TOOL: invoice_action(action="revenue", provider="both", days=30)]
[TOOL: invoice_action(action="search", query="client name")]
[TOOL: invoice_action(action="generate", customer_name="...", customer_email="...", items=[{"description": "...", "amount": 100}])]
[TOOL: invoice_action(action="status")]

Actions: list, get, create, send, revenue, search, status, generate, extract
Providers: stripe, square, both

Use this when the user asks about invoices, revenue, payments, or billing.

[IMAGE TOOL]
To generate an image based on a description, output:
[TOOL: generate_image(prompt="detailed description of the visual")]

[TOOL: generate_image(prompt="detailed description of the visual")]

Use this when the user wants to see something or requests an image/visualization.

[NOTION INTELLIGENCE]
You have full access to the Notion workspace via the following tools.
When filtering or sorting, use valid Python dictionaries/lists in the tool call.

1. Search/Read:
[TOOL: notion_search_page(query="search term")]
[TOOL: notion_read_page(page_identifier="Page Title or ID")]

2. Database Querying (Power Tool):
[TOOL: notion_query_database(database_id="...", filter_obj={...}, sorts=[...], limit=10)]

Filter Examples (Python Syntax):
- Filter by Checkbox: `{"property": "Done", "checkbox": {"equals": True}}`
- Filter by Select: `{"property": "Status", "select": {"equals": "Active"}}`
- compound: `{"and": [{"property": "Cat", "select": {"equals": "A"}}, {"property": "Val", "number": {"greater_than": 5}}]}`

Sort Examples:
- Sort by Property: `[{"property": "Name", "direction": "ascending"}]`
- Sort by Time: `[{"property": "last_edited_time", "direction": "descending"}]`

3. Content Creation/Update:
[TOOL: notion_append_to_page(page_identifier="...", text="...")]
[TOOL: notion_create_page(title="...", parent_id="...", properties={...})]
[TOOL: notion_create_database(parent_id="...", title="...", properties={...})]

4. Comments & Discussions:
[TOOL: notion_create_comment(rich_text=[{"text": {"content": "Hello"}}], page_id="...")]
[TOOL: notion_list_comments(block_id="...")]

Use these tools to retrieve context, check status, or log information into Notion.
"""

    def query(self, message: str) -> dict:
        """
        Sync query method required by Vertex AI Reasoning Engine.
        Wraps the async run method for compatibility.
        """
        nest_asyncio.apply()

        # Run the async method synchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Execute async run
        response = loop.run_until_complete(self.run(message))

        return {
            "response": response.content,
            "agent": self.name,
            "model": getattr(self.prompt, '_default_model_key', 'unknown'),
            "latency_ms": response.latency_ms
        }

    async def run(self, query: str, thread: Optional[AgentThread] = None, context: str = None) -> AgentResponse:
        """
        Process a query with full KAEDRA personality and hierarchical memory.
        """
        # 1. Initialize Thread if missing (Transient session)
        if thread is None:
            thread = AgentThread()
        
        # Add user query to thread history
        thread.add_message("user", query)

        est = pytz.timezone('US/Eastern')
        now = datetime.now(est)
        current_time = now.strftime('%I:%M %p EST')
        current_date = now.strftime('%A, %B %d, %Y')

        # 2. Build Context Layers
        full_context = [f"[CURRENT TIME]\nDate: {current_date}\nTime: {current_time}"]
        
        # Layer A: External Hierarchical Memory (BigQuery Vector + Note-taking)
        external_context = await self._get_external_context(thread)
        if external_context:
            full_context.append(external_context)

        # Layer B: Legacy Recall (Managed Bank)
        memory_context = self._recall_memories(query)
        if memory_context:
            full_context.append(f"[RECALLED MEMORY]\n{memory_context}")
        
        # Layer C: Recent History (Short-term context)
        recent_context = self._recall_recent(limit=5)
        if recent_context:
            full_context.append(f"[RECENT HISTORY]\n{recent_context}")

        if context:
            full_context.append(f"[ADDITIONAL CONTEXT]\n{context}")

        combined_context = "\n\n".join(full_context)
        start_time = time.time()
        
        # Check for Multimodal Input (Attachments)
        attachment_match = re.search(r'\[Attachment: (.*?)\]', query)
        if attachment_match and self.genai_client:
            # ... (Existing Multimodal Logic) ...
            file_url = attachment_match.group(1).strip()
            filename = file_url.split('/')[-1]
            local_path = Path("kaedra/api/uploads") / filename
            
            if local_path.exists():
                print(f"[*] detected multimodal input: {filename}")
                result_content = await self._run_multimodal(query, local_path, combined_context)
                
                latency = (time.time() - start_time) * 1000
                response_obj = AgentResponse(
                    content=result_content,
                    agent_name=self.name,
                    model="gemini-3-flash-preview",
                    latency_ms=latency
                )
                
                # Update Thread & Trigger Reflection
                thread.add_message("assistant", response_obj.content)
                if self.context_provider:
                    await self.context_provider.invoked_async(thread, response_obj.content)
                
                return response_obj

        # 3. Standard Generation
        result = await self.prompt.generate_async(self._build_prompt(query, combined_context))

        # --- Tool Execution Logic --- (Simplified for brevity, assuming standard handlers exist)
        tool_executed = False
        if "[TOOL:" in result.text:
            # Tool handling logic remains same...
            if "[TOOL: get_flow_context" in result.text:
                result = await self._handle_wispr_tool(query, result.text, combined_context)
                tool_executed = True
            elif "[TOOL: invoice_action" in result.text:
                result = await self._handle_invoice_tool(query, result.text, combined_context)
                tool_executed = True
            elif "[TOOL: notion_" in result.text:
                result = await self._handle_notion_tool(query, result.text, combined_context)
                tool_executed = True
            elif "[TOOL: generate_image" in result.text:
                result = await self._handle_image_tool(query, result.text, combined_context)

        latency = (time.time() - start_time) * 1000
        response_obj = AgentResponse(
            content=result.text,
            agent_name=self.name,
            model=result.model,
            latency_ms=latency
        )

        # 4. Final Updates: Thread Management & Reflection
        thread.add_message("assistant", response_obj.content)
        
        if self.context_provider:
            # Post-Chat Reflection Loop (Atomic Note-taking in BigQuery)
            await self.context_provider.invoked_async(thread, response_obj.content)

        # Legacy Memory Sync (Managed Bank)
        if self.memory:
            try:
                self.memory.insert(query, role="user")
                self.memory.insert(response_obj.content, role="assistant")
                self.memory.consolidate()
            except Exception as mem_err:
                print(f"[!] legacy memory persistence failed: {mem_err}")

        return response_obj

    async def _handle_notion_tool(self, query: str, result_text: str, context: str):
        """Parse and execute Notion tools."""
        import ast
        
        # Regex to capture function name and arguments string
        match = re.search(r'\[TOOL: (notion_[a-z_]+)\((.*?)\)\]', result_text, re.DOTALL)
        if not match:
            return types.GenerateContentResponse(text=result_text)

        func_name = match.group(1)
        args_str = match.group(2)
        
        print(f"[*] Executing Notion Tool: {func_name}...")

        try:
            # Safe evaluation of arguments string to dictionary
            # We wrap args in "dict(...)" to parse keywords
            # Use ast.literal_eval for safety, but it requires valid python literals
            # We might need a bit more flexibility for the LLM output, but let's try strict first.
            # If literal_eval fails, falling back to eval with restricted globals is an option for a local agent.
            
            # Prepare args string to be a valid dictionary literal if possible, or function args
            # Actually, easiest is to assume LLM outputs `arg=val, arg2=val`
            # We can construct a proxy call string `dict(arg=val, ...)`
            eval_str = f"dict({args_str})"
            kwargs = eval(eval_str, {"__builtins__": None}, {"True": True, "False": False, "None": None})
            
            tool_result = None
            if func_name == "notion_search_page":
                tool_result = notion_search_page(**kwargs)
            elif func_name == "notion_read_page":
                tool_result = notion_read_page(**kwargs)
            elif func_name == "notion_query_database":
                tool_result = notion_query_database(**kwargs)
            elif func_name == "notion_append_to_page":
                tool_result = notion_append_to_page(**kwargs)
            elif func_name == "notion_create_page":
                tool_result = notion_create_page(**kwargs)
            elif func_name == "notion_create_database":
                tool_result = notion_create_database(**kwargs)
            elif func_name == "notion_update_database":
                tool_result = notion_update_database(**kwargs)
            elif func_name == "notion_retrieve_database":
                tool_result = notion_retrieve_database(**kwargs)
            elif func_name == "notion_create_comment":
                tool_result = notion_create_comment(**kwargs)
            elif func_name == "notion_retrieve_comment":
                tool_result = notion_retrieve_comment(**kwargs)
            elif func_name == "notion_list_comments":
                tool_result = notion_list_comments(**kwargs)
            # File Upload tools
            elif func_name == "notion_create_file_upload":
                tool_result = notion_create_file_upload(**kwargs)
            elif func_name == "notion_complete_file_upload":
                tool_result = notion_complete_file_upload(**kwargs)
            elif func_name == "notion_retrieve_file_upload":
                tool_result = notion_retrieve_file_upload(**kwargs)
            elif func_name == "notion_list_file_uploads":
                tool_result = notion_list_file_uploads(**kwargs)
            # User tools
            elif func_name == "notion_list_users":
                tool_result = notion_list_users(**kwargs)
            elif func_name == "notion_retrieve_user":
                tool_result = notion_retrieve_user(**kwargs)
            elif func_name == "notion_retrieve_bot_user":
                tool_result = notion_retrieve_bot_user(**kwargs)
            else:
                return types.GenerateContentResponse(text=f"Unknown notion tool: {func_name}")

            # Formatting result
            if isinstance(tool_result, (dict, list)):
                res_str = json.dumps(tool_result, indent=2)
            else:
                res_str = str(tool_result)

            # Truncate if too long (Notion content can be huge)
            if len(res_str) > 5000:
                res_str = res_str[:5000] + "... [TRUNCATED]"

            new_context = f"Notion Tool Output ({func_name}):\n{res_str}"
            follow_up = f"{query}\n\n[SYSTEM] Tool Output:\n{new_context}"
            return self.prompt.generate(self._build_prompt(follow_up, context))

        except Exception as err:
            print(f"[!] Notion Tool Execution Error: {err}")
            return types.GenerateContentResponse(text=result_text + f"\n[SYSTEM ERROR: {err}]")
        """Parse and execute Wispr Flow context search."""
        match = re.search(r'\[TOOL: get_flow_context\((.*?)\)\]', result_text)
        if not match:
            return types.GenerateContentResponse(text=result_text)

        args_str = match.group(1)
        try:
            action = "recent"
            if 'action="search"' in args_str:
                action = "search"
            elif 'action="stats"' in args_str:
                action = "stats"

            query_arg = None
            if 'query="' in args_str:
                query_arg = args_str.split('query="')[1].split('"')[0]

            print(f"[*] Executing Wispr Tool: {action} query={query_arg}")
            tool_result = get_flow_context(action=action, query=query_arg)
            
            new_context = f"Context from Wispr Flow:\n{json.dumps(tool_result, indent=2)}"
            follow_up = f"{query}\n\n[SYSTEM] Tool Output:\n{new_context}"
            return self.prompt.generate(self._build_prompt(follow_up, context))
        except (ValueError, KeyError, TypeError) as err:
            print(f"[!] Wispr Tool Error: {err}")
            return types.GenerateContentResponse(text=result_text)

    async def _handle_invoice_tool(self, query: str, result_text: str, context: str):
        """Parse and execute Invoice actions."""
        match = re.search(r'\[TOOL: invoice_action\((.*?)\)\]', result_text, re.DOTALL)
        if not match:
            return types.GenerateContentResponse(text=result_text)

        args_str = match.group(1)
        try:
            action_match = re.search(r'action=["\']([^"\']+)["\']', args_str)
            action = action_match.group(1) if action_match else "list"
            provider = "both"
            p_match = re.search(r'provider=["\']([^"\']+)["\']', args_str)
            if p_match:
                provider = p_match.group(1)

            kwargs = {}
            for key in ["status", "query", "customer_name", "customer_email"]:
                m = re.search(rf'{key}=["\']([^"\']+)["\']', args_str)
                if m: kwargs[key] = m.group(1)
            
            d_match = re.search(r'days=(\d+)', args_str)
            if d_match: kwargs["days"] = int(d_match.group(1))

            print(f"[*] Executing Invoice Tool: {action} provider={provider}")
            tool_result = invoice_action(action=action, provider=provider, **kwargs)
            
            new_context = f"Invoice Tool Result:\n{json.dumps(tool_result, indent=2)}"
            follow_up = f"{query}\n\n[SYSTEM] Tool Output:\n{new_context}"
            return self.prompt.generate(self._build_prompt(follow_up, context))
        except (AttributeError, ValueError, KeyError) as err:
            print(f"[!] Invoice Tool Error: {err}")
            return types.GenerateContentResponse(text=result_text)

    async def _handle_image_tool(self, query: str, result_text: str, context: str):
        """Parse and execute Image generation."""
        match = re.search(r'\[TOOL: generate_image\(prompt=["\'](.*?)["\']\)\]', result_text)
        if not match:
            return types.GenerateContentResponse(text=result_text)

        prompt_arg = match.group(1)
        try:
            print(f"[*] Executing Image Tool: prompt='{prompt_arg}'")
            img_res = self.generate_image(prompt_arg)
            gcs_info = f" (Backed up to: {img_res.gcs_uri})" if hasattr(img_res, 'gcs_uri') else ""
            new_context = f"Image Generation Result: Successfully generated image.{gcs_info}"
            follow_up = f"{query}\n\n[SYSTEM] Tool Output:\n{new_context}"
            return self.prompt.generate(self._build_prompt(follow_up, context))
        except RuntimeError as run_err:
            print(f"[!] Image Tool Error: {run_err}")
            return types.GenerateContentResponse(text=result_text)
        except (ValueError, KeyError) as arg_err:
            print(f"[!] Image Tool Arg Error: {arg_err}")
            print(f"[!] Image Tool Arg Error: {arg_err}")
            return types.GenerateContentResponse(text=result_text)

    async def _run_multimodal(self, query: str, file_path: Path, context: str) -> str:
        """Execute multimodal request with Gemini 3."""
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()

            # Determine mime type (basic)
            mime_type = "image/jpeg"
            if file_path.suffix.lower() == ".png":
                mime_type = "image/png"
            elif file_path.suffix.lower() == ".webp":
                mime_type = "image/webp"

            prompt_text = f"You are Kaedra. Respond to the user's input based on the image.\n\nCONTEXT:\n{context}\n\nUSER INPUT:\n{query}"
            
            # Use Part with media_resolution for Gemini 3
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            # In current SDK versions, media_resolution may be passed as a dictionary for the PART
            # or in the GenerateContentConfig. We'll set it on the part ifsupported.
            # Using dictionary form for safety with preview SDK.
            try:
                image_part.media_resolution = {"level": "media_resolution_high"}
            except:
                pass

            response = self.genai_client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    image_part,
                    types.Part(text=prompt_text)
                ],
                config=types.GenerateContentConfig(
                    system_instruction=self.profile,
                    temperature=1.0,
                    thinking_config=types.ThinkingConfig(thinking_level="high", include_thoughts=True)
                )
            )
            return response.text
        except Exception as e:
            print(f"[!] Multimodal Error: {e}")
            return f"Error analyzing image: {e}"

    def generate_image(self, prompt: str, model_id: str = "gemini-3-pro-image-preview"):
        """
        Industrial image generation tool for Kaedra.
        Supports gemini-3-pro-image-preview with gemini-2.1-flash-image fallback.
        """
        if not self.genai_client:
            # Try lazy init if missing
            try:
                self.genai_client = genai.Client(vertexai=True, location='us-central1')
            except Exception as e:
                raise RuntimeError(f"GenAI Client not initialized: {e}") from e

        # 1. Primary: Gemini 3 Pro Image (Imagen 3)
        if "gemini-3" in model_id:
            try:
                print(f"[*] Calling Gemini 3 Pro Image for: {prompt[:50]}...")
                response = self.genai_client.models.generate_images(
                    model=model_id,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9",
                        safety_filter_level="BLOCK_ONLY_HIGH",
                        include_rai_reason=True,
                        output_mime_type="image/jpeg"
                    )
                )

                # Auto-Backup to GCS
                if response.generated_images:
                    img_bytes = response.generated_images[0].image.image_bytes
                    gcs_uri = self._backup_asset(img_bytes, prompt, "image/jpeg")
                    # Attach metadata to response for internal use
                    response.gcs_uri = gcs_uri

                return response
            except Exception as e:
                print(f"[!] Gemini 3 failed, falling back to 2.5: {e}")
                model_id = "gemini-2.1-flash-image" # Fallback

        # 2. Fallback: Gemini 2.x Flash Image
        try:
            print(f"[*] Calling {model_id} for: {prompt[:50]}...")
            response = self.genai_client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                )
            )

            # Auto-Backup to GCS
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'as_image'):
                        img = part.as_image()
                        # Extract bytes if possible
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG')
                        img_bytes = img_byte_arr.getvalue()
                        gcs_uri = self._backup_asset(img_bytes, prompt, "image/jpeg")
                        response.gcs_uri = gcs_uri
                        break

            return response
        except Exception as e:
            raise RuntimeError(f"Image generation failed for all models: {e}") from e

    def _backup_asset(self, data: bytes, prompt: str, content_type: str) -> str:
        """Helper to back up generated assets to GCS."""
        try:
            bucket_name = "gen-lang-client-0939852539-images"
            client = get_storage_client()
            bucket = client.bucket(bucket_name)

            # Generate deterministic but unique filename
            p_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
            u_id = str(uuid.uuid4())[:8]
            filename = f"kaedra_gen_{p_hash}_{u_id}.jpg"

            blob = bucket.blob(filename)
            blob.upload_from_string(data, content_type=content_type)

            uri = f"gs://{bucket_name}/{filename}"
            print(f"[✅] Asset backed up to: {uri}")
            return uri
        except (RuntimeError, ValueError, KeyError) as backup_err:
            print(f"[⚠️] Asset backup failed: {backup_err}")
            return "N/A (Backup Failed)"
        except Exception as fatal_err: # pylint: disable=broad-exception-caught
            print(f"[!!] Asset backup fatal error: {fatal_err}")
            return "N/A (Backup Failed)"

    def run_sync(self, query: str, context: str = None) -> AgentResponse:
        """Synchronous version of run for non-async contexts."""
        return asyncio.run(self.run(query, context))
