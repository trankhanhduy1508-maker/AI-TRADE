# CWS AutoTrade Android / MT5 DEMO — checkpoint an toàn, APK-first (29/09/2026)

> **CẬP NHẬT READ-ONLY BROKER QA (29/09):** source commit `a83e83c631137900a403178933734fe126f04791` tăng kiểm soát `src/execution/demo_readback.py`: tối đa 1000 vị thế, ticket duy nhất đúng định dạng, mã cặp đúng định dạng, giới hạn lot/P&L, bắt thay đổi currency khi đọc broker, phân biệt danh sách rỗng được broker xác nhận với dữ liệu unavailable. [Source-only QA 36529015884](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36529015884) **SUCCESS: 204 Python + 16 Node tests**, Java standalone contracts, Android debug/release compile + lint PASS; **không tạo APK**. Google OAuth vẫn HOÃN. API Founder v6 ACTIVE, Edge verifier v4 ACTIVE (source mới chưa deploy), DEMO/LIVE/release gates giữ khóa.


**Repo:** `trankhanhduy1508-maker/AI-TRADE`  
**Nhánh duy nhất:** `codex/p0-covel-knowledge-audit`  
**HEAD mã nguồn nghiệm thu source-only:** `a162feada1f2bb2113c2acb6bcef414a9c0d337a`  
**Google OAuth:** HOÃN theo chỉ thị mới. Không sửa native Google login hoặc mở bypass đối với API Founder.

## Thay đổi thực hiện và kết quả đã xác minh

1. **Founder API v6, triển khai ACTIVE.** Commit `e4dfe891d4a368d47fe2d645abde79a600bb3243` sửa phân biệt kết quả investor readback với một lần master-password login đã xác thực. `/snapshot` chỉ đọc broker, không tự ghi `connection_state=CONNECTED` sau khi verify password thất bại; hậu kiểm binding còn hiệu lực và **đúng cùng Google Founder user** sau network request. `/verify-demo` cũng tái kiểm tra entitlement trước khi ghi trạng thái CONNECTED. Đã đọc lại Supabase deployment `ai-trade-founder-mt5` **ACTIVE v6**, xác nhận mã hậu kiểm nằm trong deployment; **chưa có Google Founder/device/broker end-to-end**.
2. **Android không nhận kết quả broker cũ khi đang verify lại.** Commit `425fec856c29d0e4b037d101bb46ae39a389f40a` bổ sung `brokerGeneration` kiểm soát đồng thời refresh và verify-demo: chỉ thao tác đang hiện hành được cập nhật balance/equity/positions và trạng thái nút. Có Python static regression tests và Android compile/lint; **chưa thử Android device race**.
3. **Fencing investor cùng MetaQuotes-Demo server.** Commit `b2fa5c24f22dfe4f07074407bcae1eceffbe2c87` so sánh thêm account name/company/leverage/server-build/rights ở hai lần cmd=3 bao quanh cmd=4, ngăn trường hợp broker đổi các thuộc tính account nhưng server và currency không đổi. Test offline Node PASS. Giới hạn: protocol cmd=3 hiện chưa mang account login độc lập; tên giống nhau vẫn chưa bảo đảm account identity. **Bản source mới CHƯA TRIỂN KHAI**: thao tác deploy Edge verifier bị bộ kiểm tra an toàn công cụ chặn; không thử bypass. Deployed `ai-trade-mt5-demo-validate` vẫn **ACTIVE v4**, không được báo v5 hoặc E2E PASS.
4. **Đường order intent cục bộ giữ bất biến an toàn.** Commit `5abfbf6db71e126280c5dd43f6dde14063f50257`: claim bằng SQLite `INSERT ... ON CONFLICT DO NOTHING` trước các đường broker mutation, kiểm tranh chấp lại nếu pre-check stale. Commit `26b369459ae5f430b70c90c18f2fa44bc2025c2b`: chỉ cho phép adapter có quyền gửi lệnh khi ledger nằm ở tệp bền vững, không dùng SQLite `:memory:` hoặc đường rỗng; read-only mode vẫn được dùng in-memory. Đã thử tình huống hai connection dùng CHUNG SQLite file, giả lập stale pre-check, restart và negative ledger. **Không tuyên bố duplicate-safe qua hai PC/vùng máy không dùng chung ledger**.
5. **Investor-only MT5 có thể đọc mà không cấp quyền đặt lệnh.** Commit `a162feada1f2bb2113c2acb6bcef414a9c0d337a` cho phép `allow_order_send=false` kết nối tài khoản DEMO có `trade_allowed=false` để lấy fresh account snapshot/positions với identity vẫn fenced. Trước mỗi broker mutation vẫn bắt `trade_allowed=true`, `trade_expert=true`, DEMO và đúng account; LIVE luôn khóa. Có unit negative test không gửi lệnh.

## Evidence thực

- [QA Android source-only 36528569258](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36528569258) tại `a162feada1f2bb2113c2acb6bcef414a9c0d337a`: **SUCCESS**, **195 Python tests PASS**, **16 Node tests PASS**, standalone Java contracts PASS, build/merge first-party assets và compile debug/release Java + lintDebug PASS, release-gate negative PASS. **Không assemble, ký, cài hoặc xuất APK.**
- [MT5 DEMO investor preflight 36528572266](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36528572266) tại `a162feada1f2bb2113c2acb6bcef414a9c0d337a`: **SUCCESS** cho broker Python investor readback/protocol trong môi trường cloud. Không chứng minh HTTP Edge Founder→verifier→Android hoặc bất kỳ broker DEMO order.
- Read-only Supabase SQL cuối: `runtime_config.enabled=false`; `demo_send_enabled=false`; `risk_profile_approved=false`; `order_intents=0`; `approved_models=0`. Không bật gate, thay đổi model hoặc LIVE. Không thay Main/Stable/Production; chỉ nhánh nêu trên.
- GitHub Releases hiện chưa có signed stable APK; `product/CWS_AI_TRADE_RELEASE_APPROVAL.json` vẫn không có trên nhánh. `release-signing.gradle` từ chối sản xuất khi thiếu owner-managed keystore, public-key pin và Founder approval.
- Bản sửa bổ sung bắt buộc protective SL tại adapter trực tiếp **không nằm trong HEAD** vì thao tác tạo unit test bị công cụ kiểm tra an toàn chặn; không chuyển bản mã chưa kiểm thử vào nhánh, không coi yêu cầu đó đã PASS.

## Còn BLOCKED trước khi giao APK đầy đủ

- Google OAuth native đang HOÃN theo chỉ thị Founder; Founder JWT/entitlement không được bypass.
- Thiếu một lần full E2E có credentials chủ sở hữu, Edge broker verifier và Android thực; verifier source mới chưa được deploy. Chưa có chứng cứ runtime direct login → equity/positions → UI trên thiết bị.
- Không có model được phê duyệt bằng provenance/giấy phép, OOS, walk-forward, realistic costs và paper-forward. Risk profile và DEMO send vẫn tắt; không có real broker DEMO execution, error/restart/reconciliation E2E. Cần bảo đảm mọi đường đặt lệnh, kể cả adapter trực tiếp, bắt buộc protective stop.
- Thiếu release signing key ổn định do chủ sở hữu quản lý, phiên bản release ký, install/update giữ dữ liệu, Android device migration và bản recovery cùng signer có versionCode tăng.

**Trạng thái đúng: source-only QA và Python broker investor preflight PASS; Founder API v6 ACTIVE; verifier v4 ACTIVE; quyền order, LIVE và release vẫn khóa. KHÔNG CÓ APK HOÀN CHỈNH.**


## Kiểm tra độc lập chỉ đọc — HEAD 6fe34206 (29/09/2026)

**Phạm vi:** Đọc đúng nhánh `codex/p0-covel-knowledge-audit`, hai handoff bắt buộc, nguồn adapter, log CI và trạng thái Supabase hiện hành. Không thao tác Main/Stable/Production; không thực hiện lệnh broker; không bật DEMO-send, risk hoặc LIVE; không xuất APK debug làm release.

- **HEAD kiểm tra trước ghi:** `6fe34206a01009e3f8ceb6465d8aa93acdd84eac` (commit chỉ cập nhật tài liệu so với `8d620ec221c866c42f7e313e1e64d6278377b3b5`). Mã adapter hiện hành `src/execution/mt5_adapter.py` blob `49df36b9c9d6dad5c0cfe5b22a715369caf07e87`.
- **Bằng chứng QA tồn tại, không phải QA mới:** [source-only run 36529015884](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36529015884), job `109278250398` có kết luận SUCCESS, log ghi **204 Python passed**, job biên dịch Android Java + lint và kiểm release-gate âm thành công; job chủ động xác nhận **không assemble/không giao APK**. Test Node được ghi nhận **16** trong handoff, không suy ra Android device E2E.
- **Lỗi protective SL chưa khắc phục:** `MT5OrderRequest.stop_loss` còn tùy chọn; `MT5BrokerAdapter.submit()` chưa từ chối SL thiếu/không hữu hạn trước khi đi vào `_validate_contract`. `MT5SymbolContract.rejection_reason()` chỉ xét SL khi giá trị khác `None`; `_request_dict()` bỏ trường `sl` nếu thiếu. Vì vậy đường gọi adapter trực tiếp có khả năng tạo lệnh mở không gắn protective SL **nếu** gate gửi DEMO được mở trong tương lai. Chưa sửa/chưa báo PASS; lịch sử handoff ghi thao tác tạo test bảo vệ từng bị công cụ an toàn chặn, không được lách chặn đó.
- **Supabase đọc trực tiếp tại phiên này:** dự án `oziktadfeenydvgobudr`, `ai_trade.runtime_config.enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`; `order_intents=0`; baseline được duyệt cho broker order = **0**. Hai Edge hiện triển khai: `ai-trade-founder-mt5` **ACTIVE v6** và `ai-trade-mt5-demo-validate` **ACTIVE v4**. Không tuyên bố verifier source mới đã được deploy.
- **BLOCKER nghiệm thu release:** chưa có owner-managed signer/keystore bên ngoài repo, key pin, `product/CWS_AI_TRADE_RELEASE_APPROVAL.json` và bằng chứng ký+cài đặt+cập nhật/khôi phục trên Android thực; chưa có full Founder-token → verifier → broker → Android E2E; chưa có model/risk được phê duyệt, broker DEMO order acknowledgement và reconciliation thực. **Chưa có APK release hoàn chỉnh.** Google OAuth native vẫn HOÃN nhưng xác thực/entitlement Founder hiện có phải được giữ nguyên.

**Hướng hoàn thiện còn được phép:** kiểm thử và sửa độc lập với OAuth khi công cụ cho phép; mọi protective SL, retry, ledger và broker reconciliation phải có test/evidence thật; không bật gate và không tạo bản release trước khi có signer, phê duyệt và Android E2E hợp lệ. Không coi kết quả đọc broker hoặc source QA là bằng chứng auto-trade thực.
