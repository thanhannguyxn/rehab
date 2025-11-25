# AI Personalization Feature Guide

## Tổng Quan

Hệ thống AI Personalization Engine điều chỉnh các bài tập phục hồi chức năng dựa trên:
- **Độ tuổi** (age)
- **Cân nặng & chiều cao** (BMI)
- **Bệnh lý hiện tại** (medical conditions)
- **Mức độ đau** (pain level)
- **Khả năng di chuyển** (mobility level)

---

## Cách Hoạt Động

### **1. Input (User Profile)**
```json
{
  "age": 72,
  "gender": "female",
  "height_cm": 155,
  "weight_kg": 58,
  "medical_conditions": ["knee_arthritis", "osteoporosis"],
  "mobility_level": "beginner",
  "pain_level": 4
}
```

### **2. AI Processing**
Engine tính toán 5 factors:
- **Age Factor**: 0.5-1.0 (người già → dễ hơn)
- **BMI Factor**: 0.7-1.0 (béo → dễ hơn)
- **Medical Factor**: 0.7-1.0 (có bệnh → dễ hơn)
- **Mobility Factor**: 0.7-1.0 (beginner → dễ hơn)
- **Pain Factor**: 0.5-1.0 (đau nhiều → dễ hơn)

**Combined Factor** = weighted average

### **3. Output (Personalized Parameters)**
```json
{
  "down_angle": 125,  // Thay vì 90° (gập nông hơn)
  "up_angle": 160,
  "max_reps": 8,      // Thay vì 20 (ít hơn)
  "rest_seconds": 60, // Thay vì 30 (nghỉ lâu hơn)
  "difficulty_score": 0.49,
  "warnings": [
    "Có vấn đề đầu gối - Không gập quá sâu",
    "Nên tập với ghế hỗ trợ"
  ],
  "recommendations": [
    "Khởi động kỹ 5-10 phút trước khi tập",
    "Nghỉ ngơi đầy đủ giữa các set"
  ]
}
```

---

## API Endpoints

### **1. Cập nhật Profile**
```http
POST /api/profile/update
Authorization: Bearer <token>

Body:
{
  "age": 65,
  "gender": "male",
  "height_cm": 170,
  "weight_kg": 75,
  "medical_conditions": "[\"knee_arthritis\", \"diabetes\"]",
  "mobility_level": "beginner",
  "pain_level": 3
}

Response:
{
  "success": true,
  "message": "Profile updated successfully",
  "bmi": 26.0
}
```

### **2. Lấy Profile**
```http
GET /api/profile/me
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "username": "patient1",
  "full_name": "Nguyễn Văn A",
  "age": 65,
  "gender": "male",
  "height_cm": 170,
  "weight_kg": 75,
  "bmi": 26.0,
  "medical_conditions": "[\"knee_arthritis\", \"diabetes\"]",
  "mobility_level": "beginner",
  "pain_level": 3,
  ...
}
```

### **3. Lấy Personalized Parameters**
```http
POST /api/personalized-params
Authorization: Bearer <token>

Body:
{
  "exercise_type": "squat"
}

Response:
{
  "down_angle": 115.5,
  "up_angle": 160,
  "max_reps": 12,
  "rest_seconds": 45,
  "difficulty_score": 0.68,
  "age_factor": 0.85,
  "bmi_factor": 0.85,
  "medical_factor": 0.70,
  "mobility_factor": 0.70,
  "pain_factor": 0.85,
  "warnings": [
    "Có vấn đề đầu gối - Không gập quá sâu",
    "Dừng ngay nếu cảm thấy đau đầu gối"
  ],
  "recommendations": [
    "Bắt đầu chậm, tập trung vào tư thế đúng",
    "Khởi động kỹ 5-10 phút trước khi tập",
    "Giữ lưng thẳng, đầu gối không vượt qua mũi chân",
    "Có thể tập với ghế hỗ trợ phía sau"
  ]
}
```

---

## Ví Dụ Thực Tế

### **Case 1: Bà Lan - 72 tuổi, viêm khớp gối**
```
Input:
  age: 72
  BMI: 24.1 (normal)
  medical_conditions: ["knee_arthritis"]
  mobility_level: "beginner"
  pain_level: 4

Squat Parameters:
  down_angle: 125° (thay vì 90°)
  max_reps: 8 (thay vì 20)
  rest_seconds: 60s (thay vì 30s)
  difficulty_score: 0.49 (dễ hơn 51%)

Warnings:
  Có vấn đề đầu gối - Không gập quá sâu
  Nên tập với ghế hỗ trợ

Recommendations:
  Khởi động kỹ 5-10 phút
  Có thể tập với ghế hỗ trợ phía sau
  Dừng ngay nếu đau đầu gối
```

### **Case 2: Anh Minh - 35 tuổi, béo phì**
```
Input:
  age: 35
  BMI: 31.0 (obese)
  medical_conditions: []
  mobility_level: "beginner"
  pain_level: 0

Squat Parameters:
  down_angle: 105° (thay vì 90°)
  max_reps: 12 (thay vì 20)
  rest_seconds: 40s
  difficulty_score: 0.68

Warnings:
  BMI cao - Hạn chế độ sâu để bảo vệ đầu gối
  Nên tập trên bề mặt mềm (thảm tập)

Recommendations:
  Có thể chia nhỏ thành nhiều set ngắn
  Tập nhẹ nhưng đều đặn mỗi ngày
  Giữ lưng thẳng, đầu gối không vượt qua mũi chân
```

### **Case 3: Chị Hoa - 28 tuổi, khỏe mạnh**
```
Input:
  age: 28
  BMI: 22.5 (normal)
  medical_conditions: []
  mobility_level: "advanced"
  pain_level: 0

Squat Parameters:
  down_angle: 90° (tiêu chuẩn)
  max_reps: 20 (đầy đủ)
  rest_seconds: 30s
  difficulty_score: 1.0 (bình thường)

Warnings: (không có)

Recommendations:
  Giữ lưng thẳng, đầu gối không vượt qua mũi chân
```

---

## Công Thức Tính Toán

### **Age Factor**
```python
if age <= 40:
    factor = 1.0      # Trẻ - bình thường
elif age <= 60:
    factor = 0.85     # Trung niên - dễ 15%
elif age <= 75:
    factor = 0.70     # Cao tuổi - dễ 30%
else:
    factor = 0.50     # Rất cao tuổi - dễ 50%
```

### **BMI Factor**
```python
if bmi < 18.5:
    factor = 0.90     # Gầy - cẩn thận
elif bmi < 25:
    factor = 1.0      # Bình thường
elif bmi < 30:
    factor = 0.85     # Thừa cân - dễ 15%
else:
    factor = 0.70     # Béo phì - dễ 30%
```

### **Medical Factor (Squat)**
```python
factor = 1.0
if has_knee_issues:
    factor *= 0.70    # Giảm 30%
if has_back_issues:
    factor *= 0.80    # Giảm 20%
```

### **Combined Factor**
```python
combined = (
    age_factor * 0.30 +      # 30% weight
    bmi_factor * 0.20 +      # 20% weight
    medical_factor * 0.25 +  # 25% weight
    mobility_factor * 0.15 + # 15% weight
    pain_factor * 0.10       # 10% weight
)
```

### **Angle Adjustment (Squat)**
```python
# Baseline: down=90°, up=160°
# Lower factor = easier = less deep squat (higher angle)

adjusted_down_angle = 90 + (180 - 90) * (1 - factor)

Example:
  factor = 1.0 → down = 90° (normal)
  factor = 0.7 → down = 117° (easier)
  factor = 0.5 → down = 135° (much easier)
```

---

## Frontend Integration (Next Step)

### **Tạo User Profile Form**
```typescript
// frontend/src/pages/UserProfile.tsx

const [profile, setProfile] = useState({
  age: '',
  gender: 'male',
  height_cm: '',
  weight_kg: '',
  medical_conditions: [] as string[],
  mobility_level: 'beginner',
  pain_level: 0,
});

const handleSubmit = async () => {
  await fetch('/api/profile/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      ...profile,
      medical_conditions: JSON.stringify(profile.medical_conditions)
    }),
  });
};
```

### **Load Personalized Params trong Exercise Page**
```typescript
// frontend/src/pages/ExercisePage.tsx

useEffect(() => {
  const loadPersonalizedParams = async () => {
    const response = await fetch('/api/personalized-params', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        exercise_type: selectedExercise
      }),
    });
    
    const data = await response.json();
    setPersonalizedParams(data);
  };
  
  if (selectedExercise) {
    loadPersonalizedParams();
  }
}, [selectedExercise]);
```

---

## Testing

### **Test với Postman/Thunder Client**

1. **Login để lấy token**
```http
POST http://localhost:8000/api/auth/login
Body: {
  "username": "patient1",
  "password": "patient123"
}
```

2. **Update profile**
```http
POST http://localhost:8000/api/profile/update
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "age": 72,
  "gender": "female",
  "height_cm": 155,
  "weight_kg": 58,
  "medical_conditions": "[\"knee_arthritis\"]",
  "mobility_level": "beginner",
  "pain_level": 4
}
```

3. **Get personalized params**
```http
POST http://localhost:8000/api/personalized-params
Headers: {
  "Authorization": "Bearer <token>"
}
Body: {
  "exercise_type": "squat"
}
```

---

## Next Steps

1. **Database schema** - DONE
2. **AI engine** - DONE
3. **Backend API** - DONE
4. **Frontend profile form** - TODO
5. **Display personalized params** - TODO
6. **Integrate với WebSocket** - TODO
7. **Testing với real users** - TODO

---

## Notes

- BMI được tự động tính từ height & weight
- Medical conditions lưu dưới dạng JSON string: `"[\"condition1\", \"condition2\"]"`
- Difficulty score: 0.5 (rất dễ) → 1.0 (bình thường)
- Warnings & recommendations được generate tự động dựa trên profile
- Có thể fine-tune các factors trong `personalization_engine.py`

---

## Troubleshooting

**Q: Backend không start được?**
```bash
# Check ai_models package đã tạo chưa
cd backend
ls ai_models/

# Nên thấy:
# __init__.py
# feature_engineering.py
# personalization_engine.py
```

**Q: API trả về error "Unknown exercise type"?**
```
Các exercise_type hợp lệ:
- "squat"
- "arm_raise"
- "calf_raise"
- "single_leg_stand"
```

**Q: Làm sao test nhanh không cần frontend?**
```bash
# Dùng curl hoặc Postman
# Hoặc vào http://localhost:8000/docs (Swagger UI)
```
