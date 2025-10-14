# OAuth Setup Guide for ClickSafe

## Google OAuth Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: "ClickSafe OAuth"
4. Click "Create"

### Step 2: Enable APIs
1. Go to "APIs & Services" → "Library"
2. Search for "Google+ API" and enable it
3. Search for "Google Identity Services API" and enable it

### Step 3: Configure OAuth Consent Screen
1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" user type
3. Fill in required fields:
   - App name: ClickSafe
   - User support email: your email
   - Developer contact: your email
4. Add scopes: email, profile, openid
5. Save and continue

### Step 4: Create OAuth Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Application type: "Web application"
4. Name: "ClickSafe Web Client"
5. Authorized JavaScript origins:
   - http://localhost:5173
   - http://localhost:5174
   - http://localhost:5175
6. Authorized redirect URIs:
   - http://localhost:5173
   - http://localhost:5174
   - http://localhost:5175
7. Click "Create"
8. Copy the Client ID

## Facebook OAuth Setup

### Step 1: Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Consumer" app type
4. Enter app name: "ClickSafe"
5. Enter contact email
6. Click "Create App"

### Step 2: Add Facebook Login
1. In your app dashboard, click "Add Product"
2. Find "Facebook Login" and click "Set Up"
3. Choose "Web" platform
4. Enter Site URL: http://localhost:5173

### Step 3: Configure OAuth Settings
1. Go to "Facebook Login" → "Settings"
2. Add Valid OAuth Redirect URIs:
   - http://localhost:5173/
   - http://localhost:5174/
   - http://localhost:5175/
3. Save changes
4. Go to "Settings" → "Basic"
5. Copy the App ID

## Configuration

### Step 1: Update .env file
Open `h:\App-Project - 2\ClickSafe\.env` and add your credentials:

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id-here
VITE_FACEBOOK_APP_ID=your-facebook-app-id-here
VITE_API_BASE_URL=http://localhost:8000
```

### Step 2: Restart Development Server
```bash
cd "H:\App-Project - 2\ClickSafe"
npm run dev
```

## Testing

1. Navigate to http://localhost:5173/login
2. You should see Google and Facebook sign-in buttons
3. Click on either button to test OAuth flow
4. Check browser console for any errors

## Troubleshooting

### Common Issues:

1. **"OAuth client was not found"**
   - Verify VITE_GOOGLE_CLIENT_ID is correct
   - Check if the Client ID is from the correct Google Cloud project

2. **"redirect_uri_mismatch"**
   - Ensure your authorized redirect URIs include your current localhost port
   - Common ports: 5173, 5174, 5175

3. **Facebook login not working**
   - Verify VITE_FACEBOOK_APP_ID is correct
   - Check if the app is in development mode and you're added as a test user

4. **Environment variables not loading**
   - Restart the development server after updating .env
   - Ensure .env file is in the root of the ClickSafe folder

## Security Notes

- Never commit your .env file to version control
- Use different OAuth credentials for development and production
- Regularly rotate your OAuth secrets
- Monitor OAuth usage in your provider dashboards