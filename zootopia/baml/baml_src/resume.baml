enum Category {
  UserPreferenceUpdate @description("Update user's preferences based on feedback about Sam")
  PersonalityAdjustment @description("Adjust Sam's personality traits or behavior")
  ScheduleUpdate @description("Update or create events in the user's schedule")
  RelationshipMilestone @description("Mark important events or milestones in the relationship")
  EmotionalResponse @description("Trigger an appropriate emotional response from Sam")
  MemoryStorage @description("Store important information shared by the user")
  ConversationTopic @description("Identify and log conversation topics for future reference")
  UserMoodTracking @description("Track and respond to changes in the user's mood")
  InteractionFrequencyAdjustment @alias("frequency-adjust") @description("Adjust how often Sam initiates conversations")
  ContentSuggestion @description("Generate content suggestions based on user interests")
}

function ClassifyMessage(input: string) -> Category {
  client "openai/gpt-4o"
  prompt #"
    {{ ctx.output_format }}
    
    {{ _.role('user') }}
    {{ input }}
    
    {{ _.role('assistant') }}
    Response:
  "#
}