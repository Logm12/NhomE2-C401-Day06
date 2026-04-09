-- ALTER TABLE "Suggestion" DROP CONSTRAINT "Suggestion_documentId_documentCreatedAt_Document_id_createdAt_fk";
--> statement-breakpoint
-- ALTER TABLE "Document" DROP CONSTRAINT "Document_id_createdAt_pk";--> statement-breakpoint
-- ALTER TABLE "Document" ADD CONSTRAINT "Document_id_pk" PRIMARY KEY("id");--> statement-breakpoint
ALTER TABLE "Message_v2" ADD COLUMN "userId" uuid;--> statement-breakpoint
DO $$ BEGIN
 ALTER TABLE "Message_v2" ADD CONSTRAINT "Message_v2_userId_User_id_fk" FOREIGN KEY ("userId") REFERENCES "public"."User"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
--> statement-breakpoint
/*
DO $$ BEGIN
 ALTER TABLE "Suggestion" ADD CONSTRAINT "Suggestion_documentId_Document_id_fk" FOREIGN KEY ("documentId") REFERENCES "public"."Document"("id") ON DELETE no action ON UPDATE no action;
EXCEPTION
 WHEN duplicate_object THEN null;
END $$;
*/
