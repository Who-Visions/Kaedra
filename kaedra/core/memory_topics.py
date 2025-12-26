from vertexai import types

# Define Custom Topics for Extraction
CUSTOM_TOPICS = [
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="PROJECT_IDEA",
            description="""Extract ideas for new applications, websites, scripts, or features. Include:
            - The proposed name or working title (e.g., "Recall", "Wispr Flow").
            - The core problem being solved.
            - Proposed technologies or stack.
            - User goals or "jobs to be done".
            
            Example: "Project: 'Recall' - a tool to search past dictations using embeddings."
            """
        )
    ),
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="SOCIAL_STRATEGY",
            description="""Extract strategy, guidelines, or ideas for social media content. Include:
            - Targeted platforms (Instagram, YouTube, TikTok).
            - Content themes or pillars (e.g., "AI Tutorials", "Behind the Scenes").
            - Specific hooks, scripts, or caption ideas.
            - Posting schedules or frequency goals.
            
            Example: "Post idea: Show how to use Wispr Flow for coding on Instagram Reels."
            """
        )
    ),
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="CODE_PATTERN",
            description="""Extract preferred coding patterns, technology choices, and architectural decisions. Include:
            - Preferred libraries or frameworks (e.g., "Next.js 16", "TailwindCSS").
            - Coding style guidelines (e.g., "Use functional components", "Avoid class-based views").
            - Specific solutions to recurring problems ("How to handle auth", "How to structure API routes").
            - Deprecated or banned patterns.
            
            Example: "Use 'npx create-next-app@latest' with TypeScript for all new web projects."
            """
        )
    ),
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="BUG_REPORT",
            description="""Extract details about software bugs, errors, or issues encountered. Include:
            - Error messages or codes.
            - Affected components or files.
            - Steps to reproduce (if mentioned).
            - Proposed or implemented fixes.
            
            Example: "Fix for 'NameError: total not defined' in ingest script."
            """
        )
    )
]

def get_customization_config():
    """Returns the optimization config with custom topics."""
    return types.MemoryBankCustomizationConfig(memory_topics=CUSTOM_TOPICS)
