# CWS AI Trade — Kinh nghiệm đúc kết từ phiên 2026-09-28

## 1. UI giao dịch phải ưu tiên dữ liệu thật hơn vẻ đẹp

Founder yêu cầu mỗi cặp chỉ hiện một dòng tổng hợp:
- symbol/cặp;
- BUY/SELL;
- tổng Lot của các vị thế thuộc cặp;
- tổng P/L của các vị thế thuộc cặp;
- bên trên có tổng P/L toàn bộ vị thế.

Quy tắc trung thực:
- không biến `synthetic_volume` thành Lot thật;
- không biến `floatingR` hay `unrealizedR` thành P/L USD;
- thiếu dữ liệu thật thì hiện `—`;
- nếu một cặp có nhiều vị thế, tổng Lot/P&L chỉ được tính khi dữ liệu cần thiết của tất cả vị thế trong nhóm đều hợp lệ.

## 2. Training Arena khác broker position

Ảnh Founder kiểm tra cho thấy khu vực đang hiển thị là Training Arena paper, không phải MT5/broker position.

Nguồn Arena có:
- symbol;
- side/direction;
- entry/stop/current mark;
- unrealized R.

Nguồn Arena không có broker Lot thật hoặc broker P/L USD.

Giải pháp đúng:
- ghi rõ `Paper Lot` cho simulation lot;
- P/L Arena hiển thị bằng đơn vị `R`;
- tổng Arena cũng tổng theo `R`;
- broker/live/demo position mới dùng Lot + P/L tiền thật khi API cung cấp.

Không được dùng số paper/synthetic để làm người dùng tưởng là broker volume.

## 3. Aggregate position theo symbol

Founder không muốn thấy nhiều dòng EURUSD chỉ để tự cộng bằng mắt.

Ví dụ:
- EURUSD position A: 1 lot
- EURUSD position B: 2 lot

UI mong muốn:
- EURUSD: 3.00 lot, một dòng duy nhất.

P/L cũng aggregate theo symbol.

Nếu cùng một symbol đồng thời có BUY và SELL, UI phải thể hiện trạng thái mixed/hedged thay vì tự chọn một side và che mất sự thật.

## 4. Backtest: bài học quan trọng hơn con số headline

E-book không nên là dump log/report. Phải chắt lọc kinh nghiệm có evidence.

Các nguyên tắc đã đưa vào sách:
- phản ứng với thị trường thay vì dự đoán;
- win rate không đủ để đánh giá strategy;
- phải đọc expectancy, payoff, drawdown, cost và concentration cùng nhau;
- OOS và walk-forward quan trọng để giảm tự lừa bởi in-sample fit;
- spread/commission/slippage có thể xóa edge;
- execution assumption close-price quá đẹp có thể sụp khi chuyển next-open/gap-aware;
- một vài winner rất lớn có thể làm headline return nhìn khỏe trong khi hệ thống mong manh;
- diversification chỉ có ý nghĩa nếu lợi nhuận không phụ thuộc vài market;
- pyramiding phải test, không được mặc định là tốt.

## 5. Ví dụ concentration risk đáng nhớ

Gold từng có headline OOS rất cao nhưng phần lớn lợi nhuận đến từ một winner cực lớn.

Bài học:
- luôn kiểm tra top-trade contribution;
- chạy leave-one-out / remove-top-N winners;
- nếu bỏ một winner mà expectancy hoặc net R sụp mạnh thì edge chưa robust;
- headline return không phải bằng chứng đủ để promote strategy.

## 6. Thành công và thất bại đều phải vào tài liệu

Founder muốn học kinh nghiệm, không chỉ xem chiến thắng.

E-book phải có chương riêng:
`Những gì AI thử và thất bại`.

Các loại thất bại cần giữ:
- strategy âm ở holdout;
- walk-forward không ổn định;
- cost stress làm đảo dấu lợi nhuận;
- market concentration;
- parameter sensitivity;
- pyramiding làm kết quả xấu hơn;
- execution realism làm strategy từ dương thành âm;
- data/coverage không đủ để kết luận.

## 7. Quy tắc chứng cứ cho sách

- claim có số phải truy về report/database artifact thật;
- nếu không đủ evidence thì ghi inference hoặc bỏ;
- không marketing kiểu “AI thắng thị trường”;
- không hứa lợi nhuận;
- phân biệt rõ Research / Paper / Demo / Live;
- minh họa khái niệm phải ghi là minh họa, không giả thành backtest thật.

## 8. EPUB: lỗi font không nhất thiết là font

Bản EPUB đầu tiên hiển thị tiêu đề kiểu:
`CWS AI Trade ���`

Root cause thực tế là ký tự replacement `U+FFFD` đã nằm trong metadata/title XHTML sau bước convert, không chỉ là thiếu font.

Bài học:
- trước khi đổi font, scan toàn EPUB cho ký tự `�`;
- kiểm tra `content.opf`, `toc.ncx`, `nav.xhtml`, title page và cover XHTML;
- sửa encoding/source text trước;
- không chữa lỗi dữ liệu bằng cách nhúng thêm font.

## 9. EPUB TOC phải là navigation thật

Founder yêu cầu mục lục bấm vào chương phải nhảy tới đúng chương.

Validation cuối:
- EPUB đóng gói với `mimetype` là file đầu tiên và STORED/uncompressed;
- navigation nội bộ được kiểm tra;
- bản FIXED có 69 internal href và 0 broken target;
- không còn ký tự replacement `�`.

Artifact local cuối phiên:
`CWS_AI_Trade_10_Nam_Backtest_Sai_Lam_Kinh_Nghiem_AI_FIXED.epub`

## 10. Quy trình tạo EPUB nên chuẩn hóa

Pipeline nên là:
1. dùng DOCX/source có Unicode chuẩn làm nguồn;
2. tạo EPUB;
3. unpack;
4. scan Unicode replacement chars;
5. kiểm tra metadata/title/toc/nav;
6. kiểm tra mọi internal href;
7. repack với mimetype đúng quy chuẩn;
8. mở trên mobile reader và desktop reader nếu có;
9. chỉ phát hành sau khi TOC navigation và tiếng Việt PASS.

Không convert trực tiếp PDF thành EPUB nếu còn DOCX/source reflowable tốt hơn.

## 11. Bài học tiếp nối — self-learning, quyền dữ liệu và ba lớp kiểm tra (28-09-2026)

**Nguồn trạng thái:** repo `trankhanhduy1508-maker/AI-TRADE`, chỉ nhánh `codex/p0-covel-knowledge-audit`, checkpoint `docs/CWS_AI_TRADE_SELF_LEARNING_CHECKPOINT_2026-09-28.md`. Các con số sau là kết quả đã ghi nhận hoặc vừa đối chiếu từ GitHub/Supabase, không đại diện cho thành tích giao dịch.

### Quyền dữ liệu phải được kiểm tra trước khi train, kể cả nghiên cứu nội bộ

- Bài học sửa sai quan trọng nhất: tải được API công khai **không đồng nghĩa** có quyền dùng dữ liệu đó để train, validate, benchmark AI hoặc tái phân phối.
- [Coinbase Market Data Terms](https://www.coinbase.com/legal/market_data), bản cập nhật 07-08-2026, mục 3(5), hạn chế sử dụng dữ liệu Coinbase cho AI/ML nếu không có chấp thuận bằng văn bản trước. CWS hiện **không có bằng chứng chấp thuận**. Không dùng Coinbase làm bộ dữ liệu ML ngay cả khi chỉ train nội bộ.
- Mô hình BTC-USD từng được train trước khi rà soát đầy đủ quyền sử dụng. Đã sửa protocol và thực hiện migration `20260928110855_ai_trade_coinbase_ml_rights_redaction_v1.sql`: xóa raw candles, model weights và derived metrics khỏi private registry, chỉ giữ tombstone `PROHIBITED_FOR_ML / REJECTED`. Không phục hồi, re-run hoặc quảng bá thành tích của thử nghiệm này.
- `src/self_learning/rights.py` là gate fail-closed: chặn nguồn Coinbase khi chưa có quyền xác minh, nguồn bên ngoài khác phải có chứng cứ riêng về ML-training rights, bằng chứng nguồn và SHA-256. Không điền giả `PERMISSION_GRANTED` hoặc xem giấy phép MIT của chương trình tải dữ liệu là giấy phép của dữ liệu.
- Trường hợp hợp lệ về **quyền** vẫn phải qua các gate độc lập về **chất lượng, chi phí, split thời gian, OOS, walk-forward, paper và an toàn**. Không có quyền thì dừng từ bước đầu; không xử lý bằng đổi tên provider.

### Kho tri thức không phải mô hình đã học

- Masterbook đúc kết công khai khác EPUB nguyên bản. Bản EPUB của Founder được giữ trong thư mục Google Drive riêng tư; không đưa toàn văn, nội dung sách bên thứ ba hoặc file riêng lên GitHub công khai, website, APK hoặc log.
- `ai_trade.private_knowledge_ingestion_runs` hiện có hai nguồn thực đã cách ly: bản Masterbook V3 đúc kết do CWS biên soạn và snapshot replay TF-013A gồm **140 giao dịch mô phỏng của 14 symbol với 15 bài học**. Replay chỉ là bằng chứng nghiên cứu, không phải 140 lệnh broker thực và không phải nhãn supervised OHLC đã được cấp phép.
- Quy tắc trạng thái: `QUARANTINED`, `approved_for_training=false`, `public_inference=false`, `broker_orders=false`. RLS, trigger bất biến, hash nguồn và ghi phiên bản phải giữ nguyên.
- Cron `ai-trade-knowledge-quarantine-daily` được cấu hình **03:45 UTC hằng ngày** để thu thập/phiên bản hóa replay đủ điều kiện. Đã xác minh job ACTIVE và kiểm tra idempotency; **không suy diễn rằng các lần chạy trong tương lai đã thành công**. Cron không có quyền tự duyệt dữ liệu, train model hoặc mở giao dịch.

### Hai mô hình nghiên cứu bị từ chối là kết quả cần giữ, không phải lỗi để giấu

- ECB EUR/USD reference-rate candidate: đã có training/evaluation thực trên **tỷ giá tham chiếu ECB**, không phải broker-executable OHLC. Mô hình `REJECTED` do không đạt tiêu chí preregistered OOS/chi phí; không đổi ngưỡng sau khi xem OOS để làm đẹp kết quả.
- BTC research candidate: `REJECTED / PROHIBITED_FOR_ML`, dữ liệu dẫn xuất đã được xóa vì thiếu quyền sử dụng.
- Chưa có model production được duyệt. Giao diện phải mô tả trung thực `MODEL_NOT_APPROVED`, `ABSTAIN`, `LOCKED`, không gọi `MODEL_NOT_TRAINED` nếu đã có model nghiên cứu nhưng bị loại. Cần kiểm tra chính xác trạng thái runtime trước khi hiển thị.
- Không đồng nhất unit test fixture, backtest gross, paper R hoặc ECB informational reference với lợi nhuận net broker, paper-forward mới hoặc khả năng gửi lệnh. Trường hợp thiếu dữ liệu phải abstain.

### Bài học UI và chuyển môi trường

- Danh sách **16 thị trường** không có nghĩa đang có 16 vị thế; mỗi symbol chỉ một dòng aggregate. Cộng lãi dương và lỗ âm theo **từng position trước khi gom**, sau đó tính tổng lãi, tổng lỗ, net P/L và Lot. BUY+SELL cùng symbol phải hiển thị hỗn hợp; thiếu Lot/P&L → `—`. Không biến R thành USD hoặc synthetic volume thành broker Lot.
- Supabase Web App là runtime độc lập; Google Sites là lớp nhúng/điểm truy cập, chỉ báo đã publish khi có URL và kiểm thử trực tiếp dưới tài khoản được phép. `cws-ai-trade-site` hiện báo **v11 ACTIVE** khi kiểm tra trạng thái function, nhưng phải GET lại health, HTML, manifest/JS và đối chiếu bundle trước khi gọi bản mới runtime PASS.
- Android có hai thế hệ debug: APK QA cũ chỉ tải remote PWA; source mới đóng gói first-party web assets vào WebView qua `https://appassets.androidplatform.net/assets/`, cho phép offline shell. [Cloud build 36416825217](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36416825217) cho commit `8ca1f89db05cb5af0f31f42bfd367be23844e15a` báo SUCCESS (generate assets, assemble, verify, upload). Đây **chỉ là debug QA**: chưa có bằng chứng cài thử APK mới trên Android vật lý, offline E2E, khóa ký release bền vững hoặc phát hành Play Store. APK debug cũ đã lưu trên Drive **không** được coi là bản offline mới.
- Không tạo ba codebase riêng cho Sites/Web App/PWA/APK. Khi sửa web source, đối chiếu static build/Edge bundle/Android packaged assets theo đúng SHA; Git push không tự chứng minh deploy.

### Cách vận hành tránh nghiên cứu lặp và báo PASS giả

1. **Ground đúng checkpoint mới nhất:** kiểm tra HEAD hiện tại của nhánh duy nhất, đọc Founder Intent, checkpoint, tài liệu kinh nghiệm này và đúng module liên quan; không quét lại toàn repository. Có phiên khác cùng ghi → rebase/fast-forward, không force.
2. **Triple-check bắt buộc:** (a) file/source/quyền dữ liệu/hash, (b) unit + negative-path + OOS/WF/Android build hoặc HTTP runtime tương ứng với **đúng commit**, (c) readback GitHub/Supabase/Drive/bundle + runtime security. Báo rõ mỗi gate PASS/FAIL/PENDING, không suy ra test thiết bị từ build cloud.
3. **Giữ lock:** `enabled=false`, `demo_send_enabled=false`, `risk_profile_approved=false`, không phát sinh broker order intent; không sửa kill-switch, Risk Engine hoặc The5ers. Không chạm Main/Stable hoặc tạo nhánh mới.
4. **Ưu tiên connector/cloud:** GitHub + Supabase + Google Drive, không dùng local PC của Founder, AppDeploy hay billing không được duyệt. Các bước yêu cầu tài khoản/thiết bị/người phê duyệt chỉ ghi blocker thật; không tự gọi hoàn thành toàn dự án.
5. **Bàn giao:** file prompt chi tiết tại `prompts/CWS_AI_TRADE_CHAT_MOI_TIEP_TUC_2026-09-28.md`. Chat mới phải lấy HEAD lúc chạy, không mặc định SHA lịch sử là HEAD hiện hành.
