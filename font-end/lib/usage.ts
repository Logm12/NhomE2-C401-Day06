export type LanguageModelUsage = {
  inputTokens?: number;
  outputTokens?: number;
  reasoningTokens?: number;
  cachedInputTokens?: number;
  totalTokens?: number;
  context?: {
    inputMax?: number;
    outputMax?: number;
    combinedMax?: number;
    totalMax?: number;
  };
  costUSD?: {
    inputUSD?: number;
    outputUSD?: number;
    reasoningUSD?: number;
    cacheReadUSD?: number;
    totalUSD?: number;
  };
  modelId?: string;
};
export type UsageData = {
  costUSD?: {
    inputUSD?: number;
    outputUSD?: number;
    reasoningUSD?: number;
    totalUSD?: number;
  };
  context?: {
    inputMax?: number;
    outputMax?: number;
    combinedMax?: number;
    totalMax?: number;
  };
};

// Server-merged usage: base usage + TokenLens summary + optional modelId
export type AppUsage = LanguageModelUsage & UsageData & { modelId?: string };
