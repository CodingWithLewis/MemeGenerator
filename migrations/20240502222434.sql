-- Modify "meme_entry" table
ALTER TABLE "meme_entry" ADD COLUMN "meme_template_description" character varying(8000) NULL, ADD COLUMN "meme_template_embedding" vector(1536) NULL;
