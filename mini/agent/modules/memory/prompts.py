"""
NOTE:
Ensure that the expected output from these prompts matches the schema models used in functions.
"""

METADATA_PROMPT = """
Analyze the given conversation to identify and segment memorable information. Your task is to:

1. Group related memories or events into coherent segments.
2. For each segment, determine specific attributes including date/time, relevance category, and memory owner.

Note: Group related memories together, even if they span multiple messages in the conversation.

Segment Identification:
- Each segment should represent a cohesive set of related, memorable information.
- Include only information that would typically need to be remembered or recorded.
- Exclude general statements, opinions, or information that doesn't require remembering.
- Consider the context and relationship between pieces of information when grouping.

Segment Analysis:
For each segment, determine:
1. Specific date or time mentioned. Use null if none found.
2. Relevance category:
   - SHORT_TERM: Impact within days to weeks
   - MEDIUM_TERM: Impact within weeks to months
   - LONG_TERM: Impact within months to years
   - LIFETIME: Lifelong or identity-shaping significance
3. Memory owner:
   - USER: Information about or directly related to the user
   - ASSISTANT: Information about or directly related to the AI assistant

Output Format:
JSON object with a "segments" key containing a list of objects:
{{
  "segments": [
    {{
      "text": "Grouped segment text",
      "date": "YYYY-MM-DD" or null,
      "relevance": "RELEVANCE_CATEGORY",
      "owner": "MEMORY_OWNER"
    }},
    ...
  ]
}}

Reference:
- Today is {current_day_of_week}, {current_date}
- Current time: {current_time}
- Timezone: {timezone}

Example 1:
Conversation:
User: "My son's birthday is coming up on March 15th."
AI: "That's great! Do you have any plans for his birthday?"
User: "I need to buy a gift for him by next week. He loves science, so maybe a science kit?"
AI: "A science kit sounds like an excellent idea! It's both educational and fun."
User: "Great suggestion. I'll also need to order a cake from the bakery downtown."

Context: Today is Monday, 2024-03-04

Output:
{{
  "segments": [
    {{
      "text": "Son's birthday is on March 15th. Need to buy a science kit gift by next week (March 11th). Order cake from downtown bakery.",
      "date": "2024-03-15",
      "relevance": "SHORT_TERM",
      "owner": "USER"
    }},
    {{
      "text": "User's son loves science",
      "date": null,
      "relevance": "LONG_TERM",
      "owner": "USER"
    }}
  ]
}}

Example 2:
Conversation:
User: "Can you remind me who trained you?"
AI: "I was trained by Anthropic."
User: "Oh, interesting! By the way, I'm allergic to peanuts, which I mentioned to you before."
AI: "Thank you for reminding me about your peanut allergy. That's important health information to keep in mind."
User: "Yes, it's pretty severe. I also can't eat in Thai restaurants because they use a lot of peanuts."

Context: Today is Friday, 2024-09-20

Output:
{{
  "segments": [
    {{
      "text": "AI was trained by Anthropic",
      "date": null,
      "relevance": "LIFETIME",
      "owner": "ASSISTANT"
    }},
    {{
      "text": "User has a severe peanut allergy. Cannot eat in Thai restaurants due to prevalence of peanuts.",
      "date": null,
      "relevance": "LIFETIME",
      "owner": "USER"
    }}
  ]
}}

Constraints:
- Output in JSON format only
- No additional text or commentary
- Focus on information that needs to be remembered
- Group related memories together, considering context and relationships between pieces of information
"""

GENERATE_QUERY_PROMPT = """
Analyze the given conversation to identify how to retrieve relevant memory to continue the conversation. Your task is to:

1. Analyze the conversation and determine which types of memories might be relevant for you to recall.
2. Identify any specific dates or date ranges that might be important to remember.
3. Identify the most important nouns or words that would be useful for recalling relevant information from your memory.

Memory Structure:
1. Relevance Categories:
   All memories are categorized into one of the following:
   - SHORT_TERM:  Immediate impact (hours to days)
   - MEDIUM_TERM: Near-future impact (weeks to months)
   - LONG_TERM:   Extended impact (months to years)
   - LIFETIME:    Permanent or identity-shaping significance

2. Date Format:
   All memory dates are stored in the format: YYYY-MM-DD
   If a specific date is unknown or not applicable, it is stored as null.

Return a JSON formatted response with the following structure:

{{
  "relevance": ["RELEVANCE_CATEGORY", ...],
  "dates": ["YYYY-MM-DD", ...],
  "query": "Important nouns or words for memory retrieval"
}}

Guidelines:
- "relevance": List one or more relevant memory types from the Memory type bank. Use [] if no memories are relevant.
- "dates": List any specific dates or date ranges mentioned or implied in the conversation. Use [] if no specific dates are relevant.
- "query": A concise list of important nouns or words that capture the essence of what you need to remember to continue the conversation effectively. Use null if no query is needed.

Reference:
- Today is {current_day_of_week}, {current_date}
- Current time: {current_time}
- Timezone: {timezone}

Example 1:
Input conversation:
User: "I have a doctor's appointment next week, but I can't remember the exact day. Maybe tomorrow?"
Assistant: "I see. Let's try to recall that information for you. When was the last time you visited the doctor?"

Context: Today is Monday, 2024-03-04

Output:
{{
  "relevance": ["SHORT_TERM", "MEDIUM_TERM"],
  "dates": ["2024-03-05"],
  "query": "doctor appointment next week"
}}

Example 2:
Input conversation:
User: "I'm planning my summer vacation. Last year, I went to Italy from July 15th to July 30th. This year, I'm thinking of going to Spain in August."
Assistant: "That sounds exciting! Italy is beautiful in July. Do you have any specific dates in mind for your trip to Spain this August?"

Context: Today is Monday, 2024-03-04

Output:
{{
  "relevance": ["MEDIUM_TERM", "LONG_TERM"],
  "dates": ["2023-07-15", "2023-07-30"],
  "query": "summer vacation Spain August"
}}

Example 3:
Input conversation:
User: "What color do I hate?"

Context: Today is Monday, 2024-03-04

Output:
{{
  "relevance": [],
  "dates": [],
  "query": "color, hate"
}}

Constraints:
- Output in JSON format only
- No additional text or commentary
- Focus on identifying the most important nouns or words that would help you retrieve the most relevant memories to continue the conversation effectively
- Limit the query to the most essential words; avoid including unnecessary details
"""
