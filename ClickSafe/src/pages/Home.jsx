import { Link } from 'react-router-dom';
import { Shield, Lock, Users, Zap, ChevronRight, AlertTriangle, Clock, RefreshCw, ChevronLeft } from 'lucide-react';
import { useState, useEffect } from 'react';

const Home = () => {
  const [recentScams, setRecentScams] = useState([]);
  const [allScams, setAllScams] = useState([]); // Store all scams for pagination
  const [currentPage, setCurrentPage] = useState(0); // Current page for scam display
  const [scamsPerPage] = useState(3); // Number of scams to show per page
  const [loadingScams, setLoadingScams] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchRecentScams();
    
    // Set up auto-refresh every 30 seconds for real-time updates
    const interval = setInterval(() => {
      fetchRecentScams(false); // Don't show loading on refresh
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // Update displayed scams when page changes
  useEffect(() => {
    if (allScams.length > 0) {
      updateDisplayedScams(allScams, currentPage);
    }
  }, [currentPage, allScams]);

  const fetchRecentScams = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoadingScams(true);
      } else {
        setIsRefreshing(true);
      }
      
      // Add cache-busting parameter to ensure fresh data
      const timestamp = new Date().getTime();
      const response = await fetch(`http://localhost:8000/scans/recent-scams/public?_t=${timestamp}`);
      if (response.ok) {
        const scams = await response.json();
        console.log('Fetched scams:', scams.length);
        
        // Filter to only show dangerous messages - must be DANGEROUS classification AND high risk
        const dangerousScams = scams.filter(scam => {
          // Must be classified as dangerous (not just suspicious)
          const isDangerousClassification = scam.classification === 'dangerous' || 
                                           scam.classification === 'high' || 
                                           scam.classification === 'critical';
          
          // Must have high risk score (handle both decimal and percentage formats)
          const riskScore = scam.risk_score > 1 ? scam.risk_score : scam.risk_score * 100;
          const isHighRiskScore = riskScore >= 70;
          
          // Must meet BOTH criteria - dangerous classification AND high risk score
          return isDangerousClassification && isHighRiskScore;
        });
        
        // Additional frontend deduplication - remove similar content
        const deduplicatedScams = dangerousScams.filter((scam, index, array) => {
          // Check if this is the first occurrence of similar content
          const normalizeContent = (content) => {
            return content.toLowerCase()
              .replace(/[^\w\s]/g, '') // Remove punctuation
              .replace(/\s+/g, ' ')    // Normalize whitespace
              .trim();
          };
          
          const currentNormalized = normalizeContent(scam.anonymized_content);
          
          // Find first index with similar content
          const firstIndex = array.findIndex(otherScam => {
            const otherNormalized = normalizeContent(otherScam.anonymized_content);
            
            // Check for exact match or very similar content
            if (currentNormalized === otherNormalized) return true;
            
            // Check for substring similarity (one contains the other with high similarity)
            const minLength = Math.min(currentNormalized.length, otherNormalized.length);
            const maxLength = Math.max(currentNormalized.length, otherNormalized.length);
            
            if (minLength > 20) { // Only check similarity for longer content
              const lengthRatio = minLength / maxLength;
              if (lengthRatio > 0.8) { // If lengths are similar
                // Check if one contains the other
                return currentNormalized.includes(otherNormalized) || 
                       otherNormalized.includes(currentNormalized);
              }
            }
            
            return false;
          });
          
          // Keep only the first occurrence (or this one if no duplicates found)
          return firstIndex === index;
        });
        
        console.log('Filtered dangerous scams:', dangerousScams.length);
        console.log('After deduplication:', deduplicatedScams.length);
        setAllScams(deduplicatedScams); // Store only dangerous and deduplicated scams
        
        // Reset to first page if current page is out of bounds after filtering
        const maxPages = Math.ceil(deduplicatedScams.length / scamsPerPage);
        const newCurrentPage = currentPage >= maxPages ? 0 : currentPage;
        if (newCurrentPage !== currentPage) {
          setCurrentPage(newCurrentPage);
        }
        
        updateDisplayedScams(deduplicatedScams, newCurrentPage); // Update displayed scams based on current page
        setLastUpdated(new Date());
      } else {
        console.error('Failed to fetch scams:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error fetching recent scams:', error);
    } finally {
      if (showLoading) {
        setLoadingScams(false);
      } else {
        setIsRefreshing(false);
      }
    }
  };

  // Helper function to update displayed scams based on pagination
  const updateDisplayedScams = (scams, page) => {
    const startIndex = page * scamsPerPage;
    const endIndex = startIndex + scamsPerPage;
    setRecentScams(scams.slice(startIndex, endIndex));
  };

  const handleManualRefresh = () => {
    fetchRecentScams(false);
  };

  // Navigation functions for scam alerts
  const handlePreviousPage = () => {
    setCurrentPage(prev => Math.max(0, prev - 1));
  };

  const handleNextPage = () => {
    const maxPage = Math.ceil(allScams.length / scamsPerPage) - 1;
    setCurrentPage(prev => Math.min(maxPage, prev + 1));
  };

  // Calculate pagination info
  const totalPages = Math.ceil(allScams.length / scamsPerPage);
  const canGoPrevious = currentPage > 0;
  const canGoNext = currentPage < totalPages - 1;

  const features = [
    {
      icon: <Shield className="w-8 h-8 text-blue-600" />,
      title: "Advanced Protection",
      description: "AI-powered phishing detection with 99.9% accuracy rate"
    },
    {
      icon: <Lock className="w-8 h-8 text-blue-600" />,
      title: "Secure Analysis",
      description: "End-to-end encryption ensures your data remains private"
    },
    {
      icon: <Zap className="w-8 h-8 text-blue-600" />,
      title: "Real-time Scanning",
      description: "Instant URL analysis with immediate threat detection"
    },
    {
      icon: <Users className="w-8 h-8 text-blue-600" />,
      title: "Team Collaboration",
      description: "Share insights and protect your organization together"
    }
  ];

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-5xl md:text-6xl font-bold text-slate-800 mb-6 leading-tight">
              Protect Your Digital Life from 
              <span className="text-blue-600"> Phishing Attacks</span>
            </h1>
            <p className="text-xl text-slate-600 mb-8 leading-relaxed">
              Advanced AI-powered detection system that identifies and blocks phishing attempts 
              in real-time, keeping you and your organization safe from cyber threats.
            </p>
            <div className="flex justify-center">
              <div className="bg-white rounded-2xl p-2 shadow-lg border border-slate-200 flex flex-col gap-2">
                <Link 
                  to="/detector" 
                  className="bg-blue-600 text-white px-8 py-4 rounded-xl hover:bg-blue-700 transition-all transform hover:scale-105 font-semibold text-lg flex items-center justify-center group min-w-[280px]"
                  style={{ color: 'white' }}
                >
                  <Shield className="w-5 h-5 mr-3 text-white" />
                  <span className="text-white">Phishing Detection</span>
                  <ChevronRight className="w-5 h-5 ml-3 group-hover:translate-x-1 transition-transform text-white" />
                </Link>
                <Link 
                  to="/qr-scanner" 
                  className="bg-slate-600 text-white px-8 py-4 rounded-xl hover:bg-slate-700 transition-all transform hover:scale-105 font-semibold text-lg flex items-center justify-center group min-w-[280px]"
                  style={{ color: 'white' }}
                >
                  <svg className="w-5 h-5 mr-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M3 3h18v18H3V3zm16 16V5H5v14h14zM7 7h4v4H7V7zm6 0h4v4h-4V7zm-6 6h4v4H7v-4zm6 0h4v4h-4v-4z"/>
                  </svg>
                  <span className="text-white">QR Code Scanner</span>
                  <ChevronRight className="w-5 h-5 ml-3 group-hover:translate-x-1 transition-transform text-white" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Recent Scam Alerts Section */}
      {!loadingScams && recentScams.length > 0 && (
        <section className="py-16 px-4 sm:px-6 lg:px-8 bg-red-50">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <div className="flex items-center justify-center mb-4">
                <AlertTriangle className="w-8 h-8 text-red-600 mr-3" />
                <h2 className="text-3xl font-bold text-red-800">
                  Recent Scam Alerts
                </h2>
                
                {/* Navigation and refresh controls */}
                <div className="ml-4 flex items-center space-x-2">
                  {/* Previous button */}
                  <button
                    onClick={handlePreviousPage}
                    disabled={!canGoPrevious}
                    className="p-2 bg-red-100 hover:bg-red-200 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Previous scam alerts"
                  >
                    <ChevronLeft className="w-5 h-5 text-red-600" />
                  </button>
                  
                  {/* Page indicator */}
                  {totalPages > 1 && (
                    <div className="px-3 py-1 bg-red-100 rounded-full">
                      <span className="text-sm font-medium text-red-700">
                        {currentPage + 1} / {totalPages}
                      </span>
                    </div>
                  )}
                  
                  {/* Next button */}
                  <button
                    onClick={handleNextPage}
                    disabled={!canGoNext}
                    className="p-2 bg-red-100 hover:bg-red-200 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Next scam alerts"
                  >
                    <ChevronRight className="w-5 h-5 text-red-600" />
                  </button>
                  
                  {/* Refresh button */}
                  <button
                    onClick={handleManualRefresh}
                    disabled={isRefreshing}
                    className="p-2 bg-red-100 hover:bg-red-200 rounded-full transition-colors disabled:opacity-50"
                    title="Refresh scam alerts"
                  >
                    <RefreshCw className={`w-5 h-5 text-red-600 ${isRefreshing ? 'animate-spin' : ''}`} />
                  </button>
                </div>
              </div>
              <p className="text-lg text-red-700 max-w-2xl mx-auto mb-2">
                Stay alert! Only high-risk and dangerous phishing attempts are shown here. These are the most critical threats detected by our community.
              </p>
              {lastUpdated && (
                <div className="flex items-center justify-center text-sm text-red-600">
                  <Clock className="w-4 h-4 mr-1" />
                  <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
                  {isRefreshing && <span className="ml-2 text-red-500">• Updating...</span>}
                </div>
              )}
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 transition-all duration-300">
              {recentScams.map((scam, index) => (
                <div 
                  key={scam.id}
                  className="bg-white rounded-xl p-6 border-2 border-red-200 hover:border-red-300 transition-all duration-300 shadow-lg transform hover:scale-105 animate-fade-in"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-3 ${
                        scam.classification === 'dangerous' ? 'bg-red-500' : 'bg-orange-500'
                      }`}></div>
                      <span className={`text-sm font-semibold uppercase ${
                        scam.classification === 'dangerous' ? 'text-red-700' : 'text-orange-700'
                      }`}>
                        {scam.classification}
                      </span>
                    </div>
                    <div className="flex items-center text-gray-500 text-sm">
                      <Clock className="w-4 h-4 mr-1" />
                      {new Date(scam.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="mb-4">
                    <p className="text-gray-700 text-sm leading-relaxed line-clamp-3 bg-gray-50 p-3 rounded-lg italic">
                      "{scam.anonymized_content.length > 120 
                        ? scam.anonymized_content.substring(0, 120) + '...' 
                        : scam.anonymized_content}"
                    </p>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-sm text-gray-600 mr-2">Risk Score:</span>
                      <div className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        (scam.risk_score > 1 ? scam.risk_score : scam.risk_score * 100) > 70 ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'
                      }`}>
                        {Math.round(scam.risk_score > 1 ? scam.risk_score : scam.risk_score * 100)}%
                      </div>
                      {/* Show warning if low risk score but has suspicious keywords */}
                      {(scam.risk_score > 1 ? scam.risk_score : scam.risk_score * 100) < 70 && scam.suspicious_terms && scam.suspicious_terms.length > 0 && (
                        <div className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold" title="Flagged due to suspicious keywords">
                          ⚠️ Keywords
                        </div>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {scam.scan_count} report{scam.scan_count !== 1 ? 's' : ''}
                    </div>
                  </div>

                  {scam.suspicious_terms && scam.suspicious_terms.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p className="text-xs text-gray-600 mb-2">Suspicious keywords:</p>
                      <div className="flex flex-wrap gap-1">
                        {scam.suspicious_terms.slice(0, 4).map((term, termIndex) => (
                          <span 
                            key={termIndex} 
                            className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs"
                          >
                            {term}
                          </span>
                        ))}
                        {scam.suspicious_terms.length > 4 && (
                          <span className="text-xs text-gray-500">
                            +{scam.suspicious_terms.length - 4} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="text-center mt-8">
              <Link 
                to="/detector" 
                className="bg-red-600 text-white px-6 py-3 rounded-xl hover:bg-red-700 transition-all transform hover:scale-105 font-semibold inline-flex items-center group"
              >
                Check Your Messages
                <Shield className="w-5 h-5 ml-2 group-hover:scale-110 transition-transform" />
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-800 mb-4">
              Why Choose Clicksafe Srilanka?
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Our cutting-edge technology provides comprehensive protection against evolving cyber threats
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className="bg-slate-50 p-8 rounded-2xl hover:shadow-lg transition-all duration-300 group"
              >
                <div className="mb-4 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-slate-800 mb-3">
                  {feature.title}
                </h3>
                <p className="text-slate-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-indigo-700">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to Secure Your Digital World?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of users who trust Clicksafe Srilanka to protect their online activities
          </p>
          <Link 
            to="/signup" 
            className="bg-white text-blue-600 px-8 py-4 rounded-xl hover:bg-slate-50 transition-all transform hover:scale-105 font-semibold text-lg inline-flex items-center group"
          >
            Get Started Today
            <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-800 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <Shield className="w-8 h-8 text-blue-400" />
              <span className="text-xl font-bold">Clicksafe Srilanka</span>
            </div>
            <div className="flex space-x-6">
              <a href="#" className="text-slate-400 hover:text-white transition-colors">Privacy</a>
              <a href="#" className="text-slate-400 hover:text-white transition-colors">Terms</a>
              <a href="#" className="text-slate-400 hover:text-white transition-colors">Support</a>
            </div>
          </div>
          <div className="border-t border-slate-700 mt-8 pt-8 text-center text-slate-400">
            <p>&copy; 2025 Clicksafe Srilanka. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
