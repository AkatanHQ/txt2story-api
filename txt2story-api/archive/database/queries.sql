--- comics

CREATE TABLE user_comics (
    comic_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    comic_name VARCHAR(255) NOT NULL,              -- Comic's display name
    title VARCHAR(255) NOT NULL,                   -- Title of the comic
    genre VARCHAR(100),                            -- Genre of the comic
    keywords TEXT[],                               -- Array of keywords (e.g., ["AI", "storytelling"])
    description TEXT,                              -- Optional description field for the comic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cover_image_path VARCHAR(255)                   -- URL for the cover image or thumbnail
);

CREATE TABLE comic_panels (
    panel_id SERIAL PRIMARY KEY,
    comic_id INT REFERENCES user_comics(comic_id) ON DELETE CASCADE,
    panel_index INT NOT NULL,                -- Index within the comic
    description TEXT,                        -- Description of the panel
    text TEXT,                               -- Text content in the panel
    image_path VARCHAR(255)                    -- S3 key path for the image (e.g., "user_5/comics/AI_Toddler_Tales/panel-3.png")
);
