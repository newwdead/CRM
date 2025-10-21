"""
Centralized Prometheus Metrics
"""
from prometheus_client import Counter, Gauge, Histogram

# ==============================================================================
# OCR & IMAGE PROCESSING METRICS
# ==============================================================================

ocr_processing_counter = Counter(
    'ocr_processing_total',
    'Total OCR processing requests',
    ['provider', 'status']
)

ocr_processing_time = Histogram(
    'ocr_processing_seconds',
    'OCR processing time in seconds',
    ['provider']
)

qr_scan_counter = Counter(
    'qr_scan_total',
    'QR code scans',
    ['status']
)


# ==============================================================================
# CONTACT MANAGEMENT METRICS
# ==============================================================================

contacts_total = Gauge(
    'contacts_total',
    'Total number of contacts in database'
)

contacts_created_counter = Counter(
    'contacts_created_total',
    'Total contacts created'
)

contacts_updated_counter = Counter(
    'contacts_updated_total',
    'Total contacts updated'
)

contacts_deleted_counter = Counter(
    'contacts_deleted_total',
    'Total contacts deleted'
)


# ==============================================================================
# AUTHENTICATION & USER METRICS
# ==============================================================================

users_total = Gauge(
    'users_total',
    'Total number of users'
)

auth_attempts_counter = Counter(
    'auth_attempts_total',
    'Authentication attempts',
    ['status']
)

user_logins_counter = Counter(
    'user_logins_total',
    'Successful user logins'
)

user_registrations_counter = Counter(
    'user_registrations_total',
    'New user registrations'
)


# ==============================================================================
# INTEGRATION METRICS
# ==============================================================================

telegram_messages_counter = Counter(
    'telegram_messages_total',
    'Telegram messages processed',
    ['status']
)

whatsapp_messages_counter = Counter(
    'whatsapp_messages_total',
    'WhatsApp messages processed',
    ['status']
)


# ==============================================================================
# DUPLICATE DETECTION METRICS
# ==============================================================================

duplicates_found_counter = Counter(
    'duplicates_found_total',
    'Total duplicates detected'
)

duplicates_merged_counter = Counter(
    'duplicates_merged_total',
    'Total contacts merged'
)

duplicate_detection_time = Histogram(
    'duplicate_detection_seconds',
    'Time to detect duplicates'
)


# ==============================================================================
# API REQUEST METRICS
# ==============================================================================

api_requests_counter = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def increment_contact_metric(action: str):
    """Helper to increment contact-related counters"""
    if action == 'created':
        contacts_created_counter.inc()
    elif action == 'updated':
        contacts_updated_counter.inc()
    elif action == 'deleted':
        contacts_deleted_counter.inc()


def record_auth_attempt(success: bool):
    """Helper to record authentication attempts"""
    status = 'success' if success else 'failed'
    auth_attempts_counter.labels(status=status).inc()
    if success:
        user_logins_counter.inc()


def record_ocr_processing(provider: str, duration: float, success: bool):
    """Helper to record OCR processing metrics"""
    status = 'success' if success else 'failed'
    ocr_processing_counter.labels(provider=provider, status=status).inc()
    if success:
        ocr_processing_time.labels(provider=provider).observe(duration)


def record_duplicate_detection(duration: float, found_count: int = 0):
    """Helper to record duplicate detection metrics"""
    duplicate_detection_time.observe(duration)
    if found_count > 0:
        duplicates_found_counter.inc(found_count)

