# FORM GIAO VIỆC — CWS AI TRADE / CHAT MỚI (28-09-2026)

@GitHub @Supabase @Google Drive

**TIẾP TỤC NGAY CWS AI TRADE TỪ CHECKPOINT THỰC TẾ.** Đây là chat mới. Tôi là Founder Duy Trần. Tự thao tác xuyên suốt trong phạm vi quyền plugin/connector; **không báo cáo giữa chừng, không hỏi lại từng bước, không dừng chỉ để đề xuất bước tiếp theo**. Chỉ báo hoàn thành sau khi kiểm tra **ba lớp**; nếu một yêu cầu buộc phải có tài khoản Founder, thiết bị thực, giấy phép hoặc phê duyệt mà công cụ không có, chứng minh blocker, hoàn tất tối đa các phần độc lập rồi bàn giao trạng thái chính xác.

## A. ĐÚNG REPO, NHÁNH, TÀI LIỆU

Repository: `trankhanhduy1508-maker/AI-TRADE`
Nhánh DUY NHẤT: `codex/p0-covel-knowledge-audit`
HEAD gần nhất đã kiểm chứng **trước khi tạo file bàn giao này**: `8ca1f89db05cb5af0f31f42bfd367be23844e15a`. **KHÔNG coi đây là HEAD cố định:** lấy HEAD mới nhất khi bắt đầu và sau mỗi checkpoint; không ghi đè commit của chat khác.

ĐỌC THEO THỨ TỰ, KHÔNG GROUND LẠI TOÀN REPO:
1. `knowledge/CWS_AI_TRADE_SELF_LEARNING_ENGINE_FOUNDER_INTENT_2026-09-28.md`
2. `docs/CWS_AI_TRADE_SELF_LEARNING_CHECKPOINT_2026-09-28.md` (phần cuối mới nhất)
3. `product/CWS_AI_TRADE_KINH_NGHIEM_CHAT_2026-09-28.md` (đặc biệt phần 11)
4. `product/CWS_AI_TRADE_SELF_LEARNING_WEBAPP_HANDOFF_2026-09-28.md`
5. Chỉ khi sửa đúng phân hệ: `src/self_learning/rights.py`, `android/README.md`, `google-sites/cws-ai-trade/README.md`, `supabase/migrations/20260928102300_ai_trade_known_replay_quarantine_cron_v1.sql`.

## B. NHỮNG GÌ ĐÃ CÓ, KHÔNG LÀM LẠI

- Supabase project `oziktadfeenydvgobudr`. Lần kiểm tra gần nhất: `cws-ai-trade-site` **v11 ACTIVE**, `ai-trade-dashboard` v36 ACTIVE, Knowledge MCP v1 ACTIVE. ACTIVE không thay cho GET runtime; kiểm tra health/HTML/bundle thật.
- UI Web App/PWA đọc dữ liệu giá công khai, **16 symbol**, aggregate nhiều position thành một dòng/symbol, tổng Lot, lãi dương, lỗ âm, net P/L. Thiếu dữ liệu để `—`; R của paper không phải USD của broker.
- Masterbook EPUB nguyên bản chỉ lưu riêng tư; bản Markdown đúc kết ở GitHub không phải toàn EPUB. Kho private có **hai source QUARANTINED**, trong đó TF-013A là **140 replay mô phỏng / 14 symbol / 15 lessons**. Supabase Cron thu thập phiên bản lúc **03:45 UTC** hằng ngày; không tự phê duyệt nguồn/training.
- Hai model nghiên cứu **REJECTED**. ECB là reference-rate informational, không phải executable broker price. BTC từ Coinbase mang `PROHIBITED_FOR_ML`; snapshot raw, weights và metrics đã redacted. Không có model production được duyệt.
- Android debug APK **mới** ở [cloud build 36416825217](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36416825217), commit `8ca1f89db05cb5af0f31f42bfd367be23844e15a`: đã generate first-party assets, assemble, verify và upload artifact. Đây là bản đóng gói **offline shell**, khác APK debug cũ lưu Drive. **Chưa** có test cài thật Android/offline E2E hoặc khóa ký release bền vững.
- Google Sites của tài khoản Founder **chưa có bằng chứng publish**. Supabase Web App không có nghĩa đã publish Google Site. Không sử dụng AppDeploy làm dependency.

## C. CÁC NHIỆM VỤ THỰC THI, KHÔNG HỎI LẠI

**1. Verify checkpoint và sửa sai có bằng chứng.** Đọc HEAD hiện tại, xác minh migration/DB model và knowledge state, xác minh runtime read-only, so sánh mã nguồn với bản deploy. Nếu test FAIL → tìm lỗi thật → minimal diff → test lại. Không gọi fixture là dữ liệu giao dịch thật.

**2. Quyền dữ liệu và self-learning.** Điều khoản [Coinbase Market Data](https://www.coinbase.com/legal/market_data), cập nhật 07-08-2026 mục 3(5), hạn chế ML nếu thiếu chấp thuận trước bằng văn bản. **Không gọi Coinbase API cho mục tiêu training/validation/benchmark, không phục hồi tombstone và không re-run BTC experiment.** Không gán license cho dữ liệu chỉ vì phần mềm tải có giấy phép mở. Kiểm tra rõ quyền ML, phạm vi thương mại, quyền derived work/model và nguồn chi phí của **từng provider**; giữ gate `src/self_learning/rights.py` fail-closed. Nếu có nguồn thật được cấp phép hợp lệ, preregister trước, pin raw/dataset/code hash, train baseline nhỏ, time-split + purge, OOS sealed, walk-forward, baseline so sánh, slippage/cost stress, paper-forward. FAIL thì lưu REJECTED và ABSTAIN; không tự đổi ngưỡng sau OOS.

**3. Kho kiến thức tự thu thập.** Kiểm tra cron và hai record hiện có, nguồn/version/hash, tính bất biến/RLS. Chỉ ingest nguồn có provenance và quyền đã khai; **quarantine không phải quyền train**. Giữ sách EPUB trong không gian riêng tư, không đẩy full text vào GitHub public hoặc Edge public. Không coi 140 replay là 140 broker trades.

**4. Hoàn thiện UI/Website/PWA.** Giữ 16 thị trường, Lot/P&L theo position rồi theo symbol, hướng BUY/SELL hỗn hợp, `—` khi thiếu giá trị. Hiển thị `MODEL_NOT_APPROVED`, `ABSTAIN` và `LOCKED` khi chưa có model đạt gate. Chỉ deploy Supabase có chủ ý sau khi kiểm tra mã nguồn; GET live health, HTML, manifest, SW, JS, chart và đối chiếu nguồn. Google Sites chỉ publish nếu có connector/browser đang xác thực đúng tài khoản Founder; không vượt quyền, không đòi Founder dùng PC. Nếu chưa có phiên chỉnh sửa thì giữ trạng thái PENDING, nhưng vẫn hoàn thiện Web App/PWA độc lập.

**5. Android thật, không nhầm debug với release.** Đọc `android/README.md` và chính xác source/commit APK offline-shell mới. Xác minh artifact cloud build, APK signature và first-party HTML/JS/icons đã đóng gói; không dùng artifact debug cũ để chứng minh bản mới. Dùng kiểm thử thiết bị thật/emulator được cấp quyền nếu thực sự có. Chỉ đánh dấu E2E khi cài/khởi động/offline/reopen/nạp EPUB/JSON đã chạy; không tuyên bố APK production nếu vẫn debug-signed. Không tạo billing hay signing key giả.

**6. Triple-check trước khi báo xong.** Ba lớp bắt buộc:
- Kiểm nguồn, provenance/licensing, HEAD/commit, source tree và SHA/hash.
- Test thực: regression/negative-path, static build, HTTP/bundle hoặc model OOS/WF; khi cần Android E2E phải có kết quả thiết bị.
- Đọc lại GitHub sau commit, Supabase DB/Edge sau deploy, artifact thực và các khóa an toàn. Bắt buộc `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false` và không tự tạo lệnh broker. Ghi evidence path và phân biệt PASS/PENDING/FAIL.

## D. GIỚI HẠN KHÔNG ĐƯỢC PHÁ

Không sửa Main/Stable/Production hoặc tạo nhánh khác. Không dùng PC Founder, AppDeploy, dịch vụ có phí/billing chưa duyệt. Ưu tiên plugin/connector → API/mã nguồn → giao diện. Không tự gửi lệnh thật/demo, không sửa broker execution, Risk Engine, kill-switch hoặc The5ers gate. **Live-money LOCKED.** Không fake PASS, không hứa lợi nhuận, không viết thành "hoàn thành toàn bộ" khi còn nguồn thiếu quyền, model bị loại, Google Sites chưa publish hoặc chưa có Android E2E.

## E. BÀN GIAO THẬT

Commit code/docs/evidence lên đúng nhánh, fast-forward không force, đọc lại file sau ghi. Chỉ báo một lần khi đã hoàn tất phần được phép và triple-check. Nếu bất kỳ gate nào còn thiếu, nói rõ phần đó PENDING/BLOCKED kèm bằng chứng; **không** dừng kỹ thuật chỉ để nêu "bước tiếp theo" khi vẫn còn việc tự thực hiện được.
