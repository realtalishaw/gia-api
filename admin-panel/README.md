# Admin Panel

Frontend application built with Vite and React with Supabase authentication.

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Set up Supabase environment variables:
   - Create a `.env` file in the `admin-panel` directory
   - Add your Supabase project URL and anon key:
   ```
   VITE_SUPABASE_URL=your-project-url
   VITE_SUPABASE_ANON_KEY=your-anon-key
   ```
   - You can find these values in your Supabase project settings under "API" section

3. Start the development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

5. Preview production build:
```bash
npm run preview
```

## Authentication

The admin panel uses Supabase for authentication. Users must log in to access the dashboard.

### Setting up Supabase

1. Go to your Supabase project dashboard
2. Navigate to Settings > API
3. Copy your Project URL and anon/public key
4. Add them to your `.env` file

### Creating a User

You can create users through:
- Supabase Dashboard > Authentication > Users
- Or programmatically using Supabase Auth API

