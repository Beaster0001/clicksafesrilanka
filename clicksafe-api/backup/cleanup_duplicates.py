#!/usr/bin/env python3
"""
Script to clean up duplicate messages in Recent Scam Alerts
"""
import re
from datetime import datetime
from database import get_db
from models import RecentScam

def normalize_content(content):
    """Normalize content for better duplicate detection"""
    # Remove extra whitespace, normalize line breaks, convert to lowercase
    normalized = re.sub(r'\s+', ' ', content.lower().strip())
    # Remove common variations in punctuation
    normalized = re.sub(r'[!.]{2,}', '!', normalized)
    return normalized

def are_similar(content1, content2):
    """Check if two contents are similar enough to be considered duplicates"""
    norm1 = normalize_content(content1)
    norm2 = normalize_content(content2)
    
    if len(norm1) == 0 or len(norm2) == 0:
        return False
    
    # Check if one is contained in the other or they're very similar in length
    return (norm1 in norm2 or norm2 in norm1 or 
            abs(len(norm1) - len(norm2)) / max(len(norm1), len(norm2)) < 0.1)

def cleanup_duplicates():
    """Clean up duplicate messages in the RecentScam table"""
    db = next(get_db())
    
    try:
        # Get all recent scams ordered by creation date
        all_scams = db.query(RecentScam).order_by(RecentScam.created_at.asc()).all()
        
        print(f"Found {len(all_scams)} total messages")
        
        # Group similar messages
        unique_scams = []
        duplicates_to_remove = []
        
        for scam in all_scams:
            # Check if this scam is similar to any existing unique scam
            found_similar = False
            
            for unique_scam in unique_scams:
                if (scam.original_language == unique_scam.original_language and 
                    are_similar(scam.anonymized_content, unique_scam.anonymized_content)):
                    
                    # Merge this scam into the unique one
                    unique_scam.scan_count += scam.scan_count
                    unique_scam.risk_score = max(unique_scam.risk_score, scam.risk_score)
                    unique_scam.updated_at = datetime.utcnow()
                    
                    # Update classification if new one is more severe
                    severity_order = {'safe': 0, 'suspicious': 1, 'dangerous': 2, 'high': 3, 'critical': 4}
                    if severity_order.get(scam.classification, 0) > severity_order.get(unique_scam.classification, 0):
                        unique_scam.classification = scam.classification
                    
                    # Merge suspicious terms
                    if scam.suspicious_terms:
                        existing_terms = set(unique_scam.suspicious_terms or [])
                        new_terms = set(scam.suspicious_terms)
                        unique_scam.suspicious_terms = list(existing_terms.union(new_terms))
                    
                    # Mark duplicate for removal
                    duplicates_to_remove.append(scam)
                    found_similar = True
                    print(f"Merging duplicate: {scam.anonymized_content[:50]}...")
                    break
            
            if not found_similar:
                unique_scams.append(scam)
        
        # Remove duplicates
        for duplicate in duplicates_to_remove:
            db.delete(duplicate)
        
        db.commit()
        
        print(f"Cleanup complete:")
        print(f"- Kept {len(unique_scams)} unique messages")
        print(f"- Removed {len(duplicates_to_remove)} duplicates")
        
        # Show final count
        final_count = db.query(RecentScam).count()
        print(f"- Final total: {final_count} messages")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()