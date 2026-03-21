import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  vi: {
    translation: {
      /* Translations for pages */
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
      },

      doctorDashboard: {
        title: "Dashboard Bác Sĩ",
        greeting: "Xin chào",
        logout: "Đăng Xuất",

        totalPatients: "Tổng bệnh nhân",
        todaySessions: "Tập hôm nay",
        avgAccuracy: "Độ chính xác TB",

        patientList: "Danh Sách Bệnh Nhân",
        loading: "Đang tải...",
        empty: "Chưa có bệnh nhân nào"
      },

      exercisePage: {
        exercises: {
          names: {
            squat: "Squat (Gập gối)",
            arm_raise: "Nâng Tay",
            single_leg_stand: "Đứng 1 Chân",
            calf_raise: "Nâng Gót Chân"
          },

          difficulty: {
            easy: "Dễ",
            medium: "Trung bình",
            hard: "Khó",
          },

          description: {
            squat: "Bài tập tăng cường cơ chân và hông",
            armRaise: "Bài tập vai và tay",
            singleLegStand: "Bài tập cân bằng và cơ chân",
            calfRaise: "Bài tập tăng cường cơ bắp chân",
          },

          instructions: {
            squat: [
              "Đứng thẳng, hai tay duỗi thẳng hai bên",
              "Từ từ hạ thấp cơ thể xuống như ngồi ghế",
              "Giữ lưng thẳng trong suốt động tác",
              "Hạ tay từ từ về tư thế ban đầu",
            ],
            armRaise: [
              "Đứng thẳng, hai tay duỗi thẳng hai bên",
              "Từ từ nâng tay lên cao qua đầu",
              "Giữ tay thẳng trong suốt động tác",
              "Hạ tay từ từ về tư thế ban đầu",
            ],
            singleLegStand: [
              "Đứng cạnh ghế, tay phải nắm thành ghế",
              "Co chân trái lên cao, đầu gối nâng cao",
              "Tay trái giữ chân trái ở vị trí đó",
              "Giữ 10 giây, sau đó hạ chân xuống",
              "Đổi bên: tay trái nắm ghế, co chân phải",
              "Tay phải giữ chân phải, giữ 10 giây",
            ],
            calfRaise: [
              "Đứng thẳng, hai chân rộng bằng vai",
              "Tay có thể đỡ vào tường để giữ thăng bằng",
              "Từ từ nâng gót lên cao (đứng bằng mũi chân)",
              "Giữ 1-2 giây ở trên",
              "Từ từ hạ gót xuống về tư thế ban đầu",
              "Lặp lại động tác",
            ],
          },
        },

        title: "Bài Tập Phục Hồi",
        selectExercise: "Chọn Bài Tập",
        cameraPlaceholder: "Camera sẽ bật khi bạn bắt đầu",
        cameraNote: "Đảm bảo có đủ ánh sáng và không gian",

        start: "Bắt Đầu",
        pause: "Tạm Dừng",
        reset: "Đặt Lại Bộ Đếm",
        voiceSettings: "Cài Đặt Giọng Nói",

        instructions: "Hướng Dẫn",
        steps: "Các bước thực hiện",
        videoGuide: "Video Hướng Dẫn",
        noVideoSupport: "Trình duyệt của bạn không hỗ trợ video.",
        noVideo: "Chưa có video hướng dẫn cho bài tập này",
        selectToWatch: "Chọn bài tập để xem video hướng dẫn",

        progress: "Tiến độ Bài Tập",
        target: "Mục tiêu",
        targetReps: "lần trong",
        minute: "phút",
        time: "Thời gian",
        reps: "Lần lặp",
        connected: "Đang kết nối",
        disconnected: "Mất kết nối",

        personalized: "Tùy Chỉnh Cá Nhân",
        difficulty: "Độ khó",
        angle: "Góc",
        rest: "Nghỉ",
        warnings: "Lưu ý",
        recommendations: "Gợi ý",

        noProfile: "Chưa có thông tin",
        fillProfile: "Điền thông tin để nhận bài tập phù hợp",
        fillNow: "Điền thông tin",

        completed: "Hoàn Thành!",
        timeout: "Hết Giờ!",
        completedDesc: "Bạn đã hoàn thành bài tập trong thời gian quy định",
        timeoutDesc: "Bạn chưa hoàn thành bài tập trong thời gian quy định",

        accuracy: "Độ chính xác",
        totalReps: "Tổng số lần",
        correctReps: "Đúng kỹ thuật",
        duration: "Thời gian",

        commonErrors: "Lỗi cần cải thiện",
        continue: "Tập Tiếp",
        backHome: "Về Trang Chủ"
      },

      /* Translations for components */
      navbar: {
        home: "Trang Chủ",
        exercise: "Bài Tập",
        history: "Lịch Sử",
        dashboard: "Dashboard",

        greeting: "Xin chào",
        profile: "Thông Tin Cá Nhân",
        logout: "Đăng Xuất",

        login: "Đăng Nhập"
      },

      angleDisplay: {
        title: "Góc Khớp",

        notDetected: {
          title: "Đứng vào trước camera",
          subtitle: "để bắt đầu bài tập"
        },

        analyzing: "Đang phân tích...",

        labels: {
          leftShoulder: "Vai trái",
          rightShoulder: "Vai phải",
          leftKnee: "Gối trái",
          rightKnee: "Gối phải",
          leftAnkle: "Mắt cá trái",
          rightAnkle: "Mắt cá phải"
        },

        current: "Hiện tại",
        target: "Mục tiêu",

        tips: {
          armRaise: "Nâng tay thẳng lên cao, giữ khuỷu tay thẳng",
          squat: "Gập gối xuống sâu, giữ lưng thẳng",
          singleLegStand: "Nâng đầu gối cao, giữ thăng bằng, nhìn thẳng phía trước",
          calfRaise: "Nâng gót cao lên, giữ chân thẳng, hạ từ từ"
        }
      },

      errorAnalytics: {
        title: "Phân Tích Lỗi Theo Bài Tập",
        commonErrors: "Lỗi Thường Gặp Theo Bài Tập",

        loading: "Đang tải...",
        noData: "Chưa có dữ liệu lỗi",
        noErrors: "Chưa có lỗi cho bài tập này",

        chartTitle: "Biểu đồ thống kê lỗi",
        errorDetails: "Chi tiết lỗi",

        tooltip: {
          total: "Tổng",
          average: "TB",
          sessions: "Xuất hiện"
        },

        labels: {
          count: "Số lần",
          totalCount: "Tổng số lần",
          avgPerSession: "Trung bình/buổi",
          sessionCount: "Xuất hiện"
        },

        data: {
          reps: "lần",
          rps: "lần/buổi",
          sessions: "buổi"
        }
      },

      errorFallback: {
        title: "Đã xảy ra lỗi",
        message: "Vui lòng tải lại trang."
      },

      footer: {
        brandTitle: "Hệ Thống Phục Hồi Chức Năng Rehab AI",
        description: "Hệ thống phục hồi chức năng sử dụng AI để theo dõi và phân tích chuyển động, giúp bác sĩ và bệnh nhân quản lý quá trình điều trị hiệu quả hơn",
        contact: "Dự án của sinh viên Swinburne",
      },

      heatmap: {
        title: "Tiến độ tập luyện",

        filters: {
          last7Days: "7 ngày qua",
          last1Month: "1 tháng qua",
          last3Months: "3 tháng qua",
          all: "Tất cả",
        },

        stats: {
          totalSessions: "Tổng số buổi tập",
          averagePerDay: "Trung bình mỗi ngày",
          averagePerWeek: "Trung bình mỗi tuần",
          bestDay: "Ngày tốt nhất",
          bestWeek: "Tuần tốt nhất",
          sessions: "buổi",
        },

        empty: {
          noData: "Chưa có dữ liệu tập luyện",
          startNow: "Hãy bắt đầu buổi tập đầu tiên của bạn!",
          noDataInRange: "Không có dữ liệu trong khoảng thời gian này",
          tryAnotherRange: "Thử chọn khoảng thời gian khác",
          noExercise: "Chưa tập",
        },

        labels: {
          day: "Ngày",
          week: "Tuần",
        },

        legend: {
          excellent: "80%: Xuất sắc",
          good: "60%: Tốt",
          average: "40%: Khá",
          poor: "40%: Cần cố gắng",
        }
      },

      patientCard: {
        age: "tuổi",
        lastSession: "Buổi tập gần nhất:",
        noSession: "Chưa có buổi tập nào",

        time: {
          justNow: "Vừa xong",
          hoursAgo: "giờ trước",
          yesterday: "Hôm qua",
          daysAgo: "ngày trước",
        }
      },

      progressChart: {
        title: "Tiến Độ Tập Luyện",

        legend: {
          accuracy: "Độ chính xác (%)",
          reps: "Số lần tập",
        },

        tooltip: {
          accuracy: "Độ chính xác",
          reps: "Số lần tập",
          session: "Buổi",
        }
      },

      relaxation: {
        title: "Nghỉ Thư Giãn",
        subtitle: "Hãy thả lỏng cơ thể và hít thở sâu",

        timer: {
          remaining: "còn lại"
        },

        breathing: {
          inhale: "Hít vào",
          exhale: "Thở ra",
          rhythm: "Đều đặn và chậm rãi"
        },

        tips: {
          title: "Hướng dẫn thư giãn:",
          tip1: "Ngồi hoặc nằm ở tư thế thoải mái",
          tip2: "Hít thở sâu và đều đặn",
          tip3: "Thả lỏng tất cả các cơ trong cơ thể",
          tip4: "Đóng mắt và tập trung vào hơi thở"
        },

        controls: {
          musicOn: "Bật Nhạc",
          musicOff: "Tắt Nhạc",
          skip: "Bỏ Qua"
        }
      },

      sessionCard: {
        stats: {
          totalReps: "Tổng số lần",
          correctReps: "Đúng kỹ thuật",
          duration: "Thời gian",
          accuracy: "Độ chính xác"
        },

        performance: {
          excellent: "Xuất sắc",
          good: "Tốt",
          average: "Trung bình",
          needImprovement: "Cần cải thiện"
        },

        errors: {
          title: "Lỗi phổ biến nhất:"
        },

        comparison: {
          title: "So với lần trước:",
          accuracyIncrease: "Độ chính xác",
          accuracyDecrease: "Độ chính xác",
          accuracySame: "Độ chính xác không đổi",

          error: "lỗi",
          increase: "Tăng",
          decrease: "Giảm",
          errorSame: "Số lỗi không đổi"
        },

        time: {
          minute: "p",
          justNow: "Vừa xong",
          hoursAgo: "{{value}} giờ trước",
          yesterday: "Hôm qua",
          daysAgo: "{{value}} ngày trước"
        }
      },

      smartRecommendations: {
        title: "Gợi ý thông minh",

        performance: {
          excellentTitle: "Hiệu suất xuất sắc!",
          excellentMessage: "Độ chính xác trung bình của bạn rất tốt. Hãy tiếp tục duy trì!",
          lowTitle: "Cần cải thiện kỹ thuật",
          lowMessage: "Độ chính xác còn thấp. Hãy xem lại các lỗi phổ biến và tập chậm hơn để đúng tư thế."
        },

        variety: {
          title: "Đa dạng hóa bài tập",
          message: "Bạn chỉ tập 1 loại bài. Hãy thử thêm các bài tập khác để phát triển toàn diện!"
        },

        consistency: {
          inactiveTitle: "Đã lâu rồi không tập",
          inactiveMessage: "ngày kể từ buổi tập cuối. Hãy quay lại tập luyện để duy trì tiến bộ!",
          todayTitle: "Tuyệt vời!",
          todayMessage: "Bạn đã tập hôm nay. Hãy nghỉ ngơi hợp lý để cơ thể phục hồi."
        },

        errors: {
          title: "Lỗi thường gặp",
          message: "Lỗi \"{{error}}\" xuất hiện {{count}} lần. Hãy tập trung cải thiện điểm này."
        },

        progress: {
          title: "Sức mạnh tăng lên!",
          message: "Số lần tập của bạn tăng {{percent}}% so với trước. Tuyệt vời!"
        },

        rest: {
          title: "Nghỉ ngơi là quan trọng",
          message: "Bạn đã tập rất chăm chỉ tuần này! Đừng quên dành thời gian nghỉ ngơi cho cơ thể."
        }
      },

      voiceSettings: {
        title: "Cài Đặt Giọng Nói",

        toggle: {
          title: "Bật hướng dẫn giọng nói",
          description: "Hệ thống sẽ đọc hướng dẫn và phản hồi"
        },

        rate: {
          label: "Tốc độ đọc",
          slow: "Chậm",
          normal: "Bình thường",
          fast: "Nhanh"
        },

        volume: {
          label: "Âm lượng",
          low: "Nhỏ",
          medium: "Vừa",
          high: "Lớn"
        },

        actions: {
          test: "Thử Giọng Nói",
          close: "Đóng"
        },

        tip: {
          title: "Mẹo:",
          content: "Giọng nói sẽ hướng dẫn bạn trong suốt bài tập, bao gồm động viên, cảnh báo lỗi và thông báo tiến độ."
        },

        testMessage: "Xin chào! Tôi sẽ hướng dẫn bạn tập luyện."
      }
    }
  },

  en: {
    translation: {
      /* Translations for pages */
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
      },

      doctorDashboard: {
        title: "Doctor Dashboard",
        greeting: "Hello",
        logout: "Logout",

        totalPatients: "Total Patients",
        todaySessions: "Today's Sessions",
        avgAccuracy: "Average Accuracy",

        patientList: "Patient List",
        loading: "Loading...",
        empty: "No patients yet"
      },

      exercisePage: {
        exercises: {
          names: {
            squat: "Squat",
            arm_raise: "Arm Raise",
            single_leg_stand: "Single Leg Stand",
            calf_raise: "Calf Raise"
          },

          difficulty: {
            easy: "Easy",
            medium: "Medium",
            hard: "Hard",
          },

          description: {
            squat: "Exercise to strengthen legs and hips",
            armRaise: "Shoulder and arm exercise",
            singleLegStand: "Balance and leg strengthening exercise",
            calfRaise: "Exercise to strengthen calf muscles",
          },

          instructions: {
            squat: [
              "Stand straight with arms extended at your sides",
              "Slowly lower your body as if sitting on a chair",
              "Keep your back straight throughout the movement",
              "Return to the starting position",
            ],
            armRaise: [
              "Stand straight with arms extended at your sides",
              "Slowly raise your arms overhead",
              "Keep your arms straight throughout the movement",
              "Lower your arms back to the starting position",
            ],
            singleLegStand: [
              "Stand next to a chair and hold it with your right hand",
              "Lift your left leg up with the knee raised",
              "Use your left hand to hold the leg in position",
              "Hold for 10 seconds, then lower your leg",
              "Switch sides: hold chair with left hand and lift right leg",
              "Hold for 10 seconds",
            ],
            calfRaise: [
              "Stand straight with feet shoulder-width apart",
              "You may hold a wall for balance",
              "Slowly raise your heels (stand on your toes)",
              "Hold for 1–2 seconds at the top",
              "Slowly lower your heels back down",
              "Repeat the movement",
            ],
          },
        },

        title: "Rehabilitation Exercises",
        selectExercise: "Select Exercise",
        cameraPlaceholder: "Camera will turn on when you start",
        cameraNote: "Ensure proper lighting and space",

        start: "Start",
        pause: "Pause",
        reset: "Reset Counter",
        voiceSettings: "Voice Settings",

        instructions: "Instructions",
        steps: "Steps",
        videoGuide: "Instruction Video",
        noVideo: "No instruction video available for this exercise",
        selectToWatch: "Select an exercise to watch the video",

        progress: "Exercise Progress",
        target: "Target",
        targetReps: "reps in",
        minute: "minutes",
        time: "Time",
        reps: "Reps",
        connected: "Connected",
        disconnected: "Disconnected",

        personalized: "Personalized Settings",
        difficulty: "Difficulty",
        angle: "Angle",
        rest: "Rest",
        warnings: "Warnings",
        recommendations: "Recommendations",

        noProfile: "No profile data",
        fillProfile: "Fill in your profile to get personalized exercises",
        fillNow: "Fill now",

        completed: "Completed!",
        timeout: "Time's Up!",
        completedDesc: "You completed the exercise within the time limit",
        timeoutDesc: "You did not complete the exercise in time",

        accuracy: "Accuracy",
        totalReps: "Total Reps",
        correctReps: "Correct Reps",
        duration: "Duration",

        commonErrors: "Errors to Improve",
        continue: "Continue",
        backHome: "Back to Home"
      },

      /* Translations for components */
      navbar: {
        home: "Home",
        exercise: "Exercises",
        history: "History",
        dashboard: "Dashboard",

        greeting: "Hello",
        profile: "Profile",
        logout: "Logout",

        login: "Login"
      },

      angleDisplay: {
        title: "Joint Angles",

        notDetected: {
          title: "Stand in front of the camera",
          subtitle: "to start the exercise"
        },

        analyzing: "Analyzing...",

        labels: {
          leftShoulder: "Left Shoulder",
          rightShoulder: "Right Shoulder",
          leftKnee: "Left Knee",
          rightKnee: "Right Knee",
          leftAnkle: "Left Ankle",
          rightAnkle: "Right Ankle"
        },

        current: "Current",
        target: "Target",

        tips: {
          armRaise: "Raise your arms straight overhead, keep elbows straight",
          squat: "Lower your body deeply, keep your back straight",
          singleLegStand: "Lift your knee high, maintain balance, look forward",
          calfRaise: "Raise your heels high, keep legs straight, lower slowly"
        }
      },

      errorAnalytics: {
        title: "Error Analysis by Exercise",
        commonErrors: "Common Errors by Exercise",

        loading: "Loading...",
        noData: "No error data available",
        noErrors: "No errors for this exercise",

        chartTitle: "Error Statistics Chart",
        errorDetails: "Error Details",

        tooltip: {
          total: "Total",
          average: "Avg",
          sessions: "Appeared"
        },

        labels: {
          count: "Count",
          totalCount: "Total Count",
          avgPerSession: "Avg per Session",
          sessionCount: "Sessions"
        },

        data: {
          reps: "reps",
          rps: "reps/session",
          sessions: "sessions"
        },

        errorBoundary: {
          title: "Something went wrong",
          message: "Please refresh the page."
        }
      },

      errorFallback: {
        title: "Something went wrong",
        message: "Please refresh the page."
      },

      footer: {
        brandTitle: "Rehab AI Rehabilitation System",
        description: "An AI-powered rehabilitation system that tracks and analyzes movement, helping doctors and patients manage treatment more effectively",
        contact: "A project by Swinburne students",
      },

      heatmap: {
        title: "Workout Progress",

        filters: {
          last7Days: "Last 7 days",
          last1Month: "Last 1 month",
          last3Months: "Last 3 months",
          all: "All time",
        },

        stats: {
          totalSessions: "Total sessions",
          averagePerDay: "Average per day",
          averagePerWeek: "Average per week",
          bestDay: "Best day",
          bestWeek: "Best week",
          sessions: "sessions",
        },

        empty: {
          noData: "No workout data yet",
          startNow: "Start your first workout session!",
          noDataInRange: "No data in this time range",
          tryAnotherRange: "Try selecting a different time range",
          noExercise: "No activity",
        },

        labels: {
          day: "Day",
          week: "Week",
        },

        legend: {
          excellent: "80%: Excellent",
          good: "60%: Good",
          average: "40%: Average",
          poor: "40%: Needs improvement",
        }
      },

      patientCard: {
        age: "years old",
        lastSession: "Last session:",
        noSession: "No sessions yet",

        time: {
          justNow: "Just now",
          hoursAgo: "hours ago",
          yesterday: "Yesterday",
          daysAgo: "days ago",
        }
      },

      progressChart: {
        title: "Workout Progress",

        legend: {
          accuracy: "Accuracy (%)",
          reps: "Repetitions",
        },

        tooltip: {
          accuracy: "Accuracy",
          reps: "Repetitions",
          session: "Session",
        }
      },

      relaxation: {
        title: "Relaxation Break",
        subtitle: "Relax your body and take deep breaths",

        timer: {
          remaining: "remaining"
        },

        breathing: {
          inhale: "Inhale",
          exhale: "Exhale",
          rhythm: "Slow and steady"
        },

        tips: {
          title: "Relaxation tips:",
          tip1: "Sit or lie down in a comfortable position",
          tip2: "Breathe deeply and steadily",
          tip3: "Relax all muscles in your body",
          tip4: "Close your eyes and focus on your breathing"
        },

        controls: {
          musicOn: "Play Music",
          musicOff: "Pause Music",
          skip: "Skip"
        }
      },

      sessionCard: {
        stats: {
          totalReps: "Total reps",
          correctReps: "Correct reps",
          duration: "Duration",
          accuracy: "Accuracy"
        },

        performance: {
          excellent: "Excellent",
          good: "Good",
          average: "Average",
          needImprovement: "Needs improvement"
        },

        errors: {
          title: "Most common errors:"
        },

        comparison: {
          title: "Compared to previous session:",
          accuracyIncrease: "Accuracy +{{value}}%",
          accuracyDecrease: "Accuracy {{value}}%",
          accuracySame: "Accuracy unchanged",

          error: "errors",
          increase: "Increased",
          decrease: "Decreased",
          errorSame: "Errors unchanged"
        },

        time: {
          minute: "m",
          justNow: "Just now",
          hoursAgo: "{{value}} hours ago",
          yesterday: "Yesterday",
          daysAgo: "{{value}} days ago"
        }
      },

      smartRecommendations: {
        title: "Smart Recommendations",

        performance: {
          excellentTitle: "Excellent performance!",
          excellentMessage: "Your average accuracy is very high. Keep up the great work!",
          lowTitle: "Technique needs improvement",
          lowMessage: "Your accuracy is still low. Review common mistakes and practice slower for better form."
        },

        variety: {
          title: "Diversify your exercises",
          message: "You are only doing one type of exercise. Try adding more for balanced development!"
        },

        consistency: {
          inactiveTitle: "It's been a while",
          inactiveMessage: "{{days}} days since your last session. Get back to training to maintain progress!",
          todayTitle: "Great job!",
          todayMessage: "You've trained today. Make sure to rest properly for recovery."
        },

        errors: {
          title: "Most common mistake",
          message: "The error \"{{error}}\" occurred {{count}} times. Focus on improving this."
        },

        progress: {
          title: "Strength improved!",
          message: "Your reps increased by {{percent}}% compared to before. Great job!"
        },

        rest: {
          title: "Rest is important",
          message: "You've trained very hard this week! Don't forget to give your body time to recover."
        }
      },

      voiceSettings: {
        title: "Voice Settings",

        toggle: {
          title: "Enable voice guidance",
          description: "The system will read instructions and provide feedback"
        },

        rate: {
          label: "Speech rate",
          slow: "Slow",
          normal: "Normal",
          fast: "Fast"
        },

        volume: {
          label: "Volume",
          low: "Low",
          medium: "Medium",
          high: "High"
        },

        actions: {
          test: "Test Voice",
          close: "Close"
        },

        tip: {
          title: "Tip:",
          content: "Voice guidance will assist you throughout the exercise, including encouragement, error warnings, and progress updates."
        },

        testMessage: "Hello! I will guide you through your exercise."
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