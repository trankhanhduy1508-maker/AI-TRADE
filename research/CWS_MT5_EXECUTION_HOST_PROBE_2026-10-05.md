# Kiểm tra host thực thi MT5 — 2026-10-05 17:29 Asia/Saigon

Mục tiêu Founder: mở MT5 và thấy lệnh bot DEMO. Chưa đạt; orders_sent=0, không có ticket broker để bàn giao.

Đã kiểm tra đường host thay cho việc lặp lại chỉnh UI/risk:
- DigitalOcean connector list: droplets=[]; không có máy cloud hiện hữu để cài MT5.
- CWS PC Commander health: lần đầu UNAVAILABLE/429, lần hai UNAVAILABLE/404. Không đọc/sửa PC cá nhân, không giả host online.
- Cloud scratch Linux: apt-get update thất bại với Operation not permitted / failed setgroups, exit 100. Không tắt cơ chế bảo vệ hay yêu cầu sandbox escalation.
- Download script chính thức từ tài liệu MetaQuotes Linux: HTTP 403; không thực thi script, không cài Wine/MT5.
- MetaQuotes hỗ trợ MT5 qua Wine trên Linux: https://www.metatrader5.com/en/terminal/help/start_advanced/install_linux . Hướng này cần host có quyền cài và môi trường vận hành bền vững, chưa được kiểm chứng trên host hiện tại.
- MetaApi pricing hiện tại là subscription regular $30/tháng + API usage; one free MT account nằm trong subscription, không có bằng chứng miễn phí lâu dài: https://metaapi.cloud/ . Không mua/tạo subscription hay gửi credential sang MetaApi.

Policy DEMO đã được Founder giao quyền chọn ở checkpoint trước, không hỏi lại numeric risk approval. Blocker giờ là quyền truy cập host thực thi phù hợp. Nếu dùng host Windows/VPS sẵn cần owner chỉ định host được phép dùng; nếu thuê mới cần owner xác nhận ngân sách vì phát sinh tiền thật. Không bật tick The5ers/TF004 để tạo trạng thái active giả. Có host vẫn cần nối TF-013A, kiểm chứng broker account/positions/contracts/SL và lifecycle trước tự động submit; không ép tín hiệu chỉ để hiển thị lệnh.
