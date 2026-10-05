# Practitioner Distilled Knowledge — V1

Ngày: 2026-09-26

> Đây là distilled knowledge từ public/official material và publisher metadata. Không phải bản tóm tắt đầy đủ các sách có bản quyền và không tuyên bố đã ingest full book.

## LYNCH-CLAIM-001 — Idea generation != buy signal

**Nguồn:** Peter Lynch / *One Up on Wall Street* public publisher metadata + Fidelity/PBS public material.  
**Record:** `VERIFIED_PRACTITIONER_RECORD`  
**Provenance:** `VERIFIED_FROM_PRACTITIONER_PUBLIC_MATERIAL`  
**Market gốc:** U.S. equities.

Distilled principle:
- Quan sát sản phẩm/doanh nghiệp trong đời sống có thể tạo **ý tưởng nghiên cứu sớm**.
- Sự quen thuộc với sản phẩm không đủ để mua.
- Trước quyết định cần hiểu "câu chuyện" của doanh nghiệp và kiểm tra dữ liệu tài chính.

### Mapping vào AI-TRADE

Không chuyển thành Forex signal. Chuyển thành **research discipline**:
- signal chỉ là candidate;
- trước execution phải có dữ liệu đủ và rule rõ;
- không vào lệnh vì narrative/AI explanation nghe hợp lý;
- evidence gate quan trọng hơn câu chuyện.

Trạng thái: `SOURCE_ONLY -> ENGINEERING_PRINCIPLE`.

---

## LYNCH-CLAIM-002 — Edge phải nằm trong vùng hiểu được

**Nguồn:** public description của *One Up on Wall Street* và các interview/public material.  
**Record:** `VERIFIED_PRACTITIONER_RECORD`  
**Market gốc:** equities.

Distilled principle:
- Chỉ nên ra quyết định khi hiểu được lý do mình sở hữu/risk đang nằm ở đâu.
- Complexity không tự tạo edge.

### Mapping

AI-TRADE phải xuất được cho mỗi lệnh:
- strategy id;
- signal reason;
- risk amount;
- stop logic;
- exit model;
- invalidation condition.

Nếu hệ thống không giải thích được bằng state/rule deterministic -> reject.

---

## HITE-CLAIM-001 — Risk first, winner asymmetry

**Nguồn:** Larry Hite / *The Rule* publisher material và public practitioner material.  
**Record:** `VERIFIED_PRACTITIONER_RECORD` / publisher-reported fund record.  
**Provenance:** `VERIFIED_FROM_PRACTITIONER_BOOK_METADATA` + public practitioner material.  
**Market gốc:** futures / systematic multi-market.

Distilled principle:
- Xây hệ thống với giả định mình có thể sai.
- Loss cần nhỏ/định trước.
- Winner phải có không gian chạy.
- Portfolio/diversification giúp tránh phụ thuộc vào một dự đoán duy nhất.

### Mapping

- Protective SL bắt buộc.
- Không nới SL theo hướng tăng rủi ro.
- `TRAILING_ONLY` là exit mode canonical để nghiên cứu.
- Pyramiding chỉ trên winner và phải qua portfolio risk gate.
- Martingale/DCA ngược xu hướng bị cấm.

Trạng thái: `HYPOTHESIS_READY`.

---

## ONEIL-CLAIM-001 — Historical precedent + price/volume + fundamentals

**Nguồn:** William O'Neil official biography/methodology.  
**Record:** `PRACTITIONER_RECORD_PARTIAL` vì nguồn track record chính là tổ chức của O'Neil.  
**Market gốc:** equities.

Distilled principle:
- Nghiên cứu mẫu của các winner lịch sử.
- Kết hợp fundamental và technical/price-volume evidence.
- Không dựa vào một indicator độc lập.

### Mapping

Với Forex/MT5:
- fundamental stock metrics không portable.
- price/volume behavior có thể trở thành hypothesis nếu volume data của broker phù hợp.
- mọi pattern phải test out-of-sample, không nhập thẳng CAN SLIM vào FX.

Trạng thái: `HYPOTHESIS_ONLY`.

---

## MINERVINI-CLAIM-001 — Practitioner record qualifies source, not strategy

**Nguồn:** Mark Minervini official material ghi kết quả U.S. Investing Championship 1997.  
**Record:** `PRACTITIONER_RECORD_PARTIAL` do verification đang dựa trên official page dẫn IBD/Barron's.  
**Market gốc:** equities.

Distilled principle:
- Thành tích đủ để đưa sách vào practitioner corpus.
- Không đủ để tự động chuyển SEPA/stock rules thành Forex rules.

### Mapping

Các ý tưởng về trend, setup, stop, winner management sẽ chỉ được ingest claim-by-claim khi có lawful/public source cụ thể.

Trạng thái: `SOURCE_REGISTERED`.

---

## DARVAS-CLAIM-001 — Breakout box as hypothesis only

**Nguồn:** Nicolas Darvas / *How I Made $2,000,000 in the Stock Market* metadata.  
**Record:** `AUTHOR_REPORTED / HISTORICAL_PARTIAL`.  
**Market gốc:** equities.

Distilled principle:
- Box/breakout là một candidate hypothesis.
- Thành tích trong title/book không phải independent proof.

### Mapping

Có thể so sánh với existing breakout engine nhưng phải:
- định nghĩa box machine-readable;
- khóa tham số trước OOS;
- test cost/slippage;
- không đổi parameter sau khi nhìn holdout.

Trạng thái: `HYPOTHESIS_ONLY`.

---

## Knowledge synthesis boundary

Không "trộn sách" theo kiểu:
`Lynch + O'Neil + Minervini + Hite = chắc thắng`.

Cách đúng:
1. Mỗi claim giữ provenance riêng.
2. Claim được map thành hypothesis.
3. Hypothesis thành deterministic spec.
4. Chạy backtest/OOS/walk-forward.
5. Chỉ evidence của **AI-TRADE** mới quyết định giữ/bỏ rule.

Book authority không vượt qua backtest evidence và Risk Engine.
