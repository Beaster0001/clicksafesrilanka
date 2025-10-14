  // API configuration and utility functions
const API_BASE_URL = 'http://localhost:8000';

// API client with automatic token handling
class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  // Set authorization header
  getHeaders(contentType = 'application/json') {
    const headers = {
      'Content-Type': contentType,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  // Update token
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('access_token', token);
    } else {
      localStorage.removeItem('access_token');
    }
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
        
        // Handle FastAPI validation errors
        if (Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail.map(err => 
            err.msg || err.message || 'Validation error'
          );
          throw new Error(errorMessages.join(', '));
        }
        
        // Handle single error messages
        const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
        throw new Error(errorMessage);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // HTTP methods
  async get(endpoint) {
    return this.request(endpoint);
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE',
    });
  }
}

// Create API client instance
const apiClient = new ApiClient();

// Authentication API
export const authAPI = {
  // Register new user
  register: async (userData) => {
    const response = await apiClient.post('/auth/register', userData);
    return response;
  },

  // Login user
  login: async (credentials) => {
    const response = await apiClient.post('/auth/login', credentials);
    if (response.access_token) {
      apiClient.setToken(response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      localStorage.setItem('user_data', JSON.stringify(response.user));
    }
    return response;
  },

  // Logout user
  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.warn('Logout API call failed:', error);
    } finally {
      // Clear local storage regardless of API call success
      apiClient.setToken(null);
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
    }
  },

  // Get current user
  getCurrentUser: async () => {
    return await apiClient.get('/auth/me');
  },

  // Change password
  changePassword: async (passwordData) => {
    return await apiClient.post('/auth/password/change', passwordData);
  },

  // Request password reset
  requestPasswordReset: async (email) => {
    return await apiClient.post('/auth/password/reset', { email });
  },

  // Confirm password reset
  confirmPasswordReset: async (resetData) => {
    return await apiClient.post('/auth/password/reset/confirm', resetData);
  },

  // Refresh token
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    if (response.access_token) {
      apiClient.setToken(response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      localStorage.setItem('user_data', JSON.stringify(response.user));
    }

    return response;
  },
};

// Dashboard API
export const dashboardAPI = {
  // Get dashboard data
  getDashboardData: async () => {
    return await apiClient.get('/dashboard/');
  },

  // Get user scan statistics
  getScanStats: async (days = 30) => {
    return await apiClient.get(`/scans/stats/summary?days=${days}`);
  },
};

// Scans API
export const scansAPI = {
  // Create new scan
  createScan: async (scanData) => {
    return await apiClient.post('/scans/', scanData);
  },

  // Get user scans with filters
  getScans: async (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value);
      }
    });
    
    const query = params.toString();
    return await apiClient.get(`/scans/${query ? '?' + query : ''}`);
  },

  // Get scan details
  getScanDetails: async (scanId) => {
    return await apiClient.get(`/scans/${scanId}`);
  },

  // Delete scan
  deleteScan: async (scanId) => {
    return await apiClient.delete(`/scans/${scanId}`);
  },

  // Get recent scams (public)
  getRecentScams: async (language = null, limit = 20) => {
    const params = new URLSearchParams({ limit });
    if (language) params.append('language', language);
    
    return await apiClient.get(`/scans/recent-scams/public?${params.toString()}`);
  },
};

// QR Code API
export const qrAPI = {
  // Get QR scan history
  getScanHistory: async (page = 1, pageSize = 20) => {
    return await apiClient.get(`/api/qr/scan/history?page=${page}&page_size=${pageSize}`);
  },

  // Get QR scan details
  getScanDetails: async (scanId) => {
    return await apiClient.get(`/api/qr/scan/${scanId}`);
  },

  // Get QR service status
  getStatus: async () => {
    return await apiClient.get('/api/qr/status');
  },
};

// Admin API
export const adminAPI = {
  // Get admin stats
  getStats: async () => {
    return await apiClient.get('/admin/stats');
  },

  // Get all users
  getUsers: async (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value);
      }
    });
    
    const query = params.toString();
    return await apiClient.get(`/admin/users${query ? '?' + query : ''}`);
  },

  // Get user details
  getUserDetails: async (userId) => {
    return await apiClient.get(`/admin/users/${userId}`);
  },

  // Get user activities
  getUserActivities: async (userId, limit = 50) => {
    return await apiClient.get(`/admin/users/${userId}/activities?limit=${limit}`);
  },

  // Delete user
  deleteUser: async (userId) => {
    return await apiClient.delete(`/admin/users/${userId}`);
  },

  // Activate user
  activateUser: async (userId) => {
    return await apiClient.patch(`/admin/users/${userId}/activate`);
  },

  // Deactivate user
  deactivateUser: async (userId) => {
    return await apiClient.patch(`/admin/users/${userId}/deactivate`);
  },
};

// User profile API
export const userAPI = {
  // Get user profile
  getProfile: async () => {
    return await apiClient.get('/users/profile');
  },

  // Update user profile
  updateProfile: async (profileData) => {
    return await apiClient.patch('/users/profile', profileData);
  },

  // Get user activities
  getActivities: async (limit = 50) => {
    return await apiClient.get(`/users/activities?limit=${limit}`);
  },

  // Change password
  changePassword: async (passwordData) => {
    return await apiClient.post('/users/change-password', passwordData);
  },

  // Delete account
  deleteAccount: async () => {
    return await apiClient.delete('/users/account');
  },

  // Export user data
  exportData: async (format = 'json') => {
    // For XML and CSV, we need to handle the response as text to avoid JSON parsing issues
    const url = `${apiClient.baseURL}/users/export-data?format=${format}`;
    const headers = apiClient.getHeaders();
    
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Export failed' }));
      const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
      throw new Error(errorMessage);
    }
    
    // For JSON format, parse as JSON
    if (format === 'json') {
      return await response.json();
    }
    
    // For XML and CSV formats, return as text
    return await response.text();
  },

  // Get user settings
  getSettings: async () => {
    return await apiClient.get('/users/settings');
  },

  // Update user settings
  updateSettings: async (settings) => {
    return await apiClient.patch('/users/settings', settings);
  },
};

// Prediction API (legacy, but enhanced)
export const predictionAPI = {
  predict: async (message) => {
    return await apiClient.post('/predict', { message });
  },
};

// Utility function to check if user is logged in
export const isLoggedIn = () => {
  return !!localStorage.getItem('access_token');
};

// Utility function to get stored user data
export const getStoredUser = () => {
  const userData = localStorage.getItem('user');
  return userData ? JSON.parse(userData) : null;
};

// Utility function to check if user is admin
export const isAdmin = () => {
  const user = getStoredUser();
  return user && user.is_admin;
};

export default apiClient;