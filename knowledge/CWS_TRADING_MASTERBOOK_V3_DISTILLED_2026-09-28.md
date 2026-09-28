# CWS Trading Masterbook V3 — Distilled Knowledge

Ngày: 2026-09-28  
Tác giả hiển thị trên sách: **Duy Trần - Founder CWS**  
Trạng thái: knowledge checkpoint cho AI-TRADE. Không phải khuyến nghị đầu tư và không mở bất kỳ live-money gate nào.

## Vì sao có V3

Bản ebook trước quá nặng về backtest và chưa giúp Founder rút ra đủ bài học để tự đọc chart, quản lý lệnh và đánh giá một hệ thống giao dịch.

V3 thay đổi triệt để:
1. lấy bài học từ practitioner/trader có thành tích công khai, sách và phỏng vấn làm lớp ý tưởng;
2. dùng evidence của CWS AI Trade để kiểm tra, phản biện hoặc bác bỏ ý tưởng;
3. biến mỗi bài học thành hành động/checklist/bài tập;
4. không dùng uy tín tác giả để vượt qua Risk Engine hoặc evidence gate.

## Ba lớp bằng chứng

### 1. Practitioner
Nguồn ưu tiên là trader/quản lý quỹ/người thi đấu có thành tích công khai hoặc track record được ghi nhận.

Các practitioner lõi được dùng trong Masterbook:
- William J. O'Neil
- Mark Minervini
- Oliver Kell
- Larry Williams
- Larry Hite
- Peter Lynch
- Andrea Unger
- Kevin J. Davey
- các trader trong Market Wizards / New Market Wizards
- Ed Seykota và trend-following practitioners

Bài học quan trọng: thành tích practitioner chỉ giúp một ý tưởng đáng nghiên cứu hơn. Nó không tự biến chiến lược thành rule cho FX, crypto hoặc MT5.

### 2. Sách / nghiên cứu
Masterbook V3 lập bản đồ hơn 75 đầu sách/tác phẩm, chia theo:
- momentum / growth / breakout;
- trend following / systematic;
- risk / probability / randomness;
- market structure / microstructure;
- psychology / performance;
- macro / portfolio;
- FX-specific;
- backtest / optimization / quant research.

18 cuốn/tác giả lõi được đúc kết sâu:
1. William J. O'Neil — How to Make Money in Stocks
2. Mark Minervini — Trade Like a Stock Market Wizard
3. Momentum Masters
4. Oliver Kell — Victory in Stock Trading
5. Larry Williams — Long-Term Secrets to Short-Term Trading
6. Larry Hite — The Rule
7. Curtis Faith — Way of the Turtle
8. Andrea Unger — The Unger Method / money-management material
9. Kevin J. Davey — Building Winning Algorithmic Trading Systems
10. Jack Schwager — Market Wizards
11. Mark Douglas — Trading in the Zone
12. Brett Steenbarger — The Psychology of Trading / Enhancing Trader Performance
13. David Aronson — Evidence-Based Technical Analysis
14. Robert Pardo — Evaluation and Optimization of Trading Strategies
15. Robert Carver — Systematic Trading
16. Andreas Clenow — Following the Trend
17. Mike Bellafiore — One Good Trade / The PlayBook
18. Larry Harris — Trading and Exchanges

Không lưu/chia sẻ bản sao đầy đủ sách có bản quyền. Chỉ dùng metadata, public/official material, lawful summaries và kiến thức được diễn giải lại bằng ngôn ngữ riêng.

### 3. Evidence CWS
Các bài học sách được đối chiếu với:
- OOS;
- walk-forward;
- cost stress;
- execution timing stress;
- gap-aware stops;
- parameter sensitivity;
- regime sensitivity;
- start-date sensitivity;
- Monte Carlo;
- winner-concentration stress;
- feed cross-check;
- forward paper evidence.

## 12 nguyên tắc lặp lại ở trader giỏi

### 1. Edge không có nghĩa là đoán đúng nhiều nhất
Một hệ thống có thể thắng ít nhưng winner lớn hơn loser đủ nhiều để expectancy dương.

Công thức tư duy:
Expectancy = WinRate × AvgWin - LossRate × AvgLoss.

Bài học:
- không đánh giá system bằng win rate một mình;
- luôn nhìn payoff ratio, expectancy và drawdown cùng nhau.

### 2. Nghĩ về rủi ro trước lợi nhuận
Trước entry phải biết:
- invalidation ở đâu;
- số tiền/R tối đa chấp nhận mất;
- position size;
- portfolio exposure sau khi vào.

### 3. Entry phải có setup + trigger
Không vào vì "cảm giác sắp chạy".
Tách:
- context/setup;
- trigger;
- invalidation;
- execution.

### 4. Sai nhanh phải thoát nhanh
Breakout không follow-through, thesis bị phá hoặc stop chạm thì đóng theo rule.
Không mở rộng stop vì muốn tránh nhận sai.

### 5. Winner cần không gian chạy
Trend/momentum thường cần một số ít winner lớn.
Exit quá sớm có thể phá expectancy dù win rate nhìn đẹp.

### 6. Không trung bình giá loser để chữa cảm xúc
Martingale và averaging-down không được dùng để cứu một thesis đã sai.

### 7. Có thể thêm vào winner, nhưng tổng risk phải bị khóa
Pyramiding chỉ là hypothesis. CWS đã có test cho thấy pyramiding có thể làm kết quả xấu hơn trên một số FX market.
Không được hiểu "add to winner" thành "cứ lời là nhồi thêm".

### 8. Regime thay đổi
Một rule hoạt động ở trend regime không mặc nhiên hoạt động ở chop/mean-reversion regime.

### 9. Backtest đẹp chưa phải tiền thật
Phải hỏi:
- close hay next-open?
- có spread/commission/slippage/swap không?
- gap xử lý thế nào?
- top winners đóng góp bao nhiêu?
- OOS/WF ra sao?
- data feed khác có cùng kết luận không?

### 10. Kỷ luật là lợi thế thực sự
Rule đơn giản nhưng thực thi nhất quán thường hữu ích hơn một hệ thống cực phức tạp nhưng bị sửa mỗi lần thua.

### 11. Nhật ký cần có nguyên nhân, không chỉ P/L
Mỗi trade nên có:
- setup;
- regime;
- trigger;
- invalidation;
- stop ban đầu;
- size;
- MAE/MFE;
- exit reason;
- screenshot trước/sau;
- rule violation;
- lesson.

### 12. Sống sót quan trọng hơn thắng lớn một giai đoạn
Drawdown, gap risk, leverage, correlation và liquidity quyết định một trader có đủ vốn để đi tới trade tiếp theo hay không.

## 10 quy tắc thực hành được rút ra từ 18 nguồn lõi

1. Không trade khi chưa viết được setup trong một câu.
2. Không entry trước trigger chỉ vì FOMO.
3. Stop đặt tại invalidation, không đặt theo số tiền muốn mất rồi ép chart khớp.
4. Size đi từ risk budget / stop distance, không dùng lot cố định theo thói quen.
5. Không tăng risk sau chuỗi thua để gỡ.
6. Không hạ tiêu chuẩn setup sau khi bỏ lỡ một cú chạy.
7. Không đổi exit giữa lệnh chỉ vì P/L đang làm mình khó chịu.
8. Review theo batch 20/50/100 trade, không kết luận từ 3-5 trade.
9. Tách "good loss" và "bad trade": lỗ đúng rule không đồng nghĩa quyết định sai.
10. Một rule từ sách chỉ được đưa vào AI-TRADE sau khi trở thành deterministic hypothesis và qua evidence ladder.

## Bài học từ CWS backtest cần nhớ

### Gold: headline đẹp có thể do một winner
Một historical run từng có OOS khoảng +116.17R.
Nhưng:
- best single trade khoảng +112.57R;
- bỏ best trade còn khoảng +3.60R;
- bỏ 3 winner lớn thành khoảng -14.22R;
- cap winner 5R thành khoảng -5.65R;
- next-open + gap-aware execution cho OOS khoảng -99.15R và WF khoảng -160.51R.

Bài học:
- luôn test winner concentration;
- headline Net R không nói đủ;
- execution semantics có thể đảo dấu kết quả.

### BTC: trend following phụ thuộc winner lớn
Một baseline OOS khoảng +9.73R;
best trade khoảng +9.11R;
bỏ best trade còn khoảng +0.62R;
bỏ best 3 thành khoảng -13.60R.

Bài học:
- đừng cắt mọi winner ở 2R chỉ để đường equity "êm";
- nhưng cũng đừng nhầm rare outlier với robust edge.

### Conservative execution
Trong maximum robustness validation, nhiều market đẹp ở close-entry bị suy giảm mạnh khi chuyển:
- signal trên bar đóng;
- entry next-bar-open;
- stop fill gap-aware.

Chỉ vài market còn cả OOS/WF dương trong mô hình conservative, và chúng vẫn GROSS_ONLY.
Do đó historical research hiện không đủ để xác nhận broker-net profitability.

### OOS và WF có thể mâu thuẫn
Ví dụ US30 từng OOS dương nhưng WF tổng âm.
NAS100 từng OOS hơi âm nhưng WF hơi dương.

Bài học:
- không chọn một metric thuận mắt;
- evidence mâu thuẫn = chưa promote.

### Cost mode phải được đọc trước lợi nhuận
GROSS_ONLY không được gọi là broker-net profitable.
RESEARCH_PROXY vẫn chưa phải actual broker cost.

## Playbook học Founder

### Trước chart
Hỏi 5 câu:
1. Regime gì?
2. Setup nào?
3. Trigger chính xác ở đâu?
4. Thesis sai ở mức giá nào?
5. Mất tối đa bao nhiêu nếu sai?

Nếu một câu không trả lời được thì không cần trade.

### Sau trade
Tự chấm:
- Rule adherence;
- Entry quality;
- Stop quality;
- Exit quality;
- Risk discipline;
- Emotional interference.

Không chấm trader bằng P/L của một trade.

## Lộ trình 90 ngày

### Ngày 1-30: đọc chart + risk
- học cấu trúc trend/range;
- breakout và false breakout;
- expectancy, R, payoff;
- position sizing;
- 20 chart replay/ngày nếu có thể.

### Ngày 31-60: một playbook
- chỉ chọn một setup;
- paper trade;
- log đầy đủ;
- không sửa rule sau mỗi loser.

### Ngày 61-90: evidence
- review 50-100 observations/trades;
- phân nhóm theo regime;
- đo MAE/MFE;
- kiểm tra cost/entry timing;
- chỉ thay rule bằng một version mới, không rewrite lịch sử.

## Quy tắc chuyển sách thành AI-TRADE

Pipeline bắt buộc:
Book / interview / practitioner idea
→ claim có provenance
→ hypothesis
→ deterministic spec
→ IS research
→ OOS
→ walk-forward
→ execution/cost stress
→ forward paper
→ broker-aligned DEMO khi và chỉ khi các gate khác được Founder phê duyệt.

Không có shortcut từ "tác giả nổi tiếng" sang "send order".

## Ranh giới

Masterbook V3:
- không mở live-money gate;
- không thay đổi broker execution/risk/The5ers gate;
- không tuyên bố chiến lược chắc thắng;
- không biến thành tích giải đấu thành expected return bình thường;
- không dùng GROSS_ONLY như net profitability;
- không thay backtest/forward evidence bằng authority của sách.

## Artifact checkpoint

Bản xuất bản hiện tại:
- 49 trang DOCX/PDF;
- EPUB3;
- tác giả hiển thị: Duy Trần - Founder CWS;
- mục lục EPUB có internal links;
- 27 biểu đồ/hình minh họa;
- 75+ đầu sách/tác phẩm trong bản đồ đọc;
- 18 nguồn lõi được đúc kết sâu;
- có 90-day curriculum, pre-trade checklist, playbook và CWS failure lessons.

Mục tiêu khi đọc xong:
Founder phải rút được rule hành động, biết phản biện backtest đẹp, biết phân biệt good loss với bad trade, và biết cách biến một ý tưởng từ sách thành hypothesis có thể kiểm chứng.


## Final publishing QA — 2026-09-28

Final artifacts were regenerated after navigation polish.

Verified:
- DOCX: 49 pages rendered; every page visually reviewed; Vietnamese glyphs clean.
- PDF: 49 pages; A4; author metadata = `Duy Trần - Founder CWS`; 201 outline items; 59 annotations.
- Visible DOCX/PDF TOC: 29 Heading-1 chapter/appendix entries with internal hyperlinks.
- EPUB3: zip integrity PASS; no U+FFFD replacement characters; 147 internal TOC hrefs checked; 0 missing file/fragment targets.
- Displayed byline: `Duy Trần - Founder CWS`.
- Final TOC heading is Vietnamese: `Mục lục`.
- Removed a LibreOffice rendering artifact that appended `X` to linked TOC entries by changing TOC entry paragraph style from Compact to BodyText. Re-render after fix PASS.

No live-money, broker execution, risk, or The5ers gate was changed by this publishing work.
