import type { Message, CoreToolMessage, ToolInvocation, JSONValue } from "ai";
import type { DBMessage } from "./types";

const ANNOTATION_KEYS = ["sender"]

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
    let toolInvocations: Array<ToolInvocation> = []
    let annotations: Array<JSONValue> = ANNOTATION_KEYS
      .filter((key) => key in message)
      .map((key) => ({
        [key]: message[key as keyof typeof message]
      }))

    if (message.role === 'assistant') {
      toolInvocations = message.tool_calls?.map((toolCall) : ToolInvocation => ({
        toolName: toolCall.function.name,
        toolCallId: toolCall.id,
        state: 'call',
        args: {}
      })) || []
    }

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
      annotations,
    });

    return chatMessages;
  }, []);
}
