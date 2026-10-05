# CWS AutoTrade — Web thử nghiệm chi phí thấp

Founder giao quyền chọn phương án và thực hiện ngay. Dùng PWA tĩnh làm giao diện, giữ Supabase + TF-013A hiện có. Không xây lại trading brain, không thuê VPS mới, không thêm API AI vào đường đặt lệnh. Google Sites là lựa chọn trang giới thiệu, không bắt buộc.

Luồng: người dùng mở web → xem chart/danh mục → mở bảng bot bằng Google Founder → xem forward, arena, journal. Tiến trình máy chủ tiếp tục chạy khi đóng trình duyệt. Phiên MT5 cần server xác nhận DEMO; không đánh đồng xác minh đăng nhập với đặt lệnh thành công.

Tự nghiên cứu: replay, ngoài mẫu, walk-forward, forward; ghi phiên bản ứng viên và bằng chứng. Không tự đổi luật rủi ro, không tự promote chiến lược chưa vượt gate. TF-013A đang COLLECTING; không cần model LLM được duyệt để vận hành bộ quy tắc, nhưng vẫn cần gate chiến lược/rủi ro.

Ưu tiên an toàn dữ liệu trước mở broker: runtime phát hiện state.position lưu dạng JSON string. Parser đọc dạng cũ hợp lệ và chặn state thiếu direction/stop/risk; không tự phục dựng số thiếu. Ghi mới dùng sql.json để tránh double encode. Vị thế hỏng giữ nguyên để điều tra, không tạo số liệu backtest giả.

Giới hạn: DEMO send=false, risk approval=false, max total demo volume chưa chốt. Không gửi broker order hoặc mở tiền thật. Hosting mới giữ riêng tư; Google OAuth/MT5 vẫn qua cửa chính hiện có, không thêm origin chưa được backend duyệt.

Kiểm chứng: test parser trước/sau sửa, test web logic hiện có, build PWA allowlist, xác minh runtime version và parity sau deploy, xác minh xuất bản web. Lỗi baseline của các test source-contract phải ghi rõ, không gọi toàn repo PASS.
