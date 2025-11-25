# Technical Documentation - AI Personalization System

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [API Reference](#api-reference)
6. [AI Algorithm Details](#ai-algorithm-details)
7. [Testing Guide](#testing-guide)
8. [Deployment](#deployment)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ UserProfile  │  │ ExercisePage │  │   Navbar     │ │
│  │    Form      │  │  (Display)   │  │  (Links)     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘ │
│         │                  │                            │
└─────────┼──────────────────┼────────────────────────────┘
          │                  │
          │ HTTP POST/GET    │ HTTP POST
          │                  │
┌─────────▼──────────────────▼────────────────────────────┐
│                    Backend (FastAPI)                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │             API Endpoints                         │  │
│  │  • POST /api/profile/update                      │  │
│  │  • GET  /api/profile/me                          │  │
│  │  • POST /api/personalized-params                 │  │
│  └──────────┬───────────────────────────────────────┘  │
│             │                                            │
│  ┌──────────▼───────────────────────────────────────┐  │
│  │       AI Personalization Engine                   │  │
│  │  ┌────────────────────┐  ┌────────────────────┐ │  │
│  │  │ BiometricFeatures  │  │ Personalization    │ │  │
│  │  │ - calculate_bmi()  │  │ - calculate_...()  │ │  │
│  │  │ - extract_...()    │  │ - apply_...()      │ │  │
│  │  └────────────────────┘  └────────────────────┘ │  │
│  └──────────┬───────────────────────────────────────┘  │
│             │                                            │
│  ┌──────────▼───────────────────────────────────────┐  │
│  │            SQLite Database                        │  │
│  │  • users (biometric data)                        │  │
│  │  • user_exercise_limits (personalized params)   │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### **users Table (Updated)**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('patient', 'doctor')),
    full_name TEXT,
    
    -- Biometric Data
    age INTEGER,
    gender TEXT CHECK(gender IN ('male', 'female', 'other')),
    height_cm REAL,
    weight_kg REAL,
    bmi REAL,
    
    -- Medical Data
    medical_conditions TEXT,  -- JSON array: ["knee_arthritis", "diabetes"]
    injury_type TEXT,
    mobility_level TEXT CHECK(mobility_level IN ('beginner', 'intermediate', 'advanced')),
    pain_level INTEGER CHECK(pain_level BETWEEN 0 AND 10),
    doctor_notes TEXT,
    contraindicated_exercises TEXT,  -- JSON array
    
    created_at TEXT NOT NULL,
    doctor_id INTEGER,
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);
```

### **user_exercise_limits Table (New)**
```sql
CREATE TABLE user_exercise_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_type TEXT NOT NULL,
    
    -- Personalized Parameters
    max_depth_angle REAL,        -- For squat: down angle
    min_raise_angle REAL,        -- For arm_raise: up angle
    max_reps_per_set INTEGER,
    recommended_rest_seconds INTEGER,
    
    -- AI Scores
    difficulty_score REAL,       -- 0-1: how easy the exercise is
    injury_risk_score REAL,      -- 0-1: injury risk (future use)
    
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### **Example Data**
```sql
-- User with biometric data
INSERT INTO users VALUES (
    1, 'patient1', '<hash>', 'patient', 'Nguyễn Văn A',
    72, 'female', 155, 58, 24.1,
    '["knee_arthritis", "osteoporosis"]',
    NULL, 'beginner', 4, NULL, NULL,
    '2025-01-01T00:00:00', NULL
);

-- Personalized parameters
INSERT INTO user_exercise_limits VALUES (
    1, 1, 'squat',
    125.0, 160.0, 8, 60,
    0.49, 0.0,
    '2025-01-01T00:00:00', '2025-01-01T00:00:00'
);
```

---

## Backend Implementation

### **File Structure**
```
backend/
├── main.py                              # Main FastAPI app
├── ai_models/
│   ├── __init__.py
│   ├── feature_engineering.py           # Biometric feature extraction
│   └── personalization_engine.py        # AI personalization logic
└── rehab_v3.db                          # SQLite database
```

### **1. Feature Engineering (`feature_engineering.py`)**

```python
class BiometricFeatures:
    """Extract features from user biometric data"""
    
    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """
        BMI = weight (kg) / (height (m))^2
        """
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    
    @staticmethod
    def get_age_category(age: int) -> str:
        """
        Categorize age:
        - young: 18-40
        - middle: 41-60
        - senior: 61-75
        - elderly: 76+
        """
        if age <= 40: return "young"
        elif age <= 60: return "middle"
        elif age <= 75: return "senior"
        else: return "elderly"
    
    @staticmethod
    def extract_features(user_data: Dict) -> Dict:
        """
        Extract comprehensive feature vector
        
        Returns:
            {
                'age': int,
                'bmi': float,
                'age_category': str,
                'bmi_category': str,
                'gender_encoded': float,
                'has_knee_issues': int (0/1),
                'has_shoulder_issues': int (0/1),
                'has_back_issues': int (0/1),
                'mobility_level_encoded': int (0/1/2),
                'pain_level': int (0-10),
                ...
            }
        """
```

**Key Functions:**
- `calculate_bmi()`: WHO standard BMI formula
- `get_age_category()`: Age grouping for factor calculation
- `get_bmi_category()`: WHO BMI classification
- `extract_features()`: Complete feature extraction pipeline

### **2. Personalization Engine (`personalization_engine.py`)**

```python
class PersonalizationEngine:
    """AI engine for personalized exercise parameters"""
    
    def __init__(self):
        # Baseline thresholds for healthy young adults
        self.baseline_thresholds = {
            'squat': {
                'down_angle': 90,
                'up_angle': 160,
                'max_reps': 20,
                'rest_seconds': 30,
            },
            # ... other exercises
        }
    
    def calculate_personalized_params(
        self, 
        user_data: Dict, 
        exercise_type: str
    ) -> Dict:
        """
        Main calculation pipeline:
        1. Extract features
        2. Calculate 5 factors
        3. Combine factors
        4. Apply adjustments
        5. Generate warnings/recommendations
        """
```

**Factor Calculation Methods:**
```python
def _calculate_age_factor(self, age: int) -> float:
    """
    Age adjustment factor (0.5 - 1.0)
    - 18-40: 1.0 (normal)
    - 41-60: 0.85 (15% easier)
    - 61-75: 0.70 (30% easier)
    - 76+: 0.50 (50% easier)
    """

def _calculate_bmi_factor(self, bmi: float) -> float:
    """
    BMI adjustment factor (0.7 - 1.0)
    - <18.5: 0.90
    - 18.5-24.9: 1.0
    - 25-29.9: 0.85
    - 30+: 0.70
    """

def _calculate_medical_factor(
    self, 
    features: Dict, 
    exercise_type: str
) -> float:
    """
    Medical condition adjustment
    - knee_issues for squat: 0.70
    - shoulder_issues for arm_raise: 0.70
    - back_issues for squat: 0.80
    """

def _calculate_mobility_factor(
    self, 
    mobility_encoded: int
) -> float:
    """
    Mobility level adjustment
    - beginner (0): 0.70
    - intermediate (1): 0.85
    - advanced (2): 1.0
    """

def _calculate_pain_factor(self, pain_level: int) -> float:
    """
    Pain level adjustment (0.5 - 1.0)
    - 0-2: 1.0
    - 3-5: 0.85
    - 6-8: 0.70
    - 9-10: 0.50
    """
```

**Combined Factor Formula:**
```python
combined_factor = (
    age_factor * 0.30 +      # Age: 30% weight
    bmi_factor * 0.20 +      # BMI: 20% weight
    medical_factor * 0.25 +  # Medical: 25% weight
    mobility_factor * 0.15 + # Mobility: 15% weight
    pain_factor * 0.10       # Pain: 10% weight
)
```

**Angle Adjustment Formula (Squat):**
```python
# Baseline: down = 90°, up = 160°
# Lower factor = easier = less deep squat (higher angle)

adjusted_down_angle = 90 + (180 - 90) * (1 - combined_factor)

Examples:
  factor = 1.0 → down = 90° (normal)
  factor = 0.7 → down = 117° (easier)
  factor = 0.5 → down = 135° (much easier)
```

### **3. API Endpoints (`main.py`)**

```python
@app.post("/api/profile/update")
async def update_profile(
    request: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Update user profile with biometric data
    
    Request Body:
        {
            "age": 72,
            "gender": "female",
            "height_cm": 155,
            "weight_kg": 58,
            "medical_conditions": "[\"knee_arthritis\"]",
            "mobility_level": "beginner",
            "pain_level": 4
        }
    
    Response:
        {
            "success": true,
            "message": "Profile updated successfully",
            "bmi": 24.1
        }
    """
    # 1. Verify JWT token
    # 2. Calculate BMI
    # 3. Update database
    # 4. Return success

@app.get("/api/profile/me")
async def get_my_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current user's profile
    
    Response:
        {
            "id": 1,
            "username": "patient1",
            "age": 72,
            "height_cm": 155,
            "weight_kg": 58,
            "bmi": 24.1,
            "medical_conditions": "[\"knee_arthritis\"]",
            "mobility_level": "beginner",
            "pain_level": 4,
            ...
        }
    """

@app.post("/api/personalized-params")
async def get_personalized_params(
    request: PersonalizedParamsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Calculate personalized exercise parameters
    
    Request Body:
        {
            "exercise_type": "squat"
        }
    
    Response:
        {
            "down_angle": 125.0,
            "up_angle": 160.0,
            "max_reps": 8,
            "rest_seconds": 60,
            "difficulty_score": 0.49,
            "age_factor": 0.50,
            "bmi_factor": 1.0,
            "medical_factor": 0.70,
            "mobility_factor": 0.70,
            "pain_factor": 0.85,
            "warnings": [...],
            "recommendations": [...]
        }
    """
    # 1. Get user data from DB
    # 2. Call personalization_engine
    # 3. Save to user_exercise_limits
    # 4. Return personalized params
```

---

## Frontend Implementation

### **File Structure**
```
frontend/src/
├── pages/
│   └── UserProfile.tsx          # User profile form
├── components/
│   └── Navbar.tsx               # Updated with "Thông Tin" link
└── App.tsx                      # Updated with /profile route
```

### **1. UserProfile Component**

**State Management:**
```typescript
interface ProfileData {
  age: number | '';
  gender: string;
  height_cm: number | '';
  weight_kg: number | '';
  medical_conditions: string[];
  mobility_level: string;
  pain_level: number;
}

const [profile, setProfile] = useState<ProfileData>({
  age: '',
  gender: 'male',
  height_cm: '',
  weight_kg: '',
  medical_conditions: [],
  mobility_level: 'beginner',
  pain_level: 0,
});
```

**Key Functions:**
```typescript
// Load existing profile
const loadProfile = async () => {
  const response = await fetch('http://localhost:8000/api/profile/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  setProfile({...data, medical_conditions: JSON.parse(data.medical_conditions)});
};

// Calculate BMI in real-time
const calculateBMI = () => {
  if (profile.height_cm && profile.weight_kg) {
    const heightM = Number(profile.height_cm) / 100;
    return (Number(profile.weight_kg) / (heightM ** 2)).toFixed(1);
  }
  return null;
};

// Submit form
const handleSubmit = async (e: React.FormEvent) => {
  const response = await fetch('http://localhost:8000/api/profile/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      ...profile,
      medical_conditions: JSON.stringify(profile.medical_conditions)
    })
  });
};
```

**UI Components:**
- **Basic Info Card**: Age, Gender, Height, Weight + BMI display
- **Medical Conditions Card**: Checkbox grid với 8 options
- **Mobility & Pain Card**: Radio buttons + Range slider
- **Submit Button**: With loading state

**Dark Mode Support:**
```typescript
// All components use dark: prefix
className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
```

### **2. Navbar Integration**

**New Link for Patients:**
```typescript
{user.role === 'patient' && (
  <Link to="/profile" className={getLinkClasses('/profile')}>
    Thông Tin
  </Link>
)}
```

**Active State:**
```typescript
const getLinkClasses = (path: string) => {
  if (location.pathname === path) {
    return 'text-teal-500 dark:text-teal-400 font-semibold';
  }
  return 'text-gray-500 dark:text-gray-400 hover:text-teal-500';
};
```

---

## API Reference

### **Base URL**
```
Development: http://localhost:8000
Production: https://your-domain.com
```

### **Authentication**
All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

Get token from `/api/auth/login` endpoint.

### **Endpoints Summary**

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/profile/update` | Update user profile | ✅ |
| GET | `/api/profile/me` | Get current user profile | ✅ |
| POST | `/api/personalized-params` | Get personalized exercise params | ✅ |

### **Detailed API Specs**

#### **POST /api/profile/update**
```typescript
Request:
{
  age?: number,
  gender?: string,
  height_cm?: number,
  weight_kg?: number,
  medical_conditions?: string,  // JSON string
  mobility_level?: string,
  pain_level?: number
}

Response (200):
{
  success: boolean,
  message: string,
  bmi: number | null
}

Errors:
- 401: Unauthorized (invalid token)
- 400: Bad request (invalid data)
```

#### **GET /api/profile/me**
```typescript
Response (200):
{
  id: number,
  username: string,
  full_name: string,
  age: number,
  gender: string,
  height_cm: number,
  weight_kg: number,
  bmi: number,
  medical_conditions: string,  // JSON string
  injury_type: string | null,
  mobility_level: string,
  pain_level: number,
  doctor_notes: string | null,
  contraindicated_exercises: string | null,
  role: string
}

Errors:
- 401: Unauthorized
- 404: User not found
```

#### **POST /api/personalized-params**
```typescript
Request:
{
  exercise_type: string  // "squat" | "arm_raise" | "calf_raise" | "single_leg_stand"
}

Response (200):
{
  down_angle?: number,
  up_angle?: number,
  max_reps?: number,
  hold_seconds?: number,
  rest_seconds: number,
  difficulty_score: number,
  age_factor: number,
  bmi_factor: number,
  medical_factor: number,
  mobility_factor: number,
  pain_factor: number,
  warnings: string[],
  recommendations: string[]
}

Errors:
- 401: Unauthorized
- 404: User not found
- 400: Invalid exercise_type
```

---

## AI Algorithm Details

### **Factor Weights**
```python
WEIGHTS = {
    'age': 0.30,        # Most important (elderly need special care)
    'medical': 0.25,    # Medical conditions are critical
    'bmi': 0.20,        # Joint stress consideration
    'mobility': 0.15,   # Current fitness level
    'pain': 0.10        # Current pain state
}
```

### **Threshold Adjustments**

**For Squat:**
```python
baseline_down_angle = 90°  # Deep squat

# Adjustment formula
adjusted_down_angle = baseline + (180 - baseline) * (1 - combined_factor)

# Examples
combined_factor = 1.0 → 90°   (normal, young & healthy)
combined_factor = 0.7 → 117°  (easier, elderly or overweight)
combined_factor = 0.5 → 135°  (very easy, high risk)
```

**For Arm Raise:**
```python
baseline_up_angle = 160°  # Full raise

adjusted_up_angle = 90 + (baseline - 90) * combined_factor

# Examples
combined_factor = 1.0 → 160° (normal)
combined_factor = 0.7 → 139° (easier)
combined_factor = 0.5 → 125° (very easy)
```

**For Reps:**
```python
adjusted_reps = int(baseline_reps * combined_factor)
adjusted_reps = max(5, adjusted_reps)  # Minimum 5 reps
```

**For Rest:**
```python
adjusted_rest = int(baseline_rest / combined_factor)
adjusted_rest = max(15, adjusted_rest)  # Minimum 15 seconds
```

### **Warning Generation Logic**
```python
if pain_level >= 7:
    warnings.append("Mức đau cao - Nên tham khảo bác sĩ")

if bmi >= 30 and exercise in ['squat', 'single_leg_stand']:
    warnings.append("BMI cao - Hạn chế độ sâu")

if age >= 75 and exercise == 'single_leg_stand':
    warnings.append("Nên có người hỗ trợ khi tập đứng 1 chân")

if has_knee_issues and exercise == 'squat':
    warnings.append("Có vấn đề đầu gối - Không gập quá sâu")
```

---

## Testing Guide

### **Unit Tests (Backend)**
```python
# test_personalization.py

def test_age_factor():
    engine = PersonalizationEngine()
    assert engine._calculate_age_factor(25) == 1.0
    assert engine._calculate_age_factor(50) == 0.85
    assert engine._calculate_age_factor(70) == 0.70
    assert engine._calculate_age_factor(80) == 0.50

def test_bmi_factor():
    engine = PersonalizationEngine()
    assert engine._calculate_bmi_factor(22) == 1.0
    assert engine._calculate_bmi_factor(28) == 0.85
    assert engine._calculate_bmi_factor(32) == 0.70

def test_personalized_params():
    user_data = {
        'age': 72,
        'height_cm': 155,
        'weight_kg': 58,
        'medical_conditions': '["knee_arthritis"]',
        'mobility_level': 'beginner',
        'pain_level': 4
    }
    
    params = engine.calculate_personalized_params(user_data, 'squat')
    
    assert params['down_angle'] > 90  # Easier than normal
    assert params['max_reps'] < 20
    assert params['rest_seconds'] > 30
    assert len(params['warnings']) > 0
```

### **Integration Tests**
```bash
# Test full flow
pytest tests/test_integration.py

# Test specific endpoints
pytest tests/test_api.py::test_update_profile
pytest tests/test_api.py::test_get_personalized_params
```

### **Manual Testing**

**Test Case 1: Elderly with Knee Issues**
```
1. Login as patient1
2. Go to /profile
3. Fill:
   - Age: 75
   - Height: 160cm
   - Weight: 65kg
   - Medical: knee_arthritis, osteoporosis
   - Mobility: beginner
   - Pain: 5
4. Save
5. Expected BMI: 25.4 (Thừa cân)
6. Go to /exercise
7. Select Squat
8. Expected:
   - Down angle > 110°
   - Max reps < 10
   - Multiple warnings
```

---

## Deployment

### **Environment Variables**
```bash
# .env
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///./rehab_v3.db
CORS_ORIGINS=http://localhost:3001,https://your-domain.com
```

### **Docker Setup**
```dockerfile
# Backend Dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Frontend Dockerfile
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "run", "preview"]
```

### **Production Checklist**
- [ ] Change SECRET_KEY
- [ ] Setup HTTPS
- [ ] Configure CORS properly
- [ ] Setup database backups
- [ ] Add error monitoring (Sentry)
- [ ] Add analytics
- [ ] Add rate limiting
- [ ] Setup CI/CD pipeline

---

**Version:** 1.0.0  
**Last Updated:** November 6, 2025  
**Maintainer:** Development Team
