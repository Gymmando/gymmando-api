-- Create the workouts table for GYMMANDO
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.workouts (
    id text PRIMARY KEY,
    user_id text NOT NULL,
    name text NOT NULL,
    muscle_group text NOT NULL,
    difficulty text DEFAULT 'Intermediate',
    duration text,
    exercises text[] DEFAULT '{}',
    sets_reps text DEFAULT 'As performed',
    rest_time text DEFAULT '60-90 seconds',
    notes text,
    created_at timestamp with time zone DEFAULT now()
);

-- Add index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_workouts_user_id ON public.workouts(user_id);

-- Disable Row Level Security to avoid user_id errors
ALTER TABLE public.workouts DISABLE ROW LEVEL SECURITY;

-- Verify the table was created
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns
WHERE table_name = 'workouts'
ORDER BY ordinal_position;

