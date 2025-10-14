import React, { useState, useEffect } from 'react';
import { Shield, Key, CheckCircle, AlertTriangle, RefreshCw, Copy, Eye, EyeOff, Settings } from 'lucide-react';

const PasswordManager = () => {
  const [activeTab, setActiveTab] = useState('generate');
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [passwordToCheck, setPasswordToCheck] = useState('');
  const [checkResult, setCheckResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Generator settings
  const [settings, setSettings] = useState({
    length: 12,
    include_uppercase: true,
    include_lowercase: true,
    include_numbers: true,
    include_symbols: true
  });

  const generatePassword = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/password/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
      });
      
      if (response.ok) {
        const data = await response.json();
        setGeneratedPassword(data.password);
      } else {
        console.error('Failed to generate password');
      }
    } catch (error) {
      console.error('Error generating password:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPasswordStrength = async (password = passwordToCheck) => {
    if (!password) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/password/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password })
      });
      
      if (response.ok) {
        const data = await response.json();
        setCheckResult(data);
      } else {
        console.error('Failed to check password');
      }
    } catch (error) {
      console.error('Error checking password:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const getStrengthColor = (score) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-blue-500';
    if (score >= 40) return 'text-yellow-500';
    if (score >= 20) return 'text-orange-500';
    return 'text-red-500';
  };

  const getStrengthBgColor = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-blue-500';
    if (score >= 40) return 'bg-yellow-500';
    if (score >= 20) return 'bg-orange-500';
    return 'bg-red-500';
  };

  useEffect(() => {
    generatePassword();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="w-12 h-12 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-800">Password Manager</h1>
          </div>
          <p className="text-gray-600">Generate secure passwords and check password strength using AI</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-xl shadow-lg mb-6">
          <div className="flex border-b">
            <button
              className={`flex-1 py-4 px-6 text-center font-medium transition-colors duration-200 ${
                activeTab === 'generate'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('generate')}
            >
              <Key className="w-5 h-5 inline mr-2" />
              Generate Password
            </button>
            <button
              className={`flex-1 py-4 px-6 text-center font-medium transition-colors duration-200 ${
                activeTab === 'check'
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('check')}
            >
              <CheckCircle className="w-5 h-5 inline mr-2" />
              Check Strength
            </button>
          </div>

          <div className="p-6">
            {activeTab === 'generate' && (
              <div className="space-y-6">
                {/* Password Settings */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center mb-4">
                    <Settings className="w-5 h-5 text-gray-600 mr-2" />
                    <h3 className="text-lg font-medium text-gray-800">Password Settings</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Length: {settings.length}
                      </label>
                      <input
                        type="range"
                        min="8"
                        max="32"
                        value={settings.length}
                        onChange={(e) => setSettings({...settings, length: parseInt(e.target.value)})}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      {[
                        { key: 'include_uppercase', label: 'Uppercase Letters (A-Z)' },
                        { key: 'include_lowercase', label: 'Lowercase Letters (a-z)' },
                        { key: 'include_numbers', label: 'Numbers (0-9)' },
                        { key: 'include_symbols', label: 'Symbols (!@#$...)' }
                      ].map(({ key, label }) => (
                        <label key={key} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={settings[key]}
                            onChange={(e) => setSettings({...settings, [key]: e.target.checked})}
                            className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <span className="text-sm text-gray-700">{label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  onClick={generatePassword}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center"
                  style={{ backgroundColor: loading ? '#6B7280' : '#2563EB' }}
                >
                  {loading ? (
                    <RefreshCw className="w-5 h-5 animate-spin mr-2" />
                  ) : (
                    <RefreshCw className="w-5 h-5 mr-2" />
                  )}
                  {loading ? 'Generating...' : 'Generate New Password'}
                </button>

                {/* Generated Password Display */}
                {generatedPassword && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-lg font-medium text-green-800">Generated Password</h4>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setShowPassword(!showPassword)}
                          className="text-green-600 hover:text-green-800"
                        >
                          {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                        <button
                          onClick={() => copyToClipboard(generatedPassword)}
                          className="text-green-600 hover:text-green-800"
                        >
                          <Copy className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                    <div className="bg-white rounded p-3 font-mono text-lg break-all">
                      {showPassword ? generatedPassword : '•'.repeat(generatedPassword.length)}
                    </div>
                    {copied && (
                      <p className="text-sm text-green-600 mt-2">✓ Copied to clipboard!</p>
                    )}
                    <button
                      onClick={() => checkPasswordStrength(generatedPassword)}
                      className="mt-3 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors duration-200"
                      style={{ backgroundColor: '#059669' }}
                    >
                      Check Strength
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'check' && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter Password to Check
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={passwordToCheck}
                      onChange={(e) => setPasswordToCheck(e.target.value)}
                      placeholder="Enter your password..."
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-gray-500 hover:text-gray-700"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => checkPasswordStrength()}
                  disabled={loading || !passwordToCheck}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
                  style={{ backgroundColor: loading || !passwordToCheck ? '#6B7280' : '#2563EB' }}
                >
                  {loading ? 'Checking...' : 'Check Password Strength'}
                </button>

                {/* Default Strength Display */}
                {!checkResult && !loading && (
                  <div className="bg-gray-50 rounded-lg p-4 border-2 border-dashed border-gray-300">
                    <div className="text-center">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Strength Score</span>
                        <span className="text-lg font-bold text-gray-400">0/100</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div className="h-3 rounded-full bg-gray-300" style={{ width: '0%' }}></div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Very Weak</span>
                        <span>Strong</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-3">Enter a password above to check its strength</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Results Display */}
        {checkResult && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Password Analysis Results</h3>
            
            <div className="space-y-4">
              {/* Strength Score */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Strength Score</span>
                  <span className={`text-lg font-bold ${getStrengthColor(checkResult.strength_score)}`}>
                    {checkResult.strength_score}/100
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${getStrengthBgColor(checkResult.strength_score)}`}
                    style={{ width: `${checkResult.strength_score}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Very Weak</span>
                  <span>Strong</span>
                </div>
              </div>

              {/* Strength Level */}
              <div className="flex items-center">
                <AlertTriangle className={`w-5 h-5 mr-2 ${getStrengthColor(checkResult.strength_score)}`} />
                <span className="font-medium">Strength Level: </span>
                <span className={`ml-1 font-bold ${getStrengthColor(checkResult.strength_score)}`}>
                  {checkResult.strength_level}
                </span>
              </div>

              {/* Feedback */}
              {checkResult.feedback && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-800 mb-2">Feedback:</h4>
                  <p className="text-yellow-700">{checkResult.feedback}</p>
                </div>
              )}

              {/* Suggestions */}
              {checkResult.suggestions && checkResult.suggestions.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 mb-2">Suggestions for Improvement:</h4>
                  <ul className="list-disc list-inside text-blue-700 space-y-1">
                    {checkResult.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PasswordManager;