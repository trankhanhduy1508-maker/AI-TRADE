# CWS AI Trade trên Google Sites

Ngày cập nhật: 2026-09-28  
Branch: `codex/p0-covel-knowledge-audit`  
Chủ sở hữu mã nguồn: CWS / Duy Trần

## Link website đã triển khai

**Website độc lập, sẵn sàng nhúng vào Google Sites:**

https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site

Health: https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site?health=1

**Lưu ý:** website ở URL trên đã được triển khai qua Supabase. Google Site riêng của Founder **chưa được tạo/xuất bản**, vì không có phiên chỉnh sửa Google Sites của đúng tài khoản trong connector hiện tại. Đừng gọi việc dựng website độc lập là Google Site đã publish.

## Cách nhúng vào Google Sites

1. Trong trình duyệt thông thường, đăng nhập Google account muốn sở hữu Site rồi mở https://sites.google.com/new.
2. Tạo Google Site, đặt tên `CWS AI Trade`.
3. Dùng **Trang → Thêm → Nhúng toàn trang (Full page embed)** hoặc **Chèn → Nhúng → URL**.
4. Dán URL website Supabase ở trên. Chọn full width, chỉnh chiều cao để dashboard không bị cắt.
5. Dùng Preview trên mobile và desktop, sau đó mới bấm Publish.
6. Kiểm tra Site URL thực tế và quyền truy cập sau Publish.

Website được nhúng là bản **đọc và nghiên cứu**, không phải Founder Secure chứa dữ liệu riêng.

## Thành phần hiện tại

- Giao diện trading xanh đen, tối ưu desktop/mobile.
- 16 dòng thị trường theo thứ tự nhất quán.
- Chart nến lấy từ `ai-trade-dashboard?format=preview-candles` bằng public market data.
- Chỉ 14/16 symbols hiện có feed công khai; EURJPY/XAGUSD hiển thị trạng thái `Feed chưa hỗ trợ`, không vẽ nến giả.
- Bảng danh mục: từng symbol chỉ một dòng, cộng Lot và P/L của nhiều position cùng cặp.
- Tổng lãi, tổng lỗ, net P/L và tổng Lot; nếu dữ liệu thiếu thì hiển thị `—`.
- Nạp JSON position trực tiếp vào browser RAM; không upload file, **chưa được broker xác minh**.
- Dữ liệu DEMO UI luôn gắn nhãn `MINH HỌA`.
- Knowledge Search tự tải bản đúc kết Masterbook công khai ở GitHub.
- Người dùng nạp EPUB Masterbook để tra cứu **toàn bộ chương ngay trên thiết bị**. EPUB không tự đăng lên website hoặc backend.
- AI Chat trong Site là tìm kiếm có nguồn, **không phải mô hình ChatGPT**.
- Nút `Sao chép câu hỏi + nguồn`, `Mở ChatGPT` và `Kết nối CWS AI Trade Knowledge` chuyển nghiên cứu sang tài khoản ChatGPT của người dùng.

Plugin ChatGPT riêng:

https://chatgpt.com/plugins/plugins_6aba1b6ee1fc8191a5c446b1558538d3

MCP read-only:

https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-knowledge-mcp

Tools: `search_masterbook`, `search_backtest_evidence`, `get_public_candles`, `read_safety_gates`.

MCP chỉ đọc các tài liệu **đúc kết công khai** và report public ở repo. Nó **không** đọc EPUB cá nhân trừ khi người dùng chủ động nạp vào trình duyệt hoặc cung cấp tài liệu cho phiên ChatGPT. Không gọi việc index bản đúc kết là đã ingest trọn 49 trang.

## Kiến trúc không phụ thuộc AppDeploy

- Mã nguồn trang: thư mục này.
- HTTPS site: Supabase Edge Function `cws-ai-trade-site`.
- Market chart: public endpoint hiện có của `ai-trade-dashboard`.
- Masterbook distilled: GitHub public, commit pin cố định.
- EPUB import: JSZip (CDN), parse trong browser.
- ChatGPT: plugin MCP public read-only, chạy bằng tài khoản ChatGPT đã kết nối.
- Original Founder Secure giữ nguyên; không dùng AppDeploy làm dependency cho site mới.

**Miễn phí có giới hạn:** CWS không tính quota riêng cho thao tác UI, không cần OpenAI API key cho search/lookup hiện tại. Supabase, GitHub, CDN và ChatGPT vẫn có giới hạn gói/dung lượng/lưu lượng và chính sách của bên cung cấp; không hứa unlimited hoặc miễn phí vĩnh viễn. Nếu sau này cần GPT tự trả lời ngay *trong website*, phải có model inference riêng với tài nguyên thực tế hoặc API được cấp phép; hiện **không** tự kích hoạt billing.

## Data contract mẫu

```json
[
  {"symbol":"EURUSD","side":"BUY","lot":1,"floatingPL":20},
  {"symbol":"EURUSD","side":"BUY","lot":2,"floatingPL":-5}
]
```

Kết quả: EURUSD hiển thị **3.00 lot**, P/L **+$15.00**, một dòng duy nhất. Bản ghi không có `lot` hoặc `floatingPL` -> phần tổng liên quan = `—`, không thay thế bằng synthetic volume, R hoặc lot giả.

## Bảo mật và ranh giới

- Không lấy token/cookie của Founder Secure từ Google Sites iframe hay từ nguồn công khai.
- Không có API đặt lệnh, quản lý tiền hoặc gửi tín hiệu lệnh broker.
- `brokerOrders=false`; live-money/risk/The5ers gate nguyên trạng.
- Public MCP không có quyền truy cập position, account balance hoặc broker secrets.
- Local JSON/EPUB chỉ lưu trên bộ nhớ phiên; reload cần nạp lại.
- Không dùng thành tích practitioner hoặc backtest làm bằng chứng chắc thắng.

## Tình trạng kiểm thử

- GitHub JS parse / mock client startup PASS.
- Pure aggregation PASS: cộng Lot, gom symbol, missing-value guard, mixed BUY/SELL.
- Supabase site ACTIVE v3, health và JS asset URLs HTTP thực tế PASS.
- Public EURUSD H1 candles endpoint HTTP thực tế PASS.
- MCP initialize/tools/list/search thực tế HTTP PASS.
- **Google Sites embed/publish, Android visual QA, EPUB import live browser và ChatGPT plugin install trên tài khoản vẫn PENDING**. Không fake PASS.

## Cập nhật

Sau khi sửa `index.html`, `app.js`, `portfolio.js` hoặc `styles.css`, phải cập nhật bundle trong `supabase/functions/cws-ai-trade-site/index.ts` và deploy lại Edge Function có evidence thực tế. Git push không tự xuất bản site; đây là manual deploy có chủ đích.
