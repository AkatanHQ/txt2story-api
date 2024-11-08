CREATE TABLE comics (
    comic_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,                 -- Comic display name
    title VARCHAR(255) NOT NULL,                -- Title of the comic
    genre VARCHAR(100),                         -- Genre of the comic (e.g., "Fantasy Adventure")
    keywords TEXT[],                            -- Array of keywords (e.g., ["friendship", "courage"])
    description TEXT,                           -- Comic description
    cover_image_url VARCHAR(255),               -- URL for the cover image
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comic_panels (
    panel_id SERIAL PRIMARY KEY,
    comic_id INT REFERENCES comics(comic_id) ON DELETE CASCADE,
    panel_order INT NOT NULL,                   -- Order of the panel in the story (e.g., 0, 1, 2)
    narrative_text TEXT NOT NULL,               -- Text content of the panel
    image_prompt TEXT,                          -- Image prompt for generating images
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comic_characters (
    character_id SERIAL PRIMARY KEY,
    comic_id INT REFERENCES comics(comic_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,                 -- Name of the character or entity (e.g., "Elara")
    short_description TEXT,                     -- Brief description (e.g., "Tall, lean, with short black hair...")
    detailed_description TEXT,                  -- Full detailed description
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for each table
CREATE TRIGGER update_comics_timestamp
BEFORE UPDATE ON comics
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_comic_panels_timestamp
BEFORE UPDATE ON comic_panels
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_comic_characters_timestamp
BEFORE UPDATE ON comic_characters
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();