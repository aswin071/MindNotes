# Testing IsPremiumUser Permission

## Quick Tests You Can Run

### Method 1: Django Shell (RECOMMENDED - Most Reliable)

```bash
cd mindnotesBackend
python manage.py shell
```

Then run this script:

```python
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription
from focus.models import FocusProgram
from core.services import FocusService
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Clean up any existing test users
User.objects.filter(email__contains='test_premium').delete()

# Create test users
print("\n" + "="*60)
print("🧪 TESTING ISPREMIUMUSER PERMISSION")
print("="*60 + "\n")

# 1. Free user
free_user = User.objects.create_user(
    email='test_premium_free@example.com',
    password='test123',
    first_name='Free', last_name='User'
)
Subscription.objects.create(
    user=free_user, plan='free', status='active'
)
print("✅ Created FREE user")

# 2. Pro user
pro_user = User.objects.create_user(
    email='test_premium_pro@example.com',
    password='test123',
    first_name='Pro', last_name='User'
)
Subscription.objects.create(
    user=pro_user, plan='pro_monthly', status='active',
    started_at=timezone.now(),
    expires_at=timezone.now() + timedelta(days=30)
)
print("✅ Created PRO user")

# 3. Expired user
expired_user = User.objects.create_user(
    email='test_premium_expired@example.com',
    password='test123',
    first_name='Expired', last_name='User'
)
Subscription.objects.create(
    user=expired_user, plan='pro_monthly', status='expired',
    started_at=timezone.now() - timedelta(days=60),
    expires_at=timezone.now() - timedelta(days=30)
)
print("✅ Created EXPIRED user\n")

# Get programs
free_program = FocusProgram.objects.filter(is_pro_only=False).first()
pro_program = FocusProgram.objects.filter(is_pro_only=True).first()

print("="*60)
print("📋 Testing Program Access")
print("="*60 + "\n")

# Test 1: Free user + Free program
print("Test 1: Free user enrolling in FREE program...")
try:
    result = FocusService.enroll_in_program(free_user, free_program.id)
    print(f"✅ PASSED: {result['message'] if 'message' in result else 'Enrolled successfully'}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")

# Test 2: Free user + Pro program (should fail)
print("\nTest 2: Free user enrolling in PRO program (should be blocked)...")
try:
    result = FocusService.enroll_in_program(free_user, pro_program.id)
    print(f"❌ FAILED: Free user should NOT be able to enroll in pro program")
except PermissionError as e:
    print(f"✅ PASSED: Correctly blocked - {str(e)}")
except Exception as e:
    print(f"❌ FAILED: Wrong error - {str(e)}")

# Test 3: Pro user + Free program
print("\nTest 3: Pro user enrolling in FREE program...")
try:
    result = FocusService.enroll_in_program(pro_user, free_program.id)
    print(f"✅ PASSED: {result['message'] if 'message' in result else 'Enrolled successfully'}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")

# Test 4: Pro user + Pro program
print("\nTest 4: Pro user enrolling in PRO program...")
try:
    result = FocusService.enroll_in_program(pro_user, pro_program.id)
    print(f"✅ PASSED: {result['message'] if 'message' in result else 'Enrolled successfully'}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")

# Test 5: Expired user + Pro program (should fail)
print("\nTest 5: Expired user enrolling in PRO program (should be blocked)...")
try:
    result = FocusService.enroll_in_program(expired_user, pro_program.id)
    print(f"❌ FAILED: Expired user should NOT be able to enroll in pro program")
except PermissionError as e:
    print(f"✅ PASSED: Correctly blocked - {str(e)}")
except Exception as e:
    print(f"❌ FAILED: Wrong error - {str(e)}")

# Test subscription.is_pro() method
print("\n" + "="*60)
print("🔍 Testing Subscription.is_pro() Method")
print("="*60 + "\n")

free_sub = Subscription.objects.get(user=free_user)
pro_sub = Subscription.objects.get(user=pro_user)
expired_sub = Subscription.objects.get(user=expired_user)

print(f"Free user is_pro(): {free_sub.is_pro()} (should be False)")
assert not free_sub.is_pro(), "Free user should NOT be pro"
print("✅ PASSED")

print(f"\nPro user is_pro(): {pro_sub.is_pro()} (should be True)")
assert pro_sub.is_pro(), "Pro user SHOULD be pro"
print("✅ PASSED")

print(f"\nExpired user is_pro(): {expired_sub.is_pro()} (should be False)")
assert not expired_sub.is_pro(), "Expired user should NOT be pro"
print("✅ PASSED")

# Test get_available_programs
print("\n" + "="*60)
print("📜 Testing Program List with can_access Flag")
print("="*60 + "\n")

print("Free user's available programs:")
free_programs = FocusService.get_available_programs(free_user)
for prog in free_programs:
    access = "✅ CAN ACCESS" if prog['can_access'] else "🔒 LOCKED"
    print(f"  - {prog['name']}: {access}")

print("\nPro user's available programs:")
pro_programs = FocusService.get_available_programs(pro_user)
for prog in pro_programs:
    access = "✅ CAN ACCESS" if prog['can_access'] else "🔒 LOCKED"
    print(f"  - {prog['name']}: {access}")

print("\n" + "="*60)
print("🎉 ALL TESTS COMPLETED!")
print("="*60)

# Cleanup
print("\n🧹 Cleaning up test users...")
free_user.delete()
pro_user.delete()
expired_user.delete()
print("✅ Cleanup complete\n")
```

### Method 2: REST API Test (if server is running)

Save this as `test_premium_api.sh` and run it:

```bash
#!/bin/bash

# Start server if not running
# python manage.py runserver &
# sleep 3

BASE_URL="http://localhost:8000/api/v1"

# 1. Create free user and get token
echo "Creating free user..."
FREE_TOKEN=$(python manage.py shell << 'PYTHONSCRIPT'
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
User.objects.filter(email='apifree@test.com').delete()

user = User.objects.create_user(
    email='apifree@test.com',
    password='test123'
)
Subscription.objects.create(user=user, plan='free', status='active')

refresh = RefreshToken.for_user(user)
print(str(refresh.access_token))
PYTHONSCRIPT
)

echo "Free user token: ${FREE_TOKEN:0:20}..."

# 2. List programs as free user
echo -e "\n📋 Listing programs as FREE user:"
curl -s -H "Authorization: Bearer $FREE_TOKEN" \
  $BASE_URL/focus/programs/ | python -m json.tool | grep -E "(name|can_access|is_pro_only)"

# 3. Try to enroll in pro program (should fail)
echo -e "\n🔒 Trying to enroll FREE user in PRO program (should fail):"
curl -s -X POST $BASE_URL/focus/programs/enroll/ \
  -H "Authorization: Bearer $FREE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"program_id":2}' | python -m json.tool
```

### Method 3: Unit Test (Direct Permission Class Test)

```bash
cd mindnotesBackend
python manage.py shell
```

```python
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from core.permissions import IsPremiumUser
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Clean up
User.objects.filter(email__contains='perm_test').delete()

# Create test users
free_user = User.objects.create_user(email='perm_test_free@test.com', password='test')
Subscription.objects.create(user=free_user, plan='free', status='active')

pro_user = User.objects.create_user(email='perm_test_pro@test.com', password='test')
Subscription.objects.create(
    user=pro_user, plan='pro_monthly', status='active',
    started_at=timezone.now(), expires_at=timezone.now() + timedelta(days=30)
)

# Create a dummy view for testing
class TestView(APIView):
    permission_classes = [IsPremiumUser]
    def post(self, request):
        return Response({'success': True})

# Create factory and view
factory = APIRequestFactory()
view = TestView.as_view()

print("\n" + "="*60)
print("🧪 Testing IsPremiumUser Permission Class Directly")
print("="*60 + "\n")

# Test 1: Free user (should be denied)
print("Test 1: Free user access (should be DENIED)...")
request = factory.post('/test/')
request.user = free_user
response = view(request)
if response.status_code == 403:
    print("✅ PASSED: Free user correctly denied")
else:
    print(f"❌ FAILED: Expected 403, got {response.status_code}")

# Test 2: Pro user (should be allowed)
print("\nTest 2: Pro user access (should be ALLOWED)...")
request = factory.post('/test/')
request.user = pro_user
response = view(request)
if response.status_code == 200:
    print("✅ PASSED: Pro user correctly allowed")
else:
    print(f"❌ FAILED: Expected 200, got {response.status_code}")

print("\n" + "="*60)
print("🎉 Direct permission tests complete!")
print("="*60 + "\n")

# Cleanup
free_user.delete()
pro_user.delete()
```

## Summary

The **IsPremiumUser** permission class works by:

1. Checking if user is authenticated
2. Getting their Subscription record
3. Calling `subscription.is_pro()` method which checks:
   - If plan is 'free' → returns False
   - If plan is pro and status is 'active' → checks expires_at
   - If status is 'trial' → checks trial_ends_at
   - Otherwise → returns False

This permission is used in:
- `EnrollProgramView` - via FocusService business logic
- Can be added to any view that needs premium access

**The most reliable test is Method 1 (Django Shell)** as it directly tests the service layer logic without HTTP layer complications.
