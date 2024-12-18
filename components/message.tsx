'use client';

import type { ChatRequestOptions, Message } from 'ai';
import cx from 'classnames';
import { motion } from 'motion/react';
import { memo, useState, type Dispatch, type SetStateAction } from 'react';


// import type { UIBlock } from './block';
// import { DocumentToolCall, DocumentToolResult } from './document';
import { SparklesIcon } from './icons';
import { Markdown } from './markdown';
import equal from 'fast-deep-equal';
import { cn } from '@/lib/utils';
import { Button } from './ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';

const PurePreviewMessage = ({
  chatId,
  message,
  // block,
  // setBlock,
}: {
  chatId: string;
  message: Message;
  // block: UIBlock;
  // setBlock: Dispatch<SetStateAction<UIBlock>>;
}) => {

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      <div
        className={cn(
          'flex gap-4 w-full group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:w-fit',
        )}
      >
        {message.role === 'assistant' && (
          <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border bg-background">
            <SparklesIcon size={14} />
          </div>
        )}

        {message.content && (
          <div className="flex flex-row gap-2 items-start">

              <div
                className={cn('flex flex-col gap-4', {
                  'bg-primary text-primary-foreground px-3 py-2 rounded-xl':
                    message.role === 'user',
                })}
              >
                <Markdown>{message.content as string}</Markdown>
              </div>
            </div>
          )}

        <div className="flex flex-col gap-2 w-full">
          {message.toolInvocations && message.toolInvocations.length > 0 && (
            <div className="flex flex-col gap-4">
              {message.toolInvocations.map((toolInvocation) => {
                const { toolName, toolCallId, state, args } = toolInvocation;

                if (state === 'result') {
                  const { result } = toolInvocation;

                  return (
                    <div key={toolCallId}>
                      {toolName}: {result}
                    </div>
                  );
                }
                return (
                  <div
                    key={toolCallId}
                  >
                    {toolName}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export const PreviewMessage = memo(
  PurePreviewMessage,
  (prevProps, nextProps) => {
    if (prevProps.message.content !== nextProps.message.content) return false;
    if (
      !equal(
        prevProps.message.toolInvocations,
        nextProps.message.toolInvocations,
      )
    )
      return false;

    return true;
  },
);

export const ThinkingMessage = () => {
  const role = 'assistant';

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message "
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 1 } }}
      data-role={role}
    >
      <div
        className={cx(
          'flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl',
          {
            'group-data-[role=user]/message:bg-muted': true,
          },
        )}
      >
        <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
          <SparklesIcon size={14} />
        </div>

        <div className="flex flex-col gap-2 w-full">
          <div className="flex flex-col gap-4 text-muted-foreground">
            Thinking...
          </div>
        </div>
      </div>
    </motion.div>
  );
};
