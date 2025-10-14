#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api/v1"

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}🧪 Testing IsPremiumUser Permission${NC}"
echo -e "${BLUE}=================================================${NC}\n"

# Check if server is running
echo -e "${YELLOW}Checking if server is running...${NC}"
if ! curl -s --head --request GET ${BASE_URL}/focus/programs/ > /dev/null; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo -e "${YELLOW}Please start the server with: python manage.py runserver${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}\n"

# Function to create test user
create_test_user() {
    local EMAIL=$1
    local PLAN=$2
    
    echo -e "${YELLOW}Creating test user: ${EMAIL} (${PLAN})...${NC}"
    
    python manage.py shell << PYTHONSCRIPT
from django.contrib.auth import get_user_model
from subscriptions.models import Subscription
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Delete if exists
User.objects.filter(email='${EMAIL}').delete()

# Create user
user = User.objects.create_user(
    email='${EMAIL}',
    password='testpass123',
    first_name='Test',
    last_name='User'
)

# Create subscription
if '${PLAN}' == 'free':
    Subscription.objects.create(
        user=user,
        plan='free',
        status='active'
    )
elif '${PLAN}' == 'pro':
    Subscription.objects.create(
        user=user,
        plan='pro_monthly',
        status='active',
        started_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=30)
    )
elif '${PLAN}' == 'expired':
    Subscription.objects.create(
        user=user,
        plan='pro_monthly',
        status='expired',
        started_at=timezone.now() - timedelta(days=60),
        expires_at=timezone.now() - timedelta(days=30)
    )

print(f"✅ Created user: ${EMAIL}")
PYTHONSCRIPT
}

# Function to get JWT token
get_token() {
    local EMAIL=$1
    
    TOKEN=$(curl -s -X POST ${BASE_URL}/authentication/login/ \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${EMAIL}\",\"password\":\"testpass123\"}" \
        | python -c "import sys, json; print(json.load(sys.stdin)['access'])" 2>/dev/null)
    
    echo "$TOKEN"
}

# Function to test enrollment
test_enrollment() {
    local USER_TYPE=$1
    local TOKEN=$2
    local PROGRAM_ID=$3
    local EXPECTED_STATUS=$4
    
    echo -e "\n${YELLOW}Testing ${USER_TYPE} enrollment in program ${PROGRAM_ID}...${NC}"
    
    RESPONSE=$(curl -s -X POST ${BASE_URL}/focus/programs/enroll/ \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"program_id\":${PROGRAM_ID}}")
    
    STATUS=$(echo $RESPONSE | python -c "import sys, json; r=json.load(sys.stdin); print(r.get('error', 'success'))" 2>/dev/null)
    
    if [ "$EXPECTED_STATUS" == "success" ]; then
        if [[ "$STATUS" == *"Pro subscription"* ]] || [[ "$STATUS" == *"error"* ]]; then
            echo -e "${RED}❌ FAILED: ${USER_TYPE} should be able to enroll${NC}"
            echo -e "${RED}   Response: ${STATUS}${NC}"
            return 1
        else
            echo -e "${GREEN}✅ PASSED: ${USER_TYPE} successfully enrolled${NC}"
            return 0
        fi
    else
        if [[ "$STATUS" == *"Pro subscription"* ]]; then
            echo -e "${GREEN}✅ PASSED: ${USER_TYPE} correctly blocked${NC}"
            return 0
        else
            echo -e "${RED}❌ FAILED: ${USER_TYPE} should be blocked${NC}"
            echo -e "${RED}   Response: ${STATUS}${NC}"
            return 1
        fi
    fi
}

# Create test users
echo -e "\n${BLUE}Step 1: Creating test users...${NC}"
create_test_user "test_free@example.com" "free"
create_test_user "test_pro@example.com" "pro"
create_test_user "test_expired@example.com" "expired"

# Get tokens
echo -e "\n${BLUE}Step 2: Getting authentication tokens...${NC}"
FREE_TOKEN=$(get_token "test_free@example.com")
PRO_TOKEN=$(get_token "test_pro@example.com")
EXPIRED_TOKEN=$(get_token "test_expired@example.com")

if [ -z "$FREE_TOKEN" ] || [ -z "$PRO_TOKEN" ] || [ -z "$EXPIRED_TOKEN" ]; then
    echo -e "${RED}❌ Failed to get authentication tokens${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Got all authentication tokens${NC}"

# Get program IDs
echo -e "\n${BLUE}Step 3: Getting program IDs...${NC}"
PROGRAMS=$(curl -s -H "Authorization: Bearer ${FREE_TOKEN}" ${BASE_URL}/focus/programs/)
FREE_PROGRAM_ID=$(echo $PROGRAMS | python -c "import sys, json; programs=json.load(sys.stdin); print(next((p['id'] for p in programs if not p['is_pro_only']), None))" 2>/dev/null)
PRO_PROGRAM_ID=$(echo $PROGRAMS | python -c "import sys, json; programs=json.load(sys.stdin); print(next((p['id'] for p in programs if p['is_pro_only']), None))" 2>/dev/null)

echo -e "${GREEN}✅ Free Program ID: ${FREE_PROGRAM_ID}${NC}"
echo -e "${GREEN}✅ Pro Program ID: ${PRO_PROGRAM_ID}${NC}"

# Run tests
echo -e "\n${BLUE}Step 4: Running permission tests...${NC}"
echo -e "${BLUE}=================================================${NC}"

PASSED=0
FAILED=0

# Test 1: Free user + Free program (should succeed)
if test_enrollment "Free user" "$FREE_TOKEN" "$FREE_PROGRAM_ID" "success"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 2: Free user + Pro program (should fail)
if test_enrollment "Free user" "$FREE_TOKEN" "$PRO_PROGRAM_ID" "blocked"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 3: Pro user + Free program (should succeed)
if test_enrollment "Pro user" "$PRO_TOKEN" "$FREE_PROGRAM_ID" "success"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 4: Pro user + Pro program (should succeed)
if test_enrollment "Pro user" "$PRO_TOKEN" "$PRO_PROGRAM_ID" "success"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 5: Expired user + Pro program (should fail)
if test_enrollment "Expired user" "$EXPIRED_TOKEN" "$PRO_PROGRAM_ID" "blocked"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 6: No token (should fail)
echo -e "\n${YELLOW}Testing unauthenticated access...${NC}"
UNAUTH_RESPONSE=$(curl -s -X POST ${BASE_URL}/focus/programs/enroll/ \
    -H "Content-Type: application/json" \
    -d "{\"program_id\":${PRO_PROGRAM_ID}}")

if [[ "$UNAUTH_RESPONSE" == *"credentials"* ]] || [[ "$UNAUTH_RESPONSE" == *"Authentication"* ]]; then
    echo -e "${GREEN}✅ PASSED: Unauthenticated user correctly blocked${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAILED: Unauthenticated user should be blocked${NC}"
    ((FAILED++))
fi

# Summary
echo -e "\n${BLUE}=================================================${NC}"
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}✅ Passed: ${PASSED}${NC}"
echo -e "${RED}❌ Failed: ${FAILED}${NC}"
echo -e "${BLUE}=================================================${NC}\n"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ IsPremiumUser permission is working perfectly!${NC}\n"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}\n"
    exit 1
fi
