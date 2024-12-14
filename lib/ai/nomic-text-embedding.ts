import {
  EmbeddingModelV1,
  EmbeddingModelV1Embedding,
  TooManyEmbeddingValuesForCallError,
} from '@ai-sdk/provider';

import { embed, AtlasViewer, Embedder } from "@nomic-ai/atlas"

type TaskType = 'search_document' | 'search_query' | 'clustering' | 'classification';
type EmbedderOptions = {
    model?: EmbeddingModel;
    maxTokens?: number;
    taskType?: TaskType;
};
type EmbeddingModel = 'nomic-embed-text-v1' | 'nomic-embed-text-v1.5';

export default class NomicTextEmbedding implements EmbeddingModelV1<string> {
  private readonly options: EmbedderOptions;
  private readonly embedder: Embedder;

  readonly specificationVersion = 'v1';
  readonly modelId: string;

  readonly provider: string = 'nomic';
  readonly maxEmbeddingsPerCall: number | undefined = 100;
  readonly supportsParallelCalls: boolean = true;

  constructor(
    options: EmbedderOptions,
    apiKey?: string,
  ) {
    this.options = {
      model: 'nomic-embed-text-v1.5',
      ...options,
    }
    this.modelId = this.options.model!;
    this.embedder =  apiKey === undefined
      ? new Embedder(new AtlasViewer({ useEnvToken: true } as const), options)
      : new Embedder(apiKey, options);
  }

  async doEmbed(options: { values: string[]; abortSignal?: AbortSignal; headers?: Record<string, string | undefined>; }): Promise<{ embeddings: EmbeddingModelV1Embedding[] }> {
    const embeddings = await this.embedder.embed(options.values);
    return { embeddings };
  }
}
