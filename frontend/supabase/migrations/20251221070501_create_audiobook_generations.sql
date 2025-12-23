/*
  # Create audiobook generations table

  1. New Tables
    - `audiobook_generations`
      - `id` (uuid, primary key) - Unique identifier for each generation
      - `title` (text) - Title of the audiobook
      - `input_text` (text) - The input text content
      - `input_method` (text) - Method used: 'text' or 'file'
      - `file_name` (text, optional) - Original filename if uploaded
      - `audio_url` (text, optional) - URL to the generated audio file
      - `duration` (integer, optional) - Duration in seconds
      - `status` (text) - Status: 'pending', 'processing', 'completed', 'failed'
      - `error_message` (text, optional) - Error message if failed
      - `created_at` (timestamptz) - Timestamp of creation
      - `updated_at` (timestamptz) - Timestamp of last update

  2. Security
    - Enable RLS on `audiobook_generations` table
    - Add policy for public access (temporary, can be restricted with auth later)
*/

CREATE TABLE IF NOT EXISTS audiobook_generations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  input_text text NOT NULL,
  input_method text NOT NULL CHECK (input_method IN ('text', 'file')),
  file_name text,
  audio_url text,
  duration integer,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  error_message text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE audiobook_generations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
  ON audiobook_generations
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access"
  ON audiobook_generations
  FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Allow public update access"
  ON audiobook_generations
  FOR UPDATE
  TO public
  USING (true)
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_audiobook_generations_created_at 
  ON audiobook_generations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audiobook_generations_status 
  ON audiobook_generations(status);/*
  # Create audiobook generations table

  1. New Tables
    - `audiobook_generations`
      - `id` (uuid, primary key) - Unique identifier for each generation
      - `title` (text) - Title of the audiobook
      - `input_text` (text) - The input text content
      - `input_method` (text) - Method used: 'text' or 'file'
      - `file_name` (text, optional) - Original filename if uploaded
      - `audio_url` (text, optional) - URL to the generated audio file
      - `duration` (integer, optional) - Duration in seconds
      - `status` (text) - Status: 'pending', 'processing', 'completed', 'failed'
      - `error_message` (text, optional) - Error message if failed
      - `created_at` (timestamptz) - Timestamp of creation
      - `updated_at` (timestamptz) - Timestamp of last update

  2. Security
    - Enable RLS on `audiobook_generations` table
    - Add policy for public access (temporary, can be restricted with auth later)
*/

CREATE TABLE IF NOT EXISTS audiobook_generations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  input_text text NOT NULL,
  input_method text NOT NULL CHECK (input_method IN ('text', 'file')),
  file_name text,
  audio_url text,
  duration integer,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  error_message text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE audiobook_generations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
  ON audiobook_generations
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Allow public insert access"
  ON audiobook_generations
  FOR INSERT
  TO public
  WITH CHECK (true);

CREATE POLICY "Allow public update access"
  ON audiobook_generations
  FOR UPDATE
  TO public
  USING (true)
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_audiobook_generations_created_at 
  ON audiobook_generations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audiobook_generations_status 
  ON audiobook_generations(status);