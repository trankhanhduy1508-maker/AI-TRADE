# TF014 — Backtest nghiên cứu trên 26 thị trường (29/09/2026)

**Bằng chứng:** [Workflow #36563107932](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36563107932), tested SHA `4bd7a4c075070b3a20d0874ca61b06af6de4d0b2`. Cả 4 job đã thành công, 26/26 thị trường có số liệu thật. Không có lệnh broker.

**Chiến lược đóng băng:** momentum 20 nến, stop 10 nến trước, trailing 20 nến, warm-up 60 nến; tín hiệu khi nến đóng, vào giá mở của nến tiếp theo, gap stop xét theo giá mở. 70/30 IS/OOS, walk-forward 6 fold bắt đầu từ 50% dữ liệu. 1R là một đơn vị rủi ro dừng lỗ ban đầu, không phải phần trăm lợi nhuận tài khoản.

**Nguồn dữ liệu:** Yahoo Finance 1H công khai, tổng hợp bốn nến giờ liên tiếp trong cùng phiên thành H4 proxy; khoảng 29/10/2024–29/09/2026 khi có dữ liệu. Không xác nhận khớp múi giờ, spread, tick value hay nến H4 của MT5. Khối lượng = số giờ có dữ liệu, không phải tick volume thực. Mỗi phiên cổ phiếu/chỉ số Mỹ chỉ cho khoảng một nến H4 hoàn chỉnh, nên 20 nến ở nhóm này gần 20 phiên và không so sánh trực tiếp với FX. GC=F và CL=F là hợp đồng tương lai đại diện, không phải XAUUSD/USOIL CFD.

**Chi phí:** RESEARCH_PROXY dùng giá trị giả định spread/commission/slippage/swap trong code, chưa được xác thực với broker; GROSS_ONLY có chi phí 0 vì không có dữ liệu phí thích hợp. OOS và WF trong bảng là R đã thực hiện trên các lệnh đã đóng theo từng chế độ chi phí. Lệnh còn mở cuối tập mẫu bị loại khỏi P/L đã thực hiện.

| Nhóm | Mã | H4 | Lệnh OOS | OOS R* | WF R* | WF dương | Max DD R | Chi phí | OOS khi 2× phí |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
|fx_majors|EURUSD|2869|28|-6.37|-5.19|2/6|+7.88|RESEARCH_PROXY|-8.05|
|fx_majors|GBPUSD|2869|25|+4.21|-4.05|1/6|+7.16|RESEARCH_PROXY|+2.65|
|fx_majors|USDJPY|2871|35|+6.62|+0.45|2/6|+16.96|RESEARCH_PROXY|+4.11|
|fx_majors|AUDUSD|2886|26|-5.77|-8.27|1/6|+6.13|RESEARCH_PROXY|-7.61|
|fx_majors|USDCAD|2898|22|+15.98|+21.86|4/6|+2.27|GROSS_ONLY|n/a|
|fx_majors|USDCHF|2869|34|-8.66|-6.48|1/6|+9.23|GROSS_ONLY|n/a|
|fx_majors|NZDUSD|2888|24|+3.26|+2.93|3/6|+4.52|GROSS_ONLY|n/a|
|fx_crosses|EURJPY|2878|30|-1.14|-5.99|1/6|+9.58|GROSS_ONLY|n/a|
|fx_crosses|GBPJPY|2878|31|+4.63|-4.78|1/6|+8.16|GROSS_ONLY|n/a|
|fx_crosses|EURGBP|2883|27|-4.41|-15.02|1/6|+7.06|GROSS_ONLY|n/a|
|fx_crosses|AUDJPY|2878|22|+14.01|+9.86|3/6|+3.72|GROSS_ONLY|n/a|
|fx_crosses|EURCHF|2877|25|-0.68|-1.90|3/6|+9.90|GROSS_ONLY|n/a|
|fx_crosses|NZDJPY|2878|25|+16.54|+4.51|1/6|+8.00|GROSS_ONLY|n/a|
|crypto_commodities|BTCUSD|4187|40|+14.07|+4.21|3/6|+6.15|RESEARCH_PROXY|+10.61|
|crypto_commodities|ETHUSD|4185|40|+11.36|+2.58|3/6|+4.94|GROSS_ONLY|n/a|
|crypto_commodities|XAUUSD_FUTURES_PROXY|2383|23|+1.06|+2.93|4/6|+4.96|RESEARCH_PROXY|+0.81|
|crypto_commodities|USOIL_FUTURES_PROXY|2348|18|+3.57|-15.37|1/6|+3.39|RESEARCH_PROXY|+2.87|
|us_indices_stocks|US500_INDEX|472|7|-4.46|-6.20|0/6|+5.34|GROSS_ONLY|n/a|
|us_indices_stocks|NAS100_INDEX|472|5|-2.85|-6.22|0/6|+3.70|GROSS_ONLY|n/a|
|us_indices_stocks|US30_INDEX|472|2|+6.87|-2.54|0/6|0.00|GROSS_ONLY|n/a|
|us_indices_stocks|AAPL|472|3|-0.38|-3.79|0/6|+1.93|GROSS_ONLY|n/a|
|us_indices_stocks|MSFT|472|2|-0.80|-5.37|0/6|+0.80|GROSS_ONLY|n/a|
|us_indices_stocks|NVDA|472|6|-3.14|-6.53|0/6|+3.49|GROSS_ONLY|n/a|
|us_indices_stocks|AMZN|472|4|+0.04|-5.41|0/6|+1.56|GROSS_ONLY|n/a|
|us_indices_stocks|GOOGL|472|4|-2.17|-4.35|0/6|+2.24|GROSS_ONLY|n/a|
|us_indices_stocks|META|472|4|-3.33|-7.95|0/6|+3.33|GROSS_ONLY|n/a|

*R theo giả định chi phí của cột; GROSS_ONLY không phải kết quả ròng sau phí của MT5.*

**Kiểm tra chéo:** 8/26 thị trường có OOS và WF dương theo giả định nghiên cứu; 3 thị trường trong số đó có chi phí proxy (không phải broker xác nhận). 26/26 tập OOS còn vị thế mở, nên tổng P/L cuối kỳ chưa bao gồm lợi nhuận/lỗ chưa thực hiện. Không có thị trường nào đã xác nhận lãi ròng sau chi phí MT5.

**Diễn giải và giới hạn:** EURUSD, mã ứng viên DEMO hiện tại, âm OOS và WF. BTC có OOS/WF dương dưới chi phí proxy nhưng chỉ 3/6 fold WF dương. Dầu WTI có OOS dương nhưng WF âm. Nhóm cổ phiếu Mỹ ít nến 4 giờ hoàn chỉnh và nhiều mã có ít hơn 5 lệnh OOS; không thể coi đó là xác nhận hiệu quả. Chưa tính rủi ro broker 0,01 lot, margin, tài khoản USD, rủi ro gap vượt SL hay tài khoản đang mở. TF014 được thiết kế sau khi nghiên cứu TF004, do đó OOS này không phải holdout hoàn toàn mù.

**Quyết định nghiên cứu:** RESEARCH_ONLY. Không tự động bật quyền DEMO-send, không approve model, không gửi LIVE/DEMO. Cần dữ liệu H4 và chi phí MT5 thật, closed-trade + open MTM, kiểm định độc lập và forward paper.

[Mã backtest](https://github.com/trankhanhduy1508-maker/AI-TRADE/blob/4bd7a4c075070b3a20d0874ca61b06af6de4d0b2/scripts/backtest_tf014_multimarket_h4.py) · [Các job và bản thống kê gốc](https://github.com/trankhanhduy1508-maker/AI-TRADE/actions/runs/36563107932)
