# CWS AUTOTRADE — PROMPT BÀN GIAO CHAT MỚI — 2026-10-02

Dán nguyên khối này vào chat mới.

---

@GitHub
@CWS PC Commander

TIẾP TỤC CWS AUTOTRADE — MT5 DIRECT ANDROID RECOVERY.
KHÔNG NGHIÊN CỨU LẠI TỪ ĐẦU.
KHÔNG BẮT FOUNDER NHẬP LẠI LOGIN/PASSWORD NHIỀU LẦN.

Repository:
`trankhanhduy1508-maker/AI-TRADE`

Branch duy nhất:
`codex/p0-covel-knowledge-audit`

HEAD checkpoint docs mới nhất khi bàn giao:
`d4ce417d88baa214014720b343f79c646e4ccc83`

ĐỌC TRƯỚC THEO THỨ TỰ:
1. `research/CWS_AUTOTRADE_MT5_DIRECT_ANDROID_RECOVERY_2026-10-02.md`
2. `CURRENT_STATUS.md`
3. `docs/CWS_RENDER_MINIMAL_USAGE_POLICY_2026-10-02.md`
4. `research/CWS_AUTOTRADE_ANDROID_MT5_VNEXT_2026-10-02.md`

Sau đó kiểm tra HEAD mới nhất bằng GitHub connector.
SHA ở trên chỉ là checkpoint.

==================================================
TRẠNG THÁI ĐÃ XÁC MINH
==================================================

Credential DEMO Founder đã cho phép test:
- KHÔNG ghi Login/password vào repo.
- KHÔNG in password vào log.
- KHÔNG nhét password vào APK.
- KHÔNG yêu cầu Founder nhập lại nhiều lần để chẩn đoán cloud handshake.

Bằng chứng thật:
- Android -> Supabase verifier trước đây: broker trả login code 3 sau 3 retries.
- Diagnostic an toàn cho thấy input có đúng số chữ số Login và đúng độ dài password.
- Cùng credential đó trên PC Commander + pymt5 đã PASS 4 biến thể:
  1. direct + URL + SHA1 CID => LOGIN_CODE=0
  2. direct + empty URL + SHA1 CID => LOGIN_CODE=0
  3. init + URL + SHA1 CID => LOGIN_CODE=0
  4. init + empty URL + random CID => LOGIN_CODE=0
- Node/WebCrypto direct test tương đương verifier cũng đã có evidence PASS trong checkpoint mới nhất.
- Kết luận: credential hợp lệ. Không đổ lỗi cho user/password.

Android direct đã được triển khai:
- version: `0.6.0-demo-direct`
- file chính: `NativeMt5DirectClient.java`
- APK -> trực tiếp `wss://web.metatrader.app/terminal`
- bootstrap cmd=0
- login cmd=28
- account readback cmd=3
- xác minh bắt buộc server = `MetaQuotes-Demo`
- password RAM-only
- password không gửi Supabase ở luồng direct mới
- AutoTrade vẫn OFF
- live money vẫn LOCKED

HEAD Android direct evidence:
`949d9bae07cfbb0b3b03e4eb1a4ec0933c18b2fc`

PASS evidence:
- MT5 Demo Protocol Probe: run `36993597889`
- Android source-only QA: run `36993594745`
- Android DEMO APK: run `36993594339`
- Android device smoke: run `36993594344`
- emulator install/launch/relaunch/logcat gate: PASS

APK artifact:
- artifact id: `11220253706`
- name: `CWS-AutoTrade-DEMO-debug`
- SHA-256:
  `ca9d63a41ed1ef3333ca27f1b637440b52e1415c8fa5d5220137dea708549e07`

CHƯA PASS:
- physical Android direct broker login bằng APK v0.6.0-demo-direct.
- AutoTrade DEMO order execution.
- Live money phải tiếp tục LOCKED.

==================================================
NHIỆM VỤ CHAT MỚI
==================================================

1. Ground repo + đọc checkpoint trước. Không scan/research lại toàn repo.
2. Lấy đúng APK artifact của HEAD direct Android.
3. Nếu Founder đã cài/test APK mới:
   - đọc runtime evidence/log mới nhất;
   - xác định direct Android login đã PASS hay còn lỗi;
   - nếu lỗi thì sửa đúng direct client, không quay lại Supabase credential verifier trừ khi evidence bắt buộc.
4. Nếu cần test credential:
   - ưu tiên PC Commander clipboard/process runtime;
   - không lưu credential vào file/repo/log;
   - không bắt Founder gõ lại nhiều lần;
   - credential chỉ DEMO, nhưng vẫn xử lý như secret.
5. Khi physical Android direct login PASS:
   - xác minh account server = MetaQuotes-Demo;
   - xác minh trade mode DEMO;
   - xác minh password không persist;
   - xác minh app restart/reopen không crash;
   - ghi evidence vào GitHub.
6. Sau đó mới làm AutoTrade control/readiness:
   - không xây lại engine;
   - tiếp tục từ `ai-trade-tick`, risk gate, kill-switch, order-intent dedupe hiện có;
   - DEMO order execution chỉ mở khi server-authoritative gates PASS.
7. Chưa được mở live money.

==================================================
QUY TẮC RENDER
==================================================

Render.com phải làm ít việc nhất có thể:
- không lưu file;
- không lưu state;
- không lưu APK/model/log dài hạn;
- không làm database;
- không làm trading brain;
- không keep-alive chỉ để chống sleep;
- không tạo thêm Render service cho lỗi login này;
- Supabase vẫn là source of truth cho state/risk/compliance/audit.

Đọc:
`docs/CWS_RENDER_MINIMAL_USAGE_POLICY_2026-10-02.md`

==================================================
QUY TẮC LÀM VIỆC
==================================================

- Không fake PASS.
- Không báo cáo giữa chừng trừ khi có blocker thật cần Founder thao tác.
- Gặp lỗi thì tự đọc source, test, fix, test lại.
- Không reboot/shutdown PC.
- Plugin/connector trước.
- Không GitHub Actions mới nếu workflow hiện có đủ.
- Commit/push sau khi test PASS, tránh commit vụn.
- Không để credential xuất hiện trong commit, log, screenshot, artifact.
- Khi có nhiều cách test, ưu tiên cách cho bằng chứng runtime thật.

Mục tiêu gần nhất:
**physical Android direct MT5 DEMO login PASS trên APK v0.6.0-demo-direct, không cần Founder nhập credential lặp đi lặp lại.**
