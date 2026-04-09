import { type ClassValue, clsx } from 'clsx';
import { formatISO } from 'date-fns';
import { twMerge } from 'tailwind-merge';
import type { DBMessage, Document } from '@/lib/db/schema';
import { ChatSDKError, type ErrorCode } from './errors';
import type { ChatMessage, ChatMessagePart } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

function withApiBase(url: string) {
  if (API_BASE_URL && url.startsWith('/api')) {
    return `${API_BASE_URL}${url}`;
  }
  return url;
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const fetcher = async (url: string) => {
  const response = await fetch(withApiBase(url));

  if (!response.ok) {
    let code: ErrorCode = 'bad_request:api';
    let cause = '';
    const ct = response.headers.get('content-type') || '';
    try {
      if (ct.includes('application/json')) {
        const body = await response.json();
        code = (body.code as ErrorCode) || code;
        cause = String(body.cause ?? '');
      } else {
        cause = await response.text();
      }
    } catch {
      try {
        cause = await response.text();
      } catch {
        cause = '';
      }
    }
    throw new ChatSDKError(code, cause);
  }

  return response.json();
};

export async function fetchWithErrorHandlers(
  input: RequestInfo | URL,
  init?: RequestInit,
) {
  try {
    const toFetch =
      typeof input === 'string' ? withApiBase(input) : input;
    const response = await fetch(toFetch, init);

    if (!response.ok) {
      let code: ErrorCode = 'bad_request:api';
      let cause = '';
      const ct = response.headers.get('content-type') || '';
      try {
        if (ct.includes('application/json')) {
          const body = await response.json();
          code = (body.code as ErrorCode) || code;
          cause = String(body.cause ?? '');
        } else {
          cause = await response.text();
        }
      } catch {
        try {
          cause = await response.text();
        } catch {
          cause = '';
        }
      }
      throw new ChatSDKError(code, cause);
    }

    return response;
  } catch (error: unknown) {
    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      throw new ChatSDKError('offline:chat');
    }

    throw error;
  }
}

export function getLocalStorage(key: string) {
  if (typeof window !== 'undefined') {
    return JSON.parse(localStorage.getItem(key) || '[]');
  }
  return [];
}

export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

type ResponseMessage = { id: string };

export function getMostRecentUserMessage(messages: ChatMessage[]) {
  const userMessages = messages.filter((message) => message.role === 'user');
  return userMessages.at(-1);
}

export function getDocumentTimestampByIndex(
  documents: Document[],
  index: number,
) {
  if (!documents) { return new Date(); }
  if (index > documents.length) { return new Date(); }

  return documents[index].createdAt;
}

export function getTrailingMessageId({
  messages,
}: {
  messages: ResponseMessage[];
}): string | null {
  const trailingMessage = messages.at(-1);

  if (!trailingMessage) { return null; }

  return trailingMessage.id;
}

export function sanitizeText(text: string) {
  let t = text.replace('<has_function_call>', '');

  // Normalize headers
  t = t.replace(/(^|\n)\s*(?:\*\*)?Database(?:\*\*)?\s*[:：]\s*/gi, '$1**Database:** ');
  t = t.replace(/(^|\n)\s*(?:\*\*)?Thời\s*gian(?:\*\*)?\s*[:：]\s*/gi, '$1**Thời gian:** ');

  // Ensure Database and Time are on separate lines
  t = t.replace(/(\*\*Database:\*\*[\s\S]*?)\s+(?=\*\*Thời gian:\*\*)/g, '$1\n\n');

  // Ensure Time and SQL block are separated
  t = t.replace(/(\*\*Thời gian:\*\*[\s\S]*?)\s+(?=```)/g, '$1\n\n');

  // Fix malformed SQL blocks
  t = t.replace(/```\s*`sql/gi, '```sql');
  t = t.replace(/```\s+sql/gi, '```sql');
  t = t.replace(/``\s*sql/gi, '```sql');

  // Ensure newline before ```sql
  t = t.replace(/([^\n])\s*```sql/gi, '$1\n\n```sql');

  // Ensure newline after ```sql
  t = t.replace(/```sql(?!\s*\n)/gi, '```sql\n');

  // Ensure newline before closing ```
  t = t.replace(/([^\n])\s*```(?!sql)/gi, '$1\n```');

  // Remove single backticks on a line
  t = t.replace(/^\s*`\s*$/gm, '');

  // Reduce newlines
  t = t.replace(/\n{3,}/g, '\n\n');

  return t;
}

export function convertToUIMessages(messages: DBMessage[]): ChatMessage[] {
  return messages.map((message) => ({
    id: message.id,
    role: message.role as 'user' | 'assistant' | 'tool',
    parts: message.parts as ChatMessagePart[],
    metadata: {
      createdAt: formatISO(message.createdAt),
    },
  }));
}

export function getTextFromMessage(message: ChatMessage): string {
  return message.parts
    .filter((part) => part.type === 'text')
    .map((part) => (part as { type: 'text'; text: string}).text)
    .join('');
}
