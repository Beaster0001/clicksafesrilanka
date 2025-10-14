import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Camera, Upload, AlertTriangle, CheckCircle, XCircle, Eye, EyeOff, 
  ChevronRight, Shield, Clock, TrendingUp, Zap, RefreshCw, Download,
  ExternalLink, Info, Users, BarChart3, ScanLine, FileImage,
  CameraOff, Smartphone
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { scansAPI, qrAPI } from '../services/api';

const QRScanner = () => {
  const { user, isAuthenticated } = useAuth();
  
  // Scanner state
  const [scanMode, setScanMode] = useState('camera');
  const [cameraStarted, setCameraStarted] = useState(false);
  const [facingMode, setFacingMode] = useState('environment');
  const [isScanning, setIsScanning] = useState(false);
  
  // Results and UI state
  const [scanResult, setScanResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showDetails, setShowDetails] = useState(false);
  
  // CERT Reporting state
  const [showCERTModal, setShowCERTModal] = useState(false);
  const [certReporting, setCertReporting] = useState(false);
  const [certComments, setCertComments] = useState('');
  const [certReportSuccess, setCertReportSuccess] = useState(false);
  const [showEmailPreview, setShowEmailPreview] = useState(false);
  
  // Scan history state
  const [scanHistory, setScanHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  
  // Refs
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const scanIntervalRef = useRef(null);

  useEffect(() => {
    return () => {
      stopCamera();
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
      }
    };
  }, []);

  // Fetch scan history when component mounts or authentication changes
  useEffect(() => {
    if (isAuthenticated && user) {
      fetchScanHistory();
    } else {
      setScanHistory([]);
    }
  }, [isAuthenticated, user]);

  // Fetch QR scan history
  const fetchScanHistory = async () => {
    if (!isAuthenticated || !user) {
      return;
    }

    setHistoryLoading(true);
    setHistoryError('');

    try {
      console.log('Fetching QR scan history...');
      const historyData = await qrAPI.getScanHistory(1, 10);
      
      console.log('QR scan history received:', historyData);
      setScanHistory(historyData.scans || []);
    } catch (err) {
      console.error('Error fetching QR scan history:', err);
      setHistoryError('Failed to load scan history');
    } finally {
      setHistoryLoading(false);
    }
  };

  // Handle clicking on a historical scan
  const handleHistoryClick = (scan) => {
    // Set the URL from the historical scan
    const url = scan.content || '';
    
    // Create a result object from the historical scan
    const historicalResult = {
      success: true,
      decoded_url: url,
      safety_analysis: {
        risk_level: scan.classification || 'unknown',
        risk_score: scan.risk_score || 0,
        risk_percentage: Math.round(scan.risk_score || 0), // Risk score is already a percentage
        recommendations: scan.explanation ? [scan.explanation] : []
      },
      combined_assessment: {
        final_risk_score: scan.risk_score || 0,
        final_risk_level: scan.classification || 'unknown',
        recommendation: scan.explanation || 'Historical scan result'
      }
    };
    
    setScanResult(historicalResult);
    setError('');
    
    // Scroll to the top to show the populated result
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Camera management
  const startCamera = async () => {
    try {
      setError('');
      setLoading(true);
      stopCamera();
      
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera not supported by this browser');
      }
      
      const constraints = {
        video: { 
          facingMode: facingMode,
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setCameraStarted(true);
      
      // Wait for video element to be rendered
      await new Promise(resolve => setTimeout(resolve, 100));
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setLoading(false);
        startContinuousScanning();
      }
    } catch (err) {
      console.error('Camera error:', err);
      setError(err.message || 'Failed to start camera');
      setLoading(false);
      setCameraStarted(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraStarted(false);
    setIsScanning(false);
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
    }
  };

  const switchCamera = () => {
    const newFacingMode = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(newFacingMode);
    if (cameraStarted) {
      startCamera();
    }
  };

  // QR Scanning logic
  const startContinuousScanning = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
    }
    
    scanIntervalRef.current = setInterval(() => {
      if (!isScanning && videoRef.current && canvasRef.current) {
        captureAndAnalyze();
      }
    }, 1000); // Scan every second
  };

  const captureAndAnalyze = async () => {
    if (!videoRef.current || !canvasRef.current || isScanning) return;
    
    try {
      setIsScanning(true);
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);
      
      // Convert canvas to blob
      const blob = await new Promise(resolve => {
        canvas.toBlob(resolve, 'image/png');
      });
      
      await analyzeQRCode(blob);
    } catch (err) {
      console.error('Capture error:', err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB');
      return;
    }
    
    await analyzeQRCode(file);
  };

  const analyzeQRCode = async (imageData) => {
    try {
      setLoading(true);
      setError('');
      
      const formData = new FormData();
      formData.append('file', imageData, 'qr-scan.png');
      formData.append('save_to_history', 'true');
      
      const token = localStorage.getItem('access_token');
      
      // Prepare headers - include auth token if available (for history saving)
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('http://localhost:8000/api/qr/scan/image', {
        method: 'POST',
        headers: headers,
        body: formData
      });
      
      if (response.status === 401) {
        setError('Session expired. Please log in again.');
        // Clear invalid token
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        return;
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }
      
      const result = await response.json();
      
      // Only set scan result and stop camera if QR code was actually detected
      if (result.success && result.qr_detection && result.qr_detection.success) {
        setScanResult(result);
        if (scanIntervalRef.current) {
          clearInterval(scanIntervalRef.current);
        }
        // Stop the camera automatically when QR code is detected
        console.log('QR code detected successfully - stopping camera automatically');
        stopCamera();
        
        // Refresh scan history after successful scan (only if authenticated)
        if (isAuthenticated && user) {
          fetchScanHistory();
        }
      } else {
        // No QR code detected, continue scanning silently
        console.log('No QR code detected in frame, continuing to scan...');
      }
      
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze QR code');
    } finally {
      setLoading(false);
    }
  };

  const analyzeURL = async (url) => {
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('access_token');
      
      // Prepare headers - include auth token if available (for history saving)
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('http://localhost:8000/api/qr/scan/url', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          url: url,
          save_to_history: !!token  // Only save to history if authenticated
        })
      });
      
      if (response.status === 401) {
        setError('Session expired. Please log in again.');
        // Clear invalid token
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        return;
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'URL analysis failed');
      }
      
      const result = await response.json();
      setScanResult(result);
      
      // Refresh scan history after successful URL analysis (only if authenticated)
      if (isAuthenticated && user) {
        fetchScanHistory();
      }
      
    } catch (err) {
      console.error('URL analysis error:', err);
      setError(err.message || 'Failed to analyze URL');
    } finally {
      setLoading(false);
    }
  };

  const resetScanner = () => {
    setScanResult(null);
    setError('');
    setShowDetails(false);
    setShowCERTModal(false);
    setCertComments('');
    setCertReportSuccess(false);
    setShowEmailPreview(false);
    if (cameraStarted) {
      startContinuousScanning();
    }
  };

  // CERT Reporting Functions
  const isHighRisk = () => {
    const riskLevel = scanResult?.combined_assessment?.final_risk_level || '';
    // For QR Scanner: Show CERT reporting for medium, high, and critical risk threats from Security Analysis
    return riskLevel === 'medium' || riskLevel === 'high' || riskLevel === 'critical';
  };

  const generateEmailPreview = () => {
    if (!scanResult || !isAuthenticated) return '';

    const reportId = `CS-${new Date().toISOString().slice(0,10).replace(/-/g,'')}-${Date.now().toString().slice(-4)}`;
    const threatUrl = scanResult.qr_detection?.decoded_url || 
                     scanResult.qr_detection?.url || 
                     scanResult.url_analysis?.url || 
                     'Unknown URL';
    const riskScore = scanResult.combined_assessment?.final_risk_score || 0;
    const riskLevel = scanResult.combined_assessment?.final_risk_level || 'unknown';
    const confidence = Math.round((scanResult.combined_assessment?.confidence || 0) * 100);
    const reasoning = scanResult.combined_assessment?.reasoning || 'No detailed analysis available';
    
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
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 ClickSafe Phishing Threat Report</h1>
        <p>Report ID: ${reportId}</p>
    </div>
    
    <div class="content">
        <p><strong>Dear Sri Lanka CERT Team,</strong></p>
        
        <p>ClickSafe has detected a suspicious QR code threat that requires attention. This automated report contains detailed analysis and evidence.</p>
        
        <div class="threat-box">
            <h3>⚠️ Threat Summary</h3>
            <p><strong>Malicious URL:</strong> <code>${threatUrl}</code></p>
            <p><strong>Risk Score:</strong> <span class="${riskScore >= 85 ? 'risk-critical' : 'risk-high'}">${riskScore}/100 (${riskLevel.replace('_', ' ').toUpperCase()})</span></p>
            <p><strong>Detection Confidence:</strong> ${confidence}%</p>
        </div>
        
        <h3>📊 Detailed Analysis</h3>
        <table class="details-table">
            <tr><th>Detection Time</th><td>${new Date().toLocaleString('en-US', {timeZone: 'Asia/Colombo'})}</td></tr>
            <tr><th>Reporter Location</th><td>Sri Lanka</td></tr>
            <tr><th>Detection Method</th><td>QR Code Scanner + ML Analysis</td></tr>
            <tr><th>Threat Category</th><td>Phishing/Social Engineering</td></tr>
            <tr><th>Recommendation</th><td>Block and investigate immediately</td></tr>
        </table>
        
        <h3>🔍 Technical Analysis</h3>
        <p><strong>Analysis Summary:</strong></p>
        <p>${reasoning}</p>
        
        ${certComments ? `
        <h3>👤 User Report</h3>
        <p><strong>Additional Context from User:</strong></p>
        <p style="background: #f9f9f9; padding: 10px; border-radius: 5px; font-style: italic;">"${certComments}"</p>
        ` : ''}
        
        <h3>⚡ Recommended Actions</h3>
        <ul>
            <li>Block the malicious URL at DNS/ISP level</li>
            <li>Issue public warning about this threat</li>
            <li>Investigate hosting infrastructure</li>
            <li>Coordinate with international CERT teams if needed</li>
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
    if (!scanResult || !isAuthenticated) return;

    try {
      setCertReporting(true);
      setError('');

      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Authentication token not found. Please log in again.');
        return;
      }

      // Use QR-specific CERT endpoint with correct data structure
      const qrUrl = scanResult.qr_detection?.decoded_url || 
                   scanResult.qr_detection?.url || 
                   scanResult.url_analysis?.url || 
                   'Unknown URL';
      
      // Debug logging to see what data we have
      console.log('QR CERT Report - scanResult:', scanResult);
      console.log('QR URL being sent:', qrUrl);
      
      const reportData = {
        qr_url: qrUrl,
        risk_score: scanResult.combined_assessment?.final_risk_score || 0,
        risk_level: scanResult.combined_assessment?.final_risk_level || 'unknown',
        scan_id: scanResult.scan_id || 'unknown',
        user_comments: certComments
      };

      const response = await fetch('http://localhost:8000/api/qr/report/cert', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reportData)
      });

      if (response.status === 401) {
        setError('Session expired. Please log in again.');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to submit CERT report');
      }

      const result = await response.json();
      setCertReportSuccess(true);
      
      // Close modal after 3 seconds
      setTimeout(() => {
        setShowCERTModal(false);
        setCertReportSuccess(false);
      }, 3000);

    } catch (err) {
      console.error('CERT report error:', err);
      setError(err.message || 'Failed to submit CERT report');
    } finally {
      setCertReporting(false);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'very_low':
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRiskIcon = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'very_low':
      case 'low': return CheckCircle;
      case 'medium': return Info;
      case 'high':
      case 'critical': return AlertTriangle;
      default: return Shield;
    }
  };

  // Authentication is now optional - anonymous users can scan QR codes
  // but certain features like history and CERT reporting require authentication

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            QR Security Scanner
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Advanced QR code analysis with ML-powered threat detection and VirusTotal integration
          </p>
        </div>

        {/* Authentication Status Banner */}
        {!isAuthenticated ? (
          <div className="mb-6 mx-auto max-w-4xl">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <p className="text-blue-800 font-medium">Anonymous Scanning Mode</p>
                  <p className="text-blue-600 text-sm mt-1">
                    You can scan QR codes freely without signing in. To access scan history and report threats to CERT, 
                    <Link to="/login" className="underline hover:text-blue-800 ml-1">please log in</Link>.
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="mb-6 mx-auto max-w-4xl">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
                  <div>
                    <p className="text-green-800 font-medium">Authenticated Mode</p>
                    <p className="text-green-600 text-sm mt-1">
                      Your scans are saved to history and you can report medium and high-risk threats to Sri Lanka CERT.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="flex items-center px-4 py-2 bg-green-600 text-gray-800 rounded-lg hover:bg-green-700 transition-colors text-sm"
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  {showHistory ? 'Hide' : 'View'} History ({scanHistory.length})
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Scanner Mode Selection */}
        <div className="mb-8">
          <div className="flex justify-center">
            <div className="bg-white rounded-xl p-2 shadow-lg">
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setScanMode('camera');
                    setScanResult(null);
                    setError('');
                  }}
                  className={`flex items-center px-6 py-3 rounded-lg transition-all ${
                    scanMode === 'camera'
                      ? 'bg-gray-800 text-blue-700 shadow-md'
                      : 'bg-gray-700 text-gray-700 border-2 border-black-300 hover:border-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Camera className="h-5 w-5 mr-2" />
                  Camera Scan
                </button>
                <button
                  onClick={() => {
                    setScanMode('upload');
                    stopCamera();
                    setScanResult(null);
                    setError('');
                  }}
                  className={`flex items-center px-6 py-3 rounded-lg transition-all ${
                    scanMode === 'upload'
                      ? 'bg-gray-700 text-blue-700 shadow-md'
                      : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-200'
                  }`}
                >
                  <Upload className="h-5 w-5 mr-2" />
                  Upload Image
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Scanner Interface */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            
            {/* Scanner Area */}
            <div className="p-6 border-b">
              {scanMode === 'camera' ? (
                <div className="space-y-4">
                  {/* Camera Controls */}
                  <div className="flex justify-center space-x-4">
                    {!cameraStarted ? (
                      <button
                        onClick={startCamera}
                        disabled={loading}
                        className="flex items-center px-6 py-3 bg-indigo-600 text-black rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                      >
                        {loading ? (
                          <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                        ) : (
                          <Camera className="h-5 w-5 mr-2" />
                        )}
                        {loading ? 'Starting Camera...' : 'Start Camera'}
                      </button>
                    ) : (
                      <div className="flex space-x-2">
                        <button
                          onClick={stopCamera}
                          className="flex items-center px-4 py-2 bg-gray-600 text-black rounded-lg hover:bg-gray-700 transition-colors"
                        >
                          <CameraOff className="h-4 w-4 mr-2" />
                          Stop
                        </button>
                        <button
                          onClick={switchCamera}
                          className="flex items-center px-4 py-2 bg-indigo-600 text-black rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                          <Smartphone className="h-4 w-4 mr-2" />
                          Switch Camera
                        </button>
                      </div>
                    )}
                    
                  </div>

                  {/* Camera View */}
                  {cameraStarted && (
                    <div className="relative bg-black rounded-xl overflow-hidden">
                      <video
                        ref={videoRef}
                        className="w-full h-64 md:h-96 object-cover"
                        playsInline
                        muted
                      />
                      
                      {/* Scanning Overlay */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="relative">
                          <div className="w-48 h-48 border-2 border-white rounded-lg">
                            <div className="absolute top-0 left-0 w-6 h-6 border-t-4 border-l-4 border-indigo-400 rounded-tl-lg"></div>
                            <div className="absolute top-0 right-0 w-6 h-6 border-t-4 border-r-4 border-indigo-400 rounded-tr-lg"></div>
                            <div className="absolute bottom-0 left-0 w-6 h-6 border-b-4 border-l-4 border-indigo-400 rounded-bl-lg"></div>
                            <div className="absolute bottom-0 right-0 w-6 h-6 border-b-4 border-r-4 border-indigo-400 rounded-br-lg"></div>
                          </div>
                          {isScanning && (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <ScanLine className="h-8 w-8 text-indigo-400 animate-pulse" />
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Status Indicator */}
                      <div className="absolute top-4 left-4">
                        <div className="flex items-center space-x-2 bg-black bg-opacity-50 rounded-lg px-3 py-2">
                          <div className={`w-2 h-2 rounded-full ${isScanning ? 'bg-red-400 animate-pulse' : 'bg-green-400'}`}></div>
                          <span className="text-white text-sm">
                            {isScanning ? 'Scanning...' : 'Ready'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <canvas ref={canvasRef} className="hidden" />
                </div>
              ) : (
                /* File Upload */
                <div className="text-center">
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-gray-300 rounded-xl p-12 hover:border-indigo-400 transition-colors cursor-pointer"
                  >
                    <FileImage className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Upload QR Code Image
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Select an image file containing a QR code
                    </p>
                    <button className="inline-flex items-center px-6 py-3 bg-indigo-600 text-black rounded-lg hover:bg-indigo-700 transition-colors">
                      <Upload className="h-5 w-5 mr-2" />
                      Choose File
                    </button>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
              )}
            </div>

            {/* Loading State */}
            {loading && (
              <div className="p-6 text-center">
                <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Analyzing QR code...</p>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="p-6 bg-red-50 border-l-4 border-red-400">
                <div className="flex items-center">
                  <XCircle className="h-5 w-5 text-red-400 mr-3" />
                  <p className="text-red-800">{error}</p>
                </div>
              </div>
            )}

            {/* Results Display */}
            {scanResult && (
              <div className="p-6 bg-gray-50">
                <div className="space-y-6">
                  {/* QR Detection Result */}
                  {scanResult.qr_detection && (
                    <div className="bg-white rounded-xl p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <ScanLine className="h-5 w-5 mr-2 text-indigo-600" />
                        QR Code Detection
                      </h3>
                      
                      {scanResult.qr_detection.success ? (
                        <div className="space-y-3">
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <span className="text-green-800 font-medium">QR Code Detected</span>
                          </div>
                          
                          <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-sm text-gray-600 mb-2">Content Type:</p>
                            <p className="font-medium capitalize">
                              {scanResult.qr_detection.qr_type || 'Unknown'}
                            </p>
                          </div>
                          
                          {scanResult.qr_detection.decoded_url && (
                            <div className="bg-gray-50 rounded-lg p-4">
                              <p className="text-sm text-gray-600 mb-2">Decoded URL:</p>
                              <div className="flex items-center space-x-2">
                                <p className="font-mono text-sm break-all flex-1">
                                  {scanResult.qr_detection.decoded_url}
                                </p>
                                <button
                                  onClick={() => window.open(scanResult.qr_detection.decoded_url, '_blank')}
                                  className="p-2 text-indigo-600 hover:bg-indigo-50 rounded"
                                >
                                  <ExternalLink className="h-4 w-4" />
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <XCircle className="h-5 w-5 text-red-600" />
                          <span className="text-red-800">No QR Code Found</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Security Analysis */}
                  {scanResult.combined_assessment && (
                    <div className="bg-white rounded-xl p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Shield className="h-5 w-5 mr-2 text-indigo-600" />
                        Security Analysis
                      </h3>
                      
                      <div className="space-y-4">
                        {/* Risk Score */}
                        <div className={`rounded-lg border-2 p-4 ${getRiskColor(scanResult.combined_assessment.final_risk_level)}`}>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              {(() => {
                                const Icon = getRiskIcon(scanResult.combined_assessment.final_risk_level);
                                return <Icon className="h-6 w-6" />;
                              })()}
                              <div>
                                <p className="font-semibold capitalize">
                                  {scanResult.combined_assessment.final_risk_level?.replace('_', ' ') || 'Unknown'} Risk
                                </p>
                                <p className="text-sm opacity-75">
                                  Confidence: {Math.round((scanResult.combined_assessment.confidence || 0) * 100)}%
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold">
                                {scanResult.combined_assessment.final_risk_score || 0}
                              </p>
                              <p className="text-sm opacity-75">Risk Score</p>
                            </div>
                          </div>
                        </div>

                        {/* Recommendation */}
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-sm text-gray-600 mb-2">Recommendation:</p>
                          <p className="font-medium capitalize">
                            {scanResult.combined_assessment.recommendation || 'Unknown'}
                          </p>
                        </div>

                        {/* Analysis Details Toggle */}
                        <button
                          onClick={() => setShowDetails(!showDetails)}
                          className="flex items-center space-x-2 text-indigo-600 hover:text-indigo-700"
                        >
                          {showDetails ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          <span>{showDetails ? 'Hide' : 'Show'} Analysis Details</span>
                        </button>

                        {/* Detailed Analysis */}
                        {showDetails && (
                          <div className="space-y-4 border-t pt-4">
                            {/* ML Analysis */}
                            {scanResult.security_analysis && (
                              <div className="bg-blue-50 rounded-lg p-4">
                                <h4 className="font-medium text-blue-900 mb-2 flex items-center">
                                  <TrendingUp className="h-4 w-4 mr-2" />
                                  ML Analysis
                                </h4>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="text-blue-700">Classification:</span>
                                    <p className="font-medium capitalize">
                                      {scanResult.security_analysis.classification || 'Unknown'}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-blue-700">Risk Score:</span>
                                    <p className="font-medium">
                                      {scanResult.security_analysis.risk_score || 0}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* VirusTotal Analysis */}
                            {scanResult.virustotal_analysis?.success && (
                              <div className="bg-purple-50 rounded-lg p-4">
                                <h4 className="font-medium text-purple-900 mb-2 flex items-center">
                                  <Users className="h-4 w-4 mr-2" />
                                  VirusTotal Analysis
                                </h4>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="text-purple-700">Detections:</span>
                                    <p className="font-medium">
                                      {scanResult.virustotal_analysis.virustotal_data?.detection_ratio || '0/0'}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-purple-700">Reputation:</span>
                                    <p className="font-medium">
                                      {scanResult.virustotal_analysis.virustotal_data?.reputation || 0}%
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex justify-center space-x-4 flex-wrap gap-2">
                    {/* CERT Report Button - Only show for medium and high-risk threats and authenticated users */}
                    {isHighRisk() && isAuthenticated && (
                      <button
                        onClick={() => setShowCERTModal(true)}
                        className="flex items-center px-6 py-3 bg-red-600 text-red-600 rounded-lg hover:bg-red-700 transition-colors"
                      >
                        <AlertTriangle className="h-5 w-5 mr-2" />
                        Report to Sri Lanka CERT
                      </button>
                    )}
                    
                    <button
                      onClick={resetScanner}
                      className="flex items-center px-6 py-3 bg-indigo-600 text-black rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      <RefreshCw className="h-5 w-5 mr-2" />
                      Scan Another
                    </button>
                    
                    {isAuthenticated && user && (
                      <button
                        onClick={() => setShowHistory(!showHistory)}
                        className="flex items-center px-6 py-3 bg-gray-600 text-black rounded-lg hover:bg-gray-700 transition-colors"
                      >
                        <BarChart3 className="h-5 w-5 mr-2" />
                        {showHistory ? 'Hide' : 'View'} History ({scanHistory.length})
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Scan History Section */}
        {isAuthenticated && user && showHistory && (
          <div className="mb-8 bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
            <div className="p-6">
              <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center">
                <ScanLine className="w-5 h-5 mr-2" />
                QR Code Scan History
              </h2>

              {historyLoading && (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mr-2" />
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
                  <ScanLine className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No previous QR scans found. Scan your first QR code above!</p>
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
                            {scan.classification === 'safe' || scan.classification === 'low' ? (
                              <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0" />
                            ) : scan.classification === 'medium' ? (
                              <AlertTriangle className="w-4 h-4 text-yellow-600 mr-2 flex-shrink-0" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-600 mr-2 flex-shrink-0" />
                            )}
                            <span className={`text-sm font-medium ${
                              scan.classification === 'safe' || scan.classification === 'low'
                                ? 'text-green-700' 
                                : scan.classification === 'medium'
                                ? 'text-yellow-700'
                                : 'text-red-700'
                            }`}>
                              {scan.classification?.toUpperCase() || 'UNKNOWN'}
                            </span>
                            <span className="text-xs text-gray-500 ml-2">
                              {scan.created_at ? new Date(scan.created_at).toLocaleDateString() : 'Recent'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 truncate mb-1">
                            {scan.content || 'Unknown URL'}
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

              {!historyLoading && !historyError && scanHistory.length > 0 && (
                <div className="mt-4 text-center">
                  <p className="text-sm text-gray-500">
                    Click on any scan to view details. Showing last {scanHistory.length} scans.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* CERT Reporting Modal */}
        {showCERTModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-red-100 rounded-lg">
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-red-600">
                        Report to Sri Lanka CERT
                      </h3>
                      <p className="text-sm text-gray-600">
                        National Centre for Cyber Security
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowCERTModal(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <XCircle className="h-5 w-5 text-gray-400" />
                  </button>
                </div>

                {certReportSuccess ? (
                  <div className="text-center py-8">
                    <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
                    <h4 className="text-lg font-semibold text-gray-900 mb-2">
                      Report Submitted Successfully!
                    </h4>
                    <p className="text-gray-600">
                      Your phishing report has been sent to Sri Lanka CERT. They will investigate this threat.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                      <div className="flex">
                        <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
                        <div>
                          <h4 className="text-red-800 font-medium mb-1">Suspicious Threat Detected</h4>
                          <p className="text-red-700 text-sm">
                            This appears to be a potentially dangerous QR code. Reporting to CERT helps protect others.
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 mb-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Threat Details
                        </label>
                        <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                          <div><strong>URL:</strong> {scanResult?.qr_detection?.url || scanResult?.url_analysis?.url || 'Unknown'}</div>
                          <div><strong>Risk Score:</strong> {scanResult?.combined_assessment?.final_risk_score || 0}/100</div>
                          <div><strong>Classification:</strong> {scanResult?.security_analysis?.classification || 'Unknown'}</div>
                          <div><strong>Confidence:</strong> {Math.round((scanResult?.combined_assessment?.confidence || 0) * 100)}%</div>
                        </div>
                      </div>

                      <div>
                        <label htmlFor="certComments" className="block text-sm font-medium text-gray-700 mb-2">
                          Additional Comments (Optional)
                        </label>
                        <textarea
                          id="certComments"
                          value={certComments}
                          onChange={(e) => setCertComments(e.target.value)}
                          placeholder="Describe how you encountered this threat, any additional context..."
                          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                          rows="4"
                        />
                      </div>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <div className="flex">
                        <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                        <div className="text-sm text-blue-800">
                          <p className="font-medium mb-1">What happens next?</p>
                          <ul className="list-disc list-inside space-y-1">
                            <li>CERT will receive a detailed automated report</li>
                            <li>They will investigate and take appropriate action</li>
                            <li>The threat may be blocked nationally</li>
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
                        className="px-6 py-2 bg-red-600 text-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
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

        {/* Quick Stats */}
        <div className="mt-8 max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <Zap className="h-8 w-8 text-yellow-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">AI-Powered Analysis</h3>
              <p className="text-gray-600 text-sm">
                Advanced machine learning models detect sophisticated threats
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <Shield className="h-8 w-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Multi-Layer Security</h3>
              <p className="text-gray-600 text-sm">
                Combines ML analysis with VirusTotal threat intelligence
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <Clock className="h-8 w-8 text-blue-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Real-Time Results</h3>
              <p className="text-gray-600 text-sm">
                Get instant security analysis and threat assessments
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QRScanner;