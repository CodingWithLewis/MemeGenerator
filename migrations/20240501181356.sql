-- Modify "meme_entry" table
ALTER TABLE "meme_entry" ADD COLUMN "embedding" vector(3072) NULL;
