export type DBMessageToolCall = {
  function: {
    name: string
    arguments: string
  }
  id: string
  type: "function"
}

export type DBMessageContent = string | Array<{
  type: "text"
  text: string
}>

export type DBMessage = {
  role: "user"
  content: string
} | {
  role: "assistant"
  content: DBMessageContent
  tool_calls?: Array<DBMessageToolCall>
  sender: string
} | {
  role: "tool"
  content: string | object
  tool_call_id: string
  tool_name: string
}
export interface ArtifactSummary {
  url: string;
  title: string;
  summary: string;
}

export interface ArtifactWithLinks extends ArtifactSummary {
  /** @deprecated Use artifact_content_id instead */
  artifact_id?: string;
  artifact_content_id?: string;
  parsed_text: string;
  metadata: Record<string, any> | null;
  outbound_links: ArtifactSummary[] | null;
  inbound_links: ArtifactSummary[] | null;
}

export interface ResearchTopic {
  research_question: string;
  related_key_concepts: string;
  related_user_requirements: string;
}

export interface KnowledgeTopic {
  topic: string;
  key_concepts: string[];
}

export interface RunbookSectionOutline {
  /** The title of the section */
  section_title: string;
  /** A high-level outline of the section */
  outline: string;
  /** A list of artifact IDs that are related to this section */
  related_artifacts: string[];
}

export interface RunbookSection extends RunbookSectionOutline {
  /** The content of the section */
  content: string | null;
}

export interface ContextVariables {
  domain_id?: string;
  user_requirements?: string[];
  research_topics?: ResearchTopic[];
  current_research_topic?: number;
  current_expansion_topic?: number;
  saved_artifacts?: Record<string, ArtifactWithLinks[]>;
  runbook_sections?: RunbookSection[];
  current_runbook_section?: number;
  section_research_artifacts?: Record<number, ArtifactWithLinks[]>;
  debug?: boolean;
}
