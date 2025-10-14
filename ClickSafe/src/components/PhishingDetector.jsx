import React, { useState, useEffect } from 'react';
import { AlertCircle, ShieldCheck, Send, Loader, AlertTriangle, Eye, RefreshCw, Info } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { scansAPI } from '../services/api';

const PhishingDetector = () => {
  const { isAuthenticated, user } = useAuth();
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [scanHistory, setScanHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [showHistory, setShowHistory] = useState(false);

  const [showCERTModal, setShowCERTModal] = useState(false);
  const [certReporting, setCertReporting] = useState(false);
  const [certComments, setCertComments] = useState('');
  const [certReportSuccess, setCertReportSuccess] = useState(false);
  const [showEmailPreview, setShowEmailPreview] = useState(false);

  console.log('PhishingDetector component loaded', { isAuthenticated, user: user ? 'logged in' : 'not logged in' });

  // Load user's previous scans
  useEffect(() => {
    if (isAuthenticated && user) {
      fetchScanHistory();
    } else {
      setScanHistory([]);
    }
  }, [isAuthenticated, user]);

  const analyzeMessage = async () => {
    if (!message.trim()) {
      setError('Please enter a message to analyze');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      console.log('Starting analysis...', { isAuthenticated, user: !!user });
      
      if (isAuthenticated && user) {
        console.log('Using authenticated scans API');
        console.log('Current token:', localStorage.getItem('access_token') ? 'exists' : 'missing');
        console.log('User object:', user);
        
        try {
          console.log('Making API call to scansAPI.createScan...');
          const scanResult = await scansAPI.createScan({
            content: message.trim(),
            scan_type: 'message'
          });
          
          console.log('Scan result received:', scanResult);
          
          setResult({
            prediction: scanResult.classification || 'unknown',
            confidence: scanResult.risk_score || 0,
            risk_score: scanResult.risk_score || 0,
            language: scanResult.language || 'english',
            explanation: scanResult.explanation || 'Analysis completed',
            suspicious_terms: scanResult.suspicious_terms || [],
            classification: scanResult.classification || 'unknown',
            is_safe: scanResult.classification === 'safe' || scanResult.is_safe === true
          });
          
          // Refresh history
          if (isAuthenticated && user) {
            fetchScanHistory();
          }
        } catch (scanError) {
          console.error('Scans API failed, trying direct prediction:', scanError);
          // Fallback to direct prediction
          const response = await fetch('http://localhost:8000/predict', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message.trim() }),
          });

          if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
          }

          const data = await response.json();
          console.log('Fallback prediction result:', data);
          
          // Transform fallback result to match expected format
          setResult({
            prediction: data.classification || 'unknown',
            confidence: data.risk_score || 0,
            risk_score: data.risk_score || 0, // Backend now returns 0-100 scale directly
            language: data.language || 'english',
            explanation: data.explanation || 'Analysis completed',
            suspicious_terms: data.suspicious_terms || [],
            classification: data.classification || 'unknown',
            is_safe: data.classification === 'safe'
          });
        }
      } else {
        console.log('Using direct prediction API for non-authenticated user');
        const response = await fetch('http://localhost:8000/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: message.trim() }),
        });

        if (!response.ok) {
          throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        console.log('Direct prediction result:', data);
        
        // Transform direct result to match expected format
        setResult({
          prediction: data.classification || 'unknown',
          confidence: data.risk_score || 0,
          risk_score: data.risk_score || 0, // Backend now returns 0-100 scale directly
          language: data.language || 'english',
          explanation: data.explanation || 'Analysis completed',
          suspicious_terms: data.suspicious_terms || [],
          classification: data.classification || 'unknown',
          is_safe: data.classification === 'safe' || data.is_safe === true
        });
        
        // Refresh scan history after successful analysis (for direct prediction)
        if (isAuthenticated && user) {
          fetchScanHistory();
        }
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setError(`Analysis failed: ${err.message}. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      analyzeMessage();
    }
  };

  const fetchScanHistory = async () => {
    if (!isAuthenticated || !user) {
      return;
    }

    setHistoryLoading(true);
    setHistoryError('');

    try {
      console.log('Fetching scan history...');
      const historyData = await scansAPI.getScans({ 
        limit: 10, 
        scan_type: 'message',
        sort: 'created_at',
        order: 'desc'
      });
      
      console.log('Scan history received:', historyData);
      setScanHistory(historyData || []);
    } catch (err) {
      console.error('Error fetching scan history:', err);
      setHistoryError('Failed to load scan history');
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleHistoryClick = (scan) => {
    // Populate the main interface with the selected scan
    setMessage(scan.content || scan.message || '');
    
    // Set the result from the historical scan
    const historicalResult = {
      prediction: scan.classification || 'unknown',
      confidence: scan.risk_score || 0,
      risk_score: scan.risk_score || 0, // Backend already returns 0-100 scale directly
      language: scan.language || 'english',
      explanation: scan.explanation || 'Historical scan result',
      suspicious_terms: scan.suspicious_terms || [],
      classification: scan.classification || 'unknown',
      is_safe: scan.is_safe || scan.classification === 'safe'
    };
    
    setResult(historicalResult);
    setError('');
    
    // Scroll to the top to show the populated message
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getRiskColor = (riskScore) => {
    if (riskScore < 30) return 'text-green-600';
    if (riskScore < 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskBgColor = (riskScore) => {
    if (riskScore < 30) return 'bg-green-50 border-green-200';
    if (riskScore < 70) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const getLanguageFlag = (language) => {
    const flags = {
      english: '🇺🇸',
      sinhala: '🇱🇰',
      tamil: '🇱🇰'
    };
    return flags[language] || '🌐';
  };

  // CERT Reporting Functions
  const isHighRisk = () => {
    const riskScore = result?.risk_score || 0;
    const shouldShow = riskScore >= 50;
    console.log('CERT Button Debug:', {
      riskScore,
      isAuthenticated,
      shouldShow,
      result: result
    });
    return shouldShow; // Accept medium-risk and above (50+) for CERT reporting
  };

  const generateEmailPreview = () => {
    if (!result || !isAuthenticated) return '';

    const reportId = `CS-${new Date().toISOString().slice(0,10).replace(/-/g,'')}-${Date.now().toString().slice(-4)}`;
    const threatMessage = message.substring(0, 200) + (message.length > 200 ? '...' : '');
    const riskScore = result.risk_score || 0;
    const classification = result.classification || 'unknown';
    const confidence = Math.round(riskScore);
    const reasoning = result.explanation || 'No detailed analysis available';
    
    return `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: #d32f2f; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .threat-box { background: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 20px 0; }
        .details-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .details-table th, .details-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .details-table th { background: #f5f5f5; font-weight: bold; }
        .footer { background: #f5f5f5; padding: 15px; text-align: center; font-size: 12px; color: #666; }
        .risk-critical { color: #d32f2f; font-weight: bold; }
        .risk-high { color: #ff9800; font-weight: bold; }
        .message-box { background: #f9f9f9; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 ClickSafe Phishing Message Report</h1>
        <p>Report ID: ${reportId}</p>
    </div>
    
    <div class="content">
        <p><strong>Dear Sri Lanka CERT Team,</strong></p>
        
        <p>ClickSafe has detected a high-risk phishing message that requires immediate attention. This automated report contains detailed analysis and evidence.</p>
        
        <div class="threat-box">
            <h3>⚠️ Threat Summary</h3>
            <p><strong>Risk Score:</strong> <span class="${riskScore >= 85 ? 'risk-critical' : 'risk-high'}">${riskScore}% (${classification.toUpperCase()})</span></p>
            <p><strong>Message Language:</strong> ${result.language || 'Unknown'}</p>
            <p><strong>Detection Confidence:</strong> ${confidence}%</p>
        </div>
        
        <h3>📱 Malicious Message Content</h3>
        <div class="message-box">
            <p><strong>Original Message:</strong></p>
            <p style="font-style: italic;">"${threatMessage}"</p>
        </div>
        
        <h3>📊 Detailed Analysis</h3>
        <table class="details-table">
            <tr><th>Detection Time</th><td>${new Date().toLocaleString('en-US', {timeZone: 'Asia/Colombo'})}</td></tr>
            <tr><th>Reporter Location</th><td>Sri Lanka</td></tr>
            <tr><th>Detection Method</th><td>Multilingual Phishing Detection + ML Analysis</td></tr>
            <tr><th>Threat Category</th><td>Phishing/Social Engineering Message</td></tr>
            <tr><th>Recommendation</th><td>Block similar patterns and investigate</td></tr>
        </table>
        
        <h3>🔍 Technical Analysis</h3>
        <p><strong>Analysis Summary:</strong></p>
        <p>${reasoning}</p>
        
        ${result.suspicious_terms && result.suspicious_terms.length > 0 ? `
        <h3>🚩 Suspicious Elements Detected</h3>
        <ul>
            ${result.suspicious_terms.map(term => `<li><strong>${term}</strong></li>`).join('')}
        </ul>
        ` : ''}
        
        ${certComments ? `
        <h3>👤 User Report</h3>
        <p><strong>Additional Context from User:</strong></p>
        <p style="background: #f9f9f9; padding: 10px; border-radius: 5px; font-style: italic;">"${certComments}"</p>
        ` : ''}
        
        <h3>⚡ Recommended Actions</h3>
        <ul>
            <li>Issue public warning about this phishing pattern</li>
            <li>Coordinate with telecom providers to block similar messages</li>
            <li>Add keywords to national phishing detection systems</li>
            <li>Share threat intelligence with regional CERT teams</li>
        </ul>
        
        <p><strong>This is an automated report generated by ClickSafe security system.</strong><br>
        For technical questions, please contact: <a href="mailto:ClickSafe_Srilanka@outlook.com">ClickSafe_Srilanka@outlook.com</a></p>
    </div>
    
    <div class="footer">
        <p>ClickSafe - Protecting Sri Lankan Citizens from Cyber Threats<br>
        Report generated at ${new Date().toISOString()}</p>
    </div>
</body>
</html>`;
  };

  const handleCERTReport = async () => {
    if (!result || !isAuthenticated) return;

    try {
      setCertReporting(true);
      
      const reportData = {
        url: message.substring(0, 100) + '...', // Use message content as URL placeholder
        content: message, // The actual suspicious message content
        risk_score: Math.round(result.risk_score || 0),
        risk_level: result.classification || 'unknown',
        classification: result.classification || 'unknown',
        confidence: (result.risk_score || 0) / 100, // Convert percentage to 0-1 range
        reasoning: result.explanation || '',
        security_analysis: {
          threat_type: 'phishing_message',
          message_content: message,
          language: result.language || 'unknown',
          suspicious_terms: result.suspicious_terms || [],
          is_safe: result.is_safe || false
        },
        comments: certComments
      };

      console.log('Sending CERT report:', reportData);

      const response = await fetch('http://localhost:8000/api/cert/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(reportData)
      });

      console.log('CERT report response status:', response.status);
      
      if (response.ok) {
        const responseData = await response.json();
        console.log('CERT report success:', responseData);
        setCertReportSuccess(true);
        setTimeout(() => {
          setShowCERTModal(false);
          setCertComments('');
          setCertReportSuccess(false);
          setShowEmailPreview(false);
        }, 3000);
      } else {
        const errorData = await response.json();
        console.error('CERT report error response:', errorData);
        
        // Handle different error formats
        let errorMessage = 'Failed to submit report';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
          } else {
            errorMessage = errorData.detail;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
        
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('CERT report error:', error);
      
      // Better error message handling
      let displayMessage = 'Failed to submit CERT report. Please try again.';
      if (error.message && error.message !== 'Failed to submit report') {
        displayMessage = `Failed to submit CERT report: ${error.message}`;
      }
      
      alert(displayMessage);
    } finally {
      setCertReporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">Phishing Detection</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Advanced multilingual phishing detection system. Protect yourself from scams in English, Sinhala, and Tamil.
          </p>
        </div>



        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
          {/* Input Section */}
          <div className="p-8">
            <div className="mb-6">
              <label className="block text-lg font-semibold text-gray-700 mb-3">
                Enter message to analyze
              </label>
              <div className="relative">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Paste your email, SMS, or any suspicious message here..."
                  className="w-full h-32 p-4 border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:outline-none resize-none text-base transition-colors"
                  maxLength={5000}
                />
                <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                  {message.length}/5000
                </div>
              </div>
            </div>

            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            )}

            <button
              onClick={analyzeMessage}
              disabled={loading || !message.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center text-lg"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  Analyze Message
                </>
              )}
            </button>
          </div>

          {/* Results Section */}
          {result && (
            <div className="border-t border-gray-200 bg-gray-50">
              <div className="p-8">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <AlertTriangle className="w-6 h-6 mr-2" />
                  Analysis Results
                </h2>

                {/* Main Result Card */}
                <div className={`rounded-xl border-2 p-6 mb-6 ${getRiskBgColor(result.risk_score)}`}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      {result.is_safe ? (
                        <ShieldCheck className="w-8 h-8 text-green-600 mr-3" />
                      ) : (
                        <AlertCircle className="w-8 h-8 text-red-600 mr-3" />
                      )}
                      <div>
                        <h3 className="text-xl font-bold">
                          {result.is_safe ? 'LEGITIMATE MESSAGE' : 'POTENTIAL SCAM'}
                        </h3>
                        <p className="text-sm opacity-75">
                          Classification: {result.classification.toUpperCase()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-3xl font-bold ${getRiskColor(result.risk_score)}`}>
                        {Math.round(result.risk_score)}%
                      </div>
                      <div className="text-sm text-gray-600">Risk Score</div>
                    </div>
                  </div>

                  <div className="bg-white bg-opacity-70 rounded-lg p-4">
                    <p className="text-base leading-relaxed">{result.explanation}</p>
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Language Detection */}
                  <div className="bg-white rounded-xl p-6 border border-gray-200">
                    <h4 className="font-semibold text-gray-700 mb-3 flex items-center">
                      <span className="text-2xl mr-2">{getLanguageFlag(result.language)}</span>
                      Detected Language
                    </h4>
                    <p className="text-lg capitalize font-medium text-blue-600">
                      {result.language}
                    </p>
                  </div>

                  {/* Suspicious Terms */}
                  <div className="bg-white rounded-xl p-6 border border-gray-200">
                    <h4 className="font-semibold text-gray-700 mb-3">
                      Suspicious Elements
                    </h4>
                    {result.suspicious_terms.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {result.suspicious_terms.map((term, index) => (
                          <span
                            key={index}
                            className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium"
                          >
                            {term}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 italic">No suspicious elements detected</p>
                    )}
                  </div>
                </div>

                {/* Risk Meter */}
                <div className="mt-6 bg-white rounded-xl p-6 border border-gray-200">
                  <h4 className="font-semibold text-gray-700 mb-4">Risk Assessment</h4>
                  <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                    <div 
                      className={`h-4 rounded-full transition-all duration-1000 ${
                        result.risk_score < 30 ? 'bg-green-500' :
                        result.risk_score < 70 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.round(result.risk_score)}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Safe (0%)</span>
                    <span>Moderate (50%)</span>
                    <span>Dangerous (100%)</span>
                  </div>
                </div>

                {/* Safety Tips */}
                {!result.is_safe && (
                  <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-6">
                    <h4 className="font-semibold text-red-800 mb-3 flex items-center">
                      <AlertCircle className="w-5 h-5 mr-2" />
                      Safety Recommendations
                    </h4>
                    <ul className="list-disc list-inside text-red-700 space-y-1">
                      <li>Do not click any links in this message</li>
                      <li>Do not provide personal or financial information</li>
                      <li>Verify the sender through official channels</li>
                      <li>Report this message to relevant authorities</li>
                    </ul>
                  </div>
                )}

                {/* CERT Report Button - Only show for medium-risk threats and above (50+) and authenticated users */}
                {isHighRisk() && isAuthenticated && (
                  <div className="mt-6 text-center">
                    <button
                      onClick={() => setShowCERTModal(true)}
                      className="flex items-center justify-center px-8 py-4 bg-white text-red-500 rounded-lg hover:bg-red-50 transition-colors font-medium text-lg shadow-lg border-2 border-red-600"
                    >
                      <AlertTriangle className="h-6 w-6 mr-3" />
                      Report to Sri Lanka CERT
                    </button>
                    <p className="text-sm text-gray-600 mt-2">
                      Help protect other Sri Lankan citizens by reporting this medium-risk or high-risk threat
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Scan History Toggle */}
        {isAuthenticated && user && (
          <div className="mt-8 mb-6 text-center">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105 font-medium"
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              {showHistory ? 'Hide' : 'Show'} Previous Scans ({scanHistory.length})
            </button>
          </div>
        )}

        {/* Scan History Section */}
        {isAuthenticated && user && showHistory && (
          <div className="mb-8 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
            <div className="p-6">
              <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Previous Scan History
              </h2>

              {historyLoading && (
                <div className="flex items-center justify-center py-8">
                  <Loader className="w-6 h-6 animate-spin text-blue-600 mr-2" />
                  <span className="text-gray-600">Loading scan history...</span>
                </div>
              )}

              {historyError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                  <p className="text-red-600">{historyError}</p>
                </div>
              )}

              {!historyLoading && !historyError && scanHistory.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No previous scans found. Analyze your first message above!</p>
                </div>
              )}

              {!historyLoading && !historyError && scanHistory.length > 0 && (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {scanHistory.map((scan, index) => (
                    <div
                      key={scan.id || index}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => handleHistoryClick(scan)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center mb-2">
                            {scan.is_safe || scan.classification === 'safe' ? (
                              <ShieldCheck className="w-4 h-4 text-green-600 mr-2 flex-shrink-0" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-red-600 mr-2 flex-shrink-0" />
                            )}
                            <span className={`text-sm font-medium ${
                              scan.is_safe || scan.classification === 'safe' 
                                ? 'text-green-700' 
                                : 'text-red-700'
                            }`}>
                              {scan.is_safe || scan.classification === 'safe' ? 'SAFE' : 'SUSPICIOUS'}
                            </span>
                            <span className="text-xs text-gray-500 ml-2">
                              {scan.created_at ? new Date(scan.created_at).toLocaleDateString() : 'Recent'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 truncate mb-1">
                            {scan.content || scan.message || 'Scan content'}
                          </p>
                          <div className="text-xs text-gray-500">
                            Risk Score: {Math.round(scan.risk_score || 0)}%
                          </div>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <div className={`text-lg font-bold ${
                            scan.risk_score < 30 ? 'text-green-600' :
                            scan.risk_score < 70 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {Math.round(scan.risk_score || 0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* CERT Reporting Modal */}
        {showCERTModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-red-600 flex items-center">
                    <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
                    Report to Sri Lanka CERT
                  </h2>
                  <button
                    onClick={() => setShowCERTModal(false)}
                    className="text-black hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>

                {certReportSuccess ? (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                      </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-green-800 mb-2">Report Submitted Successfully!</h3>
                    <p className="text-green-600">
                      Your report has been sent to Sri Lanka CERT. They will investigate this threat and take appropriate action.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                      <h3 className="font-semibold text-gray-800 mb-3">Threat Details</h3>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div><strong>Risk Score:</strong> {result?.risk_score || 0}%</div>
                        <div><strong>Classification:</strong> {result?.classification || 'Unknown'}</div>
                        <div><strong>Language:</strong> {result?.language || 'Unknown'}</div>
                        <div><strong>Message Length:</strong> {message.length} characters</div>
                      </div>
                    </div>

                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Additional Comments (Optional)
                      </label>
                      <textarea
                        value={certComments}
                        onChange={(e) => setCertComments(e.target.value)}
                        placeholder="Describe how you received this message, any additional context..."
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                        rows="4"
                      />
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <div className="flex">
                        <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                        <div className="text-sm text-blue-800">
                          <p className="font-medium mb-1">What happens next?</p>
                          <ul className="list-disc list-inside space-y-1">
                            <li>CERT will receive a detailed automated report</li>
                            <li>They will investigate and take appropriate action</li>
                            <li>Similar messages may be blocked nationally</li>
                            <li>Your report helps protect other Sri Lankan citizens</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* Email Preview Section */}
                    <div className="mb-6">
                      <button
                        onClick={() => setShowEmailPreview(!showEmailPreview)}
                        className="flex items-center px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors mb-3"
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        {showEmailPreview ? 'Hide' : 'Preview'} Email Report
                      </button>
                      
                      {showEmailPreview && (
                        <div className="border border-gray-200 rounded-lg overflow-hidden">
                          <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                            <p className="text-sm font-medium text-gray-700">Email Preview (HTML)</p>
                            <p className="text-xs text-gray-500">This is what Sri Lanka CERT will receive</p>
                          </div>
                          <div 
                            className="max-h-96 overflow-y-auto p-4 bg-white"
                            dangerouslySetInnerHTML={{ __html: generateEmailPreview() }}
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={() => setShowCERTModal(false)}
                        className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                        disabled={certReporting}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleCERTReport}
                        disabled={certReporting}
                        className="px-6 py-2 bg-white text-red-600 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center border-2 border-red-600"
                      >
                        {certReporting ? (
                          <>
                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                            Sending Report...
                          </>
                        ) : (
                          <>
                            <AlertTriangle className="h-4 w-4 mr-2" />
                            Submit Report to CERT
                          </>
                        )}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-8 text-gray-500 text-sm">
          <p>Powered by advanced machine learning • Supports English, Sinhala & Tamil</p>
        </div>
      </div>
    </div>
  );
};

export default PhishingDetector;