# Persistent recovery state

## Mục đích

`src/execution/recovery.py` có `PersistentRecoveryState` để trạng thái kết
nối và reconciliation không bị mặc định là an toàn sau khi process mở lại.

## Quy tắc fail-closed

- Bản ghi đầu tiên luôn là `connected=false`, `reconciled=false`.
- Mất kết nối ghi đồng thời cả hai cờ về `false`.
- Chỉ reconciliation chính xác mới ghi `connected=true` và
  `reconciled=true`.
- Process mở lại đọc SQLite state để giữ evidence, nhưng luôn reset runtime
  gate về `false/false`; process mới phải reconnect và reconcile lại trước khi
  được mở risk.
- State có `updated_at` UTC để làm nền cho heartbeat/staleness monitoring.

## Evidence

- Test persistence qua ba lần mở state và reset sau disconnect: `1 passed`.
- Test recovery/reconciliation hiện hành: `4 passed`.
- Full suite phải được chạy lại trước khi commit milestone.

Đây là contract/state evidence cục bộ. Nó chưa chứng minh broker
reconciliation thực tế, MT5 demo forward trading, 24/7 operation hoặc live
readiness.
