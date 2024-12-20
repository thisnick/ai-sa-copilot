import { memo, type SetStateAction } from 'react';

// import type { BlockKind, UIBlock } from './block';
import { MessageIcon } from './icons';
import { ActiveTab, UIBlock } from './block';

type ActionType =
  | 'save_requirements'
  | 'kickoff_research'
  | 'query_for_artifacts'
  | 'save_artifacts'
  | 'finish_research'
  | 'create_runbook_outline'
  | 'retrieve_artifacts'
  | 'submit_writing_for_section'
  | 'start_writing_runbook'

const isActionType = (action: string): action is ActionType => {
  return [
    'save_requirements',
    'kickoff_research',
    'query_for_artifacts',
    'save_artifacts',
    'finish_research',
    'create_runbook_outline',
    'retrieve_artifacts',
    'submit_writing_for_section',
    'start_writing_runbook'
  ].includes(action);
};

const getAgentActionText = (
  action: ActionType,
  tense: 'present' | 'past'
) => {
  switch (action) {
    // Research Coordinator Agent
    case 'save_requirements':
      return tense === 'present' ? 'Saving requirements' : 'Saved requirements';
    case 'kickoff_research':
      return tense === 'present' ? 'Starting research' : 'Started research';

    // Topic Research Agent
    case 'query_for_artifacts':
      return tense === 'present' ? 'Searching for supporting articles' : 'Searched for supporting articles';
    case 'save_artifacts':
      return tense === 'present' ? 'Reading supporting articles' : 'Read supporting articles';
    case 'finish_research':
      return tense === 'present' ? 'Completing research for a topic' : 'Completed research for a topic';

    // Runbook Planning Agent
    case 'create_runbook_outline':
      return tense === 'present' ? 'Creating a runbook outline' : 'Created a runbook outline';

    // Runbook Section Writing Agent
    case 'retrieve_artifacts':
      return tense === 'present' ? 'Retrieving artifacts' : 'Retrieved artifacts';
    case 'submit_writing_for_section':
      return tense === 'present' ? 'Writing a section' : 'Wrote a section';

    case 'start_writing_runbook':
      return tense === 'present' ? 'Starting to write the runbook' : 'Started writing the runbook';
    default:
      return null;
  }
};

const getActiveTab = (action: ActionType): ActiveTab | undefined => {
  switch (action) {
    case 'save_artifacts':
      return 'artifacts';
    case 'submit_writing_for_section':
    case 'start_writing_runbook':
      return 'document';
    case 'create_runbook_outline':
      return 'outline'
    default:
      return undefined;
  }
};

interface AgentToolResultProps {
  type: ActionType | string;
  // result: { id: string; title: string; kind: BlockKind };
  // block: UIBlock;
  setBlock: (value: SetStateAction<UIBlock>) => void;
  // isReadonly: boolean;
}

function PureAgentToolResult({
  type,
  // result,
  setBlock,
  // isReadonly,
}: AgentToolResultProps) {
  if (!isActionType(type)) {
    return (
      <div className="w-fit border py-2 px-3 rounded-xl flex flex-row items-start justify-between gap-3">
        <div className="text-muted-foreground mt-1">
          <MessageIcon />
        </div>
        <div className="text-left">
          Performed action: {type}
        </div>
      </div>
    )
  }
  const activeTab = getActiveTab(type);
  if (activeTab) {
    return (
      <button
        type="button"
        className="cursor pointer w-fit border py-2 px-3 rounded-xl flex flex-row items-start justify-between gap-3"
        onClick={(event) => {

          const rect = event.currentTarget.getBoundingClientRect();

          const boundingBox = {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
          };

          setBlock((currentBlock): UIBlock => ({
            ...currentBlock,
            isVisible: true,
            boundingBox,
            activeTab,
          }));
        }}
      >
        <div className="text-muted-foreground mt-1">
          <MessageIcon />
        </div>
        <div className="text-left">
          {`${getAgentActionText(type, 'past')}`}
        </div>
      </button>
    )
  }

  return (
    <div className="w-fit border py-2 px-3 rounded-xl flex flex-row items-start justify-between gap-3">
      <div className="text-muted-foreground mt-1">
        <MessageIcon />
      </div>
      <div className="text-left">
        {`${getAgentActionText(type, 'past')}`}
      </div>
    </div>
  );
}

export const AgentToolResult = memo(PureAgentToolResult, () => true);

interface AgentToolCallProps {
  type: ActionType | string;
  // args: { title: string };
  setBlock: (value: SetStateAction<UIBlock>) => void;
  // isReadonly: boolean;
}

function PureAgentToolCall({
  type,
  // args,
  setBlock,
  // isReadonly,
}: AgentToolCallProps) {

  if (!isActionType(type)) {
    return (
      <div className="w-fit border py-2 px-3 rounded-xl flex flex-row items-start justify-between gap-3">
        <div className="text-muted-foreground mt-1">
          <MessageIcon />
        </div>
        <div className="text-left">
          Performing action: {type}
        </div>
      </div>
    )
  }
  const activeTab = getActiveTab(type);
  if (activeTab) {
    return (
      <button
        type="button"
        className="cursor pointer w-fit border py-2 px-3 rounded-xl flex flex-row items-start justify-between gap-3"
        onClick={(event) => {

          const rect = event.currentTarget.getBoundingClientRect();

          const boundingBox = {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
          };

          setBlock((currentBlock): UIBlock => ({
            ...currentBlock,
            isVisible: true,
            boundingBox,
            activeTab,
          }));
        }}
      >
        <div className="text-muted-foreground mt-1">
          <MessageIcon />
        </div>
        <div className="text-left">
          {`${getAgentActionText(type, 'present')}`}
        </div>
      </button>
    )
  }
  return (
    <div className="w-fit border py-2 px-3 rounded-xl flex flex-row items-start justify-between gap-3">
      <div className="text-muted-foreground mt-1">
        <MessageIcon />
      </div>
      <div className="text-left">
        {`${getAgentActionText(type, 'present')}`}
      </div>
    </div>
  );
}

export const AgentToolCall = memo(PureAgentToolCall, () => true);
