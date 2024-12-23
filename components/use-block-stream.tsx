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
    if (delta.type === 'context_delta') {
      setBlock((draftBlock) => {
        const updatedContext = delta.content;
        const previousContext = draftBlock.context;
        const updatedBlock : UIBlock = {
          ...draftBlock,
          context: {
            ...draftBlock.context,
            ...updatedContext,
          },
        }
        if (Object.keys(updatedContext.saved_artifacts ?? {}).length > 0) {
          updatedBlock.activeTab = 'artifacts';
          updatedBlock.isVisible = true;
        }
        if (updatedContext.runbook_sections) {
          updatedBlock.activeTab = 'outline';
          updatedBlock.isVisible = true;
        }
        if ((previousContext.runbook_sections ?? []).map((section) => section.content).join('') !==
        (updatedContext.runbook_sections ?? []).map((section) => section.content).join('')) {
          updatedBlock.activeTab = 'document';
          updatedBlock.isVisible = true;
        }

        return updatedBlock;
      });
    }
  }, [streamingData, setBlock]);
}
