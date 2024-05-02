-- Modify "meme_entry" table
ALTER TABLE "meme_entry" ADD COLUMN "title_embedding" vector(1536) NULL, ADD COLUMN "vector_id" integer NULL;
