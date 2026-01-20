"""
KAEDRA v1.0 - Memory Topics
Defines custom topics for extraction and categorization in the Vertex AI Memory Bank.
"""

# pylint: disable=no-name-in-module
from vertexai import types

# Define Custom Topics for Extraction
CUSTOM_TOPICS = [
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="PROJECT_IDEA",
            description="Extract ideas for new applications, websites, scripts, or features."
            " Include proposed name, core problem, stack, and user goals."
            "\n\nExample: \"Project: 'Recall' - a tool to search past "
            "dictations using embeddings.\""
        )
    ),
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="SOCIAL_STRATEGY",
            description="Extract strategy, guidelines, or ideas for social media content."
            " Include platforms, themes, specific hooks, and schedules."
            "\n\nExample: \"Post idea: Show how to use Wispr Flow for "
            "coding on Instagram Reels.\""
        )
    ),
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="CODE_PATTERN",
            description="Extract preferred coding patterns, technology choices, and"
            " architectural decisions. Include preferred libraries and style guidelines."
            "\n\nExample: \"Use 'npx create-next-app@latest' with TypeScript for new projects.\""
        )
    ),
    types.MemoryBankCustomizationConfigMemoryTopic(
        custom_memory_topic=types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic(
            label="BUG_REPORT",
            description="Extract details about software bugs, errors, or issues encountered."
            " Include error messages, affected components, and proposed fixes."
            "\n\nExample: \"Fix for 'NameError: total not defined' in ingest script.\""
        )
    )
]

def get_customization_config():
    """Returns the optimization config with custom topics."""
    return types.MemoryBankCustomizationConfig(memory_topics=CUSTOM_TOPICS)
