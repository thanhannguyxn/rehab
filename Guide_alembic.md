## **Hướng dẫn đầy đủ: Thay đổi Database với Alembic**

Dưới đây là **quy trình hoàn chỉnh** để thay đổi database schema một cách an toàn và có thể rollback.

---

## **Quy trình 5 bước cơ bản**

### **Bước 1: Thay đổi Model SQLAlchemy**
```python
# Trong backend/session.py hoặc backend/user.py
class User(Base):
    # Thêm cột mới
    new_column = Column(String(100), nullable=True)
    
    # Hoặc xóa cột (comment out)
    # old_column = Column(String(100))
```

### **Bước 2: Tạo Migration Script**
```bash
cd backend

# Cách 1: Tự động tạo (khuyên dùng)
alembic revision --autogenerate -m "test_remove"

# Cách 2: Tạo file trống để chỉnh sửa thủ công
alembic revision -m "custom changes"
```

### **Bước 3: Kiểm tra và chỉnh sửa Migration (quan trọng!)**
```python
# Mở file trong backend/alembic/versions/xxx_migration_name.py

def upgrade():
    # Alembic tự động tạo, có thể chỉnh sửa
    op.add_column('users', sa.Column('new_column', sa.String(length=100), nullable=True))

def downgrade():
    # Code để rollback
    op.drop_column('users', 'new_column')
```

### **Bước 4: Áp dụng Migration**
```bash
cd backend

# Áp dụng lên database
alembic upgrade head

# Hoặc áp dụng từng bước
alembic upgrade +1  # Áp dụng 1 migration tiếp theo
```

### **Bước 5: Xác nhận và kiểm tra**
```bash
# Kiểm tra trạng thái
alembic current      # → Hiển thị revision hiện tại
alembic history      # → Xem lịch sử migrations

# Test rollback (nếu cần)
alembic downgrade -1  # Quay lại 1 bước
```

---

## **Các lệnh Alembic quan trọng**

### **Kiểm tra trạng thái:**
```bash
alembic current          # Revision hiện tại
alembic history          # Lịch sử tất cả migrations
alembic heads            # Các head branches
alembic branches         # Các branches
```

### **Tạo migration:**
```bash
alembic revision --autogenerate -m "message"  # Tự động
alembic revision -m "message"                 # Thủ công
```

### **Áp dụng migration:**
```bash
alembic upgrade head     # Lên revision mới nhất
alembic upgrade +2       # Lên 2 revisions
alembic upgrade abc123   # Lên revision cụ thể
```

### **Rollback:**
```bash
alembic downgrade -1     # Quay lại 1 revision
alembic downgrade base   # Quay về ban đầu
alembic downgrade abc123 # Quay về revision cụ thể
```

### **Debug và kiểm tra:**
```bash
alembic check            # Kiểm tra có thay đổi chưa migrate
alembic show head        # Chi tiết migration head
alembic upgrade head --sql  # Xem SQL sẽ chạy (không thực thi)
```

---

## **Các tình huống phổ biến**

### **1. Thêm cột:**
```python
# models.py
new_field = Column(String(255), nullable=True)

# Migration tự động tạo:
op.add_column('table_name', sa.Column('new_field', sa.String(length=255), nullable=True))
```

### **2. Xóa cột:**
```python
# Comment out trong models.py
# old_field = Column(String(255))

# Migration:
op.drop_column('table_name', 'old_field')
```

### **3. Đổi tên cột:**
```python
# Migration (không thể tự động):
op.alter_column('table_name', 'old_name', new_column_name='new_name')
```

### **4. Thay đổi kiểu dữ liệu:**
```python
# Migration:
op.alter_column('table_name', 'column_name',
                existing_type=sa.String(length=100),
                type_=sa.Text(),
                existing_nullable=True)
```

### **5. Thêm/Xóa bảng:**
```python
# Alembic tự động detect khi thêm/xóa class trong models.py
```

---

## **Lưu ý quan trọng**

### **Backup database trước khi migrate:**
```bash
# Tạo backup MySQL
mysqldump -u root -p rehab_v3 > backup.sql
```

### **Kiểm tra migration trước khi chạy:**
- Luôn xem file migration trong `versions/`
- Chạy `alembic upgrade head --sql` để xem SQL
- Test trên database dev trước

### **Xử lý conflict:**
```bash
# Nếu "Target database is not up to date"
alembic stamp head  # Đánh dấu là up-to-date (cẩn thận!)

# Hoặc reset và tạo lại
alembic stamp base
alembic upgrade head
```

### **Với dữ liệu production:**
- Chạy migration trong maintenance window
- Có plan rollback sẵn
- Test trên staging environment trước

---

## **Workflow khuyến nghị**

```bash
# 1. Thay đổi models.py
# 2. Tạo migration
alembic revision --autogenerate -m "describe changes"

# 3. Kiểm tra file migration
# 4. Backup database
# 5. Áp dụng
alembic upgrade head

# 6. Verify
alembic current
alembic history

# 7. Test ứng dụng
```

---

## **Các lỗi thường gặp và cách sửa**

### **"Target database is not up to date"**
```bash
# Nguyên nhân: Model và DB không đồng bộ
# Giải pháp:
alembic stamp head  # Hoặc tạo migration thủ công
```

### **Migration conflict**
```bash
# Nguyên nhân: Multiple developers
# Giải pháp:
alembic merge heads  # Tạo merge migration
```

### **Không thể rollback**
```bash
# Nguyên nhân: Dữ liệu mất khi drop column
# Giải pháp: Restore từ backup
```

---

## **Cấu trúc thư mục Alembic**

```
backend/
├── alembic/
│   ├── versions/
│   │   ├── abc123_initial.py
│   │   ├── def456_add_column.py
│   │   └── ...
│   ├── env.py          # Config migration
│   ├── README          # Hướng dẫn
│   └── script.py.mako  # Template
├── alembic.ini         # Config chính
└── models.py           # SQLAlchemy models
```
