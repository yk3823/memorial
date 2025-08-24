"""
Payment API endpoints for Memorial Website PayPal integration.
Handles payment creation, execution, cancellation, and history.
"""

import logging
import uuid
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.deps import (
    get_db,
    get_current_user,
    get_current_active_user,
    get_client_ip
)
from app.core.config import get_settings
from app.services.payment import PaymentService, PaymentError, get_payment_service
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentExecuteRequest,
    PaymentExecuteResponse,
    PaymentCancelRequest,
    PaymentCancelResponse,
    PaymentResponse,
    PaymentListResponse,
    PaymentStatusResponse,
    PaymentSummaryResponse,
    PaymentAmountInfo,
    PaymentMethodInfo,
    PaymentErrorResponse,
    PayPalWebhookEvent,
    PayPalWebhookResponse
)
from app.models.user import User
from app.models.payment import Payment

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/payment", tags=["Payment"])

# Settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


# Payment Information Endpoints

@router.get(
    "/info/amount",
    response_model=PaymentAmountInfo,
    summary="Get payment amount information",
    description="Get standard payment amount and pricing details."
)
async def get_payment_amount_info() -> PaymentAmountInfo:
    """Get payment amount and pricing information."""
    return PaymentAmountInfo(
        standard_amount=100.00,
        currency="ILS",
        formatted_amount="₪100.00",
        description="אתר הנצחה - מנוי חודשי",
        subscription_duration_months=1,
        memorial_allowance=1
    )


@router.get(
    "/info/methods",
    response_model=PaymentMethodInfo,
    summary="Get payment method information",
    description="Get available payment methods and configuration."
)
async def get_payment_methods_info() -> PaymentMethodInfo:
    """Get available payment methods information."""
    return PaymentMethodInfo(
        paypal_enabled=settings.PAYPAL_ENABLED,
        coupon_enabled=True,
        supported_currencies=["ILS", "USD", "EUR"],
        minimum_amount=1.00,
        maximum_amount=10000.00
    )


# Payment Operations

@router.post(
    "/create",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new payment",
    description="Create a new payment for subscription activation."
)
@limiter.limit("5/minute")  # Limit payment creation attempts
async def create_payment(
    request: Request,
    payment_data: PaymentCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
    client_ip: Annotated[str, Depends(get_client_ip)]
) -> PaymentCreateResponse:
    """
    Create a new payment for subscription.
    
    - **amount**: Payment amount (default: 100 ILS)
    - **currency**: Currency code (ILS, USD, EUR)
    - **description**: Payment description
    - **coupon_code**: Optional coupon for manual payments
    - **success_url**: Custom success redirect URL
    - **cancel_url**: Custom cancel redirect URL
    
    Returns payment details and PayPal approval URL.
    """
    try:
        logger.info(f"Payment creation request from user {current_user.id}: {payment_data.amount} {payment_data.currency}")
        
        # Check if user is verified
        if not current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email must be verified before making payment"
            )
        
        # Set default URLs if not provided
        base_url = settings.BASE_URL
        success_url = payment_data.success_url or f"{base_url}/payment/success"
        cancel_url = payment_data.cancel_url or f"{base_url}/payment/cancel"
        
        # Create payment
        payment = await payment_service.create_payment(
            db=db,
            user_id=current_user.id,
            amount=payment_data.amount,
            currency=payment_data.currency.value,
            description=payment_data.description,
            success_url=success_url,
            cancel_url=cancel_url,
            coupon_code=payment_data.coupon_code
        )
        
        # Set client information
        payment.client_ip = client_ip
        payment.user_agent = request.headers.get("user-agent")
        await db.commit()
        
        # Get approval URL for PayPal payments
        approval_url = None
        requires_approval = True
        
        if payment.is_paypal_payment:
            approval_url = payment_service.get_approval_url(payment)
        elif payment.is_coupon_payment:
            requires_approval = False  # Coupon payments don't need approval
        
        # Convert to response schema
        payment_response = PaymentResponse.model_validate(payment)
        
        logger.info(f"Payment created successfully: {payment.id}")
        
        return PaymentCreateResponse(
            success=True,
            message="Payment created successfully. Please complete the payment process.",
            payment=payment_response,
            approval_url=approval_url,
            requires_approval=requires_approval
        )
        
    except PaymentError as e:
        logger.warning(f"Payment creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment creation failed"
        )


@router.post(
    "/execute",
    response_model=PaymentExecuteResponse,
    summary="Execute PayPal payment",
    description="Execute PayPal payment after user approval."
)
@limiter.limit("10/minute")  # Limit execution attempts
async def execute_payment(
    request: Request,
    execute_data: PaymentExecuteRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
) -> PaymentExecuteResponse:
    """
    Execute PayPal payment after user approval.
    
    - **payment_id**: Database payment ID
    - **paypal_payment_id**: PayPal payment ID
    - **payer_id**: PayPal payer ID
    
    Completes the payment and activates user subscription.
    """
    try:
        logger.info(f"Payment execution request from user {current_user.id}: {execute_data.payment_id}")
        
        # Execute payment
        payment = await payment_service.execute_payment(
            db=db,
            payment_id=execute_data.payment_id,
            paypal_payment_id=execute_data.paypal_payment_id,
            payer_id=execute_data.payer_id
        )
        
        # Verify payment belongs to current user
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only execute your own payments"
            )
        
        # Convert to response schema
        payment_response = PaymentResponse.model_validate(payment)
        
        logger.info(f"Payment executed successfully: {payment.id}")
        
        return PaymentExecuteResponse(
            success=True,
            message="Payment completed successfully! Your subscription is now active.",
            payment=payment_response,
            subscription_activated=payment.is_completed()
        )
        
    except PaymentError as e:
        logger.warning(f"Payment execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment execution failed"
        )


@router.post(
    "/cancel",
    response_model=PaymentCancelResponse,
    summary="Cancel payment",
    description="Cancel a pending payment."
)
async def cancel_payment(
    cancel_data: PaymentCancelRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
) -> PaymentCancelResponse:
    """
    Cancel a pending payment.
    
    - **payment_id**: Payment ID to cancel
    - **reason**: Cancellation reason
    """
    try:
        logger.info(f"Payment cancellation request from user {current_user.id}: {cancel_data.payment_id}")
        
        # Get payment first to verify ownership
        payment = await payment_service.get_payment(db, cancel_data.payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Verify payment belongs to current user
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own payments"
            )
        
        # Cancel payment
        payment = await payment_service.cancel_payment(
            db=db,
            payment_id=cancel_data.payment_id,
            reason=cancel_data.reason
        )
        
        # Convert to response schema
        payment_response = PaymentResponse.model_validate(payment)
        
        logger.info(f"Payment cancelled successfully: {payment.id}")
        
        return PaymentCancelResponse(
            success=True,
            message="Payment cancelled successfully.",
            payment=payment_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment cancellation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment cancellation failed"
        )


# Payment Query Endpoints

@router.get(
    "/status/{payment_id}",
    response_model=PaymentStatusResponse,
    summary="Get payment status",
    description="Get current status of a specific payment."
)
async def get_payment_status(
    payment_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
) -> PaymentStatusResponse:
    """Get payment status by ID."""
    try:
        payment = await payment_service.get_payment(db, payment_id)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Verify payment belongs to current user (or user is admin)
        if payment.user_id != current_user.id and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Convert to response schema
        payment_response = PaymentResponse.model_validate(payment)
        
        return PaymentStatusResponse(
            success=True,
            message="Payment status retrieved successfully",
            payment=payment_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get payment status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment status"
        )


@router.get(
    "/history",
    response_model=PaymentListResponse,
    summary="Get payment history",
    description="Get user's payment history with pagination."
)
async def get_payment_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
) -> PaymentListResponse:
    """Get user's payment history."""
    try:
        offset = (page - 1) * per_page
        
        payments = await payment_service.get_user_payments(
            db=db,
            user_id=current_user.id,
            limit=per_page,
            offset=offset
        )
        
        # Get total count for pagination
        # This is a simplified version - in production you'd want a proper count query
        all_payments = await payment_service.get_user_payments(
            db=db,
            user_id=current_user.id,
            limit=1000,  # Large number to get all
            offset=0
        )
        total_count = len(all_payments)
        
        # Convert to response schemas
        payment_responses = [PaymentResponse.model_validate(p) for p in payments]
        
        has_next = (offset + per_page) < total_count
        has_prev = page > 1
        
        return PaymentListResponse(
            success=True,
            message="Payment history retrieved successfully",
            payments=payment_responses,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Get payment history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment history"
        )


@router.get(
    "/summary",
    response_model=PaymentSummaryResponse,
    summary="Get payment summary",
    description="Get user's payment summary and subscription status."
)
async def get_payment_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
) -> PaymentSummaryResponse:
    """Get user's payment summary."""
    try:
        # Get all user payments
        payments = await payment_service.get_user_payments(
            db=db,
            user_id=current_user.id,
            limit=1000,  # Get all payments
            offset=0
        )
        
        # Calculate summary statistics
        total_payments = len(payments)
        completed_payments = sum(1 for p in payments if p.is_completed())
        total_amount_paid = sum(p.amount for p in payments if p.is_completed())
        
        # Get latest payment
        latest_payment = None
        if payments:
            latest_payment = PaymentResponse.model_validate(payments[0])
        
        return PaymentSummaryResponse(
            success=True,
            message="Payment summary retrieved successfully",
            total_payments=total_payments,
            completed_payments=completed_payments,
            total_amount_paid=total_amount_paid,
            last_payment=latest_payment,
            has_active_subscription=current_user.is_subscription_active()
        )
        
    except Exception as e:
        logger.error(f"Get payment summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment summary"
        )


# PayPal Webhook Endpoint

@router.post(
    "/webhook/paypal",
    response_model=PayPalWebhookResponse,
    summary="PayPal webhook handler",
    description="Handle PayPal webhook notifications for payment events."
)
async def paypal_webhook(
    webhook_event: PayPalWebhookEvent,
    db: Annotated[AsyncSession, Depends(get_db)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
) -> PayPalWebhookResponse:
    """
    Handle PayPal webhook notifications.
    
    This endpoint receives notifications from PayPal about payment events
    such as payment completion, cancellation, or refunds.
    """
    try:
        logger.info(f"PayPal webhook received: {webhook_event.event_type}")
        
        # For now, just log the webhook - full implementation would handle
        # specific event types like PAYMENT.SALE.COMPLETED
        
        # In a full implementation, you would:
        # 1. Verify the webhook signature
        # 2. Parse the event type and resource
        # 3. Update payment status in database
        # 4. Send notifications if needed
        
        return PayPalWebhookResponse(
            success=True,
            message="Webhook processed successfully",
            processed_event_id=webhook_event.id
        )
        
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


# Error Handler for Payment Errors

# Exception handlers are registered in the main app, not on routers
# This function can be used by the main app to register the handler
async def payment_error_handler(request: Request, exc: PaymentError):
    """Handle PaymentError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=PaymentErrorResponse(
            success=False,
            message=str(exc),
            error_code="PAYMENT_ERROR"
        ).model_dump()
    )