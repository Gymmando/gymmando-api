-- Quick fix for "user_id does not exist" error
-- Run this in Supabase SQL Editor

-- Disable Row Level Security on workouts table
ALTER TABLE workouts DISABLE ROW LEVEL SECURITY;

-- Verify it worked
SELECT 
    tablename, 
    rowsecurity 
FROM pg_tables 
WHERE tablename = 'workouts';

-- rowsecurity should show 'false'

