import { useState, useEffect } from 'react';
import { 
  Shield, 
  Bell, 
  Settings, 
  Search, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingUp,
  Users,
  Eye,
  RefreshCw,
  MessageSquare,
  Link,
  QrCode
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { dashboardAPI, scansAPI } from '../services/api';

const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const [searchUrl, setSearchUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [urlScanResult, setUrlScanResult] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [recentScans, setRecentScans] = useState([]);
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingScans, setLoadingScans] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [scanFilter, setScanFilter] = useState('all'); // Filter for scan classifications

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData();
      
      // Set up auto-refresh every 15 seconds for real-time updates
      const interval = setInterval(() => {
        fetchDashboardData(false); // Don't show loading on refresh
      }, 15000);

      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const fetchDashboardData = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoadingStats(true);
        setLoadingScans(true);
      } else {
        setIsRefreshing(true);
      }
      
      // Fetch dashboard data
      const dashboardData = await dashboardAPI.getDashboardData();
      setDashboardData(dashboardData);
      
      // Recent scans are included in dashboard data
      setRecentScans(dashboardData.stats.recent_scans || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      if (showLoading) {
        setLoadingStats(false);
        setLoadingScans(false);
      } else {
        setIsRefreshing(false);
      }
    }
  };

  const handleManualRefresh = () => {
    fetchDashboardData(false);
  };

  const handleScan = async (e) => {
    e.preventDefault();
    if (!searchUrl.trim()) return;
    
    setIsScanning(true);
    setUrlScanResult(null); // Clear previous results
    
    try {
      // Create a scan record with the URL
      const scanResult = await scansAPI.createScan({
        content: searchUrl,
        scan_type: 'url'
      });
      
      // Store the result with proper formatting
      setUrlScanResult({
        url: searchUrl,
        classification: scanResult.classification,
        risk_score: scanResult.risk_score || 0, // Keep original 0-1 scale for display
        explanation: scanResult.explanation,
        suspicious_terms: scanResult.suspicious_terms || [],
        scanned_at: new Date(),
        is_safe: scanResult.classification === 'safe'
      });
      
      // Refresh dashboard data to show new scan
      await fetchDashboardData();
      
      // Clear the input
      setSearchUrl('');
      
    } catch (error) {
      console.error('Error scanning URL:', error);
      alert('❌ Error: Failed to scan URL. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  // Helper functions for URL scan result display
  const getRiskColor = (riskScore) => {
    if (riskScore < 0.3) return '#10b981'; // Green for low risk
    if (riskScore < 0.7) return '#f59e0b'; // Yellow/Orange for medium risk
    return '#ef4444'; // Red for high risk
  };

  const getRiskBgColor = (riskScore) => {
    if (riskScore < 0.3) return '#d1fae5'; // Light green
    if (riskScore < 0.7) return '#fef3c7'; // Light yellow
    return '#fee2e2'; // Light red
  };

  const getClassificationIcon = (riskScore) => {
    if (riskScore < 0.3) return '✅';
    if (riskScore < 0.7) return '⚠️';
    return '🚨';
  };

  // Dynamic stats based on real data
  const stats = [
    { 
      label: 'URLs Scanned', 
      value: dashboardData?.stats?.total_scans || '0', 
      icon: <Search className="w-6 h-6" />, 
      color: 'blue' 
    },
    { 
      label: 'Threats Blocked', 
      value: (dashboardData?.stats?.suspicious_scans || 0) + (dashboardData?.stats?.dangerous_scans || 0), 
      icon: <Shield className="w-6 h-6" />, 
      color: 'red' 
    },
    { 
      label: 'Safe Sites', 
      value: dashboardData?.stats?.safe_scans || '0', 
      icon: <CheckCircle className="w-6 h-6" />, 
      color: 'green' 
    },
    { 
      label: 'Recent Scans', 
      value: dashboardData?.stats?.recent_scans?.length || '0', 
      icon: <Clock className="w-6 h-6" />, 
      color: 'purple' 
    },
  ];

  // Filter recent scans based on selected filter
  const filteredScans = recentScans.filter(scan => {
    if (scanFilter === 'all') return true;
    
    const classification = scan.classification?.toLowerCase();
    
    if (scanFilter === 'safe') {
      return classification === 'safe' || classification === 'legitimate';
    } else if (scanFilter === 'suspicious') {
      return classification === 'suspicious';
    } else if (scanFilter === 'dangerous') {
      return classification === 'dangerous';
    }
    
    return true;
  });

  // Helper function to get scan type icon
  const getScanTypeIcon = (scanType) => {
    switch (scanType) {
      case 'qr_code':
        return <QrCode className="w-4 h-4 mr-1 text-slate-500" />;
      case 'url':
        return <Link className="w-4 h-4 mr-1 text-slate-500" />;
      case 'message':
        return <MessageSquare className="w-4 h-4 mr-1 text-slate-500" />;
      default:
        return <Search className="w-4 h-4 mr-1 text-slate-500" />;
    }
  };

  // Helper function to get scan type label
  const getScanTypeLabel = (scanType) => {
    switch (scanType) {
      case 'qr_code':
        return 'QR Code';
      case 'url':
        return 'URL';
      case 'message':
        return 'Message';
      default:
        return 'Scan';
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-50">
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 mb-2">
            Welcome back, {user?.full_name || user?.username || 'User'}!
          </h1>
          <p className="text-slate-600">Monitor and protect your digital assets with real-time threat detection.</p>
        </div>

        {/* Quick Scan Section */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-4">Quick URL Scan</h2>
          <form onSubmit={handleScan} className="flex gap-4">
            <div className="flex-1">
              <input
                type="url"
                value={searchUrl}
                onChange={(e) => setSearchUrl(e.target.value)}
                placeholder="Enter URL to scan for phishing threats..."
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isScanning}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isScanning ? (
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Scanning...
                </div>
              ) : (
                'Scan URL'
              )}
            </button>
          </form>

          {/* URL Scan Results */}
          {urlScanResult && (
            <div className="mt-6 p-6 bg-white rounded-lg shadow-md border-l-4" 
                 style={{ borderLeftColor: getRiskColor(urlScanResult.risk_score) }}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">{getClassificationIcon(urlScanResult.risk_score)}</span>
                    <h3 className="text-lg font-semibold text-gray-800">URL Scan Results</h3>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-600">Scanned URL:</p>
                      <p className="text-gray-800 font-medium break-all">{urlScanResult.url}</p>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Risk Score:</p>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-3">
                            <div 
                              className="h-3 rounded-full transition-all duration-500"
                              style={{ 
                                width: `${urlScanResult.risk_score * 100}%`,
                                backgroundColor: getRiskColor(urlScanResult.risk_score)
                              }}
                            ></div>
                          </div>
                          <span 
                            className="font-bold text-lg"
                            style={{ color: getRiskColor(urlScanResult.risk_score) }}
                          >
                            {Math.round(urlScanResult.risk_score * 100)}%
                          </span>
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-600">Classification:</p>
                        <span 
                          className="px-3 py-1 rounded-full text-sm font-medium"
                          style={{ 
                            backgroundColor: getRiskBgColor(urlScanResult.risk_score),
                            color: getRiskColor(urlScanResult.risk_score)
                          }}
                        >
                          {urlScanResult.risk_score >= 0.7 ? 'High Risk' : 
                           urlScanResult.risk_score >= 0.3 ? 'Medium Risk' : 'Low Risk'}
                        </span>
                      </div>
                    </div>
                    
                    {urlScanResult.explanation && (
                      <div>
                        <p className="text-sm text-gray-600">Analysis:</p>
                        <p className="text-gray-700 text-sm">{urlScanResult.explanation}</p>
                      </div>
                    )}
                  </div>
                </div>
                
                <button
                  onClick={() => setUrlScanResult(null)}
                  className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Clear results"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {loadingStats ? (
            // Loading skeleton for stats
            [...Array(4)].map((_, index) => (
              <div key={index} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="h-4 bg-slate-200 rounded animate-pulse mb-2"></div>
                    <div className="h-8 bg-slate-200 rounded animate-pulse w-16"></div>
                  </div>
                  <div className="w-12 h-12 bg-slate-200 rounded-lg animate-pulse"></div>
                </div>
              </div>
            ))
          ) : (
            stats.map((stat, index) => (
              <div key={index} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600 mb-1">{stat.label}</p>
                    <p className="text-2xl font-bold text-slate-800">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-lg bg-${stat.color}-100 text-${stat.color}-600`}>
                    {stat.icon}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Recent Scans */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <h2 className="text-xl font-semibold text-slate-800">Recent Scans</h2>
                  
                  {/* Filter Dropdown */}
                  <div className="relative">
                    <select
                      value={scanFilter}
                      onChange={(e) => setScanFilter(e.target.value)}
                      className="px-3 py-2 text-sm border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    >
                      <option value="all">See All</option>
                      <option value="safe">Safe</option>
                      <option value="suspicious">Suspicious</option>
                      <option value="dangerous">Dangerous</option>
                    </select>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  {lastUpdated && (
                    <span className="text-sm text-slate-500">
                      Last updated: {lastUpdated.toLocaleTimeString()}
                    </span>
                  )}
                  <button
                    onClick={() => fetchDashboardData(false)}
                    disabled={isRefreshing}
                    className="flex items-center space-x-2 px-3 py-1.5 text-sm bg-clicksafe-primary-50 text-clicksafe-primary-600 rounded-lg hover:bg-clicksafe-primary-100 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                    <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
                  </button>
                </div>
              </div>
              <div className="space-y-4">
                {loadingScans ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-slate-600">Loading recent scans...</span>
                  </div>
                ) : recentScans.length > 0 ? (
                  filteredScans.length > 0 ? (
                    filteredScans.map((scan, index) => (
                      <div key={scan.id || index} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          {(scan.classification === 'safe' || scan.classification === 'legitimate') ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <AlertTriangle className="w-5 h-5 text-red-500" />
                          )}
                          <div>
                            <p className="font-medium text-slate-800">{scan.content || scan.message || scan.url}</p>
                            <p className="text-sm text-slate-600 flex items-center">
                              {getScanTypeIcon(scan.scan_type)}
                              <span className="mr-2">{getScanTypeLabel(scan.scan_type)}</span>
                              <Clock className="w-4 h-4 mr-1" />
                              {new Date(scan.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          (scan.classification === 'safe' || scan.classification === 'legitimate')
                            ? 'bg-green-100 text-green-700' 
                            : scan.classification === 'suspicious'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {scan.classification === 'safe' || scan.classification === 'legitimate' 
                            ? 'Safe' 
                            : scan.classification === 'suspicious'
                            ? 'Suspicious'
                            : scan.classification === 'dangerous'
                            ? 'Dangerous'
                            : scan.classification?.charAt(0).toUpperCase() + scan.classification?.slice(1) || 'Unknown'
                          }
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <Shield className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                      <p>No scans match the selected filter. Try a different filter or scan more content.</p>
                    </div>
                  )
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <Shield className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No scans yet. Start scanning to see your results here.</p>
                  </div>
                )}
              </div>
              <button className="w-full mt-4 py-2 text-blue-600 hover:text-blue-700 font-medium transition-colors">
                View All Scans
              </button>
            </div>
          </div>

          {/* Threat Alerts */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Threat Alerts</h2>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-800">High Risk Domain</p>
                    <p className="text-xs text-red-600">New phishing attempt detected</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                  <Eye className="w-5 h-5 text-yellow-500 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800">Suspicious Activity</p>
                    <p className="text-xs text-yellow-600">Multiple failed login attempts</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-xl font-semibold text-slate-800 mb-4">Protection Status</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-slate-600">Real-time Protection</span>
                  <span className="text-green-600 font-medium">Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-600">Database Updated</span>
                  <span className="text-green-600 font-medium">2 hours ago</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-600">Scan Engine</span>
                  <span className="text-green-600 font-medium">Running</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
