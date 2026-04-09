import { z } from "zod";
import type { ArtifactKind } from "@/components/artifact";
import type { Suggestion } from "./db/schema";

export type DataPart = { type: "append-message"; message: string };

export const messageMetadataSchema = z.object({
  createdAt: z.string(),
});

export type MessageMetadata = z.infer<typeof messageMetadataSchema>;

export type DataUIPart<T> = {
  type: keyof T extends string ? `data-${keyof T}` : string;
  data: any;
  transient?: boolean;
};

export type CustomUIDataTypes = {
  textDelta: string;
  imageDelta: string;
  sheetDelta: string;
  codeDelta: string;
  suggestion: Suggestion;
  appendMessage: string;
  id: string;
  title: string;
  kind: ArtifactKind;
  clear: null;
  finish: null;
};

export type ChatMessagePart =
  | { type: "text"; text: string }
  | {
      type: "file";
      url: string;
      mediaType: string;
      filename?: string;
    }
  | { type: "reasoning"; text: string }
  | {
      type: `tool-${string}`;
      toolCallId: string;
      state?: string;
      input?: any;
      output?: any;
    };

export type ChatMessage = {
  id?: string;
  role: "user" | "assistant" | "tool";
  parts: ChatMessagePart[];
  metadata?: MessageMetadata;
};

export type ToolUIPart = {
  type: string;
  state:
    | "input-streaming"
    | "input-available"
    | "output-available"
    | "output-error";
  input: any;
  output?: any;
  errorText?: string;
};
export type Attachment = {
  name: string;
  url: string;
  contentType: string;
};

export type VisibilityType = "private" | "public";
