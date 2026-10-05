"""First-party learning handbook; EPUB3 with accessible SVG and linked navigation."""
from pathlib import Path
from html import escape
import hashlib, json, re, zipfile
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'deliverables/CWS_Hoc_Giao_Dich_Va_Bai_Hoc_Backtest_2026-10-05.epub'
chapters=[]
def add(title,text): chapters.append((title,text))
add('Đọc sách này như thế nào', '''Đây là sổ tay học giao dịch của CWS, biên soạn từ kiến thức đã tích hợp và bài học kiểm thử được lưu trong dự án. Tác giả hiển thị: Duy Trần – Founder CWS. Bản ngày 05/10/2026. Sách không phải bản sao các tác phẩm thương mại và không tuyên bố đã đọc toàn văn mọi cuốn được nhắc tới.

Bạn có thể đọc theo ba vòng. Vòng một hiểu xác suất, R và drawdown. Vòng hai học cách viết setup, trigger và điều kiện thoát. Vòng ba đối chiếu với backtest và cách bot hiện tại vận hành. Mỗi chương có bài tập; hãy ghi câu trả lời trước khi nhìn kết quả một lệnh.

Ba nhãn cần nhớ: MINH HỌA là dữ liệu tự tạo để giải thích; TÀI LIỆU CWS là kết quả lịch sử được ghi trong Masterbook, chưa kiểm lại dữ liệu gốc ở lần xuất sách này; RUNTIME là điều quan sát được trong mã đang triển khai. Không trộn ba nhãn thành bằng chứng lợi nhuận tiền thật.

Bot hiện tại là phòng giao dịch mô phỏng. Bảng lệnh không phải MT5, không có lot hay lợi nhuận USD được suy ra từ R. Bốn lệnh tái mở theo yêu cầu người dùng là can thiệp thủ công, không phải bốn tín hiệu mới. Tách chúng khỏi việc đánh giá chất lượng chiến lược.

Bài tập: viết ra mục tiêu của mình bằng một câu có thể đo. Ví dụ: học thực thi một bộ quy tắc nhất quán và kiểm tra lợi nhuận sau chi phí, thay vì yêu cầu mọi tháng đều tăng.''')
add('Thắng nhiều chưa chắc kiếm được tiền', '''Một lệnh thắng hay thua không đủ để nói hệ thống đúng hay sai. Hệ thống chỉ có lợi thế khi phân phối kết quả, sau chi phí, tạo ra lợi nhuận kỳ vọng đủ để bù rủi ro. Tỷ lệ thắng là một phần của câu chuyện.

Lợi nhuận kỳ vọng = tỷ lệ thắng × lãi trung bình − tỷ lệ thua × lỗ trung bình. Khi tính theo R, hãy dùng cùng định nghĩa rủi ro ban đầu cho tất cả lệnh. Nếu thắng 30% với lãi trung bình 3 R và thua 70% với lỗ trung bình 1 R, kỳ vọng gross là 0,2 R mỗi lệnh. Thắng 70% nhưng lãi 0,3 R và lỗ 1 R thì kỳ vọng là −0,09 R. Đây là phép tính minh họa, không phải dự báo bot.

Chi phí có thể xóa lợi thế nhỏ. Với ví dụ gross 0,2 R, chi phí bình quân 0,15 R còn 0,05 R; chi phí 0,25 R biến thành −0,05 R. Spread, commission, slippage và swap cần được mô hình riêng, rồi kiểm lại bằng giao dịch thực tế của broker.

Không kết luận xác suất thắng từ ba hay bốn lệnh. Một mẫu nhỏ có thể chỉ là một đợt thị trường thuận lợi. Cần xét số lượng quan sát, sự phụ thuộc giữa các lệnh và khoảng bất định. Hai lệnh cùng đặt cược vào USD thường không phải hai cơ hội độc lập.

@FIG:expectancy.svg

Bài tập: tính kỳ vọng cho tỷ lệ thắng 40%, lãi 2 R, lỗ 1 R, chi phí 0,1 R. Đáp án gross 0,2 R và sau chi phí 0,1 R. Con số dương chưa chứng minh phương pháp có thể thực thi ngoài đời.''')
add('R, stop và vị thế: nghĩ về thua trước', '''R là đơn vị chuẩn hóa theo khoảng rủi ro ban đầu. Nếu mô phỏng BUY tại 100 và stop tại 96, khoảng rủi ro giá là 4. Giá 108 cho kết quả gross +2 R; giá 96 cho −1 R trong giả định không gap và không phí. SELL dùng công thức đảo chiều: giá vào trừ giá ra, chia khoảng rủi ro ban đầu.

Stop là điều kiện bất lợi cần xử lý; nó không bảo đảm mức lỗ tối đa khi có gap, thiếu thanh khoản hoặc trượt giá. BUY có stop 96 nhưng mở cửa ở 94 có thể phải thoát gần 94, tức −1,5 R trong ví dụ này. Một đường stop trên biểu đồ không phải cam kết khớp lệnh.

Trong giao dịch broker, khối lượng đi từ ngân sách rủi ro, khoảng stop, giá trị tick, kích thước hợp đồng, bước lot và tiền tệ tài khoản. Không lấy R của web rồi chuyển thẳng thành USD. Với vốn minh họa 10.000 đơn vị tiền và ngân sách minh họa 0,25%, số tiền dự kiến rủi ro là 25; chưa đủ thông tin để tính lot nếu chưa có hợp đồng của broker.

Nhiều lệnh nhỏ vẫn có thể tạo một cược lớn vì tương quan. Nasdaq, S&P 500 và Dow Jones đều là chỉ số cổ phiếu Mỹ; mở cả ba cùng chiều không mặc nhiên tạo ba nguồn rủi ro độc lập. Gold và oil trong arena dùng futures đại diện, không phải đúng hợp đồng CFD MT5.

@FIG:stop.svg

Bài tập: BUY 100, stop 96, thực tế thoát 94: tính R và giải thích vì sao “có stop” không đồng nghĩa “chỉ mất 1 R”.''')
add('Setup, trigger và quyền được đứng ngoài', '''Setup mô tả bối cảnh có thể giao dịch. Trigger là sự kiện cụ thể khiến hệ thống được vào. Invalidation là điều kiện cho thấy luận điểm không còn đúng. Ba thứ này nên được viết trước lệnh, để ta không đổi câu chuyện sau khi thấy giá chạy.

Ví dụ học tập: bối cảnh là xu hướng tăng; trigger là giá đóng cửa vượt vùng đã định; invalidation là mất vùng hoặc chạm stop. Đây là cấu trúc tư duy, chưa phải rule đang chạy của CWS. Muốn đưa vào bot phải định nghĩa được vùng, thời gian, cách tính và cách khớp.

Một tín hiệu cũ còn tồn tại không nhất thiết là tín hiệu vào mới. Người dùng đã đóng hết vị thế rồi yêu cầu “canh thời điểm phù hợp”. Vì vậy arena bổ sung trạng thái chờ: phải có dữ liệu mới sau lần đóng và thay đổi tín hiệu so với hướng đã quan sát. Không tự điền lại danh mục chỉ để bảng có nhiều lệnh.

Không có tín hiệu thì không giao dịch là một hành động có chủ đích. Lệnh ít không phải lỗi hệ thống nếu quy tắc đòi hỏi chờ. Ngược lại, mở liên tục để thỏa mãn nhu cầu nhìn thấy lệnh sẽ làm mất ý nghĩa của kiểm thử.

Bài tập: viết một setup bằng một câu, trigger bằng một điều kiện có thể lập trình, và invalidation bằng một mức giá hoặc sự kiện. Nếu còn chữ “có vẻ”, “cảm giác” hay “gần như”, hãy làm rõ trước khi kiểm thử.''')
add('Bộ quy tắc thực sự đang chạy', '''Arena hiện dùng TF-013A trên dữ liệu ngày. Mỗi thị trường có ba phiếu xu hướng: giá hiện tại so với 21 quan sát trước; giá so với 252 quan sát trước; SMA 10 so với SMA 200. Mỗi phiếu là +1, −1 hoặc 0. Tổng dương cho UP, tổng âm cho DOWN, tổng bằng 0 không có tín hiệu. Cần đủ lịch sử, không lấy vài nến đầu để suy luận.

Khi được phép mở, khoảng stop ban đầu là 4 × ATR 20. ATR dùng true range và làm mượt theo Wilder trong mã. BUY đặt stop dưới entry, SELL đặt stop trên entry. Hiện arena không có take-profit cố định. Exit hiện tại là chạm stop hoặc tín hiệu đổi hướng. Arena cũng chưa nâng stop theo một trailing algorithm đang vận hành; “trailing exit” trong gói nghiên cứu là ánh xạ nghiên cứu riêng.

Bản canh thị trường mới bỏ các bản ghi của ngày UTC hiện tại bằng mốc cắt bảo thủ; không coi nến còn đang hình thành là nến đã đóng. Đây là quy ước cho dữ liệu proxy, chưa phải lịch phiên chính xác của broker. Dữ liệu quá cũ bị chặn vào lệnh. Một vị thế vừa mở không được kiểm tra stop bằng nến trước thời điểm vào.

Sau lần đóng thủ công, cùng hướng xu hướng chưa được xem là một cơ hội mới. Bộ canh chờ nến mới và thay đổi hướng tín hiệu. Các trạng thái như “Chờ nến mới”, “Chờ tín hiệu mới”, “Dữ liệu cũ” và “Đang có lệnh” giúp bạn hiểu bot đang làm gì.

@FIG:workflow.svg

Mốc kiểm chứng: sau khi bổ sung điều kiện chờ, lần chạy kiểm tra không mở thêm lệnh, giữ 4 vị thế và không báo lỗi. Điều này kiểm chứng điều kiện chặn ở lần chạy đó; không chứng minh chiến lược sinh lời.''')
add('Vì sao không phải toàn bộ sách đã thành bot', '''Trong knowledge/runtime/autonomous_rules_v1.json có 12 nguyên tắc lấy từ Masterbook V3. Chúng vẫn mang trạng thái HYPOTHESIS. Gói có hash nguồn để phát hiện tài liệu bị đổi và broker_send_enabled=false. Đây là gói truy nguồn và nghiên cứu, không phải bằng chứng “AI đã học xong nên chắc thắng”.

Năm nguyên tắc có ánh xạ nghiên cứu: expectancy và marked drawdown; tín hiệu trên nến đóng với entry ở lần mở kế tiếp; stop xử lý gap; trailing exit không TP cố định; walk-forward theo thời gian và stress chi phí. Bảy nguyên tắc còn lại đòi hỏi kiểm chứng riêng. Không được nói tất cả 12 đã trở thành chiến lược chạy thật.

AI có thể giúp viết giả thuyết, đọc nhật ký và đề xuất thí nghiệm. Code deterministic mới quyết định và thực thi quy tắc trong runtime. Khi ChatGPT đóng, lịch máy chủ vẫn chạy. Điều đó không đồng nghĩa bot tự huấn luyện và thay chiến lược sau từng lệnh thua.

Quy trình nâng cấp cần phiên bản mới, dữ liệu đóng băng, kiểm thử ngoài mẫu, stress chi phí và kiểm tra vận hành. Một ứng viên tốt trong phòng nghiên cứu không tự thay TF-013A đang theo dõi. Không tự nới giới hạn để làm đường lợi nhuận đẹp.

Bài tập: chọn một nguyên tắc, viết nó thành giả thuyết đo được. Ví dụ “không cắt winner sớm” phải được chuyển thành hai cách thoát cụ thể để so sánh trên dữ liệu chưa dùng khi thiết kế.''')
add('Backtest mù và sai lầm nhìn trước tương lai', '''Backtest hữu ích khi mô phỏng quyết định chỉ với thông tin có ở thời điểm đó. Đưa toàn bộ lịch sử cho thuật toán rồi chọn tham số đẹp nhất không còn là kiểm chứng độc lập. Người nghiên cứu cũng có thể nhìn trước bằng cách chọn giai đoạn, thị trường hoặc kết quả thuận mắt.

Chia theo thời gian: phần thiết kế/huấn luyện, phần ngoài mẫu, rồi walk-forward. Trong mỗi vòng walk-forward, chỉ chọn bằng quá khứ và đánh giá trên đoạn kế tiếp. Không điều chỉnh dựa vào đoạn kiểm tra rồi tiếp tục gọi đoạn đó là OOS. Một thí nghiệm thất bại cũng phải lưu, nếu không ta chỉ còn thư viện những lần may mắn.

Tín hiệu tính ở close và khớp tại chính close là giả định thuận lợi. Chạy lại với next-open, gap và chi phí có thể thay kết luận. Nếu dữ liệu ngày không cho biết stop hay target xảy ra trước, cần giả định bảo thủ hoặc dữ liệu chi tiết hơn; không tự chọn thứ tự có lợi.

“Từ khi mã xuất hiện” còn cần dữ liệu đủ dài, đúng phiên và điều chỉnh hợp lý. Futures liên tục có vấn đề roll, cổ phiếu có chia tách và delisting, CFD có hợp đồng broker riêng. Một ticker đại diện không tương đương mọi thị trường hoặc mọi tài khoản MT5.

Bài tập: với một báo cáo đẹp, ghi ba giả định thực thi có thể làm nó xấu đi. Sau đó yêu cầu báo cáo cùng chiến lược dưới các giả định đó, không chỉ hỏi tỷ lệ thắng.''')
add('Bài học vàng: một winner có thể che cả hệ thống', '''NHÃN TÀI LIỆU CWS: Masterbook V3 ghi một historical run Gold có OOS khoảng +116,17 R, trong khi riêng lệnh tốt nhất khoảng +112,57 R. Bỏ winner lớn nhất còn khoảng +3,60 R; bỏ ba winner lớn nhất thành −14,22 R. Đây là các số đã ghi trong tài liệu nội bộ, không phải kết quả backtest mới thực hiện cho cuốn sách này.

Một phiên bản xử lý entry next-open và stop gap-aware ghi OOS khoảng −99,15 R, walk-forward khoảng −160,51 R. Không nên ghép các phiên bản thành một equity curve duy nhất: chúng là các thí nghiệm/giả định khác nhau. Biểu đồ bên dưới dùng cột so sánh để tránh tạo cảm giác đó là một quá trình theo thời gian.

@FIG:gold.svg

Winner concentration không tự động chứng minh hệ thống vô dụng. Trend following có thể cần những winner hiếm. Nhưng nó cho biết cần nhiều thời gian, nhiều quan sát và phải sống sót đến lúc winner xuất hiện. Nếu bỏ ba winner là toàn bộ kết quả đảo dấu, hãy tìm bằng chứng ở dữ liệu khác và giai đoạn khác trước khi tin rằng lợi thế sẽ lặp lại.

Không cắt mọi winner ở 2 R chỉ để tỷ lệ thắng nhìn dễ chịu; cũng không dùng một winner khổng lồ để bỏ qua hàng loạt kiểm thử thực thi thất bại. Cả hai đều có thể là cách chọn kết quả mình thích.

Bài tập: tính tỷ lệ 112,57/116,17, xấp xỉ 96,9%. Giải thích vì sao tổng lời lớn vẫn có thể là bằng chứng yếu về độ bền của hệ thống.''')
add('Bài học BTC, chỉ số và bằng chứng mâu thuẫn', '''NHÃN TÀI LIỆU CWS: một baseline BTC được ghi OOS khoảng +9,73 R; winner lớn nhất khoảng +9,11 R; bỏ winner đó còn +0,62 R; bỏ ba winner lớn nhất thành −13,60 R. Điều đáng học là mức tập trung, không phải lấy +9,73 R làm mục tiêu lợi nhuận sắp tới.

@FIG:btc.svg

Masterbook cũng ghi US30 có giai đoạn OOS dương nhưng tổng walk-forward âm, NAS100 có OOS hơi âm nhưng WF hơi dương. Không có đủ bảng gốc trong lần biên soạn này để vẽ số cụ thể cho hai chỉ số đó; sách giữ mô tả định tính thay vì chế số. Khi các thước đo mâu thuẫn, kết luận hợp lý là chưa đủ bằng chứng để promote.

S&P 500, Nasdaq 100 và Dow Jones có thành phần và trọng số khác nhau. Dữ liệu chỉ số trong arena là các proxy ^GSPC, ^NDX và ^DJI. Chưa thể lấy stop theo điểm của proxy rồi suy ra lot CFD, chi phí hay P/L MT5. Dầu và vàng là CL=F, GC=F nên cũng cần bước ánh xạ hợp đồng riêng.

Bài tập: viết một bảng đối chiếu ticker nghiên cứu và symbol broker của mình, gồm tick size, tick value, phiên và chi phí. Trường nào chưa có bằng chứng thì ghi CHƯA BIẾT, không đoán.''')
add('Drawdown, chuỗi thua và việc giữ nguyên luật', '''Drawdown là mức giảm từ đỉnh trước đó xuống điểm hiện tại hoặc đáy kế tiếp. Trong đường minh họa, equity từ 110 xuống 95: drawdown là 15/110 = 13,64%. Để từ 95 quay lại 110 cần tăng 15/95 = 15,79%. Tỷ lệ hồi phục luôn lớn hơn tỷ lệ mất khi mẫu số đã nhỏ đi.

@FIG:drawdown.svg

Đường cong trong hình là dữ liệu tự tạo. Nó không phải tài khoản hay backtest CWS. Mục đích là giúp bạn nhìn thấy một hệ thống vẫn có thể đạt đỉnh mới sau giai đoạn giảm, nhưng không có bảo đảm sẽ hồi phục. Kỳ vọng dương không biến mọi đoạn thời gian thành đoạn có lãi.

Chuỗi thua có thể xảy ra trong một phương pháp hợp lệ. Ngược lại, thắng vài lệnh không chứng minh phương pháp hợp lệ. Phản ứng đúng là kiểm tra việc tuân thủ luật, chất lượng dữ liệu, chi phí và thay đổi regime; không tăng lot để gỡ hay thay exit tùy cảm xúc.

Review theo nhóm quan sát, chẳng hạn 20/50/100 lệnh, là gợi ý quy trình trong Masterbook chứ không phải số mẫu bảo đảm thống kê. Lệnh cùng thị trường và cùng regime có thể phụ thuộc nhau. Luôn xem số quan sát độc lập thực tế.

Bài tập: tính drawdown từ 200 xuống 150 và mức tăng cần để quay lại 200. Đáp án 25% và 33,33%. Viết một hành động kiểm tra thay vì một hành động gỡ lỗ.''')
add('Nhật ký và lệnh tốt nhưng bị lỗ', '''Một good loss là lệnh thua nhưng tuân thủ setup, trigger, risk và exit đã định. Một bad trade có thể lời nhưng vào tùy hứng, không có stop hợp lệ hoặc thay luật giữa chừng. Chấm quá trình riêng với kết quả để không học nhầm từ may mắn.

Nhật ký tối thiểu: thời điểm tín hiệu; thời điểm giá nguồn; thời điểm thao tác; setup; hướng; entry; stop và rủi ro ban đầu; lý do thoát; kết quả gross/net; có can thiệp thủ công hay không. Với dữ liệu đủ chi tiết hãy thêm MAE, MFE và ảnh trước/sau. Không bịa MAE/MFE chỉ từ vài mức giá.

Can thiệp đóng 14 và tái mở 4 ngày 05/10/2026 được ghi USER_CLOSE và USER_REOPEN_EXISTING_DIRECTION. Chúng phải được phân biệt với lệnh do bộ quy tắc tự tạo. Kết quả can thiệp không được dùng để tuyên bố cải thiện edge của TF-013A. Giữ lịch sử giúp điều này kiểm tra được.

Một lesson tốt viết được điều kiện hành động: “tín hiệu ở nến chưa đóng nên lệnh này không thuộc mẫu kiểm định”. Một lesson yếu chỉ nói “lần sau hãy khôn hơn” hoặc “AI cần thông minh hơn”.

Bài tập: ghi một lệnh giả định thua đúng luật và một lệnh thắng sai luật. Chấm từng lệnh về chất lượng quyết định mà chưa nhìn số tiền.''')
add('Lộ trình học và mẫu kiểm tra trước lệnh', '''Giai đoạn một: học R, expectancy, gap và drawdown. Dùng các bài tập số trong sách; đọc biểu đồ mà chưa đặt lệnh. Giải thích được chỗ nào là dữ liệu nguồn và chỗ nào là giả định.

Giai đoạn hai: chọn một playbook. Viết setup, trigger, invalidation và cách thoát. Replay theo thứ tự thời gian, dừng trước nến tiếp theo để quyết định. Không chọn lại chỉ những chart nhìn đẹp sau khi biết tương lai.

Giai đoạn ba: paper và review. Ghi cả lệnh bỏ qua, dữ liệu lỗi và tín hiệu không đủ. Review các nhóm lệnh; đối chiếu OOS, walk-forward, chi phí và concentration. Đổi rule bằng phiên bản mới, không sửa lịch sử cũ.

Trước lệnh, trả lời năm câu: bối cảnh thị trường là gì; setup nào; trigger chính xác; điều kiện sai; rủi ro tổng sau khi vào. Với web CWS thêm ba câu: đây là lệnh tự động hay theo yêu cầu; giá được đánh dấu lúc nào; kết quả là gross R hay khớp broker đã xác minh.

Sau lệnh: luật có được tuân thủ; dữ liệu có đủ; giá khớp có thể thực thi; lý do thoát có đúng; có thay đổi cảm tính; bài học nào cần thí nghiệm riêng. Nếu chưa trả lời được, đừng dùng P/L để lấp khoảng trống.

Đích đến là đọc được một hệ thống, biết khi nào nên đứng ngoài và biết phản biện báo cáo đẹp. Không có số lệnh, tác giả hay công thức nào bảo đảm lợi nhuận luôn dương.''')

def markdown(text):
    out=[]
    for block in re.split(r'\n\s*\n',text.strip()):
        if block.startswith('@FIG:'):
            name=block[5:].strip();out.append(f'<figure><img src="images/{name}" alt="{escape(figure_alt[name])}"/><figcaption>{escape(figure_alt[name])}</figcaption></figure>')
        elif block.startswith('#'):
            lines=block.splitlines()
            for line in lines:
                m=re.match(r'^(#{1,6})\s+(.*)',line)
                if m: out.append(f'<h{min(len(m[1])+1,6)}>{escape(m[2])}</h{min(len(m[1])+1,6)}>')
                elif line:out.append('<p>'+escape(line)+'</p>')
        else:out.append('<p>'+escape(block).replace('\n','<br/>')+'</p>')
    return '\n'.join(out)

figure_alt={
 'expectancy.svg':'MINH HỌA: 30% thắng, lãi 3 R/lỗ 1 R → gross +0,20 R. Chi phí 0,15 R còn +0,05 R; chi phí 0,25 R thành −0,05 R.',
 'stop.svg':'MINH HỌA: BUY 100, stop 96, giá 108 là +2 R. Gap đến 94 gây −1,5 R; stop không bảo đảm khớp ở 96.',
 'gold.svg':'TÀI LIỆU CWS: các thí nghiệm Gold khác nhau; +116,17 R baseline, +3,60 R bỏ winner lớn nhất, −14,22 R bỏ ba winner, −99,15 R next-open/gap-aware.',
 'btc.svg':'TÀI LIỆU CWS: BTC baseline +9,73 R; bỏ winner lớn nhất +0,62 R; bỏ ba winner −13,60 R. Không phải dự báo.',
 'drawdown.svg':'MINH HỌA: equity tự tạo giảm từ đỉnh 110 xuống 95; drawdown 13,64%, cần tăng 15,79% để hồi về đỉnh.',
 'workflow.svg':'RUNTIME: dữ liệu → kiểm tra nến và độ mới → tín hiệu → chờ thay đổi sau đóng thủ công → mô phỏng → nhật ký. Chưa đủ điều kiện thì chờ.'
}
def svg(body):return '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="430" viewBox="0 0 800 430"><rect width="800" height="430" fill="#f8fafc"/><g font-family="sans-serif" fill="#142b45">'+body+'</g></svg>'
def txt(x,y,s,size=19):return f'<text x="{x}" y="{y}" font-size="{size}">{escape(s)}</text>'
def bars(title,items,scale):
    body=txt(25,36,title,24)+'<line x1="430" y1="65" x2="430" y2="385" stroke="#9aabba"/>'
    for i,(label,value) in enumerate(items):
        y=85+i*70;w=abs(value)*scale;x=430 if value>=0 else 430-w
        body+=txt(25,y+20,label,16)+f'<rect x="{x}" y="{y}" width="{w}" height="30" fill="'+('#087f75' if value>=0 else '#bf455a')+'"/>'+txt(690,y+23,f'{value:+.2f} R',16)
    return svg(body)

def build():
    source=ROOT/'knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md'
    master=source.read_text().split('## Artifact checkpoint')[0]
    add('Phụ lục: kiến thức tích hợp Masterbook V3',master)
    rules=json.loads((ROOT/'knowledge/runtime/autonomous_rules_v1.json').read_text())
    mapping='\n\n'.join(p['id']+' — '+p['source_heading'].lstrip('# ')+'\nTrạng thái: '+p['status']+'; ánh xạ: '+p['research_mapping'] for p in rules['principles'])
    add('Phụ lục: bản đồ 12 nguyên tắc và nguồn', 'Các trạng thái sau là dữ liệu thật của gói kiến thức, không phải chứng nhận lợi nhuận.\n\n'+mapping+'\n\nNguồn biên soạn: knowledge/CWS_TRADING_MASTERBOOK_V3_DISTILLED_2026-09-28.md; knowledge/KNOWLEDGE_INGESTION_POLICY.md; knowledge/runtime/autonomous_rules_v1.json; research/CWS_AUTOTRADE_AUTONOMOUS_RULES_2026-10-05.md; mã ai-trade-training-arena và watch-gate.\n\nSHA-256 Masterbook ở bản sách này: '+hashlib.sha256(source.read_bytes()).hexdigest()+'\n\nCác số backtest Gold/BTC lấy từ Masterbook, chưa tái chạy ở lần xuất sách. Sách không bao gồm chứng chỉ hay track record của tác giả sách thương mại. “18 nguồn lõi” là bản đồ tóm tắt đã có, không khẳng định đã nạp 18 bản toàn văn. Một phần mô tả nghiên cứu không phải hành vi runtime.\n\nBản quyền: diễn giải và tài liệu CWS; không phân phối toàn văn sách thương mại được nhắc tới. Tài khoản, mật khẩu MT5 và thông tin riêng tư không nằm trong EPUB.')
    figures={
      'expectancy.svg':bars('Kỳ vọng và chi phí · minh họa',[('30% thắng, +3 R / −1 R',.2),('Sau chi phí 0,15 R',.05),('Sau chi phí 0,25 R',-.05)],900),
      'gold.svg':bars('Gold · các thí nghiệm trong tài liệu CWS',[('Baseline OOS',116.17),('Bỏ winner lớn nhất',3.6),('Bỏ ba winner lớn',-14.22),('Next-open / gap-aware',-99.15)],2),
      'btc.svg':bars('BTC · concentration trong tài liệu CWS',[('Baseline OOS',9.73),('Bỏ winner lớn nhất',.62),('Bỏ ba winner lớn',-13.6)],18),
      'stop.svg':svg(txt(25,35,'Giá, stop và gap · minh họa',24)+''.join(f'<line x1="160" y1="{y}" x2="680" y2="{y}" stroke="{color}"/>'+txt(25,y+6,label,17) for y,label,color in [(95,'108: +2 R','#087f75'),(220,'100: Entry','#2978b7'),(280,'96: Stop','#bf455a'),(335,'94: Gap','#bf455a')])+txt(170,395,'Không có take-profit bắt buộc ở +2 R.',18)),
      'drawdown.svg':svg(txt(25,35,'Drawdown · equity hoàn toàn minh họa',24)+'<polyline points="60,240 145,180 230,120 315,205 400,300 485,250 570,190 660,95" fill="none" stroke="#2978b7" stroke-width="4"/>'+txt(230,95,'Đỉnh 110')+txt(375,330,'Đáy 95')+txt(35,385,'Giảm 13,64% · cần hồi 15,79% để trở lại 110.',20)),
      'workflow.svg':svg(txt(25,35,'Canh tín hiệu · không ép vào lệnh',24)+''.join(f'<rect x="40" y="{70+i*57}" width="710" height="42" rx="8" fill="#e5edf6"/>'+txt(55,98+i*57,t,18) for i,t in enumerate(['1. Dữ liệu ngày đủ lịch sử và đủ mới','2. Bỏ ngày UTC hiện tại (mốc bảo thủ)','3. Tính phiếu xu hướng 21 / 252 / SMA10–200','4. Sau đóng thủ công: chờ nến và thay đổi tín hiệu','5. Đủ điều kiện → mô phỏng và ghi nhật ký; còn lại → chờ'])))
    }
    files={'mimetype':b'application/epub+zip','META-INF/container.xml':b'<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'}
    css='body{font-family:serif;line-height:1.6;margin:5%;color:#142b45}h1,h2,h3{font-family:sans-serif;color:#174b71}p{text-align:left}img{width:100%;height:auto}figure{margin:1em 0}figcaption{font-size:.85em;color:#44566a}nav li{margin:.5em 0}h1{break-before:page}'
    files['EPUB/style.css']=css.encode()
    manifest=['<item id="css" href="style.css" media-type="text/css"/>'];spine=[];toc=[]
    def xhtml(title,body):return ('<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="vi" xml:lang="vi"><head><title>'+escape(title)+'</title><link rel="stylesheet" href="style.css"/></head><body>'+body+'</body></html>').encode()
    for i,(title,text) in enumerate(chapters):
        name=f'ch{i+1:02}.xhtml';cid=f'c{i+1}'
        files['EPUB/'+name]=xhtml(title,'<h1>'+escape(title)+'</h1>'+markdown(text))
        manifest.append(f'<item id="{cid}" href="{name}" media-type="application/xhtml+xml"/>');spine.append(f'<itemref idref="{cid}"/>');toc.append(f'<li><a href="{name}">{escape(title)}</a></li>')
    for name,content in figures.items():
        files['EPUB/images/'+name]=content.encode();manifest.append(f'<item id="img{len(manifest)}" href="images/{name}" media-type="image/svg+xml"/>')
    files['EPUB/nav.xhtml']=xhtml('Mục lục','<h1>CWS · Học giao dịch và bài học backtest</h1><p>Duy Trần – Founder CWS · 05/10/2026</p><nav epub:type="toc" id="toc"><h2>Mục lục</h2><ol>'+''.join(toc)+'</ol></nav>')
    manifest.append('<item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml"/>')
    files['EPUB/package.opf']=('''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:cws:learning:20261005:v1</dc:identifier><dc:title>CWS – Học giao dịch và bài học backtest</dc:title><dc:creator>Duy Trần – Founder CWS</dc:creator><dc:language>vi</dc:language><dc:description>Sổ tay kiến thức thực tế đã tích hợp, quy tắc mô phỏng và bài học kiểm thử; 6 biểu đồ có nhãn nguồn.</dc:description><meta property="dcterms:modified">2026-10-05T12:00:00Z</meta></metadata><manifest>'''+''.join(manifest)+'</manifest><spine><itemref idref="nav"/>'+''.join(spine)+'</spine></package>').encode()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT,'w') as z:
        for name,data in files.items():z.writestr(name,data,compress_type=zipfile.ZIP_STORED if name=='mimetype' else zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(OUT) as z:
        assert z.testzip() is None and z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==zipfile.ZIP_STORED
        for name in z.namelist():
            if name.endswith(('.xhtml','.opf','.svg','.xml')):
                tree=ET.fromstring(z.read(name))
                for e in tree.iter():
                    for k in ('href','src'):
                        link=e.get(k)
                        if link and '://' not in link:
                            target=(Path(name).parent/link.split('#')[0]).as_posix()
                            assert target in z.namelist(),(name,target)
            if name.endswith('.xhtml'):assert '\ufffd' not in z.read(name).decode()
    print(json.dumps({'file':str(OUT),'chapters':len(chapters),'figures':len(figures),'bytes':OUT.stat().st_size,'validation':'ZIP/XML/internal links/Vietnamese text PASS'},ensure_ascii=False))
if __name__=='__main__':build()
