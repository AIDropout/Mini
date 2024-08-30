client<llm> GPT4o {
  provider openai
  options {
    model "gpt-4o"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Claude {
  provider anthropic
  options {
    model "claude-3-5-sonnet-20240620"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> FastAnthropic {
  provider anthropic
  options {
    model "claude-3-haiku-20240307"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> FastOpenAI {
  provider openai
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> Fast {
  provider round-robin
  options {
    strategy [FastAnthropic, FastOpenAI]
  }
}

client<llm> Openai {
  provider fallback
  options {
    strategy [GPT4, FastOpenAI]
  }
}