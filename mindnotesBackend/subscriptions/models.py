from django.db import models
from django.utils import timezone
from authentication.models import User
from utils.model_abstracts import Model


class Subscription(Model):
    """User subscription management"""

    PLAN_CHOICES = [
        ('free', 'Free Plan'),
        ('pro_monthly', 'Pro Monthly'),
        ('pro_yearly', 'Pro Yearly'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('trial', 'Trial'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='free'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Subscription dates
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    # Trial information
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    # Payment information
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    # Billing
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    # Auto-renewal
    auto_renew = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.plan}"

    def is_pro(self):
        """Check if user has active pro subscription"""
        if self.plan == 'free':
            return False

        if self.status == 'active':
            # Check if subscription hasn't expired
            if self.expires_at:
                return timezone.now() < self.expires_at
            return True

        if self.status == 'trial':
            # Check if trial hasn't expired
            if self.trial_ends_at:
                return timezone.now() < self.trial_ends_at

        return False

    def get_plan_display_name(self):
        """Get user-friendly plan name"""
        return dict(self.PLAN_CHOICES).get(self.plan, 'Free Plan')

    def days_until_expiry(self):
        """Calculate days until subscription expires"""
        if not self.expires_at:
            return None

        delta = self.expires_at - timezone.now()
        return max(0, delta.days)


class SubscriptionFeature(Model):
    """Define features available for each plan"""

    PLAN_TYPES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
    ]

    plan = models.CharField(max_length=20, choices=PLAN_TYPES)
    feature_key = models.CharField(max_length=100)
    feature_name = models.CharField(max_length=255)
    feature_value = models.JSONField(default=dict)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscription_features'
        unique_together = ['plan', 'feature_key']
        ordering = ['plan', 'feature_key']

    def __str__(self):
        return f"{self.plan} - {self.feature_name}"


class PaymentHistory(Model):
    """Track payment transactions"""

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_history'
    )

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)

    # Payment gateway info
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)

    # Transaction metadata
    description = models.TextField(blank=True)
    invoice_url = models.URLField(blank=True)
    receipt_url = models.URLField(blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payment_history'
        verbose_name_plural = 'Payment histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} - {self.status}"
