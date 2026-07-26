"""
CAWNCADE AI v3.5 — Backward Compatibility Wrapper for Tier 4 Verification Package.
Delegates to app.services.tier4.tier4_verification_service.
"""

from app.services.tier4.verification_service import tier4_verification_service, Tier4VerificationService

# Re-export singleton for backward compatibility
offline_nlp_service = tier4_verification_service
OfflineNLPService = Tier4VerificationService
