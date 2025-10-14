import React from 'react';
import FacebookLogin from 'react-facebook-login';
import { useAuth } from '../contexts/AuthContext';

const FacebookSignIn = ({ onSuccess, onError }) => {
  const { login } = useAuth();

  // Check if Facebook App ID is configured
  const facebookAppId = import.meta.env.VITE_FACEBOOK_APP_ID;
  
  // Check if it's a demo/placeholder ID
  const isDemoId = !facebookAppId || facebookAppId.includes('demo') || facebookAppId.includes('your-');
  
  if (!facebookAppId) {
    return (
      <div className="w-full bg-gray-100 text-gray-500 py-3 px-4 rounded-lg text-center">
        <div className="flex items-center justify-center space-x-2">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#1877f2">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
          </svg>
          <span>Facebook Sign-In (Setup Required)</span>
        </div>
        <p className="text-xs mt-1">Please configure VITE_FACEBOOK_APP_ID in .env file</p>
      </div>
    );
  }
  
  if (isDemoId) {
    return (
      <button 
        onClick={() => {
          alert('🔧 Demo Mode: Facebook OAuth is configured but using placeholder credentials.\n\nTo enable real Facebook sign-in:\n1. Go to Facebook Developers\n2. Create an app and get App ID\n3. Replace demo-facebook-app-id with real App ID');
        }}
        className="w-full bg-[#1877f2] text-white font-medium py-3 px-4 rounded-lg hover:bg-[#166fe5] transition-all duration-200 flex items-center justify-center space-x-2"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
        <span>Continue with Facebook (Demo)</span>
      </button>
    );
  }

  const handleFacebookResponse = async (response) => {
    try {
      if (response.accessToken) {
        // Prepare user data for OAuth login
        const oauthUserData = {
          email: response.email,
          username: response.email ? response.email.split('@')[0] : response.name.replace(/\s+/g, '').toLowerCase(),
          full_name: response.name,
          profile_picture: response.picture?.data?.url || null,
          google_id: null,
          facebook_id: response.id,
          oauth_provider: 'facebook'
        };

        // Call backend OAuth login endpoint
        const apiResponse = await fetch('http://localhost:8000/auth/oauth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(oauthUserData),
        });

        if (apiResponse.ok) {
          const result = await apiResponse.json();
          
          // Store the access token and user data
          localStorage.setItem('access_token', result.access_token);
          localStorage.setItem('refresh_token', result.refresh_token);
          localStorage.setItem('user', JSON.stringify(result.user));
          
          // Update auth context
          if (onSuccess) {
            onSuccess(result);
          }
          
          // Reload the page to trigger auth context update
          window.location.href = '/dashboard';
        } else {
          const error = await apiResponse.json();
          throw new Error(error.detail || 'Facebook sign-in failed');
        }
      } else {
        throw new Error('No access token received from Facebook');
      }
    } catch (error) {
      console.error('Facebook sign-in error:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  const handleFacebookError = (error) => {
    console.error('Facebook sign-in error:', error);
    if (onError) {
      onError(error);
    }
  };

  return (
    <FacebookLogin
      appId={facebookAppId}
      autoLoad={false}
      fields="name,email,picture"
      scope="public_profile,email"
      callback={handleFacebookResponse}
      onFailure={handleFacebookError}
      cssClass="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 border-0 cursor-pointer"
      textButton="Continue with Facebook"
      icon={
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      }
    />
  );
};

export default FacebookSignIn;