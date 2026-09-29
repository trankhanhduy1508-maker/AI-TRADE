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


## Mã nguồn MT5 DEMO sau sửa protective SL và idempotence (29/09/2026)

**Trạng thái đúng theo evidence:** mã nguồn kiểm thử PASS; **APK release tự giao dịch MT5 DEMO chưa hoàn thành và chưa được ký.** Các ghi nhận lịch sử nói protective SL chưa sửa ở trên đã được thay thế bằng commit mới dưới đây, nhưng không được suy ra broker DEMO E2E PASS.

### Thay đổi trên đúng nhánh `codex/p0-covel-knowledge-audit`

- `a3a388c70c2ef9bd78e402a560edc15e21d62d0e` / `af694d9cf7d6d892be5b335fb9fbbb84c7e9a1dc`: yêu cầu protective SL hữu hạn và dương trước lệnh mở MT5 DEMO trực tiếp; từ chối TP không hợp lệ; sửa đường chỉnh SL/TP; hậu kiểm tài khoản DEMO sau khi đọc vị thế. Test âm bao phủ missing/NaN/infinite/nonpositive stop, broker switch và bảo đảm không gọi order-send khi đầu vào sai.
- `387938602f4ab67f059e45b3529cc173dc0bcdd0`: adapter cloud MetaApi DEMO cũng bắt SL hợp lệ; yêu cầu ledger SQLite bền vững khi có khả năng gửi; thay ghi `SUBMITTING` bằng atomic intent claim trước mở/chỉnh/đóng; test concurrent stale precheck, timeout và restart. Atomic SQLite claim chỉ có hiệu lực với các worker dùng chung **cùng tệp**; không suy ra an toàn đa máy/vùng độc lập. MetaApi cloud không phải đường broker-to-Android đã nghiệm thu và không được tự mua dịch vụ.
- `08d4a7617606bb33ed3a30bf4a09ff25a98e6742`: expose unresolved `SUBMITTING` intents; chặn **mở rủi ro mới** trong coordinator và cloud engine khi còn mutation chưa đối soát, ngay cả khi SafetySnapshot báo `reconciled=true`. Không tự gửi lại lệnh khi timeout/crash; trạng thái phải đối chiếu broker bằng evidence thật. Không thay đổi chính sách đóng/giảm rủi ro dưới kill-switch.
- `2407fca941959530f863faac882b1fa4e499b2fb`: sửa fixture cloud test sau lỗi attribute do thụt dòng. `3e12e39a029a394af7f0f2f2e8dbc2e9b3e8d75a`: sửa PaperBrokerAdapter expose pending ledger cho coordinator, thêm test chặn lệnh mới nếu paper intent cũ chưa xác định và bổ sung QA workflow path filters cho paper. Lỗi QA trung gian được sửa tối thiểu và kiểm thử lại, không tính các run lỗi/hủy là PASS.

### Evidence QA tại đúng mã nguồn

- [Source-only QA 36530966738](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36530966738), SHA `3e12e39a029a394af7f0f2f2e8dbc2e9b3e8d75a`, job `109284332092`: **SUCCESS**; log **250 Python PASS / 16 Node PASS**, standalone Java security/portfolio contracts, 13 offline Android assets/whitelist, compile debug/release Java + lint PASS, release prerequisite **fail-closed PASS** khi thiếu approval/signer, xác nhận **không tạo APK**. Không có Android physical-device test, APK signing/install/upgrade hoặc broker DEMO order-send E2E.
- Các broker protocol probe trước đây PASS ở read-only DEMO preflight, **không chứng minh** lệnh mới gửi tới broker hoặc recovery sau lỗi broker. Không biến kết quả mô phỏng ledger thành broker acknowledgment thật.

### Kiểm tra Supabase và release (read-only cùng phiên)

- Dự án `oziktadfeenydvgobudr`: `runtime_config.enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, `order_intents=0`, số model `APPROVED` được phép broker orders = `0`. Không thay đổi các cờ/trạng thái này, không bật LIVE.
- GitHub Releases trả **0 release**. `product/CWS_AI_TRADE_RELEASE_APPROVAL.json` không tồn tại (GitHub contents API 404). Founder API đang chạy v6, verifier hiện triển khai v4; mã verifier mới đã bị chặn deploy trong handoff và không được lách safety gate để tự triển khai.
- Google OAuth native tiếp tục HOÃN; Google JWT/Founder entitlement của API hiện hành vẫn bắt buộc, tuyệt đối không được thay bằng anonymous/bypass.

### Blocker bên ngoài source-only QA, chưa được phép gọi DONE

1. Thiếu model/chiến lược deterministic được phê duyệt bằng provenance và kiểm định riêng (OOS, walk-forward, spread/slippage/cost, paper-forward) và risk profile/DEMO send được Founder cho phép; kiến thức Masterbook và rule engine chỉ là nguyên liệu, không tự nâng thành model approved.
2. Chưa nghiệm thu Android thực và full HTTPS Founder token → `/verify-demo` → verifier → MT5 DEMO broker → `/snapshot` → Android gồm Balance, Equity, positions/P&L; chưa kiểm thử broker **order acknowledgment**, đối soát server-side, timeout và khởi động lại dưới lệnh DEMO thật. Không có quyền/secret để thay thế xác thực chủ tài khoản.
3. Thiếu keystore ổn định do Founder quản lý bên ngoài Git checkout, release public-key pin, Founder approval manifest và bằng chứng cùng signer/versionCode tăng khi install, update, encrypted-data migration và native recovery trên Android. Không commit keystore/password/secret; debug APK hoặc unit test với signer giả không phải release.

**Kết luận nghiệm thu:** deterministic engine và safety source được củng cố; SOURCE QA PASS tại SHA nêu trên. **Chưa có bản APK release được ký hay khả năng bật auto-trade DEMO đã nghiệm thu.** Giữ fail-closed và chỉ tiếp tục với xác thực, approval, signing và Android/broker evidence thật.


## Nghiên cứu chiến lược và risk DEMO tự thiết kế (29/09/2026)

**Phạm vi:** Founder giao tự thiết kế ứng viên chiến lược deterministic và cấu hình risk cho MT5 DEMO. Chỉ nhánh codex/p0-covel-knowledge-audit; không thay Main/Stable/Production, không dùng máy Founder, không tốn dịch vụ mới, không bật runtime DEMO-send/risk/LIVE hoặc bypass Founder authentication.

### Mã đã bổ sung

- [Risk caps 89444f31](https://github.com/trankhanhduy1508-maker/AI-TRADE/commit/89444f31e65c6f846cf5cc5a5948930abd9938bd): bổ sung giới hạn broker equity, rủi ro tiền dự kiến từ khoảng entry đến SL và loss-side tick value/lot, giới hạn lỗ ngày theo equity, từ chối metadata thiếu/sai currency.
- [Ứng viên 96f0e2cc](https://github.com/trankhanhduy1508-maker/AI-TRADE/commit/96f0e2cc38b3277596971afb0b96da3c21ff7818): source src/execution/demo_candidate.py và strategies/CWS_DEMO_TF014_EURUSD_H4_CANDIDATE.md. Phiên bản CWS-DEMO-TF014-EURUSD-H4-V1: EURUSD H4, 60 nến đóng để warmup, momentum 20 nến, protective stop từ 10 nến trước, trailing 20 nến, không pyramiding. Dữ liệu không hữu hạn/nến chưa đóng/timestamp trùng hoặc đảo thứ tự -> ABSTAIN. RESEARCH_CANDIDATE, broker_orders_approved=false; không tự nâng thành mô hình duyệt.
- [MT5 broker metadata d6251f2b](https://github.com/trankhanhduy1508-maker/AI-TRADE/commit/d6251f2b85b2fe69d96f5473ac0954738340543e): verified_demo_risk_context lấy equity, balance, tick-size và loss-side tick-value/lot từ MT5 DEMO; tính account-wide positions/symbol volume, lỗ giao dịch đóng của toàn tài khoản và floating loss âm; so login/server/currency trước và sau readback. Thiếu broker metadata hoặc đổi account -> fail closed. Chưa nối E2E đến APK.

**Thông số risk ứng viên:** max 0,01 lot/lệnh và /symbol, 1 vị thế trên tài khoản, spread 20 broker points, lỗ ngày tối đa 100 USD hoặc 1% equity (mức chạm trước), stop exposure tối đa 0,25% verified broker equity, USD account, broker-side protective SL bắt buộc. Khoảng lỗ đến SL là ước tính, có thể bị vượt do gap/slippage/chi phí. Chưa triển khai cấu hình này thành quyền giao dịch.

### QA có thể kiểm chứng

- [Source QA 36531889315](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36531889315): SUCCESS tại 96f0e2cc; 259 Python + 16 Node PASS.
- [Source QA 36532127519](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36532127519): SUCCESS tại d6251f2b; **263 Python + 16 Node PASS**, Java debug/release compilation + lint, release signing gate fail-closed đúng thiết kế, **không tạo APK**. Các test broker dùng fake, chưa phải broker order-send hoặc Android physical-device E2E.

### BLOCKER phát hành còn nguyên

Runtime Supabase đọc trực tiếp: enabled=false, demo_send_enabled=false, risk_profile_approved=false, approved_execution_models=0, order_intents=0. GitHub Releases=0 và release approval manifest chưa tồn tại.

1. Chiến lược mới vẫn thiếu OOS, walk-forward, kiểm chi phí/spread/slippage, next-open/gap và forward paper trên dữ liệu broker thật; không kế thừa bằng chứng TF-004 đã bị bác bỏ và không tự tạo model APPROVED.
2. Chưa nghiệm thu xác thực Founder -> MT5 DEMO login/server/password và account snapshot -> order-check/send cùng SL broker acknowledgement -> reconciliation/restart -> Android thực. Không lách các giới hạn tool/safety hoặc tự bật execution.
3. Chưa có khóa ký release ổn định do Founder quản lý bên ngoài Git, public-key pin, release approval và thử cài/update/recovery cùng signer trên Android thực. Không đóng gói debug APK giả danh bản release. Native Google OAuth vẫn hoãn; xác thực Founder hiện có không được bỏ.

**Kết luận:** ứng viên chiến lược và risk code đã có, source-only QA PASS. Bản APK MT5 DEMO tự giao dịch **chưa thể bàn giao hợp lệ** cho đến khi có bằng chứng broker, chiến lược, signing và thiết bị thật.


## Founder đồng ý thử lệnh MT5 DEMO có điều kiện (29/09/2026)

Founder đã trả lời **"Tôi cho phép"** sau đề xuất thử lệnh có giới hạn trên **MT5 DEMO, chỉ sau khi kiểm định đạt yêu cầu** và quản lý ký release/cài thử. Phạm vi được hiểu là cho phép tiến hành các bước kiểm định và phép thử DEMO nhỏ theo profile nghiên cứu đã nêu, không phải xác nhận rằng chiến lược đã qua OOS/WF/forward hoặc rằng đã trao khóa ký hay quyền bỏ xác thực. Không cho phép LIVE, đặt lệnh không có SL, bỏ kill-switch, truy cập tài khoản khác, hay tự đánh dấu approval/evidence giả.

### Thực thi sau khi nhận phép thử

- [Commit eedd3f29](https://github.com/trankhanhduy1508-maker/AI-TRADE/commit/eedd3f29400a91dec8c76d78b8a5f41e771d98b3) gia cố đóng nến H4: ứng viên từ chối H1/M15 bị đưa nhầm dưới nhãn H4, gap lịch sử quá dài; adapter không còn tự sắp xếp/che giấu timestamp broker đảo thứ tự hay trùng nhau. Bổ sung ba test fail-closed, một số có nhiều biến thể.
- [Source QA 36560397006](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36560397006), job 109379603478 ở commit eedd3f29: **SUCCESS: 266 Python PASS, 16 Node PASS**, Java debug/release compile + lint, release prerequisite fail-closed PASS. Job kiểm chứng **không assemble/không giao APK**; không có lệnh broker DEMO hay thử Android thiết bị thật trong run này.
- Supabase read-only sau phép cho: enabled=false, demo_send_enabled=false, risk_profile_approved=false, forward_shadow_trades=0, approved_execution_models=0, order_intents=0. Vì chưa có dữ liệu forward/model được duyệt, các điều kiện đã được chính Founder nêu vẫn chưa đạt; **không tự thay đổi gate** hay phát lệnh dưới vỏ bọc phép cho.
- Runtime runner hiện tại vẫn hard-block option enable-demo-send, cloud runner chưa nối server-authoritative per-order approval và broker readback/strategy candidate không được tích hợp E2E. Các broker login/order actions trước đó từng bị tool safety chặn; không dùng một con đường thay thế để lách. Founder-owned release keystore/public-key pin và Android install/update evidence chưa có.

**Trạng thái:** CHẤP NHẬN PHẠM VI PHÉP THỬ DEMO; KIỂM THỬ MÃ NGUỒN PASS; GỬI LỆNH DEMO CHƯA ĐỦ ĐIỀU KIỆN; APK RELEASE CHƯA CÓ. Không biến phản hồi "Tôi cho phép" thành approval của mô hình, ký hộ hay bằng chứng E2E.
