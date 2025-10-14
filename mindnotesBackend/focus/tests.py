from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from subscriptions.models import Subscription
from focus.models import FocusProgram

User = get_user_model()


class PremiumPermissionTest(APITestCase):
    """Test IsPremiumUser permission for Focus Programs"""

    def setUp(self):
        """Set up test data"""
        # Create test users
        self.free_user = User.objects.create_user(
            email='free@example.com',
            password='testpass123',
            first_name='Free',
            last_name='User'
        )

        self.pro_user = User.objects.create_user(
            email='pro@example.com',
            password='testpass123',
            first_name='Pro',
            last_name='User'
        )

        self.expired_user = User.objects.create_user(
            email='expired@example.com',
            password='testpass123',
            first_name='Expired',
            last_name='User'
        )

        # Create subscriptions
        # Free user (default free subscription)
        Subscription.objects.create(
            user=self.free_user,
            plan='free',
            status='active'
        )

        # Pro user (active subscription)
        Subscription.objects.create(
            user=self.pro_user,
            plan='pro_monthly',
            status='active',
            started_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Expired user (subscription expired)
        Subscription.objects.create(
            user=self.expired_user,
            plan='pro_monthly',
            status='expired',
            started_at=timezone.now() - timedelta(days=60),
            expires_at=timezone.now() - timedelta(days=30)
        )

        # Create test programs
        self.free_program = FocusProgram.objects.create(
            name='14-Day Focus Challenge',
            program_type='14_day',
            description='Free program',
            duration_days=14,
            objectives=['Test objective'],
            is_pro_only=False,
            order=1
        )

        self.pro_program = FocusProgram.objects.create(
            name='30-Day Focus Mastery',
            program_type='30_day',
            description='Pro program',
            duration_days=30,
            objectives=['Test objective'],
            is_pro_only=True,
            order=2
        )

    def test_free_user_can_access_free_program(self):
        """Free user should be able to enroll in free programs"""
        self.client.force_authenticate(user=self.free_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.free_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['enrolled'])
        print("✅ Test 1 PASSED: Free user can access free program")

    def test_free_user_cannot_access_pro_program(self):
        """Free user should NOT be able to enroll in pro programs"""
        self.client.force_authenticate(user=self.free_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Pro subscription', response.data['error'])
        print("✅ Test 2 PASSED: Free user blocked from pro program")

    def test_pro_user_can_access_free_program(self):
        """Pro user should be able to enroll in free programs"""
        self.client.force_authenticate(user=self.pro_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.free_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['enrolled'])
        print("✅ Test 3 PASSED: Pro user can access free program")

    def test_pro_user_can_access_pro_program(self):
        """Pro user should be able to enroll in pro programs"""
        self.client.force_authenticate(user=self.pro_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['enrolled'])
        print("✅ Test 4 PASSED: Pro user can access pro program")

    def test_expired_user_cannot_access_pro_program(self):
        """Expired subscription user should NOT be able to enroll in pro programs"""
        self.client.force_authenticate(user=self.expired_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Pro subscription', response.data['error'])
        print("✅ Test 5 PASSED: Expired user blocked from pro program")

    def test_unauthenticated_user_blocked(self):
        """Unauthenticated user should be blocked"""
        # No authentication
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print("✅ Test 6 PASSED: Unauthenticated user blocked")

    def test_program_list_shows_can_access_flag(self):
        """Program list should show can_access flag based on subscription"""
        url = '/api/v1/focus/programs/'
        
        # Free user
        self.client.force_authenticate(user=self.free_user)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programs = response.data
        free_prog = next(p for p in programs if p['id'] == self.free_program.id)
        pro_prog = next(p for p in programs if p['id'] == self.pro_program.id)
        
        self.assertTrue(free_prog['can_access'])
        self.assertFalse(pro_prog['can_access'])
        print("✅ Test 7 PASSED: Free user sees correct can_access flags")
        
        # Pro user
        self.client.force_authenticate(user=self.pro_user)
        response = self.client.get(url)
        
        programs = response.data
        free_prog = next(p for p in programs if p['id'] == self.free_program.id)
        pro_prog = next(p for p in programs if p['id'] == self.pro_program.id)
        
        self.assertTrue(free_prog['can_access'])
        self.assertTrue(pro_prog['can_access'])
        print("✅ Test 8 PASSED: Pro user sees correct can_access flags")

    def test_subscription_is_pro_method(self):
        """Test the Subscription.is_pro() method"""
        free_sub = Subscription.objects.get(user=self.free_user)
        pro_sub = Subscription.objects.get(user=self.pro_user)
        expired_sub = Subscription.objects.get(user=self.expired_user)
        
        self.assertFalse(free_sub.is_pro())
        self.assertTrue(pro_sub.is_pro())
        self.assertFalse(expired_sub.is_pro())
        print("✅ Test 9 PASSED: Subscription.is_pro() works correctly")


class PremiumPermissionEdgeCasesTest(APITestCase):
    """Test edge cases for premium permissions"""

    def setUp(self):
        """Set up edge case test data"""
        # User with no subscription record
        self.no_sub_user = User.objects.create_user(
            email='nosub@example.com',
            password='testpass123',
            first_name='No',
            last_name='Sub'
        )

        # User with trial subscription
        self.trial_user = User.objects.create_user(
            email='trial@example.com',
            password='testpass123',
            first_name='Trial',
            last_name='User'
        )
        Subscription.objects.create(
            user=self.trial_user,
            plan='pro_monthly',
            status='trial',
            trial_started_at=timezone.now(),
            trial_ends_at=timezone.now() + timedelta(days=7)
        )

        # User with expired trial
        self.expired_trial_user = User.objects.create_user(
            email='expiredtrial@example.com',
            password='testpass123',
            first_name='Expired',
            last_name='Trial'
        )
        Subscription.objects.create(
            user=self.expired_trial_user,
            plan='pro_monthly',
            status='trial',
            trial_started_at=timezone.now() - timedelta(days=14),
            trial_ends_at=timezone.now() - timedelta(days=7)
        )

        # Pro program
        self.pro_program = FocusProgram.objects.create(
            name='30-Day Focus Mastery',
            program_type='30_day',
            description='Pro program',
            duration_days=30,
            objectives=['Test objective'],
            is_pro_only=True
        )

    def test_user_with_no_subscription_blocked(self):
        """User with no subscription record should be blocked from pro programs"""
        self.client.force_authenticate(user=self.no_sub_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("✅ Test 10 PASSED: User with no subscription blocked")

    def test_trial_user_can_access_pro_program(self):
        """User with active trial should be able to access pro programs"""
        self.client.force_authenticate(user=self.trial_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print("✅ Test 11 PASSED: Active trial user can access pro program")

    def test_expired_trial_user_blocked(self):
        """User with expired trial should be blocked from pro programs"""
        self.client.force_authenticate(user=self.expired_trial_user)
        
        url = '/api/v1/focus/programs/enroll/'
        data = {'program_id': self.pro_program.id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("✅ Test 12 PASSED: Expired trial user blocked from pro program")
