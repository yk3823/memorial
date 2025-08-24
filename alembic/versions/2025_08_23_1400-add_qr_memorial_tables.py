"""Add QR memorial tables

Revision ID: add_qr_memorial_tables
Revises: b9c506a8c889
Create Date: 2025-08-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_qr_memorial_tables'
down_revision = 'b9c506a8c889'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add QR memorial tables for QR code generation and tracking."""
    
    # Create manufacturing_partners table
    op.create_table('manufacturing_partners',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the record'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='Soft delete flag - true if record is logically deleted'),
        sa.Column('company_name', sa.String(length=200), nullable=False, comment='Company name'),
        sa.Column('contact_email', sa.String(length=255), nullable=False, comment='Primary contact email'),
        sa.Column('contact_phone', sa.String(length=20), nullable=True, comment='Primary contact phone number'),
        sa.Column('website_url', sa.String(length=500), nullable=True, comment='Company website URL'),
        sa.Column('specialties', postgresql.ARRAY(sa.String(length=100)), nullable=True, comment='Partner specialties (Hebrew, weather-resistant, etc.)'),
        sa.Column('supported_materials', postgresql.ARRAY(sa.String(length=50)), nullable=True, comment='Supported materials for engraving'),
        sa.Column('minimum_order_quantity', sa.Integer(), nullable=False, comment='Minimum order quantity'),
        sa.Column('maximum_order_quantity', sa.Integer(), nullable=True, comment='Maximum order quantity (null for unlimited)'),
        sa.Column('base_price_cents', sa.Integer(), nullable=False, comment='Base price per unit in cents'),
        sa.Column('setup_fee_cents', sa.Integer(), nullable=False, comment='One-time setup fee in cents'),
        sa.Column('rush_order_fee_cents', sa.Integer(), nullable=False, comment='Rush order additional fee in cents'),
        sa.Column('turnaround_days', sa.Integer(), nullable=False, comment='Standard turnaround time in days'),
        sa.Column('rush_turnaround_days', sa.Integer(), nullable=True, comment='Rush order turnaround time in days'),
        sa.Column('rating', sa.DECIMAL(precision=3, scale=2), nullable=False, comment='Average customer rating (0.00-5.00)'),
        sa.Column('total_orders', sa.Integer(), nullable=False, comment='Total number of orders completed'),
        sa.Column('successful_orders', sa.Integer(), nullable=False, comment='Number of successfully completed orders'),
        sa.Column('average_delivery_days', sa.DECIMAL(precision=4, scale=1), nullable=True, comment='Average actual delivery time in days'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether partner is currently accepting orders'),
        sa.Column('is_preferred', sa.Boolean(), nullable=False, comment='Whether partner is featured as preferred'),
        sa.Column('onboarded_at', sa.DateTime(timezone=True), nullable=True, comment='When partner was onboarded'),
        sa.Column('last_order_at', sa.DateTime(timezone=True), nullable=True, comment='When last order was placed with partner'),
        sa.Column('api_webhook_url', sa.Text(), nullable=True, comment='Webhook URL for order status updates'),
        sa.Column('api_key', sa.String(length=255), nullable=True, comment='API key for partner integration'),
        sa.Column('supports_api', sa.Boolean(), nullable=False, comment='Whether partner supports API integration'),
        sa.PrimaryKeyConstraint('id'),
        comment='Manufacturing partners for aluminum QR memorial pieces'
    )
    
    # Create QR memorial codes table
    op.create_table('qr_memorial_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the record'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='Soft delete flag - true if record is logically deleted'),
        sa.Column('memorial_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the memorial this QR code belongs to'),
        sa.Column('qr_code_data', sa.Text(), nullable=False, comment='The actual URL/data encoded in the QR code'),
        sa.Column('qr_code_url', sa.Text(), nullable=False, comment='Full URL that the QR code resolves to'),
        sa.Column('qr_image_path', sa.String(length=500), nullable=True, comment='File path to generated QR code image'),
        sa.Column('design_template', sa.String(length=50), nullable=False, comment='Design template used for QR code'),
        sa.Column('custom_message', sa.Text(), nullable=True, comment='Custom message to display with QR code'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether the QR code is active and scannable'),
        sa.Column('activation_date', sa.DateTime(timezone=True), nullable=True, comment='When the QR code was activated'),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True, comment='When the QR code expires (optional)'),
        sa.Column('manufacturing_partner_id', postgresql.UUID(as_uuid=True), nullable=True, comment='ID of manufacturing partner for aluminum piece'),
        sa.Column('aluminum_piece_order_id', sa.String(length=100), nullable=True, comment='Partner\'s order ID for tracking'),
        sa.Column('order_status', sa.String(length=20), nullable=False, comment='Current status of aluminum piece order'),
        sa.Column('order_placed_at', sa.DateTime(timezone=True), nullable=True, comment='When the aluminum piece order was placed'),
        sa.Column('shipped_at', sa.DateTime(timezone=True), nullable=True, comment='When the aluminum piece was shipped'),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True, comment='When the aluminum piece was delivered'),
        sa.Column('subscription_tier', sa.String(length=20), nullable=False, comment='QR subscription tier (basic, premium)'),
        sa.Column('annual_fee_cents', sa.Integer(), nullable=False, comment='Annual QR service fee in cents'),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True, comment='Next billing date for QR service'),
        sa.Column('total_scans', sa.Integer(), nullable=False, comment='Total number of QR code scans'),
        sa.Column('last_scan_at', sa.DateTime(timezone=True), nullable=True, comment='When the QR code was last scanned'),
        sa.ForeignKeyConstraint(['manufacturing_partner_id'], ['manufacturing_partners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['memorial_id'], ['memorials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='QR codes for memorial pages with manufacturing integration'
    )
    
    # Create QR scan events table
    op.create_table('qr_scan_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the record'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='Soft delete flag - true if record is logically deleted'),
        sa.Column('qr_code_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the QR code that was scanned'),
        sa.Column('scanned_at', sa.DateTime(timezone=True), nullable=False, comment='When the QR code was scanned'),
        sa.Column('visitor_ip', postgresql.INET(), nullable=True, comment='Visitor\'s IP address (anonymized for privacy)'),
        sa.Column('visitor_location_lat', sa.DECIMAL(precision=10, scale=8), nullable=True, comment='Visitor\'s approximate latitude'),
        sa.Column('visitor_location_lng', sa.DECIMAL(precision=11, scale=8), nullable=True, comment='Visitor\'s approximate longitude'),
        sa.Column('visitor_country', sa.String(length=100), nullable=True, comment='Visitor\'s country (from IP geolocation)'),
        sa.Column('visitor_city', sa.String(length=100), nullable=True, comment='Visitor\'s city (from IP geolocation)'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='Visitor\'s browser user agent string'),
        sa.Column('device_type', sa.String(length=20), nullable=True, comment='Device type (mobile, tablet, desktop)'),
        sa.Column('browser_name', sa.String(length=50), nullable=True, comment='Browser name (Chrome, Safari, etc.)'),
        sa.Column('operating_system', sa.String(length=50), nullable=True, comment='Operating system (iOS, Android, Windows, etc.)'),
        sa.Column('session_duration_seconds', sa.Integer(), nullable=True, comment='How long visitor spent on memorial page'),
        sa.Column('pages_visited', sa.Integer(), nullable=False, comment='Number of pages visited in session'),
        sa.Column('bounce_rate', sa.Boolean(), nullable=False, comment='True if visitor left immediately (bounce)'),
        sa.Column('scan_source', sa.String(length=50), nullable=False, comment='Where the QR code was scanned (gravesite, online, etc.)'),
        sa.Column('referrer_url', sa.Text(), nullable=True, comment='URL that referred the visitor (if any)'),
        sa.Column('tracking_consent', sa.Boolean(), nullable=False, comment='Whether visitor consented to detailed tracking'),
        sa.ForeignKeyConstraint(['qr_code_id'], ['qr_memorial_codes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Analytics tracking for QR code scans'
    )
    
    # Create indexes for manufacturing_partners
    op.create_index('ix_partner_active_rating', 'manufacturing_partners', ['is_active', 'rating'])
    op.create_index('ix_partner_preferred', 'manufacturing_partners', ['is_preferred', 'rating'])
    op.create_index('ix_partner_pricing', 'manufacturing_partners', ['base_price_cents', 'turnaround_days'])
    op.create_index('ix_partner_performance', 'manufacturing_partners', ['rating', 'total_orders', 'successful_orders'])
    op.create_index('ix_manufacturing_partners_company_name', 'manufacturing_partners', ['company_name'])
    op.create_index('ix_manufacturing_partners_is_active', 'manufacturing_partners', ['is_active'])
    op.create_index('ix_manufacturing_partners_is_preferred', 'manufacturing_partners', ['is_preferred'])
    op.create_index('ix_manufacturing_partners_created_at', 'manufacturing_partners', ['created_at'])
    op.create_index('ix_manufacturing_partners_updated_at', 'manufacturing_partners', ['updated_at'])
    op.create_index('ix_manufacturing_partners_is_deleted', 'manufacturing_partners', ['is_deleted'])
    
    # Create indexes for qr_memorial_codes
    op.create_index('ix_qr_memorial_active', 'qr_memorial_codes', ['memorial_id', 'is_active'])
    op.create_index('ix_qr_order_status', 'qr_memorial_codes', ['order_status', 'order_placed_at'])
    op.create_index('ix_qr_billing', 'qr_memorial_codes', ['next_billing_date', 'subscription_tier'])
    op.create_index('ix_qr_analytics', 'qr_memorial_codes', ['total_scans', 'last_scan_at'])
    op.create_index('ix_qr_memorial_codes_memorial_id', 'qr_memorial_codes', ['memorial_id'])
    op.create_index('ix_qr_memorial_codes_manufacturing_partner_id', 'qr_memorial_codes', ['manufacturing_partner_id'])
    op.create_index('ix_qr_memorial_codes_aluminum_piece_order_id', 'qr_memorial_codes', ['aluminum_piece_order_id'])
    op.create_index('ix_qr_memorial_codes_is_active', 'qr_memorial_codes', ['is_active'])
    op.create_index('ix_qr_memorial_codes_order_status', 'qr_memorial_codes', ['order_status'])
    op.create_index('ix_qr_memorial_codes_created_at', 'qr_memorial_codes', ['created_at'])
    op.create_index('ix_qr_memorial_codes_updated_at', 'qr_memorial_codes', ['updated_at'])
    op.create_index('ix_qr_memorial_codes_is_deleted', 'qr_memorial_codes', ['is_deleted'])
    
    # Create indexes for qr_scan_events
    op.create_index('ix_scan_events_time', 'qr_scan_events', ['scanned_at', 'qr_code_id'])
    op.create_index('ix_scan_events_location', 'qr_scan_events', ['visitor_country', 'visitor_city'])
    op.create_index('ix_scan_events_device', 'qr_scan_events', ['device_type', 'browser_name'])
    op.create_index('ix_scan_events_engagement', 'qr_scan_events', ['session_duration_seconds', 'pages_visited'])
    op.create_index('ix_scan_events_source', 'qr_scan_events', ['scan_source', 'scanned_at'])
    op.create_index('ix_qr_scan_events_qr_code_id', 'qr_scan_events', ['qr_code_id'])
    op.create_index('ix_qr_scan_events_scanned_at', 'qr_scan_events', ['scanned_at'])
    op.create_index('ix_qr_scan_events_created_at', 'qr_scan_events', ['created_at'])
    op.create_index('ix_qr_scan_events_updated_at', 'qr_scan_events', ['updated_at'])
    op.create_index('ix_qr_scan_events_is_deleted', 'qr_scan_events', ['is_deleted'])
    
    # Set default values for new columns
    op.execute("UPDATE manufacturing_partners SET minimum_order_quantity = 1 WHERE minimum_order_quantity IS NULL")
    op.execute("UPDATE manufacturing_partners SET setup_fee_cents = 0 WHERE setup_fee_cents IS NULL")
    op.execute("UPDATE manufacturing_partners SET rush_order_fee_cents = 0 WHERE rush_order_fee_cents IS NULL")
    op.execute("UPDATE manufacturing_partners SET rating = 0.00 WHERE rating IS NULL")
    op.execute("UPDATE manufacturing_partners SET total_orders = 0 WHERE total_orders IS NULL")
    op.execute("UPDATE manufacturing_partners SET successful_orders = 0 WHERE successful_orders IS NULL")
    op.execute("UPDATE manufacturing_partners SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE manufacturing_partners SET is_preferred = false WHERE is_preferred IS NULL")
    op.execute("UPDATE manufacturing_partners SET supports_api = false WHERE supports_api IS NULL")
    
    op.execute("UPDATE qr_memorial_codes SET design_template = 'standard' WHERE design_template IS NULL")
    op.execute("UPDATE qr_memorial_codes SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE qr_memorial_codes SET order_status = 'pending' WHERE order_status IS NULL")
    op.execute("UPDATE qr_memorial_codes SET subscription_tier = 'basic' WHERE subscription_tier IS NULL")
    op.execute("UPDATE qr_memorial_codes SET annual_fee_cents = 1800 WHERE annual_fee_cents IS NULL")
    op.execute("UPDATE qr_memorial_codes SET total_scans = 0 WHERE total_scans IS NULL")
    
    op.execute("UPDATE qr_scan_events SET pages_visited = 1 WHERE pages_visited IS NULL")
    op.execute("UPDATE qr_scan_events SET bounce_rate = true WHERE bounce_rate IS NULL")
    op.execute("UPDATE qr_scan_events SET scan_source = 'gravesite' WHERE scan_source IS NULL")
    op.execute("UPDATE qr_scan_events SET tracking_consent = false WHERE tracking_consent IS NULL")


def downgrade() -> None:
    """Remove QR memorial tables."""
    
    # Drop indexes
    op.drop_index('ix_qr_scan_events_is_deleted', 'qr_scan_events')
    op.drop_index('ix_qr_scan_events_updated_at', 'qr_scan_events')
    op.drop_index('ix_qr_scan_events_created_at', 'qr_scan_events')
    op.drop_index('ix_qr_scan_events_scanned_at', 'qr_scan_events')
    op.drop_index('ix_qr_scan_events_qr_code_id', 'qr_scan_events')
    op.drop_index('ix_scan_events_source', 'qr_scan_events')
    op.drop_index('ix_scan_events_engagement', 'qr_scan_events')
    op.drop_index('ix_scan_events_device', 'qr_scan_events')
    op.drop_index('ix_scan_events_location', 'qr_scan_events')
    op.drop_index('ix_scan_events_time', 'qr_scan_events')
    
    op.drop_index('ix_qr_memorial_codes_is_deleted', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_updated_at', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_created_at', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_order_status', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_is_active', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_aluminum_piece_order_id', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_manufacturing_partner_id', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_codes_memorial_id', 'qr_memorial_codes')
    op.drop_index('ix_qr_analytics', 'qr_memorial_codes')
    op.drop_index('ix_qr_billing', 'qr_memorial_codes')
    op.drop_index('ix_qr_order_status', 'qr_memorial_codes')
    op.drop_index('ix_qr_memorial_active', 'qr_memorial_codes')
    
    op.drop_index('ix_manufacturing_partners_is_deleted', 'manufacturing_partners')
    op.drop_index('ix_manufacturing_partners_updated_at', 'manufacturing_partners')
    op.drop_index('ix_manufacturing_partners_created_at', 'manufacturing_partners')
    op.drop_index('ix_manufacturing_partners_is_preferred', 'manufacturing_partners')
    op.drop_index('ix_manufacturing_partners_is_active', 'manufacturing_partners')
    op.drop_index('ix_manufacturing_partners_company_name', 'manufacturing_partners')
    op.drop_index('ix_partner_performance', 'manufacturing_partners')
    op.drop_index('ix_partner_pricing', 'manufacturing_partners')
    op.drop_index('ix_partner_preferred', 'manufacturing_partners')
    op.drop_index('ix_partner_active_rating', 'manufacturing_partners')
    
    # Drop tables
    op.drop_table('qr_scan_events')
    op.drop_table('qr_memorial_codes')
    op.drop_table('manufacturing_partners')