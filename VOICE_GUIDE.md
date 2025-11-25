# Voice Guidance System

## Tổng quan
Hệ thống hướng dẫn giọng nói tự động giúp người dùng (đặc biệt là người cao tuổi) thực hiện bài tập chính xác mà không cần nhìn màn hình liên tục.

## Công nghệ sử dụng
- **Web Speech API**: Tích hợp sẵn trong trình duyệt, miễn phí 100%
- **Ngôn ngữ**: Tiếng Việt (vi-VN)
- **Voice Rate**: 0.85x (chậm hơn bình thường để người cao tuổi nghe rõ)

## Tính năng Voice Feedback

### 1. **Thông báo bắt đầu/kết thúc**
- Khi bắt đầu: "Bắt đầu bài tập. Hãy đứng vào vị trí."
- Khi hoàn thành: "Hoàn thành! Bạn đã làm rất tốt."
- Khi hết giờ: "Hết giờ. Hãy nghỉ ngơi."

### 2. **Đọc số rep (Real-time)**
- Đọc số rep mỗi khi hoàn thành: "1", "2", "3"...
- Tự động, không lặp lại

### 3. **Cảnh báo thời gian**
- Còn 60 giây: "Còn một phút"
- Còn 30 giây: "Còn ba mươi giây"
- Còn 10 giây: "Còn mười giây"

### 4. **Động viên theo milestone**
- 25% tiến độ: "Tốt lắm!"
- 50% tiến độ: "Đã được một nửa rồi!"
- 75% tiến độ: "Sắp xong rồi!"
- Rep cuối: "Rep cuối cùng!"

### 5. **Cảnh báo lỗi (Real-time với cooldown 3 giây)**
Chỉ đọc lỗi sau khi phát hiện lỗi **liên tục trong 1.5 giây** (giảm false positive)

**Lỗi Arm Raise:**
- "Nâng tay cao hơn nữa" (góc vai chưa đủ)
- "Duỗi thẳng tay" (tay cong)
- "Hạ tay xuống hẳn" (chưa hạ hết)

**Lỗi Squat:**
- "Gập gối sâu hơn" (chưa xuống đủ)
- "Đẩy gối ra sau" (gối vượt mũi chân)
- "Đứng thẳng lên" (tư thế không thẳng)

**Lỗi Calf Raise:**
- "Nâng gót chân cao hơn" (gót chưa cao)
- "Giữ chân thẳng" (chân cong)

## Cài đặt Voice

### Cách mở Voice Settings:
1. Vào trang **Exercise**
2. Click nút **Cài Đặt Giọng Nói**

### Các tùy chọn:
- **Bật/Tắt**: Toggle switch để bật/tắt giọng nói
- **Tốc độ đọc**: 0.5x - 1.5x (mặc định 0.85x cho người cao tuổi)
- **Âm lượng**: 0% - 100% (mặc định 100%)
- **Thử giọng**: Test voice với câu mẫu

### Lưu ý:
- Settings tự động lưu vào **localStorage**
- Voice hoạt động trên Chrome, Edge, Firefox hiện đại
- Cần cho phép quyền audio trong trình duyệt

## Cơ chế hoạt động

### Speech Queue Management:
- **speak(text, interrupt)**: Đọc ngay, có thể ngắt voice hiện tại
- **addToQueue(text)**: Thêm vào hàng đợi, đọc sau khi voice trước xong

### Cooldown System:
- **Rep counting**: Chỉ đọc khi rep thay đổi (dùng `useRef`)
- **Error feedback**: 3 giây cooldown để tránh spam
- **Milestone**: Chỉ đọc 1 lần cho mỗi milestone

### Error Persistence (Backend):
- Backend chỉ gửi lỗi sau **1.5 giây** phát hiện liên tục
- Frontend map lỗi từ backend sang voice message phù hợp
- Tránh false positive khi người dùng đang chuyển động

## Browser Support

| Browser | Support | Note |
|---------|---------|------|
| Chrome 33+ | Excellent | Giọng Việt tốt nhất |
| Edge 14+ | Excellent | Giọng Windows TTS |
| Firefox 49+ | Limited | Giọng robotic hơn |
| Safari 7+ | Limited | iOS có thể hạn chế |
| Opera 21+ | Good | Dùng Chromium engine |

## Kiến trúc Code

```
frontend/src/
├── utils/
│   └── voiceService.ts          # VoiceService class + VoiceMessages
├── components/
│   └── VoiceSettings.tsx        # UI cho voice settings
└── pages/
    └── ExercisePage.tsx         # Tích hợp voice feedback
```

### VoiceService Methods:
- `speak(text, interrupt)` - Đọc ngay lập tức
- `addToQueue(text)` - Thêm vào queue
- `stop()` - Dừng tất cả voice
- `pause()` / `resume()` - Tạm dừng/tiếp tục
- `setEnabled(enabled)` - Bật/tắt voice
- `setRate(rate)` - Tốc độ đọc
- `setVolume(volume)` - Âm lượng

## Roadmap (Tương lai)

### Phase 2:
- [ ] Custom voice recordings (giọng chuyên nghiệp)
- [ ] Google Cloud TTS upgrade (chất lượng cao hơn)
- [ ] Multi-language support (English)
- [ ] Voice feedback theo exercise type chi tiết hơn

### Phase 3:
- [ ] Doctor customizable voice messages per patient
- [ ] AI-powered voice coaching
- [ ] Voice commands (bật/tắt bằng giọng nói)

## Testing

### Test checklist:
- [x] Voice đọc số rep mỗi khi hoàn thành
- [x] Voice cảnh báo lỗi sau 1.5s (không lặp liên tục)
- [x] Voice settings lưu vào localStorage
- [x] Voice dừng khi stop exercise
- [x] Voice không overlap (queue hoạt động đúng)
- [ ] Test trên nhiều browser
- [ ] Test với người cao tuổi thực tế

## Troubleshooting

**Không nghe thấy voice:**
1. Kiểm tra voice settings (đã bật chưa?)
2. Kiểm tra volume slider
3. Kiểm tra audio output device
4. Thử click "Thử Giọng Nói"

**Voice bị lag:**
- Tốc độ mạng ổn định
- Close các tab khác
- Restart browser

**Voice không rõ:**
- Tăng volume
- Giảm tốc độ đọc xuống 0.6x - 0.7x
- Kiểm tra speaker/headphone

---
