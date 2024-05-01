-- Create "meme_entry" table
CREATE TABLE "meme_entry" (
  "id" uuid NOT NULL DEFAULT gen_random_uuid(),
  "name" character varying(200) NOT NULL,
  "url" character varying NOT NULL,
  "content" text NOT NULL,
  "meme_added" timestamp NULL,
  PRIMARY KEY ("id")
);
-- Create "meme_image" table
CREATE TABLE "meme_image" (
  "id" serial NOT NULL,
  "meme_entry" uuid NOT NULL,
  "source_url" character varying NOT NULL,
  "caption_text" character varying(600) NULL,
  PRIMARY KEY ("id"),
  CONSTRAINT "meme_image_meme_entry_fkey" FOREIGN KEY ("meme_entry") REFERENCES "meme_entry" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);
