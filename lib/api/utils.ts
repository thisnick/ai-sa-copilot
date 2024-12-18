import type { Message, CoreToolMessage, ToolInvocation } from "ai";
import type { DBMessage } from "./types";

function addToolMessageToChat({
  toolMessage,
  messages,
}: {
  toolMessage: DBMessage & { role: "tool" };
  messages: Array<Message>;
}): Array<Message> {
  return messages.map((message) => {
    if (message.toolInvocations) {
      return {
        ...message,
        toolInvocations: message.toolInvocations.map((toolInvocation) => {
          if (toolInvocation.toolCallId == toolMessage.tool_call_id) {
            return {
              ...toolInvocation,
              state: 'result',
              result: toolMessage.content,
            };
          }

          return toolInvocation;
        }),
      };
    }

    return message;
  });
}

export function convertToUIMessages(
  messages: Array<DBMessage>,
): Array<Message> {
  return messages.reduce((chatMessages: Array<Message>, message, index) => {
    if (message.role === 'tool') {
      return addToolMessageToChat({
        toolMessage: message,
        messages: chatMessages,
      });
    }


    let textContent = '';
    const toolInvocations: Array<ToolInvocation> = [];

    if (typeof message.content === 'string') {
      textContent = message.content;
    } else if (Array.isArray(message.content)) {
      for (const content of message.content) {
        if (content.type === 'text') {
          textContent += content.text;
        }
      }
    }

    chatMessages.push({
      id: index.toString(),
      role: message.role as Message['role'],
      content: textContent,
      toolInvocations,
    });

    return chatMessages;
  }, []);
}
