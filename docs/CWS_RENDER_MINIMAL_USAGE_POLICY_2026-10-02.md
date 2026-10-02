# CWS — QUY TẮC SỬ DỤNG RENDER.COM TIẾT KIỆM

**Ngày chốt:** 2026-10-02  
**Phạm vi:** toàn bộ CWS, đặc biệt CWS AutoTrade.

## Founder intent

Render.com chỉ là tài nguyên phụ. Mục tiêu là **giao cho Render ít việc nhất có thể** để giảm quota, chi phí và rủi ro phụ thuộc nền tảng.

## Luật bắt buộc

1. **Không dùng Render làm nơi lưu trữ file hoặc source of truth.**
   - Không lưu APK, video, ảnh, dataset, model, log dài hạn hoặc file người dùng trên filesystem Render.
   - Không dựa vào local disk của Free Web Service cho dữ liệu cần tồn tại sau restart/sleep/redeploy.
   - File bền vững phải đi qua storage chuyên dụng đã có của CWS, hoặc Supabase/Google Drive/B2 tùy luồng đã được chốt.

2. **Không dùng Render làm database/state store.**
   - Không giữ session, position, order intent, kill switch, queue hoặc audit state quan trọng chỉ trên Render.
   - Với AutoTrade, Supabase là source of truth cho state/risk/compliance/audit.

3. **Render chỉ làm compute/gateway mỏng khi có lý do rõ ràng.**
   - Ưu tiên request ngắn, stateless, run-once.
   - Không polling vô hạn nếu Supabase/event-driven có thể thay.
   - Không keep-alive chỉ để ngăn Free service ngủ.
   - Không load model AI lớn trên Render nếu có thể chạy ở lớp khác.

4. **Plugin/connector trước.**
   - Kiểm tra Render connector và service hiện có trước khi tạo service mới.
   - Không tạo service trùng.
   - Auto-deploy mặc định OFF cho CWS nếu không có quyết định riêng.

5. **Không tiêu quota Render cho việc nền tảng khác làm tốt hơn.**
   - Storage -> storage chuyên dụng.
   - State/database -> Supabase/Postgres.
   - Scheduler/event -> Supabase/cron/webhook khi phù hợp.
   - Render chỉ nhận phần còn lại mà thật sự cần runtime riêng.

6. **Mọi thay đổi làm Render nặng hơn phải có lý do.**
   Trước khi thêm package, worker loop, disk, cron, background task hoặc storage lên Render, phải trả lời được:
   - Tại sao không làm ở Supabase/connector/storage hiện có?
   - Tăng quota/chi phí gì?
   - Có đường stateless nhẹ hơn không?

7. **Không đánh đổi an toàn để tiết kiệm quota.**
   Với AutoTrade:
   - DEMO/live-money gate vẫn fail-closed.
   - Render không có quyền tự bật broker order execution.
   - Risk/compliance/kill-switch phải nằm ở server-authoritative layer.

## Kiến trúc AutoTrade chuẩn hiện tại

```text
Android / caller
    -> Render Free thin proxy (chỉ khi cần)
        -> Supabase ai-trade-tick
            -> state/risk/compliance/audit
            -> MetaApi/MT5 DEMO
```

Render không giữ state và không phải trading brain.

## Quy tắc cho chat/agent sau

Khi đọc repo này:
- không đề xuất chuyển file/storage/state sang Render chỉ vì “tiện”;
- không nghiên cứu lại Render từ đầu;
- đọc checkpoint Render mới nhất trước;
- giữ nguyên nguyên tắc **Render = ít việc nhất có thể** trừ khi Founder đổi quyết định.
