import type { JSONValue } from 'ai';
import { type Dispatch, type SetStateAction, useEffect, useState } from 'react';
import { useSWRConfig } from 'swr';

import type { UIBlock } from './block';
import { ContextVariables } from '@/lib/api/types';

type StreamingDelta = {
  type: "context_delta"
  content: ContextVariables;
} | {
  type: "thread_title"
  content: string;
}

export function useBlockStream({
  streamingData,
  setBlock,
  setTitle,
}: {
  streamingData: JSONValue[] | undefined;
  setBlock: Dispatch<SetStateAction<UIBlock>>;
  setTitle: Dispatch<SetStateAction<string>>;
}) {
  const { mutate } = useSWRConfig();


  useEffect(() => {
    const mostRecentDelta = streamingData?.at(-1);
    if (!mostRecentDelta) return;

    const delta = mostRecentDelta as StreamingDelta;

    if (delta.type === 'thread_title') {
      setTitle(delta.content as string);
      return;
    }

    setBlock((draftBlock) => {
      const currentRunbookSection = delta.content.current_runbook_section;
      const updatedRunbookSection = delta.content.runbook_sections?.[currentRunbookSection ?? 0];
      const updatedRunbookSectionContent = updatedRunbookSection?.content;
      if (updatedRunbookSectionContent) {
        const updatedBlock : UIBlock = {
          ...draftBlock,
          context: delta.content as ContextVariables,
          activeTab: 'document',
          isVisible: true,
        }
        return updatedBlock;
      }
      if (updatedRunbookSection) {
        const updatedBlock : UIBlock = {
          ...draftBlock,
          context: delta.content as ContextVariables,
          activeTab: 'outline',
          isVisible: true,
        }
        return updatedBlock;
      }
      if (Object.keys(delta.content.saved_artifacts ?? {}).length > 0) {
        const updatedBlock : UIBlock = {
          ...draftBlock,
          context: delta.content as ContextVariables,
          activeTab: 'artifacts',
          isVisible: true,
        }
        return updatedBlock;
      }
      return draftBlock;
    });
  }, [streamingData, setBlock]);
}
