# Practitioner Book Corpus — V1

Ngày: 2026-09-26

## Mục tiêu

Danh mục ban đầu cho knowledge base mới theo rule **Practitioner First**. Đây không phải bảng xếp hạng "ai giỏi nhất"; nó là registry để biết claim nào có nguồn gốc từ đâu và mức bằng chứng đến đâu.

## Core corpus

| ID | Tác giả / sách | Bằng chứng practitioner | Tier | Dùng cho AI-TRADE |
|---|---|---|---|---|
| LYNCH-001 | Peter Lynch — *One Up on Wall Street* (VN thường phát hành với tên *Trên đỉnh Phố Wall*) | Wharton ghi nhận Lynch quản lý Fidelity Magellan 1977–1990, lợi nhuận trung bình khoảng 29.2%/năm và chỉ thua S&P 500 hai năm trong giai đoạn đó | A | Quy trình nghiên cứu, phân loại cơ hội, kiên nhẫn với thesis, chống chạy theo câu chuyện. Không dùng trực tiếp làm Forex entry rule |
| LYNCH-002 | Peter Lynch — *Beating the Street* | Cùng track record quản lý Magellan; sách do practitioner trực tiếp viết | A | Case-study discipline, portfolio thinking, thesis review |
| HITE-001 | Larry Hite — *The Rule* | Publisher bio ghi Mint Investment Management composite đạt CAGR trên 30% trước phí trong 13 năm và là một trong các quỹ định lượng lớn thời kỳ đầu | A/B | Risk-first, systematic thinking, cắt lỗ, sizing, trend-following mindset; gần với futures/FX hơn Lynch |
| ONEIL-001 | William J. O'Neil — *How to Make Money in Stocks* | William O'Neil + Co. ghi nhận ông trở thành broker hiệu suất cao nhất tại công ty và tài khoản cá nhân tăng 20 lần trong 26 tháng; đây là nguồn tổ chức của chính ông, cần giữ provenance rõ | B | Price/volume research, loss control, strength; stock-specific nên chỉ thành hypothesis khi chuyển sang FX |
| MINERVINI-001 | Mark Minervini — *Trade Like a Stock Market Wizard* | Trang chính thức của Minervini ghi chiến thắng U.S. Investing Championship 1997 với 155% và dẫn nguồn IBD/Barron's | B | Trend template, risk discipline, pyramiding winner; stock-specific, cần backtest độc lập |
| DARVAS-001 | Nicolas Darvas — *How I Made $2,000,000 in the Stock Market* | Thành tích nổi tiếng chủ yếu đến từ chính cuốn sách và hồ sơ lịch sử; bằng chứng audit độc lập yếu hơn các nguồn ở trên | B | Box/breakout hypothesis; không dùng claim lợi nhuận làm bằng chứng cho AI-TRADE |

## Secondary corpus

| ID | Nguồn | Vai trò |
|---|---|---|
| COVEL-SECONDARY | Michael Covel — *Trend Following* | Tổng hợp trường phái, dẫn đường tới primary traders/papers; không còn là nguồn practitioner duy nhất hoặc tối cao |
| SCHWAGER-SECONDARY | Jack Schwager — *Market Wizards* series | Phỏng vấn practitioner; dùng để tìm primary claim và so sánh nguyên tắc, không gắn mọi câu trong sách thành rule |
| SEYKOTA-SECONDARY | Ed Seykota — public material / *The Trading Tribe* | Practitioner quan trọng cho systematic trend/risk psychology; track-record công khai cần tách rõ nguồn phỏng vấn/secondary khỏi source trực tiếp |

## Mapping kiến thức vào engine

### 1. Entry
Chỉ các nguyên tắc có thể định nghĩa bằng dữ liệu mới được chuyển sang rule:
- breakout;
- relative/absolute strength;
- trend qualification;
- price/volume confirmation khi dữ liệu phù hợp.

Không dùng câu chuyện định tính để tự gửi lệnh.

### 2. Stop Loss
Nguồn sách chỉ cung cấp nguyên tắc. Khoảng SL thật phải đến từ strategy spec + broker contract + backtest.

### 3. Take Profit
AI-TRADE hỗ trợ cả:
- fixed target;
- no fixed TP + trailing exit;
- partial profit + trailing phần còn lại.

Không chọn một kiểu vì một tác giả nói hay; phải so sánh bằng evidence.

### 4. Gồng lời
Canonical meaning:
- `LET_WINNER_RUN`: giữ vị thế thắng khi exit rule chưa xuất hiện, chỉ ratchet SL theo hướng có lợi.
- `PYRAMID_WINNER`: thêm vị thế chỉ khi lệnh hiện tại đang đúng hướng và tổng risk vẫn qua Risk Engine.

Cấm:
- nới SL để giữ lệnh thua;
- martingale;
- DCA ngược xu hướng chỉ để hạ giá vốn.

## Nguồn kiểm chứng ban đầu

- Wharton Magazine, Peter Lynch profile: https://magazine.wharton.upenn.edu/issues/anniversary-issue/stock-superstar-who-beat-the-street-peter-s-lynch-wg68/
- William O'Neil official bio: https://www.williamoneil.com/about-us/our-team/bios/founder
- Mark Minervini official strategy bio: https://minerviniselect.com/strategy.php
- Google Books / publisher metadata for Larry Hite, *The Rule*: https://books.google.com/books?id=BVWsDwAAQBAJ
- Google Books metadata for Nicolas Darvas: https://books.google.com/books/about/How_I_Made_2000000_in_the_Stock_Market.html?id=gKTl0AEACAAJ

## Gap

Repo hiện chưa có full lawful copy của *One Up on Wall Street* để ingest chapter-by-chapter. Cho tới khi có source hợp pháp, chỉ được dùng metadata, public author material, trustworthy summaries và claim ngắn có provenance. Không giả vờ "đã đọc toàn bộ sách".
