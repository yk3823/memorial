"""add_payment_table_for_paypal_integration

Revision ID: add_payment_table_paypal
Revises: 78df446128e1
Create Date: 2025-08-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_payment_table_paypal'
down_revision = '78df446128e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema - Add payment table for PayPal integration."""
    
    # Create payments table
    op.create_table('payments',
        # Base model fields
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Primary key UUID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last update timestamp'),
        
        # User relationship
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='ID of the user making the payment'),
        
        # Payment identification
        sa.Column('payment_id', sa.String(length=100), nullable=True, comment='PayPal payment ID'),
        sa.Column('order_id', sa.String(length=100), nullable=True, comment='PayPal order ID'),
        
        # Payment details
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False, comment='Payment amount'),
        sa.Column('currency', sa.String(length=3), nullable=False, default='ILS', comment='Currency code (ILS, USD, EUR)'),
        sa.Column('description', sa.String(length=500), nullable=False, default='Memorial Website Subscription', comment='Payment description'),
        
        # Payment method and status
        sa.Column('payment_method', sa.String(length=20), nullable=False, default='paypal', comment='Payment method used'),
        sa.Column('status', sa.String(length=20), nullable=False, default='pending', comment='Payment status'),
        
        # PayPal specific fields
        sa.Column('paypal_payer_id', sa.String(length=100), nullable=True, comment='PayPal payer ID'),
        sa.Column('paypal_payer_email', sa.String(length=255), nullable=True, comment='PayPal payer email'),
        sa.Column('paypal_transaction_id', sa.String(length=100), nullable=True, comment='PayPal transaction ID'),
        
        # Coupon handling (for manual payments)
        sa.Column('coupon_code', sa.String(length=50), nullable=True, comment='Coupon code used (for manual office payments)'),
        
        # Processing timestamps
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True, comment='When the payment was processed'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='When the payment was completed'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='When the payment approval expires'),
        
        # Error handling
        sa.Column('error_code', sa.String(length=50), nullable=True, comment='Error code if payment failed'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Detailed error message if payment failed'),
        
        # Metadata for audit trail
        sa.Column('client_ip', sa.String(length=45), nullable=True, comment='Client IP address when payment was initiated'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='User agent when payment was initiated'),
        
        # PayPal webhook data (stored as JSON)
        sa.Column('webhook_data', sa.Text(), nullable=True, comment='PayPal webhook notification data (JSON)'),
        
        # Subscription management
        sa.Column('subscription_months', sa.Integer(), nullable=False, default=1, comment='Number of subscription months purchased'),
        sa.Column('max_memorials_granted', sa.Integer(), nullable=False, default=1, comment='Number of memorials granted with this payment'),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for performance
    op.create_index('ix_payment_user_status', 'payments', ['user_id', 'status'])
    op.create_index('ix_payment_method_status', 'payments', ['payment_method', 'status'])
    op.create_index('ix_payment_created_status', 'payments', ['created_at', 'status'])
    op.create_index('ix_payment_paypal_ids', 'payments', ['payment_id', 'order_id', 'paypal_transaction_id'])
    op.create_index('ix_payment_currency_amount', 'payments', ['currency', 'amount'])
    
    # Create unique indexes
    op.create_index('ix_payment_payment_id_unique', 'payments', ['payment_id'], unique=True)
    op.create_index('ix_payment_order_id_unique', 'payments', ['order_id'], unique=True)
    op.create_index('ix_payment_paypal_transaction_id', 'payments', ['paypal_transaction_id'])


def downgrade() -> None:
    """Downgrade database schema - Remove payment table."""
    
    # Drop indexes
    op.drop_index('ix_payment_paypal_transaction_id', table_name='payments')
    op.drop_index('ix_payment_order_id_unique', table_name='payments')
    op.drop_index('ix_payment_payment_id_unique', table_name='payments')
    op.drop_index('ix_payment_currency_amount', table_name='payments')
    op.drop_index('ix_payment_paypal_ids', table_name='payments')
    op.drop_index('ix_payment_created_status', table_name='payments')
    op.drop_index('ix_payment_method_status', table_name='payments')
    op.drop_index('ix_payment_user_status', table_name='payments')
    
    # Drop table
    op.drop_table('payments')