import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Camera, Upload, AlertTriangle, CheckCircle, XCircle, Eye, EyeOff, 
  ChevronRight, Shield, Clock, TrendingUp, Zap, RefreshCw, Download,
  ExternalLink, Info, Users, BarChart3, ScanLine, FileImage,
  CameraOff, Smartphone, Flag, Send
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const ModernQRScanner = () => {
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
  
  // CERT reporting state
  const [showCertForm, setShowCertForm] = useState(false);
  const [certLoading, setCertLoading] = useState(false);
  const [certComments, setCertComments] = useState('');
  
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
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'URL analysis failed');
      }
      
      const result = await response.json();
      setScanResult(result);
      
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
    setShowCertForm(false);
    setCertComments('');
    if (cameraStarted) {
      startContinuousScanning();
    }
  };

  // CERT Reporting Function
  const submitCertReport = async () => {
    if (!isAuthenticated) {
      setError('Please sign in to report threats to CERT');
      return;
    }

    if (!scanResult?.qr_detection?.decoded_url) {
      setError('No URL found to report');
      return;
    }

    try {
      setCertLoading(true);
      setError('');

      // Prepare CERT report data
      const certData = {
        url: scanResult.qr_detection.decoded_url,
        qr_url: scanResult.qr_detection.decoded_url,
        content: `QR Code detected containing: ${scanResult.qr_detection.decoded_url}`,
        risk_score: scanResult.combined_assessment?.final_risk_score || 50,
        risk_level: scanResult.combined_assessment?.final_risk_level || 'medium',
        classification: scanResult.security_analysis?.classification || 'Unknown',
        confidence: scanResult.combined_assessment?.confidence || 0.5,
        reasoning: scanResult.combined_assessment?.recommendation || 'QR code analysis results',
        security_analysis: scanResult.security_analysis || {},
        comments: certComments,
        user_comments: certComments,
        scan_id: scanResult.scan_id
      };

      const token = localStorage.getItem('token');
      const response = await fetch('/api/qr/report/cert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(certData)
      });

      const result = await response.json();

      if (response.ok && result.success) {
        alert(`✅ Threat report successfully submitted to Sri Lanka CERT!\n\nReport ID: ${result.report_id}\n\nYou will receive a confirmation email shortly.`);
        setShowCertForm(false);
        setCertComments('');
      } else {
        throw new Error(result.detail || result.message || 'Failed to submit CERT report');
      }

    } catch (err) {
      console.error('CERT report error:', err);
      setError(`Failed to submit CERT report: ${err.message}`);
    } finally {
      setCertLoading(false);
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
        <div className="mb-6">
          <div className={`max-w-4xl mx-auto p-4 rounded-xl border ${
            isAuthenticated 
              ? 'bg-green-50 border-green-200' 
              : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="font-medium text-green-800">Authenticated Mode</p>
                    <p className="text-sm text-green-700">
                      Welcome {user?.email}! Your scans are saved to history and you can report suspicious QR codes to CERT.
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <Info className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="font-medium text-blue-800">Anonymous Scanning Mode</p>
                    <p className="text-sm text-blue-700">
                      You can scan QR codes without signing in. <Link to="/auth" className="underline font-medium">Sign in</Link> to save scan history and report threats to CERT.
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Scanner Mode Selection */}
        <div className="mb-8">
          <div className="flex justify-center">
            <div className="bg-black rounded-xl p-2 shadow-lg">
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setScanMode('camera');
                    setScanResult(null);
                    setError('');
                  }}
                  className={`flex items-center px-6 py-3 rounded-lg transition-all ${
                    scanMode === 'camera'
                      ? 'bg-gray-700 text-black shadow-md'
                      : 'bg-gray-100 text-gray-700 border-2 border-gray-300 hover:border-gray-400 hover:bg-gray-200'
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
                      ? 'bg-gray-700 text-white shadow-md'
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
                          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
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
                    <button className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
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
                  <div className="flex justify-center space-x-4 flex-wrap">
                    <button
                      onClick={resetScanner}
                      className="flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      <RefreshCw className="h-5 w-5 mr-2" />
                      Scan Another
                    </button>
                    
                    {/* CERT Reporting Button - Only show for authenticated users and suspicious QR codes */}
                    {isAuthenticated && scanResult?.qr_detection?.decoded_url && (
                      <button
                        onClick={() => setShowCertForm(!showCertForm)}
                        className="flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                      >
                        <Flag className="h-5 w-5 mr-2" />
                        Report to CERT
                      </button>
                    )}
                    
                    <Link
                      to="/dashboard"
                      className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      <BarChart3 className="h-5 w-5 mr-2" />
                      View History
                    </Link>
                  </div>

                  {/* CERT Reporting Form */}
                  {showCertForm && isAuthenticated && (
                    <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
                      <h4 className="text-lg font-semibold text-red-900 mb-4 flex items-center">
                        <Flag className="h-5 w-5 mr-2" />
                        Report Threat to Sri Lanka CERT
                      </h4>
                      
                      <div className="space-y-4">
                        <div>
                          <p className="text-sm text-red-700 mb-2">URL to Report:</p>
                          <p className="font-mono text-sm bg-red-100 p-2 rounded border break-all">
                            {scanResult.qr_detection.decoded_url}
                          </p>
                        </div>
                        
                        <div>
                          <label htmlFor="cert-comments" className="block text-sm font-medium text-red-700 mb-2">
                            Additional Comments (Optional)
                          </label>
                          <textarea
                            id="cert-comments"
                            value={certComments}
                            onChange={(e) => setCertComments(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-red-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                            placeholder="Describe where you found this QR code or any suspicious behavior..."
                          />
                        </div>
                        
                        <div className="flex space-x-3">
                          <button
                            onClick={submitCertReport}
                            disabled={certLoading}
                            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {certLoading ? (
                              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <Send className="h-4 w-4 mr-2" />
                            )}
                            {certLoading ? 'Submitting...' : 'Submit Report'}
                          </button>
                          
                          <button
                            onClick={() => setShowCertForm(false)}
                            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                        
                        <p className="text-xs text-red-600">
                          <strong>Privacy:</strong> Your identity will be protected when reporting to CERT. Only the threat information will be shared.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

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

export default ModernQRScanner;