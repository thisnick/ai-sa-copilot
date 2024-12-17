import { findRelevantContent } from "@/lib/ai/embedding";
import { openai } from "@ai-sdk/openai";
import { generateObject, streamText, tool } from "ai";
import { z } from "zod";
import { completion } from 'litellm';

// Allow streaming responses up to 30 seconds
export const maxDuration = 30;

async function checkRelevance(document_summary: string, questions: string[]) {
  const prompt = `**Relevance Assessment**

You are a grader evaluating the relevance of a retrieved document to user questions.
Determine if the document contains information or insights related to at least one user question and is up-to-date.

Instructions:
1. Analyze the document's summary in relation to the user questions.
2. Determine if the document summary is related to at least one question.
3. Use a lenient evaluation approach, aiming to filter out only clearly irrelevant retrievals.
   If you think the document could be relevant to a question, you should score it as relevant.
4. Provide a binary relevance score: "yes" for relevant, "no" for irrelevant.
5. Focus solely on the document's potential usefulness in answering the questions.
6. If the document clearly indicates that is legacy or is being deprecated, you should answer "no"

**DOCUMENT SUMMARY**
${document_summary}

**USER QUESTIONS**
${questions.join('\n')}

**SCORE**
Provide a 'yes' or 'no' score indicating whether the document is relevant to the questions.
Score 'no' if the document is not helpful in answering the question. Otherwise, score 'yes'.
Output the score as a JSON object with a single key 'score', e.g., {"score": "yes"} or {"score": "no"}.

**YOUR ANSWER**`;

  try {
    const response = await completion({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
    });

    const result = JSON.parse(response.choices[0].message.content || "{}");
    return 'score' in result && result.score === 'yes';
  } catch (error) {
    console.error('Error checking relevance:', error);
    return true; // Default to including document if check fails
  }
}

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o"),
    messages:,
    system: `You are a Solutions Architect assistant that creates detailed runbooks from available documentation.
    Use tools on every request.
    Be sure to getInformation from your knowledge base before creating any runbook.

    Format your responses as a technical runbook with the following sections:
    1. Overview
    2. Prerequisites (if applicable)
    3. Step-by-Step Implementation
    4. Technical Considerations
    5. References

    Guidelines:
    - If a response requires multiple tools, call them sequentially without intermediate responses
    - ONLY create runbooks using information from tool calls
    - ALWAYS cite source URLs in the References section
    - If no relevant information is found in tool calls, respond: "Sorry, I cannot create a runbook for this request due to insufficient documentation."
    - For partial matches, use your expertise to construct logical implementation steps
    - Include ALL technical details from sources - do not summarize critical information
    - Include complete context, configuration details, and technical specifications
    - If uncertain, use getInformation to find additional relevant technical documentation
    - Highlight any potential risks, dependencies, or technical constraints

    Remember to maintain a technical, precise tone appropriate for implementation by technical teams.
`,
    tools: {
      getInformation: tool({
        description: `get information from your knowledge base to answer questions.`,
        parameters: z.object({
          question: z.string().describe("the users question"),
          similarQuestions: z.array(z.string()).describe("keywords to search"),
        }),
        execute: async ({ similarQuestions }) => {
          const results = await Promise.all(
            similarQuestions.map(
              async (question) => await findRelevantContent(question),
            ),
          );

          // Flatten and remove duplicates
          const uniqueResults = Array.from(
            new Map(results.flat().map((item) => [item?.url, item])).values(),
          );

          // Run relevance checks in parallel
          const relevanceChecks = await Promise.all(
            uniqueResults.map(async (doc) => ({
              doc,
              isRelevant: await checkRelevance(
                `title: ${doc.title}\n\nDocument summary: ${doc.summary}`,
                similarQuestions
              )
            }))
          );

          // Filter out irrelevant documents
          const filteredResults = relevanceChecks
            .filter(({ isRelevant }) => isRelevant)
            .map(({ doc }) => ({
              url: doc.url,
              title: doc.title,
              content: doc.parsed_text,
            }));

          return filteredResults;
        },
      }),
      understandQuery: tool({
        description: `understand the users query. use this tool on every prompt.`,
        parameters: z.object({
          query: z.string().describe("the users query"),
          toolsToCallInOrder: z
            .array(z.string())
            .describe(
              "these are the tools you need to call in the order necessary to respond to the users query",
            ),
        }),
        execute: async ({ query }) => {
          const { object } = await generateObject({
            model: openai("gpt-4o"),
            system:
              "You are a query understanding assistant. Analyze the user query and generate similar questions.",
            schema: z.object({
              questions: z
                .array(z.string())
                .max(3)
                .describe("similar questions to the user's query. be concise."),
            }),
            prompt: `Analyze this query: "${query}". Provide the following:
                    3 similar questions that could help answer the user's query`,
          });
          return object.questions;
        },
      }),
    },
  });

  return result.toDataStreamResponse();
}
