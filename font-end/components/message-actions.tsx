import equal from "fast-deep-equal";
import { memo } from "react";
import { toast } from "sonner";
import { useSWRConfig } from "swr";
import { useCopyToClipboard } from "usehooks-ts";
import type { Vote } from "@/lib/db/schema";
import type { ChatMessage } from "@/lib/types";
import { Action, Actions } from "./elements/actions";
import { CopyIcon, PencilEditIcon, ThumbDownIcon, ThumbUpIcon } from "./icons";

export function PureMessageActions({
  chatId,
  message,
  vote,
  isLoading,
  setMode,
}: {
  chatId: string;
  message: ChatMessage;
  vote: Vote | undefined;
  isLoading: boolean;
  setMode?: (mode: "view" | "edit") => void;
}) {
  const { mutate } = useSWRConfig();
  const [_, copyToClipboard] = useCopyToClipboard();

  if (isLoading) {
    return null;
  }

  const textFromParts = message.parts
    ?.filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();

  const handleCopy = async () => {
    if (!textFromParts) {
      toast.error("Không có văn bản nào để sao chép!");
      return;
    }

    await copyToClipboard(textFromParts);
    toast.success("Đã sao chép!");
  };

  // User messages get edit (on hover) and copy actions
  if (message.role === "user") {
    return (
      <Actions className="-mr-0.5 justify-end">
        <div className="relative">
          {setMode && (
            <Action
              className="-left-10 absolute top-0 opacity-0 transition-opacity focus-visible:opacity-100 group-hover/message:opacity-100"
              data-testid="message-edit-button"
              onClick={() => setMode("edit")}
              tooltip="Chỉnh sửa"
            >
              <PencilEditIcon />
            </Action>
          )}
          <Action onClick={handleCopy} tooltip="Sao chép">
            <CopyIcon />
          </Action>
        </div>
      </Actions>
    );
  }

  return (
    <Actions className="-ml-0.5">
      <Action onClick={handleCopy} tooltip="Sao chép">
        <CopyIcon />
      </Action>

      <Action
        data-testid="message-upvote"
        disabled={vote?.isUpvoted}
        onClick={() => {
          if (!message.id) {
            toast.error("Mã số tin nhắn bị thiếu.");
            return;
          }
          const msgId = message.id;
          const upvote = fetch("/api/vote", {
            method: "PATCH",
            body: JSON.stringify({
              chatId,
              messageId: msgId,
              type: "up",
            }),
          });

          toast.promise(upvote, {
            loading: "Đang bình chọn tích cực...",
            success: () => {
              mutate(
                `/api/vote?chatId=${chatId}`,
                (currentVotes: Vote[] | undefined) => {
                  if (!currentVotes) {
                    return [];
                  }

                  const votesWithoutCurrent = currentVotes.filter(
                    (currentVote) => currentVote.messageId !== msgId
                  );

                  return [
                    ...votesWithoutCurrent,
                    {
                      chatId,
                      messageId: msgId,
                      isUpvoted: true,
                    },
                  ];
                },
                { revalidate: false }
              );

              return "Phản hồi được bình chọn tích cực!";
            },
            error: "Không thể bình chọn cho câu trả lời.",
          });
        }}
        tooltip="Bình chọn tích cực"
      >
        <ThumbUpIcon />
      </Action>

      <Action
        data-testid="message-downvote"
        disabled={vote && !vote.isUpvoted}
        onClick={() => {
          if (!message.id) {
            toast.error("Mã số tin nhắn bị thiếu.");
            return;
          }
          const msgId = message.id;
          const downvote = fetch("/api/vote", {
            method: "PATCH",
            body: JSON.stringify({
              chatId,
              messageId: msgId,
              type: "down",
            }),
          });

          toast.promise(downvote, {
            loading: "Đang bình chọn tiêu cực...",
            success: () => {
              mutate(
                `/api/vote?chatId=${chatId}`,
                (currentVotes: Vote[] | undefined) => {
                  if (!currentVotes) {
                    return [];
                  }

                  const votesWithoutCurrent = currentVotes.filter(
                    (currentVote) => currentVote.messageId !== msgId
                  );

                  return [
                    ...votesWithoutCurrent,
                    {
                      chatId,
                      messageId: msgId,
                      isUpvoted: false,
                    },
                  ];
                },
                { revalidate: false }
              );

              return "Phản hồi được bình chọn tiêu cực!";
            },
            error: "Không thể bình chọn cho câu trả lời.",
          });
        }}
        tooltip="Bình chọn tiêu cực"
      >
        <ThumbDownIcon />
      </Action>
    </Actions>
  );
}

export const MessageActions = memo(
  PureMessageActions,
  (prevProps, nextProps) => {
    if (!equal(prevProps.vote, nextProps.vote)) {
      return false;
    }
    if (prevProps.isLoading !== nextProps.isLoading) {
      return false;
    }

    return true;
  }
);
