"""
KAEDRA v0.0.9 - Skills Module
Progressive disclosure skill system inspired by Claude Agent Skills.

Features:
- Filesystem-based SKILL.md definitions
- Auto-discovery from kaedra/skills/*/SKILL.md
- Lazy loading (metadata at startup, full content on trigger)
- Backward compatible with legacy Python skills
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import re

# Try to use yaml, fall back to simple parsing
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    
def simple_yaml_parse(text: str) -> Dict[str, Any]:
    """Simple YAML frontmatter parser (no external deps)."""
    result = {}
    for line in text.strip().split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # Handle lists
            if value.startswith('[') and value.endswith(']'):
                items = value[1:-1].split(',')
                result[key] = [item.strip().strip('"\'') for item in items if item.strip()]
            elif value.isdigit():
                result[key] = int(value)
            elif value.lower() in ('true', 'false'):
                result[key] = value.lower() == 'true'
            else:
                result[key] = value.strip('"\'')
    return result


@dataclass
class SkillContext:
    """Context passed to skill activation checks."""
    user_transcription: str
    active_playbook: Optional[str] = None
    recent_history: List[Any] = None
    metadata: Dict[str, Any] = None


@dataclass
class SkillMetadata:
    """
    Lightweight skill metadata loaded at startup.
    Full instructions are lazy-loaded on first access.
    """
    name: str
    description: str
    keywords: List[str]
    priority: int
    path: Path
    light_feedback: Dict[str, str] = field(default_factory=dict)
    _instructions: Optional[str] = field(default=None, repr=False)
    _full_content: Optional[str] = field(default=None, repr=False)

    @property
    def instructions(self) -> str:
        """Load full instructions on first access (lazy loading)."""
        if self._instructions is None:
            content = self.path.read_text(encoding='utf-8')
            # Strip YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    self._instructions = parts[2].strip()
                else:
                    self._instructions = content
            else:
                self._instructions = content
        return self._instructions

    @property
    def system_prompt_extension(self) -> str:
        """Compatibility property for legacy code."""
        return self.instructions

    def matches(self, transcription: str) -> bool:
        """Check if this skill should activate based on keywords."""
        if not self.keywords:
            return False  # Default skill has no keywords
        lower = transcription.lower()
        return any(kw.lower() in lower for kw in self.keywords)


# ============================================================================
# LEGACY SKILLS (Kept for backward compatibility)
# ============================================================================

class BaseSkill(ABC):
    """Abstract base class for legacy Python skills."""
    
    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def system_prompt_extension(self) -> str: pass

    @abstractmethod
    async def should_activate(self, context: SkillContext) -> bool:
        """Determine if this skill should be activated based on context."""
        pass


# ============================================================================
# SKILL MANAGER
# ============================================================================

class SkillManager:
    """
    Manages skill registration and selection.
    
    Supports both:
    - Filesystem-based SKILL.md files (new, preferred)
    - Legacy Python BaseSkill classes (backward compatible)
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        # Default to kaedra/skills directory
        if skills_dir is None:
            skills_dir = Path(__file__).parent.parent / "skills"
        
        self.skills_dir = skills_dir
        self.filesystem_skills: List[SkillMetadata] = []
        self.legacy_skills: List[BaseSkill] = []
        self.current_skill: Optional[SkillMetadata] = None
        self._default_skill: Optional[SkillMetadata] = None
        
        # Discover filesystem-based skills
        self._discover_filesystem_skills()
        
        # Load legacy skills as fallback
        self._load_legacy_skills()
        
    def _discover_filesystem_skills(self):
        """Scan skills directory for SKILL.md files."""
        if not self.skills_dir.exists():
            print(f"[!] Skills directory not found: {self.skills_dir}")
            return
            
        for skill_path in self.skills_dir.glob("*/SKILL.md"):
            try:
                metadata = self._parse_metadata(skill_path)
                if metadata:
                    self.filesystem_skills.append(metadata)
                    # Track default skill (priority 0 or name contains 'default')
                    if metadata.priority == 0 or 'default' in metadata.name.lower():
                        self._default_skill = metadata
                    print(f"[+] Discovered skill: {metadata.name} (priority: {metadata.priority})")
            except Exception as e:
                print(f"[!] Failed to parse {skill_path}: {e}")
        
        # Sort by priority (higher = checked first)
        self.filesystem_skills.sort(key=lambda s: s.priority, reverse=True)
        
        # Set default skill as current if available
        if self._default_skill:
            self.current_skill = self._default_skill
        elif self.filesystem_skills:
            self.current_skill = self.filesystem_skills[-1]  # Lowest priority as default
    
    def _parse_metadata(self, path: Path) -> Optional[SkillMetadata]:
        """Parse YAML frontmatter only (no full content load for efficiency)."""
        content = path.read_text(encoding='utf-8')
        
        if not content.startswith('---'):
            print(f"[!] No YAML frontmatter in {path}")
            return None
            
        # Extract frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            print(f"[!] Invalid YAML frontmatter in {path}")
            return None
            
        try:
            if HAS_YAML:
                data = yaml.safe_load(match.group(1))
            else:
                data = simple_yaml_parse(match.group(1))
        except Exception as e:
            print(f"[!] YAML parse error in {path}: {e}")
            return None
            
        return SkillMetadata(
            name=data.get('name', path.parent.name),
            description=data.get('description', ''),
            keywords=data.get('keywords', []),
            priority=data.get('priority', 5),  # Default middle priority
            path=path,
            light_feedback=data.get('light_feedback', {})
        )
    
    def _load_legacy_skills(self):
        """Load legacy Python-based skills for backward compatibility."""
        # Only load if no filesystem skills found
        if self.filesystem_skills:
            return
            
        print("[*] No filesystem skills found, loading legacy skills...")
        
        try:
            from kaedra.skills.universe import UniverseSkill
            self.legacy_skills.append(UniverseSkill())
        except ImportError:
            pass
    
    async def update_context(self, transcription: str) -> SkillMetadata:
        """
        Select skill based on keyword matching.
        Returns the activated skill's metadata.
        """
        # Check filesystem skills first (sorted by priority)
        for skill in self.filesystem_skills:
            if skill.matches(transcription):
                self.current_skill = skill
                return skill
        
        # Check legacy skills
        context = SkillContext(user_transcription=transcription)
        for skill in self.legacy_skills:
            if await skill.should_activate(context):
                # Wrap legacy skill in metadata for compatibility
                self.current_skill = SkillMetadata(
                    name=skill.name,
                    description="Legacy skill",
                    keywords=[],
                    priority=0,
                    path=Path("."),
                    _instructions=skill.system_prompt_extension
                )
                return self.current_skill
        
        # Fallback to default
        if self._default_skill:
            self.current_skill = self._default_skill
        
        return self.current_skill
    
    def get_skill_prompt(self) -> str:
        """Get full instructions for current skill (lazy loaded)."""
        if self.current_skill:
            return self.current_skill.instructions
        return ""
    
    def get_light_feedback(self, feedback_type: str) -> Optional[str]:
        """Get light feedback color for current skill."""
        if self.current_skill and self.current_skill.light_feedback:
            return self.current_skill.light_feedback.get(feedback_type)
        return None
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all available skills with their metadata."""
        skills = []
        for skill in self.filesystem_skills:
            skills.append({
                "name": skill.name,
                "description": skill.description,
                "priority": skill.priority,
                "keywords": skill.keywords,
                "path": str(skill.path)
            })
        return skills
