# Supabase Setup for GYMMANDO

This guide will help you set up Supabase to store your workout data in the cloud.

## 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in:
   - Project name: `gymmando` (or any name you prefer)
   - Database password: (create a strong password)
   - Region: Choose closest to you
4. Click "Create new project"

## 2. Create the Workouts Table

1. In your Supabase project dashboard, go to **Table Editor** (left sidebar)
2. Click **"New Table"**
3. Configure the table:
   - **Name**: `workouts`
   - **Description**: "User workout routines"
   - **IMPORTANT**: UNCHECK "Enable Row Level Security (RLS)" for now

4. Add the following columns:

| Column Name    | Type        | Default Value               | Extra Settings          |
|----------------|-------------|----------------------------|-------------------------|
| `id`           | `text`      | -                          | Primary Key             |
| `name`         | `text`      | -                          | Required                |
| `muscle_group` | `text`      | -                          | Required                |
| `difficulty`   | `text`      | `'Intermediate'`           | Optional                |
| `duration`     | `text`      | -                          | Optional                |
| `exercises`    | `text[]`    | `'{}'`                     | Array of text           |
| `sets_reps`    | `text`      | `'As performed'`           | Optional                |
| `rest_time`    | `text`      | `'60-90 seconds'`          | Optional                |
| `notes`        | `text`      | -                          | Optional                |
| `created_at`   | `timestamp` | `now()`                    | Auto-generated          |

5. Click **"Save"**

## 3. Disable Row Level Security (RLS)

For development/testing, we'll keep RLS **DISABLED** to avoid permission errors:

1. In the **Table Editor**, click on your `workouts` table
2. Look for the **RLS** toggle or go to **Authentication > Policies**
3. Make sure RLS is **disabled** (toggle should be OFF/gray)

If RLS is already enabled and causing errors, run this SQL in the **SQL Editor** to disable it:

```sql
ALTER TABLE workouts DISABLE ROW LEVEL SECURITY;
```

> **Note**: For a production app, you'd want to enable RLS and restrict access by user. For GYMMANDO development/testing, keeping it disabled is simpler and avoids the `user_id` error.

## 4. Get Your Supabase Credentials

1. Go to **Project Settings** (⚙️ icon in sidebar)
2. Click **"API"** in the settings menu
3. Find and copy:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon public** API key (under "Project API keys")

## 5. Add Credentials to .env File

Add these to your `.env` file in the project root:

```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# Your other existing variables
DEEPGRAM_API_KEY=your-deepgram-key
OPENAI_API_KEY=your-openai-key
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-livekit-key
LIVEKIT_API_SECRET=your-livekit-secret
LLM_CHOICE=gpt-4o-mini
```

## 6. Install Supabase Package

```bash
pip install supabase
```

Or if using conda:
```bash
conda activate agentic_sys
pip install supabase
```

## 7. Test It!

Run your GYMMANDO agent:
```bash
python main.py dev
```

You should see:
```
✅ Supabase client initialized
```

When you save a workout, you'll see:
```
💾 Saved workout 'My Leg Day' to Supabase
🔗 Workout ID: legs_custom_001
```

## 8. View Your Data in Supabase

1. Go to your Supabase project dashboard
2. Click **Table Editor**
3. Select the `workouts` table
4. You'll see all your saved workouts!

You can also query your data in the **SQL Editor**:
```sql
SELECT * FROM workouts ORDER BY created_at DESC;
```

---

## Troubleshooting

### ❌ ERROR: column "user_id" does not exist
This means Row Level Security (RLS) is enabled and looking for a user_id column.

**Quick Fix Option 1**: Run the provided SQL script
1. Open `fix_supabase_rls.sql` in this repo
2. Copy the contents
3. Go to Supabase **SQL Editor**
4. Paste and run the script

**Quick Fix Option 2**: Manually disable RLS in SQL Editor:
```sql
ALTER TABLE workouts DISABLE ROW LEVEL SECURITY;
```

### "Supabase not configured" message
- Check that `SUPABASE_URL` and `SUPABASE_KEY` are in your `.env` file
- Make sure the `.env` file is in the correct location
- Restart the agent after adding credentials

### "Could not load workouts from Supabase"
- Verify your table name is exactly `workouts` (lowercase)
- Make sure RLS is disabled (see above)
- Check your internet connection

### Permission denied errors
- Make sure RLS is disabled
- Verify your API key is the **anon public** key (not the service role key)
- Check that the table is created in the same project as your credentials

---

🎉 **You're all set!** Your workout data will now be stored in the cloud and accessible from anywhere!

