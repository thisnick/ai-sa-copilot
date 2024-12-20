import {
  type Dispatch,
  memo,
  type SetStateAction,
  useCallback,
  useEffect,
  useState,
} from 'react';
import useSWR, { useSWRConfig } from 'swr';
import { useDebounceCallback, useWindowSize } from 'usehooks-ts';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'motion/react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

import { ContextVariables } from "@/lib/api/types";
import { ChatRequestOptions, CreateMessage, Message } from 'ai';
import { BlockMessages } from './block-messages';
import { ChatInput } from './chat-input';
import { BlockCloseButton } from './block-close-button';
import { DocumentationViewer } from './documentation-viewer'
import { RunbookOutline } from './runbook-outline'
import { RunbookDocument } from './runbook-document'
export type ActiveTab = 'artifacts' | 'outline' | 'document'

export interface UIBlock {
  context: ContextVariables;
  activeTab: ActiveTab;
  isVisible: boolean;
  status: 'streaming' | 'idle';
  boundingBox: {
    top: number;
    left: number;
    width: number;
    height: number;
  };
}


function PureBlock({
  chatId,
  input,
  setInput,
  handleSubmit,
  isLoading,
  stop,
  append,
  block,
  setBlock,
  messages,
  setMessages,
  reload,
}: {
  chatId: string;
  input: string;
  setInput: (input: string) => void;
  isLoading: boolean;
  stop: () => void;
  block: UIBlock;
  setBlock: Dispatch<SetStateAction<UIBlock>>;
  messages: Array<Message>;
  setMessages: Dispatch<SetStateAction<Array<Message>>>;
  append: (
    message: Message | CreateMessage,
    chatRequestOptions?: ChatRequestOptions,
  ) => Promise<string | null | undefined>;
  handleSubmit: (
    event?: {
      preventDefault?: () => void;
    },
    chatRequestOptions?: ChatRequestOptions,
  ) => void;
  reload: (
    chatRequestOptions?: ChatRequestOptions,
  ) => Promise<string | null | undefined>;
}) {

  const { width: windowWidth, height: windowHeight } = useWindowSize();
  const isMobile = windowWidth ? windowWidth < 768 : false;

  return (
    <motion.div
      className="flex flex-row h-dvh w-dvw fixed top-0 left-0 z-50 bg-muted"
      initial={{ opacity: 1 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { delay: 0.4 } }}
    >
      {!isMobile && (
        <motion.div
          className="relative w-[400px] bg-muted dark:bg-background h-dvh shrink-0"
          initial={{ opacity: 0, x: 10, scale: 1 }}
          animate={{
            opacity: 1,
            x: 0,
            scale: 1,
            transition: {
              delay: 0.2,
              type: 'spring',
              stiffness: 200,
              damping: 30,
            },
          }}
          exit={{
            opacity: 0,
            x: 0,
            scale: 0.95,
            transition: { delay: 0 },
          }}
        >

          <div className="flex flex-col h-full justify-between items-center gap-4">
            <BlockMessages
              chatId={chatId}
              block={block}
              isLoading={isLoading}
              setBlock={setBlock}
              messages={messages}
              setMessages={setMessages}
              reload={reload}
            />

            <form className="flex flex-row gap-2 relative items-end w-full px-4 pb-4">
              <ChatInput
                chatId={chatId}
                input={input}
                setInput={setInput}
                handleSubmit={handleSubmit}
                isLoading={isLoading}
                stop={stop}
                messages={messages}
                append={append}
                className="bg-background dark:bg-muted"
                setMessages={setMessages}
              />
            </form>
          </div>
        </motion.div>
      )}

      <motion.div
        className="fixed dark:bg-muted bg-background h-dvh flex flex-col overflow-y-scroll"
        initial={
          isMobile
            ? {
                opacity: 0,
                x: 0,
                y: 0,
                width: windowWidth,
                height: windowHeight,
                borderRadius: 50,
              }
            : {
                opacity: 0,
                x: block.boundingBox.left,
                y: block.boundingBox.top,
                height: block.boundingBox.height,
                width: block.boundingBox.width,
                borderRadius: 50,
              }
        }
        animate={
          isMobile
            ? {
                opacity: 1,
                x: 0,
                y: 0,
                width: windowWidth,
                height: '100dvh',
                borderRadius: 0,
                transition: {
                  delay: 0,
                  type: 'spring',
                  stiffness: 200,
                  damping: 30,
                },
              }
            : {
                opacity: 1,
                x: 400,
                y: 0,
                height: windowHeight,
                width: windowWidth ? windowWidth - 400 : 'calc(100dvw-400px)',
                borderRadius: 0,
                transition: {
                  delay: 0,
                  type: 'spring',
                  stiffness: 200,
                  damping: 30,
                },
              }
        }
        exit={{
          opacity: 0,
          scale: 0.5,
          transition: {
            delay: 0.1,
            type: 'spring',
            stiffness: 600,
            damping: 30,
          },
        }}
      >
        <div className="p-2 flex flex-row justify-between items-start">
          <div className="flex flex-row gap-4 items-start">
            <BlockCloseButton setBlock={setBlock} />
          </div>
        </div>

        <Tabs defaultValue={block.activeTab} className="flex-1">
          <TabsList className="mx-4">
            <TabsTrigger value="artifacts">Supporting Articles</TabsTrigger>
            <TabsTrigger value="outline">Draft Outline</TabsTrigger>
            <TabsTrigger value="document">Final Runbook</TabsTrigger>
          </TabsList>

          <TabsContent value="artifacts" className="flex-1 p-4">
            <DocumentationViewer savedArtifacts={block.context.saved_artifacts || {}} />
          </TabsContent>

          <TabsContent value="outline" className="flex-1 p-4">
            <RunbookOutline runbook_sections={block.context.runbook_sections || []} saved_artifacts={block.context.saved_artifacts || {}} />
          </TabsContent>

          <TabsContent value="document" className="flex-1 p-4">
            <RunbookDocument runbook_sections={block.context.runbook_sections || []} />
          </TabsContent>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}

export const Block = memo(PureBlock, (prevProps, nextProps) => {
  return false;
});

