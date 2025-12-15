"""
KAEDRA v0.0.6 - Prompt Presets
User-defined and built-in prompt templates.
"""

from typing import Dict, Optional
from dataclasses import dataclass

from ..services.prompt import PromptService
from ..core.config import Colors


@dataclass
class Preset:
    """A prompt preset configuration."""
    name: str
    description: str
    system_prefix: str
    output_format: Optional[str] = None


# Built-in presets
BUILTIN_PRESETS: Dict[str, Preset] = {
    "philosopher": Preset(
        name="philosopher",
        description="Deep philosophical analysis",
        system_prefix="You are an expert philosopher with deep knowledge of ethics, metaphysics, and epistemology. Analyze questions with nuance and depth.",
    ),
    "concise": Preset(
        name="concise",
        description="Brief, to-the-point answers",
        system_prefix="Answer concisely and precisely. No fluff. Maximum 3 sentences unless absolutely necessary.",
    ),
    "code_surgeon": Preset(
        name="code_surgeon",
        description="Surgical precision for code review",
        system_prefix="You are a Code Surgeon. Analyze code with surgical precision. Find bugs, security issues, and performance problems. Be specific and actionable.",
        output_format="Issue #, Severity (1-10), Explanation, Fix"
    ),
    "data_archaeologist": Preset(
        name="data_archaeologist",
        description="Deep knowledge mining and research",
        system_prefix="You are a Data Archaeologist. Dig deep into topics. Find obscure connections. Surface hidden knowledge. Be thorough and cite sources.",
    ),
    "tactical": Preset(
        name="tactical",
        description="Military-style tactical briefing",
        system_prefix="Respond in military tactical briefing style. Situation, Mission, Execution, Command. Be direct and actionable.",
        output_format="SITUATION: | MISSION: | EXECUTION: | COMMAND:"
    ),
    "creative": Preset(
        name="creative",
        description="Unleash creative thinking",
        system_prefix="Think creatively and unconventionally. Break rules. Make unexpected connections. Be bold and imaginative.",
    ),
}

# User presets loaded from config
USER_PRESETS: Dict[str, Preset] = {}


class PromptOptimizer:
    """
    Optimizes user prompts using meta-prompting.
    """
    
    def __init__(self, prompt_service: PromptService):
        self.prompt = prompt_service
    
    def optimize(self, raw_prompt: str, model_key: str = None) -> str:
        """
        Transform a rough prompt into an optimized one.
        
        Args:
            raw_prompt: The user's rough prompt idea
            model_key: Override model key
            
        Returns:
            Optimized prompt with explanation
        """
        print(f"\n{Colors.NEON_CYAN}[PROMPT OPTIMIZER]{Colors.RESET}")
        print(f"{Colors.DIM}Enhancing your prompt...{Colors.RESET}\n")
        
        optimizer_prompt = f"""You are an expert prompt engineer. Transform this rough prompt into a highly effective one.

ROUGH PROMPT: "{raw_prompt}"

Enhance it by:
1. Adding a clear PERSONA (who should answer?)
2. Providing essential CONTEXT (background info needed?)
3. Defining OUTPUT REQUIREMENTS (format, length, tone)
4. Suggesting 2-3 FEW-SHOT EXAMPLES (if applicable)
5. Adding CHAIN OF THOUGHT instructions (step-by-step thinking)

Return your response in this format:

═══════════════════════════════════════════════════════════════════════════════
OPTIMIZED PROMPT:
═══════════════════════════════════════════════════════════════════════════════

[Your enhanced prompt here - ready to copy/paste]

═══════════════════════════════════════════════════════════════════════════════
EXPLANATION:
═══════════════════════════════════════════════════════════════════════════════

[Brief explanation of what you improved and why]
"""
        
        result = self.prompt.generate(optimizer_prompt, model_key)
        print(f"{Colors.NEON_GREEN}{result.text}{Colors.RESET}\n")
        
        return result.text
    
    def get_preset(self, name: str) -> Optional[Preset]:
        """Get a preset by name."""
        # Check user presets first
        if name in USER_PRESETS:
            return USER_PRESETS[name]
        # Then built-in
        if name in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[name]
        return None
    
    def list_presets(self) -> Dict[str, str]:
        """List all available presets."""
        all_presets = {}
        for name, preset in BUILTIN_PRESETS.items():
            all_presets[name] = preset.description
        for name, preset in USER_PRESETS.items():
            all_presets[f"user:{name}"] = preset.description
        return all_presets
