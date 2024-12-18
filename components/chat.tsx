'use client';

import type { Attachment, Message } from 'ai';
import { useChat } from 'ai/react';
import { AnimatePresence } from 'motion/react';
import { useState } from 'react';
import useSWR, { useSWRConfig } from 'swr';
import { useWindowSize } from 'usehooks-ts';

import { ChatHeader } from './chat-header';

// import { Block, type UIBlock } from './block';
// import { BlockStreamHandler } from './block-stream-handler';
import { ChatInput } from './chat-input';
import { Messages } from './messages';
import { ProfileContext } from './profile-context';
import { useContext } from 'react';

export function Chat({
  id,
  domainId,
  initialMessages,
}: {
  id: string;
  domainId: string;
  initialMessages: Array<Message>;
}) {
  const { mutate } = useSWRConfig();
  const { accessToken } = useContext(ProfileContext);
  const {
    messages,
    setMessages,
    handleSubmit,
    input,
    setInput,
    append,
    isLoading,
    stop,
    reload,
    data: streamingData,
  } = useChat({
    api: '/api/chat/chat',
    id,
    fetch: async (url, options) => {
      return fetch(url, {
        ...options,
        headers: {
          ...options?.headers,
          Authorization: `Bearer ${accessToken}`,
        },
      });
    },
    initialMessages,
    experimental_prepareRequestBody: ({messages}) => ({
      message: messages[messages.length - 1].content,
      thread_id: id,
      domain_id: domainId,
    }),
    onFinish: () => {
      mutate('/api/chat/chat');
    },
  });

  const { width: windowWidth = 1920, height: windowHeight = 1080 } =
    useWindowSize();

  // const [block, setBlock] = useState<UIBlock>({
  //   documentId: 'init',
  //   content: '',
  //   kind: 'text',
  //   title: '',
  //   status: 'idle',
  //   isVisible: false,
  //   boundingBox: {
  //     top: windowHeight / 4,
  //     left: windowWidth / 4,
  //     width: 250,
  //     height: 50,
  //   },
  // });

  return (
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-background">
        <ChatHeader
          chatId={id}
        />

        <Messages
          chatId={id}
          // block={block}
          // setBlock={setBlock}
          isLoading={isLoading}
          messages={messages}
          setMessages={setMessages}
          reload={reload}
        />

        <form className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
          <ChatInput
            chatId={id}
            input={input}
            setInput={setInput}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            stop={stop}
            messages={messages}
            setMessages={setMessages}
            append={append}
          />
        </form>
      </div>

      {/* <AnimatePresence>
        {block?.isVisible && (
          <Block
            chatId={id}
            input={input}
            setInput={setInput}
            handleSubmit={handleSubmit}
            isLoading={isLoading}
            stop={stop}
            attachments={attachments}
            setAttachments={setAttachments}
            append={append}
            block={block}
            setBlock={setBlock}
            messages={messages}
            setMessages={setMessages}
            reload={reload}
          />
        )}
      </AnimatePresence> */}

      {/* <BlockStreamHandler streamingData={streamingData} setBlock={setBlock} /> */}
    </>
  );
}
