"""
Modern QR URL Safety Analysis Service
Advanced QR code scanning with ML-based URL safety prediction
"""
import os
import pickle
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
import hashlib
import base64

# Core dependencies
import cv2
import numpy as np
from PIL import Image
import pyzbar.pyzbar as pyzbar
import tldextract
import requests
import aiohttp
from dotenv import load_dotenv

# ML dependencies
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif hasattr(obj, 'item') and callable(obj.item):  # Any numpy scalar type
        try:
            return obj.item()
        except:
            pass
    elif hasattr(obj, 'tolist') and callable(obj.tolist):
        try:
            return obj.tolist()
        except:
            pass
    elif str(type(obj)).startswith("<class 'numpy."):  # Catch any remaining numpy types
        try:
            return obj.item() if hasattr(obj, 'item') else obj.tolist() if hasattr(obj, 'tolist') else int(obj)
        except:
            try:
                return float(obj)
            except:
                return str(obj)
    else:
        return obj

class QRURLSafetyService:
    """
    Modern QR URL Safety Analysis Service
    
    Features:
    - QR code detection and decoding
    - ML-based URL safety prediction
    - VirusTotal integration
    - URL feature extraction
    - Caching and optimization
    """
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.model_loaded = False
        self.virustotal_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        self.model_path = os.getenv('MODEL_PATH', 'qr_url_safety_model.pkl')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Initialize the service
        self._load_model()
        
    def _load_model(self) -> bool:
        """Load the trained ML model and preprocessors"""
        # TEMPORARILY DISABLED: ML model loading causing serialization issues
        logger.info("🔄 ML model temporarily disabled for debugging")
        
        # Create fallback components for basic functionality
        self._create_fallback_components()
        return False
    
    def _create_fallback_components(self):
        """Create basic components when model isn't available"""
        logger.info("🔄 Creating fallback components for basic QR scanning")
        self.model_loaded = False
    
    async def scan_qr_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Scan QR code from image data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dict containing QR detection results and safety analysis
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert PIL image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Convert to OpenCV format (RGB to BGR)
            cv_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Detect QR codes
            qr_codes = pyzbar.decode(cv_image)
            
            if not qr_codes:
                return {
                    "success": False,
                    "message": "No QR code found in image",
                    "qr_detection": None,
                    "safety_analysis": None
                }
            
            # Process first QR code found
            qr_code = qr_codes[0]
            decoded_url = qr_code.data.decode('utf-8')
            
            # Analyze URL safety
            safety_analysis = await self.analyze_url_safety(decoded_url)
            
            result = {
                "success": True,
                "message": "QR code detected and analyzed",
                "qr_detection": {
                    "success": True,
                    "decoded_url": decoded_url,
                    "qr_type": qr_code.type,
                    "position": {
                        "x": int(int(qr_code.rect.left)),  # Force native Python int
                        "y": int(int(qr_code.rect.top)),
                        "width": int(int(qr_code.rect.width)),
                        "height": int(int(qr_code.rect.height))
                    }
                },
                "safety_analysis": safety_analysis
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"❌ QR scanning error: {str(e)}")
            result = {
                "success": False,
                "message": f"Failed to scan QR code: {str(e)}",
                "qr_detection": None,
                "safety_analysis": None
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(result)
    
    async def analyze_url_safety(self, url: str) -> Dict[str, Any]:
        """
        Analyze URL safety using ML model and external services
        
        Args:
            url: URL to analyze
            
        Returns:
            Dict containing safety analysis results
        """
        try:
            # Extract URL features
            features = self._extract_url_features(url)
            
            # ML-based prediction (temporarily disabled to fix serialization)
            ml_prediction = None  # self._predict_url_safety(url, features) if self.model_loaded else None
            
            # VirusTotal analysis (if API key available)
            vt_analysis = await self._virustotal_analysis(url) if self.virustotal_api_key else None
            
            # Combine results
            risk_score = self._calculate_risk_score(ml_prediction, vt_analysis, features)
            
            result = {
                "url": url,
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
                "features": features,
                "ml_prediction": ml_prediction,
                "virustotal_analysis": vt_analysis,
                "recommendations": self._get_recommendations(risk_score),
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"❌ URL analysis error: {str(e)}")
            result = {
                "url": url,
                "risk_score": 50,  # Default medium risk
                "risk_level": "medium",
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(result)
    
    def _extract_url_features(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive features from URL"""
        try:
            parsed = urlparse(url)
            extracted = tldextract.extract(url)
            
            # Basic URL features
            features = {
                "url_length": len(url),
                "domain_length": len(parsed.netloc),
                "path_length": len(parsed.path),
                "query_length": len(parsed.query or ""),
                "subdomain_count": len(extracted.subdomain.split('.')) if extracted.subdomain else 0,
                "domain_has_numbers": any(c.isdigit() for c in extracted.domain),
                "url_has_ip": self._is_ip_address(parsed.netloc),
                "is_https": parsed.scheme == 'https',
                "has_suspicious_keywords": self._has_suspicious_keywords(url),
                "domain_age_days": 0,  # Would need WHOIS lookup
                "special_char_count": sum(1 for c in url if not c.isalnum() and c not in '.-_~:/?#[]@!$&\'()*+,;='),
                "tld": extracted.suffix,
                "domain": extracted.domain,
                "subdomain": extracted.subdomain
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(features)
            
        except Exception as e:
            logger.error(f"❌ Feature extraction error: {str(e)}")
            return {"error": str(e)}
    
    def _predict_url_safety(self, url: str, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make ML-based prediction on URL safety"""
        if not self.model_loaded:
            return None
            
        try:
            # Prepare features for model
            feature_vector = self._prepare_feature_vector(url, features)
            
            # Make prediction
            prediction_proba = self.model.predict_proba([feature_vector])[0]
            prediction = self.model.predict([feature_vector])[0]
            
            # Get class labels
            classes = self.label_encoder.classes_
            
            result = {
                "prediction": prediction,
                "confidence": float(max(prediction_proba)),
                "probabilities": {
                    classes[i]: float(prob) for i, prob in enumerate(prediction_proba)
                },
                "model_version": "2.0.0"
            }
            
            # Convert numpy types to native Python types
            return convert_numpy_types(result)
            
        except Exception as e:
            logger.error(f"❌ ML prediction error: {str(e)}")
            return None
    
    async def _virustotal_analysis(self, url: str) -> Optional[Dict[str, Any]]:
        """Analyze URL using VirusTotal API"""
        if not self.virustotal_api_key:
            return None
            
        try:
            # Encode URL for VirusTotal API
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            
            headers = {
                "x-apikey": self.virustotal_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                # Submit URL for analysis
                submit_url = "https://www.virustotal.com/api/v3/urls"
                async with session.post(submit_url, headers=headers, data={"url": url}) as response:
                    if response.status == 200:
                        submit_data = await response.json()
                        analysis_id = submit_data.get("data", {}).get("id")
                        
                        # Wait a bit for analysis
                        await asyncio.sleep(2)
                        
                        # Get analysis results
                        result_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
                        async with session.get(result_url, headers=headers) as result_response:
                            if result_response.status == 200:
                                result_data = await result_response.json()
                                stats = result_data.get("data", {}).get("attributes", {}).get("stats", {})
                                
                                return {
                                    "malicious": stats.get("malicious", 0),
                                    "suspicious": stats.get("suspicious", 0),
                                    "harmless": stats.get("harmless", 0),
                                    "undetected": stats.get("undetected", 0),
                                    "total_scans": sum(stats.values()) if stats else 0,
                                    "analysis_date": datetime.now().isoformat()
                                }
            
        except Exception as e:
            logger.error(f"❌ VirusTotal analysis error: {str(e)}")
        
        return None
    
    def _calculate_risk_score(self, ml_prediction: Optional[Dict], vt_analysis: Optional[Dict], features: Dict) -> int:
        """Calculate overall risk score from multiple sources"""
        base_score = 30  # Base medium risk
        
        # ML model contribution
        if ml_prediction:
            malicious_prob = ml_prediction.get("probabilities", {}).get("malicious", 0)
            base_score += int(malicious_prob * 40)
        
        # VirusTotal contribution
        if vt_analysis and vt_analysis.get("total_scans", 0) > 0:
            malicious_ratio = vt_analysis.get("malicious", 0) / vt_analysis.get("total_scans", 1)
            suspicious_ratio = vt_analysis.get("suspicious", 0) / vt_analysis.get("total_scans", 1)
            base_score += int((malicious_ratio * 30) + (suspicious_ratio * 15))
        
        # Feature-based adjustments
        if features.get("url_has_ip"):
            base_score += 15
        if not features.get("is_https"):
            base_score += 10
        if features.get("has_suspicious_keywords"):
            base_score += 20
        if features.get("url_length", 0) > 100:
            base_score += 5
        
        return min(100, max(0, base_score))
    
    def _get_risk_level(self, risk_score: int) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _get_recommendations(self, risk_score: int) -> List[str]:
        """Get safety recommendations based on risk score"""
        if risk_score >= 80:
            return [
                "⚠️ HIGH RISK: Do not visit this URL",
                "Block this URL in your security systems",
                "Report this URL to security authorities",
                "Warn others about this potential threat"
            ]
        elif risk_score >= 60:
            return [
                "⚠️ CAUTION: Exercise extreme caution",
                "Do not enter personal information",
                "Verify the URL through official channels",
                "Consider using additional security tools"
            ]
        elif risk_score >= 40:
            return [
                "⚠️ BE CAREFUL: Proceed with caution",
                "Verify the website's authenticity",
                "Avoid entering sensitive information",
                "Check for HTTPS and valid certificates"
            ]
        else:
            return [
                "✅ Appears relatively safe",
                "Still verify website authenticity",
                "Keep security software updated",
                "Be cautious with personal information"
            ]
    
    def _prepare_feature_vector(self, url: str, features: Dict) -> List:
        """Prepare feature vector for ML model"""
        # This would depend on how your model was trained
        # Adjust based on your actual model requirements
        if not self.vectorizer:
            return []
        
        try:
            # Text features
            text_features = self.vectorizer.transform([url]).toarray()[0]
            
            # Numerical features
            numerical_features = [
                features.get("url_length", 0),
                features.get("domain_length", 0),
                features.get("path_length", 0),
                features.get("subdomain_count", 0),
                int(features.get("domain_has_numbers", False)),
                int(features.get("url_has_ip", False)),
                int(features.get("is_https", False)),
                int(features.get("has_suspicious_keywords", False)),
                features.get("special_char_count", 0)
            ]
            
            return np.concatenate([text_features, numerical_features]).tolist()
            
        except Exception as e:
            logger.error(f"❌ Feature vector preparation error: {str(e)}")
            return []
    
    def _is_ip_address(self, netloc: str) -> bool:
        """Check if netloc is an IP address"""
        try:
            parts = netloc.split(':')[0].split('.')
            return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def _has_suspicious_keywords(self, url: str) -> bool:
        """Check for suspicious keywords in URL"""
        suspicious_keywords = [
            'secure', 'account', 'update', 'verify', 'login', 'signin',
            'banking', 'paypal', 'amazon', 'microsoft', 'google',
            'free', 'win', 'prize', 'urgent', 'suspend', 'limited'
        ]
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in suspicious_keywords)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": "QR URL Safety Analysis",
            "version": "2.0.0",
            "model_loaded": self.model_loaded,
            "model_path": self.model_path,
            "virustotal_enabled": bool(self.virustotal_api_key),
            "debug_mode": self.debug,
            "status": "operational",
            "features": [
                "QR Code Detection",
                "URL Safety Analysis",
                "ML-based Prediction",
                "VirusTotal Integration",
                "Feature Extraction",
                "Risk Assessment"
            ]
        }

# Global service instance
qr_service = QRURLSafetyService()

# Import fix for missing io
import io