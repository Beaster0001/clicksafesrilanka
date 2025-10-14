import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon,
  Lock,
  Trash2,
  Globe,
  Smartphone,
  Key,
  RefreshCw,
  Download,
  Upload,
  Database,
  AlertTriangle,
  CheckCircle,
  X,
  Save,
  Mail,
  MessageSquare,
  UserX,
  LogOut
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { userAPI } from '../services/api';

const Settings = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Settings state
  const [settings, setSettings] = useState({
    // Security Settings
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    
    // Privacy Settings
    profileVisibility: 'public',
    showActivity: true,
    showStats: true,
    dataSharing: false,
    analyticsTracking: true,
    
    // Notification Settings
    emailNotifications: true,
    pushNotifications: true,
    threatAlerts: true,
    weeklyReports: true,
    systemUpdates: true,
    marketingEmails: false,
    
    // Language & Region
    language: 'en',
    timezone: 'Asia/Colombo',
    dateFormat: 'MM/DD/YYYY',
    numberFormat: 'US',
    
    // Data Management
    autoBackup: true,
    dataRetention: '12months',
    exportFormat: 'json'
  });

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  useEffect(() => {
    loadUserSettings();
  }, []);

  const loadUserSettings = async () => {
    try {
      // Load user settings from API if available
      const userSettings = await userAPI.getSettings();
      setSettings(prev => ({ ...prev, ...userSettings }));
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSettingChange = (category, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  const handlePasswordChange = async () => {
    if (!settings.currentPassword || !settings.newPassword || !settings.confirmPassword) {
      setError('Please fill in all password fields');
      return;
    }

    if (settings.newPassword !== settings.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (settings.newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await userAPI.changePassword({
        current_password: settings.currentPassword,
        new_password: settings.newPassword
      });

      setSuccess('Password changed successfully!');
      setSettings(prev => ({
        ...prev,
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }));

      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error.message || 'Failed to change password');
      setTimeout(() => setError(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    setLoading(true);
    setError('');

    try {
      // Save settings to API
      await userAPI.updateSettings(settings);
      setSuccess('Settings saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error.message || 'Failed to save settings');
      setTimeout(() => setError(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE MY ACCOUNT') {
      setError('Please type "DELETE MY ACCOUNT" to confirm');
      return;
    }

    setLoading(true);
    try {
      await userAPI.deleteAccount();
      logout();
    } catch (error) {
      setError(error.message || 'Failed to delete account');
    } finally {
      setLoading(false);
    }
  };

  const exportData = async () => {
    try {
      const data = await userAPI.exportData(settings.exportFormat);
      
      // Handle different export formats
      let blobData, mimeType, fileExtension;
      
      switch (settings.exportFormat) {
        case 'csv':
          blobData = data; // API returns CSV string
          mimeType = 'text/csv';
          fileExtension = 'csv';
          break;
        case 'xml':
          blobData = data; // API returns XML string
          mimeType = 'application/xml';
          fileExtension = 'xml';
          break;
        case 'json':
        default:
          // For JSON, data is already an object, so stringify it
          blobData = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
          mimeType = 'application/json';
          fileExtension = 'json';
          break;
      }
      
      const blob = new Blob([blobData], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `clicksafe-data-${new Date().toISOString().split('T')[0]}.${fileExtension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setSuccess('Data exported successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError('Failed to export data');
      setTimeout(() => setError(''), 5000);
    }
  };

  const ToggleSwitch = ({ enabled, onChange, disabled = false }) => (
    <button
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
        enabled ? 'bg-blue-600' : 'bg-gray-200'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );

  const renderGeneralTab = () => (
    <div className="space-y-8">
      {/* Change Password */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-black mb-4 flex items-center">
          <Lock className="w-5 h-5 mr-2 text-blue-600" />
          Change Password
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Password
            </label>
            <input
              type="password"
              value={settings.currentPassword}
              onChange={(e) => handleSettingChange('security', 'currentPassword', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                New Password
              </label>
              <input
                type="password"
                value={settings.newPassword}
                onChange={(e) => handleSettingChange('security', 'newPassword', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Confirm New Password
              </label>
              <input
                type="password"
                value={settings.confirmPassword}
                onChange={(e) => handleSettingChange('security', 'confirmPassword', e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          <button
            onClick={handlePasswordChange}
            disabled={loading}
            className="px-6 py-3 bg-gray-200 text-gray-600 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50 border border-gray-300"
          >
            {loading ? 'Changing...' : 'Change Password'}
          </button>
        </div>
      </div>

      {/* Data Management */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="w-5 h-5 mr-2 text-teal-600" />
          Data Management
        </h3>
        
        <div className="space-y-6">
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="font-medium text-gray-900">Auto Backup</p>
              <p className="text-sm text-gray-600">Automatically backup your data weekly</p>
            </div>
            <ToggleSwitch
              enabled={settings.autoBackup}
              onChange={(value) => handleSettingChange('data', 'autoBackup', value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Retention Period
            </label>
            <select
              value={settings.dataRetention}
              onChange={(e) => handleSettingChange('data', 'dataRetention', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="3months">3 Months</option>
              <option value="6months">6 Months</option>
              <option value="12months">12 Months</option>
              <option value="forever">Forever</option>
            </select>
          </div>
          
          <div className="border-t pt-6">
            <h4 className="font-medium text-gray-900 mb-4">Export Your Data</h4>
            <div className="flex items-center space-x-4">
              <select
                value={settings.exportFormat}
                onChange={(e) => handleSettingChange('data', 'exportFormat', e.target.value)}
                className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="xml">XML</option>
              </select>
              <button
                onClick={exportData}
                className="flex items-center px-6 py-3 bg-gray-200 text-black rounded-lg hover:bg-gray-300 transition-colors"
              >
                <Download className="w-4 h-4 mr-2" />
                Export Data
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Account Management - Danger Zone */}
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-red-900 mb-4 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
          Danger Zone
        </h3>
        
        <div className="space-y-4">
          <div className="bg-white rounded-lg p-4 border border-red-200">
            <h4 className="font-medium text-gray-900 mb-2">Delete Account</h4>
            <p className="text-sm text-gray-600 mb-4">
              Permanently delete your account and all associated data. This action cannot be undone.
            </p>
            
            {!showDeleteConfirm ? (
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center px-4 py-2 bg-red-500 text-red-700 rounded-lg hover:bg-red-600 transition-colors border-2 border-red-600"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Account
              </button>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Type "DELETE MY ACCOUNT" to confirm:
                  </label>
                  <input
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    placeholder="DELETE MY ACCOUNT"
                  />
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={handleDeleteAccount}
                    disabled={deleteConfirmText !== 'DELETE MY ACCOUNT' || loading}
                    className="flex items-center px-4 py-2 bg-red-500 text-red-700 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 border-2 border-red-600"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {loading ? 'Deleting...' : 'Confirm Delete'}
                  </button>
                  
                  <button
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setDeleteConfirmText('');
                    }}
                    className="flex items-center px-4 py-2 bg-gray-500 text-gray-600 rounded-lg hover:bg-gray-600 transition-colors"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-2">Manage your account preferences and security settings</p>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
            <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            <span className="text-green-700">{success}</span>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        <div className="max-w-4xl mx-auto">
          {/* Main Content */}
          <div>
            <div className="space-y-6">
              {renderGeneralTab()}
              
              {/* Save Button */}
              <div className="flex justify-end pt-6">
                <button
                  onClick={handleSaveSettings}
                  disabled={loading}
                  className="flex items-center px-6 py-3 bg-black text-black rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {loading ? 'Saving...' : 'Save Settings'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;