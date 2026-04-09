import type { UserType } from "@/app/(auth)/auth";

type Entitlements = {
  maxMessagesPerDay: number;
  availableChatModelIds: string[];
};

export const entitlementsByUserType: Record<UserType, Entitlements> = {
  /*
   * For users without an account
   */
  guest: {
    maxMessagesPerDay: 10000,
    availableChatModelIds: ["chat-model"],
  },

  /*
   * For users with an account
   */
  regular: {
    maxMessagesPerDay: 10000,
    availableChatModelIds: ["chat-model"],
  },

  /*
   * TODO: For users with an account and a paid membership
   */
};
