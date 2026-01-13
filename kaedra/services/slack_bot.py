import os
import logging
import asyncio
from typing import Optional
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# Configure logging
logger = logging.getLogger("kaedra.slack")

class SlackService:
    """
    Service to handle Slack interactions via Socket Mode.
    Integrates with Kaedra agent to process messages.
    """
    def __init__(self):
        # Load credentials (prefer env vars)
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.bot_token = os.getenv("SLACK_BOT_TOKEN") # Must be provided by user (xoxb-...)
        
        self.app: Optional[AsyncApp] = None
        self.handler: Optional[AsyncSocketModeHandler] = None
        self.agent = None  # Reference to Kaedra agent

    def initialize(self, agent=None):
        """Initialize the Slack app and handler."""
        self.agent = agent
        
        if not self.bot_token:
            logger.warning("⚠️ SLACK_BOT_TOKEN (xoxb-...) is missing. Slack integration will not start.")
            return

        try:
            self.app = AsyncApp(token=self.bot_token, signing_secret=self.signing_secret)
            
            # Register Event Listeners
            self._register_listeners()
            
            # Initialize Socket Mode Handler
            self.handler = AsyncSocketModeHandler(self.app, self.app_token)
            logger.info("✅ SlackService initialized.")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize SlackService: {e}")

    def _register_listeners(self):
        """Register Slack event listeners."""
        
        @self.app.event("app_mention")
        async def handle_app_mention(event, say):
            """Handle @Kaedra mentions."""
            user = event.get("user")
            text = event.get("text")
            channel = event.get("channel")
            ts = event.get("ts")
            
            logger.info(f"📩 Slack Mention from {user}: {text}")
            
            # Indicate processing
            # await self.app.client.reactions_add(channel=channel, name="eyes", timestamp=ts)

            response_text = await self._process_with_agent(text, user)
            
            await say(text=response_text, thread_ts=ts)

        # Ralph-style Operations Commands
        
        @self.app.command("/kaedra-ingest")
        async def handle_ingest(ack, body, say):
            await ack()
            input_data = body.get("text", "").strip()
            user = body.get("user_id")
            logger.info(f"📥 /kaedra-ingest from {user}: {input_data}")
            
            if self.agent and hasattr(self.agent, "orchestrator"):
                await self.agent.orchestrator.ingest_job(input_data, user)
                await say(f"📥 **Job Ingested**\nSource: `{input_data}`\nStatus: `QUEUED`")
            else:
                await say(f"⚠️ Orchestrator offline. Cannot ingest `{input_data}`.")

        @self.app.command("/kaedra-run")
        async def handle_run(ack, body, say):
            await ack()
            job_id = body.get("text", "").strip()
            logger.info(f"▶️ /kaedra-run: {job_id}")
            # For now, treat run same as ingest or re-trigger
            if self.agent and hasattr(self.agent, "orchestrator"):
                 await self.agent.orchestrator.ingest_job(job_id, body.get("user_id"))
                 await say(f"▶️ **Starting Job**\nID: `{job_id}`\nStatus: `RUNNING`")

        @self.app.command("/kaedra-status")
        async def handle_status(ack, body, say):
            await ack()
            job_id = body.get("text", "").strip() or "active"
            logger.info(f"📊 /kaedra-status: {job_id}")
            
            status = "UNKNOWN"
            if self.agent and hasattr(self.agent, "orchestrator"):
                status = self.agent.orchestrator.get_status(job_id)
            
            await say(f"📊 **Job Status**\nID: `{job_id}`\nState: `{status}`")

        @self.app.command("/kaedra-pause")
        async def handle_pause(ack, body, say):
            await ack()
            logger.info("⏸️ /kaedra-pause called")
            if self.agent and hasattr(self.agent, "orchestrator"):
                self.agent.orchestrator.pause_system()
            await say("⏸️ **System Paused**\nKill Switch: `ACTIVE`\nAll jobs suspended.")

        @self.app.command("/kaedra-resume")
        async def handle_resume(ack, body, say):
            await ack()
            logger.info("▶️ /kaedra-resume called")
            if self.agent and hasattr(self.agent, "orchestrator"):
                self.agent.orchestrator.resume_system()
            await say("▶️ **System Resumed**\nKill Switch: `OFF`\nJobs processing.")

        @self.app.command("/kaedra-kill")
        async def handle_kill(ack, body, say):
            await ack()
            job_id = body.get("text", "").strip()
            logger.info(f"💀 /kaedra-kill: {job_id}")
            if self.agent and hasattr(self.agent, "orchestrator"):
                await self.agent.orchestrator.kill_task(job_id)
            await say(f"💀 **Job Killed**\nID: `{job_id}`\nStatus: `TERMINATED`")

        @self.app.command("/kaedra-approve")
        async def handle_approve(ack, body, say):
            await ack()
            job_id = body.get("text", "").strip()
            logger.info(f"✅ /kaedra-approve: {job_id}")
            if self.agent and hasattr(self.agent, "orchestrator"):
                await self.agent.orchestrator.approve_task(job_id)
            await say(f"✅ **Job Approved**\nID: `{job_id}`\nMoving to `EXECUTION` queue.")

        @self.app.command("/kaedra-deny")
        async def handle_deny(ack, body, say):
            await ack()
            job_id = body.get("text", "").strip()
            logger.info(f"🚫 /kaedra-deny: {job_id}")
            if self.agent and hasattr(self.agent, "orchestrator"):
                await self.agent.orchestrator.deny_task(job_id)
            await say(f"🚫 **Job Denied**\nID: `{job_id}`\nStatus: `REJECTED`")

        @self.app.message("")
        async def handle_dm(message, say):
            """Handle Direct Messages."""
            if message.get("channel_type") != "im":
                return
                
            user = message.get("user")
            text = message.get("text")
            ts = message.get("ts")
            
            logger.info(f"📩 Slack DM from {user}: {text}")
            
            response_text = await self._process_with_agent(text, user)
            await say(text=response_text)

    async def _process_with_agent(self, text: str, user_id: str) -> str:
        """Process message via Kaedra Agent."""
        try:
            # Clean text (remove mention)
            clean_text = text.replace(f"<@{self.app.client.auth_test()['user_id']}>", "").strip()
            
            if self.agent:
                # TODO: Integrate valid agent call
                # response = await self.agent.process(clean_text, context={"user": user_id, "platform": "slack"})
                # return response.content
                return f"🤖 Kaedra received: '{clean_text}' (Agent logic pending)"
            else:
                return f"🤖 Echo: {clean_text} (Agent not connected)"
                
        except Exception as e:
            logger.error(f"Agent Processing Error: {e}")
            return "⚠️ I encountered an error processing your request."

    async def start(self):
        """Start the Socket Mode listener."""
        if self.handler:
            logger.info("🚀 Starting Slack Socket Mode...")
            await self.handler.start_async()
