import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  vi: {
    translation: {
      landing: {
          heroBadge: "Công nghệ AI Tiên tiến",
          heroTitle1: "Phục Hồi Chức Năng",
          heroTitle2: "Tự Động & Thông Minh",
          heroSubtitle: "Theo dõi tập luyện tự động với AI. Không cần video. Chỉ cần máy ảnh và hệ thống sẽ đếm số lần thực hiện, phát hiện lỗi ngay lập tức.",
          getStarted: "Bắt Đầu Ngay",
          watchTutorial: "Xem Hướng Dẫn",

          stats1Title: "Bài Tập",
          stats2Title: "Độ Chính Xác",
          stats3Title: "Phản Hồi",
          stats3Subtitle: "Tức Thì",

          featuresTitle: "Công Nghệ AI Đột Phá",
          featuresSubtitle: "Hệ thống theo dõi tập luyện tự động sử dụng AI tiên tiến, không cần thiết bị đeo",
          gridTitle1: "Phát Hiện Tự Động",
          gridSubtitle1: "AI tự động phát hiện bài tập và đếm số lần tập mà không cần bạn nhập thủ công",
          gridTitle2: "Phản Hồi Tức Thì",
          gridSubtitle2: "Nhận cảnh báo ngay lập tức khi phát hiện tư thế không đúng",
          gridTitle3: "Thống Kê Chi Tiết",
          gridSubtitle3: "Theo dõi tiến độ với biểu đồ và phân tích lỗi chi tiết",
          gridTitle4: "An Toàn Tối Đa",
          gridSubtitle4: "Phát hiện lỗi tư thế giúp tránh chấn thương khi tập luyện",

          howItWorks: "Cách Hoạt Động",
          howItWorksSubtitle: "Chỉ 3 bước đơn giản để bắt đầu hành trình phục hồi của bạn",
          step1Title: "Chọn Bài Tập",
          step1Subtitle: "Chọn từ 4+ bài tập phục hồi được thiết kế cho người cao tuổi",
          step2Title: "AI Theo Dõi",
          step2Subtitle: "AI tự động đếm số lần tập và phát hiện lỗi tư thế ngay lập tức",
          step3Title: "Xem Báo Cáo",
          step3Subtitle: "Nhận phân tích chi tiết và theo dõi tiến độ phục hồi",

          exercisesTitle: "Bài Tập Phục Hồi",
          exercisesSubtitle: "Các bài tập được thiết kế đặc biệt cho người cao tuổi",
          exercise1Title: "Squat (Gập Gối)",
          exercise1Subtitle: "Tăng cường cơ chân và khả năng di chuyển",
          exercise2Title: "Nâng Tay",
          exercise2Subtitle: "Cải thiện sức mạnh vai và độ linh hoạt",
          exercise3Title: "Đứng 1 Chân",
          exercise3Subtitle: "Rèn luyện thăng bằng và ổn định",
          exercise4Title: "Nâng Gót Chân",
          exercise4Subtitle: "Tăng cường cơ bắp chân",
          findOutMore: "Tìm hiểu thêm",

          ctaTitle: "Bắt Đầu Hành Trình Phục Hồi",
          ctaSubtitle: "Tham gia ngay hôm nay và trải nghiệm công nghệ AI tiên tiến",
          ctaButton: "Bắt Đầu Miễn Phí"
      },

      loginChoice: {
          title: "Chọn Loại Tài Khoản",
          subtitle: "Bạn là bệnh nhân hay bác sĩ?",
          login: "Đăng Nhập",
          backToHome: "Quay lại trang chủ",

          patientTitle: "Bệnh Nhân",
          patientSubtitle: "Đăng nhập để tập luyện phục hồi chức năng với AI",

          doctorTitle: "Bác Sĩ",
          doctorSubtitle: "Quản lý và theo dõi tiến độ của bệnh nhân"
      },

      login: {
        doctor: "Bác Sĩ",
        patient: "Bệnh Nhân",

        titleDoctor: "Đăng Nhập Bác Sĩ",
        titlePatient: "Đăng Nhập Bệnh Nhân",

        systemName: "Hệ Thống Phục Hồi Chức Năng",

        sampleAccounts: "Tài khoản mẫu:",
        doctorAccount: "Bác sĩ:",
        patientAccount: "Bệnh nhân:",

        switchAccount: "Đăng nhập loại tài khoản khác",

        usernameLabel: "Tên đăng nhập",
        usernamePlaceholder: "Nhập tên đăng nhập",

        passwordLabel: "Mật khẩu",
        passwordPlaceholder: "Nhập mật khẩu",

        loginButton: "Đăng Nhập",
        loggingIn: "Đang đăng nhập...",

        loginFailed: "Đăng nhập thất bại. Vui lòng thử lại."
      },

      patientDashboard: {
        greeting: "Xin chào",
        subtitle: "Sẵn sàng tập luyện hôm nay",

        logout: "Đăng Xuất",

        startExercise: "Bắt Đầu Tập Luyện",

        totalSessions: "Tổng buổi tập",
        avgAccuracy: "Độ chính xác TB",
        totalReps: "Tổng số lần",

        recentSessions: "Buổi Tập Gần Đây",
        viewAll: "Xem tất cả",

        loading: "Đang tải...",
        noSessions: "Chưa có buổi tập nào. Hãy bắt đầu ngay!",

        justNow: "Vừa xong",
        hoursAgo: "giờ trước",
        yesterday: "Hôm qua",
        daysAgo: "ngày trước",

        reps: "lần"
      },

      patientDetail: {
        title: "Chi Tiết Bệnh Nhân",
        patientId: "Mã bệnh nhân",

        exportPDF: "Xuất PDF",
        back: "Quay Lại",

        loading: "Đang tải...",
        noSessions: "Bệnh nhân chưa có buổi tập nào",

        summary: "Tổng Quan",
        totalSessions: "Tổng buổi tập",
        avgAccuracy: "Độ chính xác TB",
        totalReps: "Tổng số lần",
        totalTime: "Tổng thời gian",

        minutes: "phút",

        sessionDetails: "Chi Tiết Các Buổi Tập",

        reportTitle: "BÁO CÁO TIẾN ĐỘ PHỤC HỒI CHỨC NĂNG",
        reportDate: "Ngày tạo",

        exercise: "Bài tập",
        date: "Ngày",
        reps: "Số lần",
        accuracy: "Chính xác",
        duration: "Thời gian",

        recommendations: "Nhận Xét Và Khuyến Nghị",

        goodProgress1: "Bệnh nhân có tiến độ tốt, duy trì tập luyện đều đặn",
        goodProgress2: "Có thể tăng cường độ tập luyện",

        mediumProgress1: "Tiến độ khá, cần cải thiện kỹ thuật",
        mediumProgress2: "Tập trung sửa các lỗi thường gặp",

        lowProgress1: "Cần theo dõi sát sao và hướng dẫn kỹ hơn",
        lowProgress2: "Đề xuất tập với cường độ thấp hơn"
      },

      patientHistory: {
        title: "Lịch Sử Luyện Tập",
        subtitle: "Xem lại các buổi tập và theo dõi tiến trình của bạn",

        loading: "Đang tải...",
        noSessions: "Chưa có buổi tập nào",
        startExercise: "Bắt Đầu Tập Ngay",

        weeklyGoalTitle: "Mục tiêu tuần này",
        weeklyGoalSubtitle: "Tập ít nhất 5 buổi mỗi tuần",
        sessions: "buổi tập",

        goalCompleted: "Xuất sắc! Bạn đã hoàn thành mục tiêu tuần này!",

        streakTitle: "Chuỗi ngày tập",
        streakStart: "Bắt đầu chuỗi mới!",
        streakDays: "ngày liên tiếp",

        totalSessions: "Tổng buổi tập",
        avgAccuracy: "Độ chính xác TB",
        totalReps: "Tổng số lần",
        totalTime: "Tổng thời gian",
        minutes: "phút",

        sessionDetails: "Chi Tiết Các Buổi Tập",

        filterAllExercises: "Tất cả bài tập",
        sortByDate: "Ngày tập",
        sortByAccuracy: "Độ chính xác",
        sortByReps: "Số lần tập",

        sortAsc: "Tăng dần",
        sortDesc: "Giảm dần",

        showingResults1: "Hiển thị",
        showingResults2: "buổi tập"
      },

      userProfile: {
        title: "Thông Tin Cá Nhân",
        subtitle: "Cập nhật thông tin để nhận được bài tập phù hợp với bạn",

        tabs: {
          basic: "Thông Tin Cơ Bản",
          medical: "Tình Trạng Sức Khỏe",
          mobility: "Vận Động & Đau Đớn"
        },

        fields: {
          age: "Tuổi",
          gender: "Giới tính",
          height: "Chiều cao",
          weight: "Cân nặng",
          mobilityLevel: "Khả năng di chuyển hiện tại",
          painLevel: "Mức độ đau hiện tại"
        },

        placeholders: {
          age: "Nhập tuổi của bạn",
          height: "Ví dụ: 170",
          weight: "Ví dụ: 65",
        },

        genderOptions: {
          male: "Nam",
          female: "Nữ",
          other: "Khác"
        },

        medicalConditions: {
          arthritis: "Viêm khớp gối",
          shoulderPain: "Đau vai",
          backPain: "Đau lưng",
          osteoporosis: "Loãng xương",
          diabetes: "Tiểu đường",
          heartDisease: "Bệnh tim",
          hypertension: "Cao huyết áp",
          strokeRecovery: "Phục hồi sau đột quỵ"
        },

        bmi: {
          label: "Chỉ số BMI của bạn",
          category: "Phân loại",
          underweight: "Thiếu cân",
          normal: "Bình thường",
          overweight: "Thừa cân",
          obese: "Béo phì"
        },

        mobilityLevels: {
          beginner: "Mới bắt đầu",
          beginnerDesc: "Ít vận động",
          intermediate: "Trung bình",
          intermediateDesc: "Vận động vừa phải",
          advanced: "Nâng cao",
          advancedDesc: "Vận động tốt"
        },

        painScale: {
          none: "Không đau",
          medium: "Đau vừa",
          severe: "Rất đau"
        },

        medicalTitle: "Tình Trạng Sức Khỏe",
        medicalSubtitle: "Chọn các vấn đề sức khỏe hiện tại (nếu có)",

        loading: "Đang tải...",
        saving: "Đang lưu...",
        save: "Lưu Thông Tin",
        cancel: "Hủy",

        success: "Cập nhật thông tin thành công!",
        error: "Có lỗi xảy ra, vui lòng thử lại",
        serverError: "Không thể kết nối đến server"
      }
    }
  },

  en: {
    translation: {
      landing: {
          heroBadge: "Advanced AI Technology",
          heroTitle1: "Rehabilitation",
          heroTitle2: "Automated & Intelligent",
          heroSubtitle: "Automatically track your exercises with AI. No video required. Just a camera and the system will count repetitions and detect mistakes instantly.",
          getStarted: "Get Started",
          watchTutorial: "Watch Tutorial",

          stats1Title: "Exercises",
          stats2Title: "Accuracy",
          stats3Title: "Feedback",
          stats3Subtitle: "Instant",

          featuresTitle: "Breakthrough AI Technology",
          featuresSubtitle: "An automated exercise tracking system powered by advanced AI, no wearable devices required",
          gridTitle1: "Automatic Detection",
          gridSubtitle1: "AI automatically detects exercises and counts repetitions without manual input",
          gridTitle2: "Instant Feedback",
          gridSubtitle2: "Receive immediate alerts when incorrect posture is detected",
          gridTitle3: "Detailed Analytics",
          gridSubtitle3: "Track your progress with charts and detailed error analysis",
          gridTitle4: "Maximum Safety",
          gridSubtitle4: "Detect posture mistakes to help prevent injuries during exercise",

          howItWorks: "How It Works",
          howItWorksSubtitle: "Just 3 simple steps to begin your recovery journey",
          step1Title: "Choose an Exercise",
          step1Subtitle: "Select from 4+ rehabilitation exercises designed for seniors",
          step2Title: "AI Tracking",
          step2Subtitle: "AI automatically counts repetitions and detects posture mistakes instantly",
          step3Title: "View Reports",
          step3Subtitle: "Receive detailed analysis and track your recovery progress",

          exercisesTitle: "Rehabilitation Exercises",
          exercisesSubtitle: "Exercises specially designed for seniors",
          exercise1Title: "Squat (Knee Bend)",
          exercise1Subtitle: "Strengthens leg muscles and improves mobility",
          exercise2Title: "Arm Raise",
          exercise2Subtitle: "Improves shoulder strength and flexibility",
          exercise3Title: "Single Leg Stand",
          exercise3Subtitle: "Improves balance and stability",
          exercise4Title: "Heel Raise",
          exercise4Subtitle: "Strengthens calf muscles",
          findOutMore: "Find out more",

          ctaTitle: "Start Your Recovery Journey",
          ctaSubtitle: "Join today and experience advanced AI technology",
          ctaButton: "Start Free"
      },

      loginChoice: {
          title: "Choose Account Type",
          subtitle: "Are you a patient or a doctor?",
          login: "Login",
          backToHome: "Back to home page",

          patientTitle: "Patient",
          patientSubtitle: "Login to use the AI rehabilitation system",

          doctorTitle: "Doctor",
          doctorSubtitle: "Manage and monitor patient's progress"
      },

      login: {
        doctor: "Doctor",
        patient: "Patient",

        titleDoctor: "Doctor Login",
        titlePatient: "Patient Login",

        systemName: "Rehabilitation System",

        sampleAccounts: "Sample Accounts:",
        doctorAccount: "Doctor:",
        patientAccount: "Patient:",

        switchAccount: "Login with another account type",

        usernameLabel: "Username",
        usernamePlaceholder: "Enter username",

        passwordLabel: "Password",
        passwordPlaceholder: "Enter password",

        loginButton: "Login",
        loggingIn: "Logging in...",

        loginFailed: "Login failed. Please try again."
      },

      patientDashboard: {
        greeting: "Hello",
        subtitle: "Ready to exercise today",

        logout: "Logout",

        startExercise: "Start Exercise",

        totalSessions: "Total Sessions",
        avgAccuracy: "Average Accuracy",
        totalReps: "Total Repetitions",

        recentSessions: "Recent Sessions",
        viewAll: "View all",

        loading: "Loading...",
        noSessions: "No sessions yet. Start your first exercise!",

        justNow: "Just now",
        hoursAgo: "hours ago",
        yesterday: "Yesterday",
        daysAgo: "days ago",

        reps: "reps"
      },

      patientDetail: {
        title: "Patient Details",
        patientId: "Patient ID",

        exportPDF: "Export PDF",
        back: "Back",

        loading: "Loading...",
        noSessions: "This patient has no exercise sessions yet",

        summary: "Summary",
        totalSessions: "Total Sessions",
        avgAccuracy: "Average Accuracy",
        totalReps: "Total Repetitions",
        totalTime: "Total Time",

        minutes: "min",

        sessionDetails: "Exercise Session Details",

        reportTitle: "REHABILITATION PROGRESS REPORT",
        reportDate: "Date Generated",

        exercise: "Exercise",
        date: "Date",
        reps: "Reps",
        accuracy: "Accuracy",
        duration: "Duration",

        recommendations: "Comments & Recommendations",

        goodProgress1: "Patient shows good progress, maintain consistent training",
        goodProgress2: "Exercise intensity can be increased",

        mediumProgress1: "Progress is fair, technique needs improvement",
        mediumProgress2: "Focus on correcting common errors",

        lowProgress1: "Requires closer monitoring and guidance",
        lowProgress2: "Recommend reducing exercise intensity"
      },

      patientHistory: {
        title: "Exercise History",
        subtitle: "Review your exercise sessions and track your progress",

        loading: "Loading...",
        noSessions: "No exercise sessions yet",
        startExercise: "Start Exercising",

        weeklyGoalTitle: "This Week's Goal",
        weeklyGoalSubtitle: "Exercise at least 5 sessions per week",
        sessions: "sessions",

        goalCompleted: "Excellent! You have completed this week's goal!",

        streakTitle: "Exercise Streak",
        streakStart: "Start a new streak!",
        streakDays: "consecutive days",

        totalSessions: "Total Sessions",
        avgAccuracy: "Average Accuracy",
        totalReps: "Total Repetitions",
        totalTime: "Total Time",
        minutes: "min",

        sessionDetails: "Exercise Session Details",

        filterAllExercises: "All exercises",
        sortByDate: "Date",
        sortByAccuracy: "Accuracy",
        sortByReps: "Repetitions",

        sortAsc: "Ascending",
        sortDesc: "Descending",

        showingResults1: "Showing",
        showingResults2: "sessions"
      },

      userProfile: {
        title: "User Profile",
        subtitle: "Update your information to receive personalized exercises",

        tabs: {
          basic: "Basic Information",
          medical: "Medical Conditions",
          mobility: "Mobility & Pain"
        },

        fields: {
          age: "Age",
          gender: "Gender",
          height: "Height",
          weight: "Weight",
          mobilityLevel: "Current mobility level",
          painLevel: "Current pain level"
        },

        placeholders: {
          age: "Enter your age",
          height: "Example: 170",
          weight: "Example: 65",
        },

        genderOptions: {
          male: "Male",
          female: "Female",
          other: "Other"
        },

        medicalConditions: {
          arthritis: "Arthritis",
          shoulderPain: "Shoulder pain",
          backPain: "Back pain",
          osteoporosis: "Osteoporosis",
          diabetes: "Diabetes",
          heartDisease: "Heart disease",
          hypertension: "Hypertension",
          strokeRecovery: "Stroke recovery"
        },

        bmi: {
          label: "Your BMI",
          category: "Category",
          underweight: "Underweight",
          normal: "Normal",
          overweight: "Overweight",
          obese: "Obese"
        },

        mobilityLevels: {
          beginner: "Beginner",
          beginnerDesc: "Low activity",
          intermediate: "Intermediate",
          intermediateDesc: "Moderate activity",
          advanced: "Advanced",
          advancedDesc: "High activity"
        },

        painScale: {
          none: "No pain",
          medium: "Moderate pain",
          severe: "Severe pain"
        },

        medicalTitle: "Medical Conditions",
        medicalSubtitle: "Select current health conditions (if any)",

        loading: "Loading...",
        saving: "Saving...",
        save: "Save Information",
        cancel: "Cancel",

        success: "Profile updated successfully!",
        error: "Something went wrong. Please try again.",
        serverError: "Cannot connect to server"
      }
    }
  }
};

i18n.use(initReactI18next).init({
  resources,
  lng: "vi",
  fallbackLng: "en",

  interpolation: {
    escapeValue: false
  }
});

export default i18n;