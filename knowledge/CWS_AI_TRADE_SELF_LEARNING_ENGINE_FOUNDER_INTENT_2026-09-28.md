# CWS AI Trade — Founder Intent: cỗ máy học và quyết định giao dịch riêng

Ngày: 2026-09-28  
Chủ dự án: **Duy Trần - Founder CWS**  
Repo: `trankhanhduy1508-maker/AI-TRADE`  
Nhánh duy nhất của công việc hiện tại: `codex/p0-covel-knowledge-audit`  
Trạng thái: **FOUNDER INTENT / KIẾN TRÚC ĐỀ XUẤT / CHƯA HUẤN LUYỆN MODEL MỚI / CHƯA TRIỂN KHAI LIVE**.

## 1. Ý tưởng đã chốt qua trao đổi

Founder muốn CWS AI Trade có **cỗ máy giao dịch học máy do CWS sở hữu**, thay vì một chatbot sử dụng GPT/API trả lời câu hỏi rồi gắn nhãn là AI giao dịch.

Mong muốn:
1. Nạp tri thức từ CWS Trading Masterbook, nguồn sách/nghiên cứu hợp pháp, bằng chứng thực nghiệm của CWS, dữ liệu thị trường và nhật ký kết quả.
2. Học được mối quan hệ từ dữ liệu để đánh giá thị trường và đề xuất quyết định **giao dịch hoặc đứng ngoài**.
3. Có cơ chế bổ sung kiến thức, dữ liệu và kinh nghiệm mới; kiểm tra phiên bản trước khi sử dụng.
4. Tự chủ mã nguồn, kiến thức và artifact model ở mức tối đa, không phụ thuộc AppDeploy/GPT/API trả phí cho đường chạy bắt buộc.
5. Giao diện CWS AI Trade là nơi quan sát chart, 16 cặp, Lot/P&L, quá trình học, bằng chứng và quyết định, không phải chatbot đa năng.

**Diễn giải kỹ thuật chính xác:** mọi mô hình huấn luyện/suy luận đều cần thuật toán tính toán. Yêu cầu "không dùng thuật toán" được hiểu là **không dùng bộ quy tắc BUY/SELL thủ công, cứng và duy nhất thay cho học máy**; không hứa một mô hình hoàn toàn không có thuật toán. Hệ thống vẫn cần kiểm soát rủi ro/kiểm tra an toàn xác định và độc lập với model.

Không coi việc cho mô hình đọc sách là đã train được khả năng giao dịch. Retrieval/tri thức văn bản, học từ dữ liệu có nhãn, thực nghiệm và model weights là các lớp khác nhau.

## 2. Nguồn tri thức đúng bản quyền và provenance

Nguồn ưu tiên:
- `knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md`, sách **CWS Trading Masterbook**: byline `Duy Trần - Founder CWS`.
- `knowledge/PRACTITIONER_BOOK_CORPUS.md`, `knowledge/PRACTITIONER_DISTILLED_V1.md`, `knowledge/MARKET_WIZARDS_LESSONS.md`, `knowledge/BEST_PRACTICES.md`, `knowledge/COMMON_FAILURES.md`.
- `reports/MULTIASSET_10Y_BACKTEST_2026-09-27.md`, `reports/TF004_MAXIMUM_ROBUSTNESS_VALIDATION_2026-09-27.md`, dữ liệu/nhật ký khác đã xác minh tại repo.
- Dữ liệu giá, OHLCV, spread/commission/slippage khi có nguồn, khung thời gian, phiên giao dịch, regime, kết quả mô phỏng và DEMO có dấu thời gian.

Mọi mẩu tri thức phải gắn:
- `source_id`, tài liệu/phần/trang nếu có, bản quyền/điều kiện sử dụng, ngày tạo và ngày nạp.
- Loại: `PRACTITIONER_CLAIM`, `BOOK_LESSON`, `CWS_BACKTEST_EVIDENCE`, `MARKET_OBSERVATION`, `HYPOTHESIS`, `RULE`, `REJECTED_CLAIM`.
- Mức bằng chứng, thị trường/timeframe/regime, phạm vi hiệu lực và nguy cơ sai lệch.
- Không thu thập/sao chép trọn sách có bản quyền khi không được phép. Dùng bản CWS sở hữu hoặc tài liệu/ngữ liệu được cấp quyền và bản tóm lược hợp pháp.

**Cập nhật kiến thức không đồng nghĩa tự đổi model.** Knowledge store, training dataset, candidate model và production model phải version riêng.

## 3. Kiến trúc mục tiêu, không dùng GPT làm bộ não bắt buộc

```text
Nguồn được phép: sách/bài học CWS + nghiên cứu + OHLCV/cost + giao dịch/kết quả
   ↓
Ingestion / chuẩn hóa / kiểm tra bản quyền / provenance / chống trùng
   ↓
Knowledge store có version + dataset thị trường có version và kiểm tra data leakage
   ↓
Research & training (model CWS, chọn kỹ thuật theo dữ liệu/chi phí)
   ↓
Evaluation: IS → OOS → walk-forward → costs → regime → concentration → stress
   ↓
Candidate model / champion-challenger / model registry
   ↓
Suy luận read-only: setup, confidence/calibration, uncertainty, abstain
   ↓
Risk & safety gate độc lập (không do model tự viết lại)
   ↓
Paper → DEMO qua gate đã duyệt → live chỉ khi Founder duyệt riêng
   ↑
Outcome & journal → dữ liệu mới → candidate version / đánh giá lại
```

Model ban đầu cần một **baseline đo được** trước khi chọn kỹ thuật phức tạp. Có thể đánh giá supervised model hoặc time-series model nhẹ so với baseline; không khẳng định sẵn thuật toán/model cụ thể nào tốt. Ràng buộc chi phí: ưu tiên mã nguồn mở, khả năng huấn luyện theo lô và inference nhẹ; không tuyên bố train/inference miễn phí vĩnh viễn hay unlimited. Không âm thầm tự bật dịch vụ trả phí.

### Kiến thức từ sách và dữ liệu số

Sách có thể cung cấp giả thuyết/feature/giải thích cho con người; việc học quyết định phải được chứng minh qua **dataset thị trường và nhãn kết quả**. Tránh nhãn tương lai bị đưa ngược vào feature, survivorship bias, data-snooping và lộ OOS trong training.

Định nghĩa đầu ra đầu tiên:
- `market`, `timeframe`, `as_of`, `data_version`, `model_version`.
- Đánh giá trạng thái, điểm/ước lượng đã hiệu chuẩn nếu được chứng minh, cảnh báo uncertainty.
- `ABSTAIN` là quyết định hợp lệ khi dữ liệu thiếu/ngoài phân phối hoặc risk gate không đạt.
- Giải thích bằng evidence/feature contribution **trong phạm vi model thực sự hỗ trợ**; không tự bịa "lý do AI nghĩ thế".

## 4. Learning/update governance

Quy trình cập nhật:
1. Nhận nguồn mới và lưu vào khu vực `quarantine`.
2. Kiểm tra nguồn, license, định dạng, timestamp, data quality, xung đột và leakage.
3. Chuyển nội dung hợp lệ sang knowledge version; đối với numerical training, tạo dataset version.
4. Train candidate mới **ngoài đường chạy chính**.
5. So sánh baseline/champion bằng tiêu chí pre-registered và evidence OOS/WF/realistic execution.
6. Test regression, security, cost, drift; thất bại thì rollback/reject.
7. Promote model qua cơ chế phê duyệt đã chốt; không tự động đẩy model chưa kiểm chứng vào DEMO/LIVE.
8. Ghi immutable audit: input snapshot, code SHA, hyperparameters, seed, metrics, artifacts và phê duyệt.

Không dùng P/L của vài lệnh hoặc lời đồn từ sách để tự chỉnh quy tắc đang chạy. Không tự thay đổi workflow/order mà Founder chưa duyệt.

## 5. Giao diện và nền tảng đã thảo luận

Hướng sản phẩm: **Web App trước → PWA cài Android → APK khi cần**; một mã nguồn khi khả thi. Founder muốn dùng **Google Sites** làm trang chính/điểm truy cập, nhưng ứng dụng trading có runtime riêng và nhúng vào Google Sites.

Đã có code/README ở:
- `google-sites/cws-ai-trade/`
- Website độc lập: `https://oziktadfeenydvgobudr.supabase.co/functions/v1/cws-ai-trade-site`
- Health: URL website + `?health=1`.

Theo README đã kiểm tra: Supabase site đã deploy; **Google Site thuộc tài khoản Founder chưa được tạo/publish**, vì chưa có phiên chỉnh sửa phù hợp. Browser Android visual QA, EPUB live import, plugin install vẫn cần evidence độc lập. Không gọi Google Sites là hoàn thành trước khi publish và verify.

### UI Founder muốn giữ

- Tông xanh đen, chart chính, danh mục **16 cặp**, tối ưu mobile.
- Một dòng cho mỗi symbol; nhiều vị thế cùng symbol → cộng `lot` và `floatingPL` hợp lệ.
- Tổng **lãi dương**, tổng **lỗ âm**, **lãi/lỗ ròng**, tổng Lot và số cặp.
- BUY/SELL trái chiều cùng symbol → hiển thị `HỖN HỢP`, không che một hướng.
- Nếu thiếu bất kỳ Lot/P&L cần thiết thì tổng tương ứng `—`, không cộng nửa thật nửa đoán.
- Không lấy `synthetic_volume`/Paper Lot thành broker Lot; không dùng `R` giả thành USD P/L.
- **Bỏ panel AI Trading Assistant cố định** ở giao diện trading. Có thể giữ trang `AI Chat / Kiến thức` riêng cho nghiên cứu, không ép chatbot thành core trading engine.
- 16 dòng trong mockup **không chứng minh có 16 position thật**; phân biệt market universe với số cặp đang có vị thế.
- Không dùng hình mô phỏng làm bằng chứng giá hoặc P/L runtime thật.

Bản website hiện có: chart public data, đọc/import EPUB trong browser, local knowledge search và đường dẫn sử dụng ChatGPT riêng. Đây là công cụ **nghiên cứu/tra cứu**, chưa phải model học máy. Nếu bản thân model không triển khai thì phải hiển thị đúng trạng thái `CHƯA HUẤN LUYỆN / CHƯA KẾT NỐI`.

## 6. Chi phí/tự chủ

Mục tiêu là giảm chi phí và điểm phụ thuộc bằng GitHub source, Supabase control plane, website riêng và model mã nguồn mở. Không có cam kết "free forever": GPU/CPU/RAM, storage, băng thông, hosting, inference và training có chi phí/quota thực tế. Ưu tiên baseline nhẹ, batch training có kiểm soát, inference tiết kiệm; nếu thiếu compute thì checkpoint `BLOCKED` có evidence thay vì lách quota qua nhiều provider/project.

Không dùng AppDeploy làm dependency mới. Không tạo nhiều builder/project chỉ để né quota. Không sử dụng máy cục bộ Founder khi chưa cần hoặc khi Founder đã cấm.

## 7. Ranh giới an toàn đã chốt

- **KHÔNG** tự ý bật live-money.
- **KHÔNG** thay broker execution, risk gate, kill-switch hoặc The5ers gate.
- **KHÔNG** để model tự thay mã/giới hạn rủi ro hoặc cấp quyền giao dịch.
- **KHÔNG** chia sẻ public Google Sites/knowledge MCP với vị thế riêng, token hay account secrets.
- **KHÔNG** tự gửi lệnh vì đọc được một chương sách hoặc có xác suất model.
- **KHÔNG** tuyên bố chiến lược thắng thị trường nếu chưa qua evidence.
- Phân biệt rõ `RESEARCH`, `PAPER`, `DEMO`, `LIVE` và quyền thực thi của từng chế độ.
- Với bất kỳ thay đổi nào vào execution flow, người sở hữu phải duyệt Founder Intent trước khi áp dụng.

## 8. Trạng thái thực tế tại checkpoint

**Đã có:** ý tưởng/kiến trúc được ghi lại; nguồn knowledge Masterbook, báo cáo backtest và code Google Sites Web App; bản Supabase site độc lập được README ghi nhận đã deploy.

**Chưa có bằng chứng để gọi xong:** model trading tự học mới được train/evaluate; vòng feedback production; Google Sites Founder được publish; APK; quyền inference compute dài hạn; authenticated Founder/live position; bất kỳ khả năng ra lệnh thật nào của model.

Chặng đầu được ủy quyền cho chat tiếp theo: **ground tối thiểu → kiểm tra runtime/chi phí → tạo baseline nghiên cứu học máy read-only trên dữ liệu được phép → thử nghiệm chứng cứ → checkpoint**, giữ nguyên gate. Triển khai Google Site thực tế chỉ khi có phiên chỉnh sửa được phép; không bịa publish.


## 9. Founder chốt lại quy trình (2026-09-28, thay thế thứ tự APK trước đó)

Quy tắc có hiệu lực ở `docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md`: **làm và nghiệm thu Web App đầy đủ trước → xác minh MT5 demo + dữ liệu hợp pháp + auto-trade và toàn bộ gate → chỉ sau đó mới tạo một APK release hoàn chỉnh có cập nhật tại chỗ**. Không build hay chuyển APK debug cho Founder từng checkpoint. Tự cập nhật APK cần cùng package ID, khóa ký release ổn định, versionCode tăng và kênh Play In-App Updates hoặc manifest HTTPS đã kiểm chứng với xác nhận cài đặt Android. Không đổi quyết định live-money LOCKED.


## 10. Founder chuyển hướng APK-first (2026-09-28, MỚI NHẤT, thay thế §5/§9 về thứ tự)

Founder yêu cầu chuyển trọng tâm từ Web App/Google Pages sang **APK Android do CWS kiểm soát**, vẫn không bàn giao APK debug từng checkpoint và **chỉ phát hành khi DEMO auto-trade, update, rollback và QA đạt gate thật**. App phải có auto-update giữ dữ liệu và cơ chế cho khách phục hồi phiên bản model/strategy đã được duyệt; native APK recovery tuân thủ Android versionCode + khóa ký. Cho AI thường xuyên nạp/đối chiếu kiến thức đã cấp quyền, chạy thử ứng viên ngoài production và không tự promote REJECTED. Vấn đề quyền đóng lệnh thủ công và TradingView là câu hỏi sản phẩm đang cân nhắc; phương án được phân tích tại `product/CWS_AI_TRADE_ANDROID_CONTROL_LEARNING_UPDATE_SPEC_2026-09-28.md`, **chưa được hiểu là quyền sửa broker execution**. Chính sách canonical mới ở `docs/CWS_AI_TRADE_RELEASE_AND_AUTOUPDATE_POLICY_2026-09-28.md`; nếu tài liệu cũ nói Web-first thì áp dụng cập nhật mục này.
