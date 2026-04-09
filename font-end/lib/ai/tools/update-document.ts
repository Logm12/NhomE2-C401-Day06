import type { Session } from "next-auth";
import { z } from "zod";
import { documentHandlersByArtifactKind } from "@/lib/artifacts/server";
import { getDocumentById } from "@/lib/db/queries";

type UpdateDocumentProps = {
  session: Session;
  dataStream: any;
};

export const updateDocument = ({
  session,
  dataStream,
}: UpdateDocumentProps) => ({
  description: "Update a document with the given description.",
  inputSchema: z.object({
    id: z.string().describe("The ID of the document to update"),
    description: z
      .string()
      .describe("The description of changes that need to be made"),
  }),
  execute: async ({ id, description }: { id: string; description: string }) => {
    const document = await getDocumentById({ id });

    if (!document) {
      return {
        error: "Document not found",
      };
    }

    dataStream.write({
      type: "data-clear",
      data: null,
      transient: true,
    });

    const documentHandler = documentHandlersByArtifactKind.find(
      (documentHandlerByArtifactKind) =>
        documentHandlerByArtifactKind.kind === document.kind
    );

    if (!documentHandler) {
      throw new Error(`No document handler found for kind: ${document.kind}`);
    }

    await documentHandler.onUpdateDocument({
      document,
      description,
      dataStream,
      session,
    });

    dataStream.write({ type: "data-finish", data: null, transient: true });

    return {
      id,
      title: document.title,
      kind: document.kind,
      content: "The document has been updated successfully.",
    };
  },
});
