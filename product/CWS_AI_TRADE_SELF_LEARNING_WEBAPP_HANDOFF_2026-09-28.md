# FORM GIAO VIỆC — CWS AI TRADE SELF-LEARNING ENGINE + WEB APP

Ngày: 2026-09-28  
Đối tượng: ChatGPT Work / chat mới  
Người giao: **Duy Trần - Founder CWS**  
Trạng thái: Bắt đầu từ checkpoint, **không ngộ nhận đã có model mới hoặc Google Sites đã publish**.

## Prompt chuyển giao (dán nguyên văn cho chat mới)

@GitHub @Supabase @Google Drive

TIẾP TỤC DỰ ÁN **CWS AI TRADE — CỖ MÁY HỌC VÀ RA QUYẾT ĐỊNH RIÊNG**.

ĐÂY LÀ CHAT MỚI. Tự thực hiện những tác vụ kỹ thuật trong phạm vi plugin/connector có quyền. Không yêu cầu Founder tự gõ lệnh hoặc dùng PC khi cloud/connector có thể thực hiện.

### 1. REPO VÀ CHECKPOINT

Repository: `trankhanhduy1508-maker/AI-TRADE`

**Nhánh DUY NHẤT:** `codex/p0-covel-knowledge-audit`

**Checkpoint chính, PHẢI ĐỌC TRƯỚC:**
`knowledge/CWS_AI_TRADE_SELF_LEARNING_ENGINE_FOUNDER_INTENT_2026-09-28.md`

Đọc thêm đúng các file tối thiểu:
- `google-sites/cws-ai-trade/README.md`
- `knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md`
- `knowledge/PRACTITIONER_BOOK_CORPUS.md`
- `product/CWS_AI_TRADE_KINH_NGHIEM_CHAT_2026-09-28.md`
- `auto_trade/CURRENT_STATUS.md` (đọc phần checkpoint gần nhất, không nghiên cứu lại toàn file lịch sử).

Khi cần bằng chứng chuyên sâu thì mới mở:
- `reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md`
- `reports/TF004_MAXIMUM_ROBUSTNESS_VALIDATION_2026-09-27.md`
- báo cáo/evidence/dataset khác theo nhu cầu cụ thể.

Không ground lại toàn repo. Kiểm tra branch HEAD hiện tại trước khi ghi; tránh ghi đè thay đổi của phiên khác. Không tự tạo nhánh.

### 2. FOUNDER INTENT

Founder không muốn dùng GPT làm bộ não bắt buộc của hệ thống giao dịch.

Mục tiêu là **CWS Trading Engine, model học máy do CWS kiểm soát**, được huấn luyện bằng dữ liệu hợp lệ và có thể tiếp thu:
- bài học từ sách/CWS Trading Masterbook;
- nghiên cứu practitioner có provenance;
- OHLCV và dữ liệu execution/cost hợp lệ;
- backtest, OOS, walk-forward, forward paper và nhật ký đúng/sai.

Không dùng chatbot để giả làm model trading. Từ "không dùng thuật toán" được hiểu là không hardcode toàn bộ quyết định bằng rule BUY/SELL thủ công; training/inference của ML vẫn cần thuật toán. Risk gate có thể và phải là kiểm soát xác định độc lập.

Model phải biết **đứng ngoài / ABSTAIN** khi không đủ dữ liệu hoặc không đạt gate. Không hứa tự động thắng. Không dùng tri thức sách làm quyền gửi lệnh.

### 3. KIẾN TRÚC KIẾN THỨC VÀ HỌC

Dựng hoặc xác minh pipeline:
`nguồn hợp pháp → provenance/license → knowledge version → dataset version → model candidate → OOS/WF/cost/regime/stress evaluation → model registry → read-only inference → paper evidence → approval gate`.

Yêu cầu:
- phân biệt `knowledge ingestion` với `training model weights`;
- tách nguồn text khỏi numerical training dataset;
- kiểm tra data leakage/look-ahead, timestamp, missing data, survivorship/cost assumptions;
- không train lại model production trực tiếp theo vài trade thắng/thua;
- mỗi phiên bản có model artifact, code SHA, dataset hash, metrics, lý do giữ/reject, rollback;
- đề xuất baseline nhẹ/mã nguồn mở và kiểm chứng được trước model phức tạp;
- có cơ chế nhận nguồn mới trong quarantine, đánh giá, rồi tạo candidate.

Không khẳng định có GPU free forever; phân tích tài nguyên thực tế và lưu evidence. Không tự mở billing hoặc tạo nhiều project/provider để né quota.

### 4. THỨ TỰ CÔNG VIỆC

**NHIỆM VỤ A — VERIFY GROUNDING / RUNTIME:**
- verify branch, checkpoint, trạng thái Supabase site và public health;
- kiểm tra phần nào thực sự chạy, phần nào mới có code;
- kiểm kê tối thiểu dataset, training code, report thực tế;
- ghi rõ blocker và nguồn evidence, không fake PASS.

**NHIỆM VỤ B — SELF-LEARNING RESEARCH BASELINE:**
- chọn một bài toán dự đoán/đánh giá trạng thái cụ thể với dữ liệu đã được cấp phép và đủ chất lượng;
- tạo dataset version có nhãn rõ, train/test phân theo thời gian;
- huấn luyện baseline nhỏ nếu có compute thật;
- so sánh với baseline ngây thơ và strategy hiện hữu, có OOS/WF, cost/slippage khi phù hợp;
- kiểm tra calibration/uncertainty, drift, concentration;
- lưu model candidate, kết quả và các lần thất bại;
- chưa đủ data/compute thì thiết kế và checkpoint blocker, không tuyên bố model đã train.

**NHIỆM VỤ C — KNOWLEDGE UPDATE:**
- gắn bản đúc kết Masterbook vào knowledge store có nguồn/phiên bản;
- nếu dùng EPUB bản 49 trang, chỉ dùng đúng file mà Founder cung cấp/quyền truy cập thực tế;
- không giả rằng public distilled Markdown là toàn bộ EPUB;
- bổ sung nguồn mới có provenance, phân biệt `CLAIM / EVIDENCE / HYPOTHESIS`;
- cho model candidate học từ dataset đã duyệt, không tự promote vì sách mới.

**NHIỆM VỤ D — READ-ONLY ENGINE INTERFACE:**
- đưa ra API/dữ liệu `model_version,as_of,market,timeframe,data_version,signal_or_abstain,uncertainty,evidence_refs,gate_status`;
- không đặt lệnh; không cho model viết lại risk/kill-switch;
- hiển thị minh bạch `MODEL_NOT_TRAINED` hoặc `DATA_UNAVAILABLE` khi phù hợp;
- phân biệt paper, demo và broker thật.

**NHIỆM VỤ E — WEB APP / GOOGLE SITES:**
- tiếp tục code trong `google-sites/cws-ai-trade/`, không xây lại AppDeploy clone;
- giữ UI giao dịch xanh đen, mobile, biểu đồ và 16 cặp;
- bảng **mỗi cặp một dòng**, tổng Lot/P&L theo cặp, tổng lãi, tổng lỗ, P/L ròng, tổng Lot; missing value → `—`;
- 16 market trong giao diện KHÔNG phải 16 vị thế thật;
- bỏ panel AI Trading Assistant cố định bên phải; phần học sách/AI Chat nghiên cứu ở tab riêng nếu cần;
- Google Sites là wrapper/điểm truy cập; Supabase Web App độc lập là runtime;
- Google Site chỉ được gọi là published khi tạo/publish thành công dưới tài khoản Founder được phép và browser verify thật;
- không cố lấy AppDeploy login cookie/token từ iframe để vượt bảo mật;
- ưu tiên PWA sau khi Web App đạt gate, APK cuối cùng, không tách 3 codebase;
- `git push` KHÔNG tự động coi là deployment; chủ động deploy và ghi đúng SHA/source bundle.

**NHIỆM VỤ F — VERIFICATION VÀ CHECKPOINT:**
- unit/contract: aggregate Lot/P&L, mixed BUY/SELL, missing fields, phân tách R/USD, book provenance, model abstain;
- runtime: HTTP health, public chart, auth guard, no secret leak, read-only;
- browser thật desktop/mobile; fresh reload/reopen khi có thể;
- model: chỉ PASS với train/test logs, dataset/version/model artifact và evidence thật;
- sửa minimal diff sau FAIL rồi test lại;
- checkpoint đúng branch với đường dẫn evidence và trạng thái PASS/BLOCKED/PENDING.

### 5. GIỚI HẠN KHÔNG ĐƯỢC PHÁ

- Không dùng AppDeploy cho phần hạ tầng mới.
- Không dùng local Founder PC nếu chưa thật sự cần và chưa được phép.
- Không dùng GitHub Actions khi connector/API đủ khả năng.
- Không khởi động dịch vụ tính tiền khi chưa được Founder duyệt.
- Không sao chép trọn sách bản quyền hoặc dùng tài liệu thiếu quyền.
- Không làm giả dữ liệu thị trường, vị thế, lot, P/L, win rate hay kết quả backtest.
- Không đổi broker execution, risk gate, kill-switch hoặc The5ers gate.
- **Live-money LOCKED.** Không mở/tắt/bỏ qua gate, không tự gửi lệnh thật.
- Không tự thay đổi thứ tự workflow đã được Founder duyệt.
- Chỉ gọi DONE/PASS với evidence chạy thật.

### 6. CÁC FACT ĐÃ BIẾT KHI BÀN GIAO

- Đã có CWS Trading Masterbook V3, metadata/byline `Duy Trần - Founder CWS`.
- Public distilled knowledge ở repo không tương đương toàn bộ sách 49 trang.
- Đã có Supabase Web App riêng: `https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site`.
- README báo Supabase site ACTIVE, nhưng Google Site thuộc tài khoản Founder chưa được publish.
- Website hiện là tra cứu kiến thức + public chart + JSON/EPUB client-side, **chưa phải model trading được huấn luyện**.
- Knowledge MCP read-only: `https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-knowledge-mcp`.
- Founder Secure cũ: `https://cws-ai-trade-founder-secure-sm4gs9.v2.appdeploy.ai/`; đừng biến nó thành dependency của sản phẩm mới.
- Chi phí: không hứa API/GPU/inference miễn phí vĩnh viễn hoặc unlimited.

### 7. ĐẦU RA MONG ĐỢI

1. Source + docs + unit/runtime evidence trên đúng branch.
2. Model candidate có kiểm chứng nếu tài nguyên/dữ liệu cho phép; nếu không, checkpoint blocker chính xác.
3. Knowledge/version pipeline có nguồn và đường nâng cấp rõ ràng.
4. Website hoạt động thực tế và kế hoạch Google Sites/PWA không giả trạng thái.
5. Báo cáo cuối: `ĐÃ LÀM / ĐÃ TEST / CHƯA XONG / BLOCKER / NEXT EXACT ACTION`.

TỰ THAO TÁC LIÊN TỤC TRONG PHẠM VI ĐÃ ỦY QUYỀN. KHÔNG DỪNG CHỈ ĐỂ HỎI CÁC BƯỚC KỸ THUẬT MÀ CONNECTOR CÓ THỂ TỰ LÀM. KHÔNG TỰ MỞ QUYỀN GIAO DỊCH THẬT.
