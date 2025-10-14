"""
Simple phishing detection using keyword matching
Backup method when the ML model is not available
"""

import re
import urllib.parse
from typing import Dict, List

# Keywords that usually indicate phishing
PHISHING_KEYWORDS = {
    'english': [
        # Original keywords
        'urgent', 'suspended', 'verify', 'confirm', 'click here', 'act now',
        'limited time', 'expires', 'winner', 'congratulations', 'free money',
        'inheritance', 'lottery', 'prince', 'deposit', 'transfer', 'bitcoin',
        'cryptocurrency', 'investment', 'profit', 'guarantee', 'risk-free',
        'bank account', 'credit card', 'social security', 'paypal', 'amazon',
        'microsoft', 'apple', 'google', 'facebook', 'login', 'password',
        
        # Enhanced financial/banking scams
        'account suspended', 'account locked', 'unauthorized access', 'fraud alert',
        'security breach', 'suspicious activity', 'update payment', 'billing issue',
        'refund', 'chargeback', 'overdraft', 'statement', 'wire transfer',
        'routing number', 'account verification', 'card expired', 'payment failed',
        
        # Authority/government impersonation
        'irs', 'tax refund', 'government', 'federal', 'homeland security',
        'customs', 'immigration', 'visa', 'arrest warrant', 'legal action',
        'court', 'lawsuit', 'fine', 'penalty', 'compliance',
        
        # Tech support scams
        'computer infected', 'virus detected', 'malware', 'trojan', 'ransomware',
        'tech support', 'microsoft support', 'windows license', 'subscription renewal',
        'software update', 'security update', 'firewall', 'antivirus',
        
        # Romance/social engineering
        'lonely', 'love', 'relationship', 'meet', 'dating', 'widow', 'military',
        'deployed', 'gold', 'diamonds', 'beneficiary',
        
        # Cryptocurrency/investment scams
        'crypto', 'ethereum', 'nft', 'trading', 'forex', 'stocks', 'portfolio',
        'investment opportunity', 'guaranteed returns', 'double your money',
        'passive income', 'financial freedom', 'secret strategy',
        
        # COVID-19 related
        'covid relief', 'stimulus', 'vaccine', 'health insurance', 'medical bill',
        'contact tracing', 'quarantine', 'isolation', 'pandemic',
        
        # Delivery/package scams
        'package delivery', 'shipment', 'customs fee', 'delivery fee',
        'fedex', 'ups', 'dhl', 'postal service', 'tracking number',
        'delivery failed', 'address confirmation'
    ],
    'sinhala': [
        # Original keywords
        'ත්‍රස්ත', 'ගිණුම', 'තහවුරු', 'ක්ලික්', 'දැන්', 'කාලය', 'ජයග්‍රාහක',
        'සුභාශිර්වාද', 'නොමිලේ', 'මුදල්', 'උරුමය', 'ප්‍රින්ස්', 'බැංකු',
        'ක්‍රෙඩිට්', 'ලොගින්', 'මුරපදය',
        
        # Enhanced financial/security
        'ගිණුම අවහිර', 'ගිණුම අඩාල', 'වංචා අනතුරු', 'ආරක්ෂක කඩාකප්පල්කිරීම',
        'සැක සහිත ක්‍රියාකාරකම්', 'ගෙවීම යාවත්කාලීන', 'ප්‍රතිපූර්ණය',
        'තහවුරු කරන්න', 'ක්ෂණික ක්‍රියාමාර්ග', 'මුදල් අඩන්ගුව',
        
        # Tech/modern scams
        'කම්ප්‍යුටර් ආසාදිත', 'වයිරස් අනාවරණය', 'මැල්වේර්', 'තාක්ෂණික සහාය',
        'මයික්‍රොසොෆ්ට් සහාය', 'මෘදුකාංග යාවත්කාලීන', 'ඇන්ටිවයිරස්',
        
        # COVID/delivery
        'කොවිඩ් සහන', 'ප්‍රතිකාර', 'ඇති කිරීම', 'පැකේජ සැපයුම', 'බෙදාහැරීම',
        'තැපැල් සේවය', 'ලුහුබැඳීමේ අංකය', 'බෙදාහැරීම අසාර්ථක'
    ],
    'tamil': [
        'அவசரம்', 'கணக்கு', 'உறுதி', 'கிளிக்', 'இப்போது', 'நேரம்', 'வெற்றியாளர்',
        'வாழ்த්துகள்', 'இலவசம்', 'பணம்', 'வங்கி', 'கிரெடிட்', 'லாகின்', 'கடவுச்சொல்'
    ]
}

# Suspicious URL patterns
SUSPICIOUS_URL_PATTERNS = [
    # URL shorteners
    r'bit\.ly', r'tinyurl', r'goo\.gl', r't\.co', r'short\.link', r'ow\.ly',
    r'is\.gd', r'buff\.ly', r'adf\.ly', r'bl\.ink', r'rb\.gy', r'cutt\.ly',
    
    # IP addresses instead of domains
    r'\d+\.\d+\.\d+\.\d+',
    
    # Hyphenated domains (often suspicious)
    r'[a-z0-9]+-[a-z0-9]+-[a-z0-9]+\.',
    
    # Suspicious prefixes
    r'secure[^.]*\.', r'account[^.]*\.', r'verify[^.]*\.', r'update[^.]*\.',
    r'login[^.]*\.', r'signin[^.]*\.', r'auth[^.]*\.', r'support[^.]*\.',
    
    # Suspicious TLDs
    r'\.tk$', r'\.ml$', r'\.ga$', r'\.cf$', r'\.pw$', r'\.top$',
    
    # Brand impersonation patterns
    r'amazon[^.]*\.(?!amazon\.)', r'paypal[^.]*\.(?!paypal\.)',
    r'microsoft[^.]*\.(?!microsoft\.)', r'apple[^.]*\.(?!apple\.)',
    r'google[^.]*\.(?!google\.)', r'facebook[^.]*\.(?!facebook\.)',
    
    # Suspicious keywords in URL
    r'(verify|confirm|update|secure).*account', r'login.*secure',
    r'account.*suspended', r'security.*alert'
]

# Legitimate domains (whitelist)
LEGITIMATE_DOMAINS = [
    'google.com', 'youtube.com', 'facebook.com', 'amazon.com', 'microsoft.com',
    'apple.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'github.com',
    'stackoverflow.com', 'wikipedia.org', 'reddit.com', 'netflix.com'
]

def detect_language(text: str) -> str:
    """Simple language detection based on character patterns"""
    # Count different script characters
    sinhala_chars = len(re.findall(r'[\u0D80-\u0DFF]', text))
    tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return 'english'
    
    sinhala_ratio = sinhala_chars / total_chars
    tamil_ratio = tamil_chars / total_chars
    english_ratio = english_chars / total_chars
    
    if sinhala_ratio > 0.3:
        return 'sinhala'
    elif tamil_ratio > 0.3:
        return 'tamil'
    else:
        return 'english'

def analyze_url(url: str) -> Dict:
    """Analyze URL for suspicious patterns"""
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check against whitelist
        for legit_domain in LEGITIMATE_DOMAINS:
            if domain == legit_domain or domain.endswith('.' + legit_domain):
                return {
                    'is_suspicious': False,
                    'risk_score': 10,
                    'reasons': ['Known legitimate domain']
                }
        
        suspicious_reasons = []
        risk_score = 0
        
        # Check for suspicious patterns
        for pattern in SUSPICIOUS_URL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                suspicious_reasons.append(f'Matches suspicious pattern: {pattern}')
                risk_score += 20
        
        # Check for suspicious keywords in URL
        url_lower = url.lower()
        for keyword in PHISHING_KEYWORDS['english']:
            if keyword in url_lower:
                suspicious_reasons.append(f'Contains suspicious keyword: {keyword}')
                risk_score += 15
        
        # Additional checks
        if len(domain.split('.')) > 3:
            suspicious_reasons.append('Unusual domain structure')
            risk_score += 10
        
        if len(domain) > 30:
            suspicious_reasons.append('Unusually long domain name')
            risk_score += 15
        
        # Cap risk score at 90
        risk_score = min(risk_score, 90)
        
        return {
            'is_suspicious': risk_score > 40,
            'risk_score': risk_score,
            'reasons': suspicious_reasons
        }
        
    except Exception as e:
        return {
            'is_suspicious': True,
            'risk_score': 60,
            'reasons': [f'URL parsing error: {str(e)}']
        }

def analyze_message(text: str) -> Dict:
    """Analyze message content for phishing indicators"""
    text_lower = text.lower()
    language = detect_language(text)
    
    keywords = PHISHING_KEYWORDS.get(language, PHISHING_KEYWORDS['english'])
    
    found_keywords = []
    risk_score = 0
    
    # Check for phishing keywords
    for keyword in keywords:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)
            risk_score += 10
    
    # Additional pattern checks
    suspicious_patterns = []
    
    # Enhanced urgency indicators
    urgency_patterns = [
        r'urgent', r'immediate', r'expires?', r'deadline', r'act now',
        r'limited time', r'hurry', r'don\'t wait', r'time sensitive',
        r'expires today', r'expires soon', r'final notice', r'last chance'
    ]
    for pattern in urgency_patterns:
        if re.search(pattern, text_lower):
            suspicious_patterns.append('Urgency indicators')
            risk_score += 15
            break
    
    # Enhanced financial indicators
    financial_patterns = [
        r'\$\d+', r'money', r'payment', r'credit', r'bank', r'account',
        r'refund', r'billing', r'invoice', r'transaction', r'transfer',
        r'wire', r'deposit', r'withdraw', r'balance', r'overdraft'
    ]
    for pattern in financial_patterns:
        if re.search(pattern, text_lower):
            suspicious_patterns.append('Financial content')
            risk_score += 12
            break
    
    # Emotional manipulation patterns
    emotional_patterns = [
        r'congratulations', r'winner', r'selected', r'lucky', r'special offer',
        r'exclusive', r'free', r'gift', r'prize', r'reward', r'bonus'
    ]
    for pattern in emotional_patterns:
        if re.search(pattern, text_lower):
            suspicious_patterns.append('Emotional manipulation')
            risk_score += 10
            break
    
    # Authority impersonation patterns
    authority_patterns = [
        r'government', r'irs', r'fbi', r'police', r'court', r'legal',
        r'tax', r'customs', r'immigration', r'homeland security'
    ]
    for pattern in authority_patterns:
        if re.search(pattern, text_lower):
            suspicious_patterns.append('Authority impersonation')
            risk_score += 20
            break
    
    # Tech support scam patterns
    tech_patterns = [
        r'computer', r'virus', r'malware', r'infected', r'security',
        r'tech support', r'microsoft', r'windows', r'antivirus'
    ]
    for pattern in tech_patterns:
        if re.search(pattern, text_lower):
            suspicious_patterns.append('Tech support scam indicators')
            risk_score += 15
            break
    
    # Check for suspicious requests
    request_patterns = [r'click here', r'verify', r'confirm', r'update', r'login']
    for pattern in request_patterns:
        if re.search(pattern, text_lower):
            suspicious_patterns.append('Suspicious requests')
            risk_score += 18
            break
    
    # Cap risk score at 95
    risk_score = min(risk_score, 95)
    
    return {
        'language': language,
        'risk_score': risk_score,
        'found_keywords': found_keywords,
        'suspicious_patterns': suspicious_patterns,
        'is_suspicious': risk_score > 50
    }

def simple_predict(text: str) -> Dict:
    """Main prediction function using simple keyword detection"""
    
    # Determine if it's a URL or message
    is_url = bool(re.match(r'https?://', text.strip()))
    
    if is_url:
        # Analyze as URL
        url_analysis = analyze_url(text)
        risk_score = url_analysis['risk_score']
        
        # Classify based on risk score
        if risk_score <= 30:
            classification = 'safe'
        elif risk_score <= 60:
            classification = 'suspicious'
        else:
            classification = 'dangerous'
        
        return {
            'text': text,
            'language': 'english',
            'classification': classification,
            'risk_score': risk_score / 100.0,  # Convert to 0-1 scale
            'suspicious_terms': url_analysis.get('reasons', []),
            'explanation': f"URL analysis shows {classification} content. " + "; ".join(url_analysis.get('reasons', [])),
            'is_safe': classification == 'safe'
        }
    
    else:
        # Analyze as message
        message_analysis = analyze_message(text)
        risk_score = message_analysis['risk_score']
        
        # Classify based on risk score
        if risk_score <= 30:
            classification = 'safe'
        elif risk_score <= 60:
            classification = 'suspicious'
        else:
            classification = 'dangerous'
        
        explanation_parts = []
        if message_analysis['found_keywords']:
            explanation_parts.append(f"Found suspicious keywords: {', '.join(message_analysis['found_keywords'][:3])}")
        if message_analysis['suspicious_patterns']:
            explanation_parts.append(f"Contains: {', '.join(message_analysis['suspicious_patterns'])}")
        
        explanation = f"Message analysis shows {classification} content. " + "; ".join(explanation_parts) if explanation_parts else f"Content appears {classification}."
        
        return {
            'text': text,
            'language': message_analysis['language'],
            'classification': classification,
            'risk_score': risk_score,  # Keep 0-100 scale for consistency with frontend
            'suspicious_terms': message_analysis['found_keywords'][:5],  # Limit to 5
            'explanation': explanation,
            'is_safe': classification == 'safe'
        }