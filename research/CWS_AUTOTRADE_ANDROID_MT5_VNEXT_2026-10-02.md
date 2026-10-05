# CWS AUTOTRADE ANDROID ↔ MT5 VNEXT — 2026-10-02

## Nguyên tắc
Không xây lại AutoTrade từ đầu. Tái sử dụng các thành phần đã có và chỉ sửa đúng lớp đang thiếu.

## Thành phần đã có
- Android native MT5 screen: broker selector, Login, Password, session restore.
- Supabase `ai-trade-mt5-session`: connect/account/disconnect.
- Supabase `ai-trade-tick`: strategy + risk + compliance + MetaApi execution lane.
- DB state: runtime config, order intents, managed positions, events.
- MT5 DEMO verifier/readback.
- Render Free thin proxy chỉ là phụ, không nằm trong đường bắt buộc.

## Kiến trúc chuẩn
```text
Android APK
  -> ai-trade-mt5-session
      -> MT5 DEMO login/session
      -> opaque session token (Android Keystore)

Android control/status
  -> Supabase control plane
      -> runtime readiness
      -> kill switch
      -> risk/compliance approvals

Supabase scheduler/event
  -> ai-trade-tick
      -> strategy hiện có
      -> risk gate
      -> compliance gate
      -> order intent dedupe
      -> MetaApi
      -> MT5 DEMO

Render
  -> KHÔNG bắt buộc trong critical path
  -> chỉ thin proxy nếu có use case riêng
```

## Mục tiêu “nhạy”
“Nhạy” không có nghĩa polling dày hoặc vào lệnh nhiều hơn.

1. Xử lý ngay sau closed bar hợp lệ.
2. Một bar chỉ có một intent, idempotent theo strategy/symbol/bar/action.
3. Scheduler chỉ đánh thức execution gần thời điểm cần, không vòng lặp 30 giây vô tận.
4. Android refresh trạng thái ngay sau connect, reconnect và khi app resume.
5. Broker/account snapshot phải fresh; stale thì BLOCKED.
6. UI hiển thị blocker thật thay vì chỉ nút xám:
   - APPROVAL_REQUIRED
   - RISK_NOT_APPROVED
   - EXECUTION_DISABLED
   - DEMO_SEND_DISABLED
   - PROVIDER_NOT_READY
   - KILL_SWITCH_ACTIVE
   - SESSION_REQUIRED

## AutoTrade control
Android KHÔNG giữ cron secret, MetaApi token hoặc quyền order-send.

Nút AutoTrade chỉ gửi yêu cầu control qua endpoint server-authoritative.
Backend mới được phép đổi trạng thái khi tất cả gate đã pass.

Không để APK gọi trực tiếp `ai-trade-tick` bằng cron secret.

## Trạng thái runtime tại checkpoint này
- MT5 session backend REAL DEMO E2E: PASS.
- Android source QA HEAD `64f64c368d1d7965d39bac9091a8fbb5c94f6145`: PASS.
- Android device smoke cùng HEAD: PASS.
- DEMO APK build cùng HEAD: PASS.
- AutoTrade execution: chưa unlock.
- Live money: LOCKED.
- orders_sent: 0.
- runtime approval/risk/demo-send gates vẫn fail-closed.

## Sửa Android trong vòng này
- password contract đồng bộ backend: 4–32 ký tự;
- không xóa session cũ trước khi validate input mới;
- thêm `X-CWS-Client` + version để trace request trong runtime logs;
- phân biệt timeout/DNS/bridge unavailable;
- versionCode 4, versionName `0.4.0-demo`.

## Bước phát triển tiếp theo
1. Tạo AutoTrade status/control endpoint server-authoritative.
2. Trả blocker list cụ thể cho Android.
3. Android bật nút chỉ khi server trả DEMO_READY.
4. Scheduler closed-bar gọi `ai-trade-tick` trực tiếp trong Supabase.
5. Reconcile broker positions sau restart/reconnect.
6. Test DEMO order E2E với volume tối thiểu sau khi approval + risk + provider đều PASS.
7. Chỉ sau DEMO evidence mới bàn tới live-money.

## Quy tắc không đổi
- không fake PASS;
- không dùng APK cũ làm evidence cho source mới;
- không lưu credential trong APK;
- không bật order_send bằng env flag;
- không để Render làm trading brain;
- không live-money trước gate riêng.
