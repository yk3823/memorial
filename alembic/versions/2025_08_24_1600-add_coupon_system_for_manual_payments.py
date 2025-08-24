"""add coupon system for manual payments

Revision ID: add_coupon_system_for_manual_payments
Revises: add_payment_table_for_paypal_integration
Create Date: 2025-08-24 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_coupon_system_for_manual_payments'
down_revision = 'add_payment_table_paypal'
branch_labels = None
depends_on = None


def upgrade():
    """Create coupon table and update user relationships."""
    
    # Create coupons table
    op.create_table('coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('payment_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_by_admin_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('used_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('office_payment_reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('subscription_months', sa.Integer(), nullable=False),
        sa.Column('max_memorials_granted', sa.Integer(), nullable=False),
        sa.Column('validation_ip', sa.String(length=45), nullable=True),
        sa.Column('validation_user_agent', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['used_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.CheckConstraint('payment_amount > 0', name='ck_coupon_payment_amount_positive'),
        sa.CheckConstraint('subscription_months > 0', name='ck_coupon_subscription_months_positive'),
        sa.CheckConstraint('max_memorials_granted > 0', name='ck_coupon_memorials_positive')
    )
    
    # Create indexes for performance
    op.create_index('ix_coupon_code', 'coupons', ['code'])
    op.create_index('ix_coupon_status_created', 'coupons', ['status', 'created_at'])
    op.create_index('ix_coupon_customer_name', 'coupons', ['customer_name'])
    op.create_index('ix_coupon_used_status', 'coupons', ['is_used', 'status'])
    op.create_index('ix_coupon_expires_status', 'coupons', ['expires_at', 'status'])
    op.create_index('ix_coupon_created_by_admin_id', 'coupons', ['created_by_admin_id'])
    op.create_index('ix_coupon_used_by_user_id', 'coupons', ['used_by_user_id'])
    
    # Set default values for existing records
    op.execute(
        sa.text(
            """
            UPDATE coupons SET 
                currency = 'ILS' WHERE currency IS NULL;
            """
        )
    )
    
    op.execute(
        sa.text(
            """
            UPDATE coupons SET 
                is_used = false WHERE is_used IS NULL;
            """
        )
    )
    
    op.execute(
        sa.text(
            """
            UPDATE coupons SET 
                status = 'active' WHERE status IS NULL;
            """
        )
    )
    
    op.execute(
        sa.text(
            """
            UPDATE coupons SET 
                subscription_months = 1 WHERE subscription_months IS NULL;
            """
        )
    )
    
    op.execute(
        sa.text(
            """
            UPDATE coupons SET 
                max_memorials_granted = 1 WHERE max_memorials_granted IS NULL;
            """
        )
    )
    
    op.execute(
        sa.text(
            """
            UPDATE coupons SET 
                is_deleted = false WHERE is_deleted IS NULL;
            """
        )
    )


def downgrade():
    """Drop coupon table and related indexes."""
    
    # Drop indexes
    op.drop_index('ix_coupon_used_by_user_id', table_name='coupons')
    op.drop_index('ix_coupon_created_by_admin_id', table_name='coupons')
    op.drop_index('ix_coupon_expires_status', table_name='coupons')
    op.drop_index('ix_coupon_used_status', table_name='coupons')
    op.drop_index('ix_coupon_customer_name', table_name='coupons')
    op.drop_index('ix_coupon_status_created', table_name='coupons')
    op.drop_index('ix_coupon_code', table_name='coupons')
    
    # Drop table
    op.drop_table('coupons')