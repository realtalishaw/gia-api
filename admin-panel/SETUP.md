# Supabase Setup Guide

## Step 1: Choose Your Supabase Project

You have access to the following Supabase projects:

1. **Cereal** (slug: cereal-X6Bb)
   - Project Ref: `proj_ixbewcfjtgjrpbitdkmj`
   - Created: Tue Nov 18 2025

2. **triggerdotdev** (slug: triggerdotdev-y-FW)
   - Project Ref: `proj_eecdsplduphhpwbztltz`
   - Created: Tue Nov 18 2025

## Step 2: Get Your Supabase Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select the project you want to use
3. Navigate to **Settings** → **API**
4. Copy the following values:
   - **Project URL** (under "Project URL")
   - **anon/public key** (under "Project API keys" → "anon public")

## Step 3: Configure Environment Variables

1. Create a `.env` file in the `admin-panel` directory:
   ```bash
   cd admin-panel
   touch .env
   ```

2. Add your credentials to the `.env` file:
   ```
   VITE_SUPABASE_URL=https://your-project-ref.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key-here
   ```

   Replace:
   - `your-project-ref` with your actual project reference
   - `your-anon-key-here` with your actual anon key

## Step 4: Create a Test User

Before you can log in, you need to create a user:

1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Users**
3. Click **Add user** → **Create new user**
4. Enter an email and password
5. Click **Create user**

Alternatively, you can enable email signup in Authentication settings if you want users to be able to register themselves.

## Step 5: Start the Development Server

```bash
npm run dev
```

The app will:
- Show a login page if you're not authenticated
- Show the "Hello, World!" dashboard after successful login

## Troubleshooting

- **"Missing Supabase environment variables"**: Make sure your `.env` file exists and contains both `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
- **Login fails**: Verify your credentials are correct and the user exists in Supabase
- **CORS errors**: Make sure your Supabase project allows requests from your development URL (usually `http://localhost:5173`)


