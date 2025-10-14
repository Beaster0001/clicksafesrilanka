import React from 'react';
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';

const GoogleSignIn = ({ onSuccess, onError }) => {
  const { oauthLogin } = useAuth();
  
  // Check if Google Client ID is configured
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  
  if (!googleClientId) {
    return (
      <div className="w-full bg-gray-100 text-gray-500 py-3 px-4 rounded-lg text-center">
        <div className="flex items-center justify-center space-x-2">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span>Google Sign-In (Setup Required)</span>
        </div>
        <p className="text-xs mt-1">Please configure VITE_GOOGLE_CLIENT_ID in .env file</p>
      </div>
    );
  }

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      console.log('Google credential response:', credentialResponse);
      
      if (!credentialResponse || !credentialResponse.credential) {
        console.error('Invalid credential response:', credentialResponse);
        throw new Error('No credential received from Google');
      }
      
      // Decode the JWT token from Google
      const token = credentialResponse.credential;
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      
      const googleUser = JSON.parse(jsonPayload);
      console.log('Decoded Google user:', googleUser);
      
      // Prepare user data for OAuth login
      const oauthUserData = {
        email: googleUser.email,
        username: googleUser.email.split('@')[0], // Use email prefix as username
        full_name: googleUser.name,
        profile_picture: googleUser.picture,
        google_id: googleUser.sub,
        facebook_id: null,
        oauth_provider: 'google'
      };

      console.log('Sending OAuth data to backend:', oauthUserData);

      // Call backend OAuth login endpoint
      console.log('Making request to:', 'http://localhost:8000/auth/oauth/login');
      
      const response = await fetch('http://localhost:8000/auth/oauth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(oauthUserData),
      }).catch(error => {
        console.error('Network error during OAuth request:', error);
        throw new Error('Failed to connect to server. Please ensure the backend is running.');
      });

      console.log('Backend response status:', response.status);
      console.log('Backend response ok:', response.ok);
      
      if (response.ok) {
        const result = await response.json();
        console.log('Backend response data:', result);
        
        // Store the access token and user data
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('refresh_token', result.refresh_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Update auth context with OAuth data
        if (oauthLogin) {
          await oauthLogin(result.user, result.access_token);
        }
        
        // Trigger success callback
        if (onSuccess) {
          onSuccess(result);
        }
        
        // Navigate to dashboard
        window.location.href = '/dashboard';
      } else {
        const error = await response.json();
        console.error('Backend error response:', error);
        throw new Error(error.detail || error.message || 'Google sign-in failed');
      }
    } catch (error) {
      console.error('Google sign-in error:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  const handleGoogleError = (error) => {
    console.error('Google sign-in error details:', error);
    const errorMessage = error?.details || error?.error || 'Google sign-in was unsuccessful';
    const finalError = new Error(`Google sign-in failed: ${errorMessage}`);
    console.error('Google sign-in error:', finalError);
    if (onError) {
      onError(finalError);
    }
  };

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={handleGoogleError}
        useOneTap={false}
        theme="outline"
        size="large"
        text="signin_with"
        shape="rectangular"
        logo_alignment="left"
        width="100%"
        locale="en"
      />
    </GoogleOAuthProvider>
  );
};

export default GoogleSignIn;