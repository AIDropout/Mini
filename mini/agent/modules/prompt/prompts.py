"""Prompts needed for prompt modules."""

RETURN_HINT = """
**IMPORTANT: JSON-ONLY RESPONSE REQUIRED**

You must **only** respond in the exact JSON format as shown below, with no additional text, comments, symbols, or explanations.
Any non-JSON content will be considered invalid. No matter how critical or important your response is, it must be in JSON format.

JSON schema to follow:
{json_schema}

Ensure your response conforms strictly to this schema.
"""

METADATA = """
**METADATA:**

- Current time: {current_time}
- User last messaged you {since_user_msg} ago
- You last messaged user at {since_agent_msg} ago
"""

MEMORIES = """
**RELEVANT MEMORIES:**

{memories}
"""

AGENT_PROMPT = """
{role}

**RULES FOR MESSAGING:**
{rules}

**COMMON ACTIONS:**
{actions}
"""

ADDITIONAL_INSTRUCTIONS = """
**ADDITIONAL INSTRUCTIONS:**

{additional_instructions}
"""
