# SPEC — VinFast Car Recommender

**Nhóm:** C401-E2

**Track:** VinFast

**Problem statement:** Khách hàng đến hệ thống showroom hoặc trang web VinFast hiện tại gặp khó khăn khi chưa xác định mẫu xe phù hợp với nhu cầu. Việc tra cứu và so sánh thủ công tốn nhiều thời gian và dễ gây nản chí. Hệ thống AI tư vấn sinh ra để đóng vai trò trợ lý cá nhân, tương tác qua vài câu hỏi trọng tâm nhằm đánh giá nhu cầu, từ đó đề xuất trực tiếp top 3 mẫu xe VinFast tối ưu nhất kèm theo luận điểm hỗ trợ.

---

## 1. AI Product Canvas

| | Giá trị (Value) | Niềm tin (Trust) và Giới hạn (Boundary) | Khả năng thực thi (Feasibility) |
|---|---|---|---|
| **Câu hỏi** | Hướng tới người dùng nào? Giữ vai trò giải quyết bài toán gì? | Khi AI gợi ý sai thì chuyện gì xảy ra? Hệ thống giới hạn nội dung thế nào để bảo vệ trải nghiệm? Bằng cách nào người dùng biết để điều chỉnh? | Chi phí hệ thống ra sao? Độ trễ phản hồi (latency)? Rủi ro kỹ thuật chính? |
| **Trả lời** | **Người dùng:** Khách hàng mua xe đang phân vân. **Khó khăn:** Quá tải thông tin, việc chọn sai phân khúc xe gây lãng phí/mất cơ hội bán hàng. **Giải pháp AI:** Lấy ngân sách và mục đích sử dụng để phân tích và chỉ ra top 3 xe khớp nhất. | **Ranh giới:** AI dùng Node Guard từ chối trả lời mọi câu hỏi lan man, ngoài luồng (off-topic). **Sự cố:** Nếu gợi ý sai mẫu xe, người dùng cảm thấy thông tin không hữu ích. **Khắc phục:** Hệ thống hiển thị sẵn một tùy chọn "Liên hệ tư vấn viên trực tiếp" tại mọi bước. | **Chi phí API:** Mức ~$0.01/lượt gọi. **Độ trễ:** Dưới 20 giây cho một vòng truy vấn. **Rủi ro rào cản:** Khách hàng cung cấp nhu cầu xe chung chung, thông tin giữa các dòng xe có thể bị nhận diện chồng chéo về tập tính vận hành. |

**Hệ thống tự động hóa (Automation) hay Hỗ trợ tăng cường (Augmentation)?**
[x] Augmentation 
Cơ sở đánh giá: AI tư vấn với vai trò chắt lọc dữ liệu và gợi ý thông tin cho khách hàng tham khảo. Quyết định mua xe là ở khách hàng. Hệ thống không thay mặt khách hàng thực hiện các giao dịch không kiểm soát; chi phí đền bù (cost of reject) khi khách hàng bỏ qua gợi ý của AI bằng 0.

**Tín hiệu học hỏi (Learning signal):**
1. Hành vi người dùng để đánh giá độ chính xác nằm ở việc người dùng nhấp đúp vào mục "Tìm hiểu chi tiết" cho mẫu xe được gợi ý thay vì đóng phiên truy cập.
2. Tín hiệu thu thập định lượng (phản hồi click) và lưu vào bảng ghi correction (log).
3. Tập dữ liệu là dữ kiện theo thời gian thực (Real-time) dựa vào các tình huống nhập ngữ cảnh cá nhân của mỗi khách hàng. Nó cung cấp giá trị phân tích vi mô (marginal value) để tinh chỉnh cách Node Elicitation đặt câu hỏi về sau.

---

## 2. User stories — 4 kịch bản

### Tính năng: Hệ thống thu thập thông tin (Elicitation) và gợi ý xe (Recommender)

**Kích hoạt:** Người dùng bắt đầu trò chuyện trong khung chat tư vấn hỗ trợ.

| Kịch bản (Path) | Câu hỏi thiết kế | Mô tả luồng tương tác |
|---|---|---|
| **Happy** — AI tự tin, xử lý chuẩn xác | Trải nghiệm người dùng thế nào? Kết thúc ra sao? | Khách hàng nhập thông tin "Tôi có ngân sách 1 tỷ 5, cần xe chở gia đình 7 người chạy nội thành". AI nắm bắt đúng dữ kiện (độ tin cậy > 90%), hồi đáp danh sách top 3 mẫu xe (tiêu biểu như VF 9 hoặc VF 8 cao cấp) kèm phân tích điểm khớp nhu cầu và đề xuất liên kết yêu cầu lái thử. Tương tác hoàn tất chu trình bán hàng cơ sở. |
| **Low-confidence** — AI chưa đủ dữ kiện để chắc chắn | Hệ thống báo chưa chắc bằng cách nào? Người dùng xử lý thế nào? | Khách hàng nhắn "Khoảng một tỷ mua xe nào hợp". Với mức vốn giao thoa giữa Sedan và SUV, AI thiếu bối cảnh cấu hình. Hệ thống chuyển đổi sang dạng đặt câu hỏi phản biện: "Anh/Chị di chuyển chủ yếu trên tuyến đường đồi núi hay đô thị, và thiên về gầm cao hay cốp rộng?". Khách hàng tiếp tục trả lời để thu hẹp khoảng xác suất. |
| **Failure** — AI xử lý sai hoặc gặp câu hỏi ngoài phạm vi | Người dùng làm sao để nhận biết xử lý lỗi và cách hệ thống phục hồi lại luồng? | Khách hàng đặt câu hỏi so sánh với các dòng xe động cơ đốt trong của hãng đối thủ hoặc hỏi về giá xăng. Lớp chặn Node Guard/Router phát hiện từ khóa ngoại vi, AI ngắt luồng thảo luận phi giá trị, phản hồi: "Trợ lý VinFast chỉ hỗ trợ tư vấn và so sánh trong danh mục các dùng xe điện VinFast. Chuyên mục anh/chị cần không nằm trong phạm vi. Bạn muốn tham khảo dải xe SUV hay xe đô thị của chúng tôi?". |
| **Correction** — Khách hàng tự hiệu chỉnh thông tin | Khách hàng chỉnh sửa thế nào? Dữ liệu đi về đâu? | AI gợi ý một xe VF 5 dư dả cho đi phố hạng nhẹ nhưng khách hàng lập tức nhắn "Nhưng mẫu này bé so với nhà tôi" dù trước đó khách hàng không đề cập tới không gian. Hệ thống chuyển qua luồng Correction, tiếp nhận sự phản đối, cập nhật trọng số cho ưu tiên "không gian cabin lớn", tiến hành chạy lại Retrieval fan-out và đưa ra ngay mẫu VF 7. Tập dữ liệu hiệu chỉnh được lưu dưới dạng nhật ký phản bác để tinh chỉnh prompt hệ thống. |

---

## 3. Eval metrics + threshold

**Tối ưu Precision hay Recall?**
[x] Precision

Cơ sở chọn lựa: Độ chính xác thực tế được đặt lên hàng đầu. Khách hàng tham khảo tư vấn AI mong đợi một chuyên gia sâu sắc, khi AI tư vấn thì kết quả gợi ý phải là chiếc xe thực sự thuộc phân khúc ngân sách họ đáp ứng. Nêu ra quá nhiều gợi ý kém liên quan (tăng Recall nhưng giảm thiểu độ chính xác) sẽ làm mức độ tin cậy tụt dốc, khách hàng thoát ngay trang chat.

| Thước đo (Metric) | Ngưỡng mục tiêu (Threshold) | Báo động đỏ (Dừng hệ thống khi - Red flag) |
|---|---|---|
| Độ chính xác nhận biết luồng của phân hệ Router/Guard | ≥ 90% (qua tệp kiểm thử chuyên dụng chứa 10 edge case) | < 80% (Hệ thống thất bại trong việc thiết lập giới hạn, trả lời lan man) |
| Độ chuẩn xác của danh sách Top 3 xe gợi ý sau cùng | ≥ 70% | Mức rớt xuống < 50% ở các tuần liền kề (gợi ý sai lầm quá nhiều) |
| Tổng thời gian phản hồi (Latency) mỗi truy vấn toàn phần | Dưới 20 giây | Phản hồi vượt 30 giây (đi ngược lại mục tiêu phản hồi nhanh ban đầu) |

---

## 4. Top 3 Failure modes

*Đây là các tình huống người dùng có độ rủi ro trải nghiệm từ hệ thống cao nhất và biện pháp phòng ngừa kiến trúc.*

| # | Tác nhân kích hoạt (Trigger) | Hậu quả (Rủi ro ẩn) | Phương án phòng ngừa (Mitigation) |
|---|---|---|---|
| 1 | Truy vấn đầu vào quá chung chung từ phía khách hàng (Ví dụ: "Cần mẫu xe gia đình"). | Kiến trúc sinh ra gợi ý vô giá trị (quá rộng), đánh đồng toàn bộ xe. Người dùng không thấy khác biệt. | Kích hoạt Node Elicitation. Hệ thống buộc phải tự đặt từ 1 đến 3 câu hỏi sàng lọc hẹp theo tiêu chí giá công bố và không gian trải nghiệm trước khi kết nối dữ liệu. |
| 2 | Khách hàng cố tình gửi prompt mang tính bẻ khóa (Injection) đòi báo giá hoặc cung cấp luận điểm trái với các chuẩn mực thông thường. | Rủi ro rò rỉ thông tin hoặc câu trả lời lệch tư tưởng hệ thống, gây tác hại nguy hiểm tới định hướng thương hiệu. | Node Guard với cấu hình strict prompt được xây dựng riêng, chuyên để sàng lọc ngôn ngữ ngoại vi (off-topic) – từ chối hồi đáp nếu giá trị xác suất từ khóa lệch biên độ. |
| 3 | Ngân sách kỳ vọng do khách hàng điền quá chênh lệch hoặc không tồn tại với mẫu xe (Ví dụ: "Tìm mua xe điện rộng 200 triệu"). | AI đối mặt với ảo giác (hallucination) trong việc cố gắng lấp liếm khớp dữ kiện với giá thực tế. | Xây dựng quy tắc cứng trước node tìm kiếm: Node Router bắt buộc cảnh báo và tự động cung cấp mốc giá trị xe thấp nhất hiện đang lưu hành thay vì cố tạo ra truy vấn truy xuất cơ sở dữ liệu. |

---

## 5. Phân tích ROI – 3 kịch bản:

| | Conservative | Realistic | Optimistic |
|---|---|---|---|
| **Assumption** | Có khoảng 100 truy cập mới/ngày, đạt 40% khả năng tương tác duy trì đủ phiên AI. | Đạt mốc 500 truy cập/ngày, tỷ lệ hoàn tất tương tác là 60%. | Mở rộng diện tiếp cận lên 2000 truy cập/ngày, tỷ lệ hoàn thành 80%. |
| **Cost** | Trả phí ~$1/ngày cho toàn bộ lượt API Inference model nhỏ gọn. | ~$5/ngày chi phí hệ thống. | ~$20/ngày tổng chi phí server lẫn model. |
| **Benefit** | Chia sẻ một phần nhẹ sức đỡ (tiết kiệm ước tính khoảng 3 giờ nhân sự tương tác tư vấn chát/ngày). | Chia tải hiệu quả tới 15 giờ xử lý khách hàng thông tin cơ bản; phân tách luồng nhóm khách mua thực tế. | Tối giản nguồn lực (cắt giảm hơn 60 giờ làm việc) - thu gom trọn bộ các lead khách hàng ở bước chuyển tiếp phễu nóng (mục chat hẹn lịch lái thử). |
| **Net** | Hệ thống bù đắp được chi phí trực tiếp nhưng chênh lệch chưa ấn tượng. | Số tiền duy trì nhỏ hơn thời gian nhân sự, gia tăng lợi nhuận vận hành thông qua tối ưu điểm chạm tư vấn trực tuyến (touchpoint). | Kéo dài khả năng bán hàng 24/7 với biên độ chi phí hầu như bằng 0 khi scale (khả năng tiếp cận thị trường quy mô rộng). |

**Kill criteria:** 
Dự án được xem xét đánh giá lại hoặc dừng hẳn khi thống kê định kỳ cho ra điểm chuẩn gợi ý chính xác (top-3 match) suy thoái dưới mức 50% quá 2 tháng liên tiếp, khiến chi phí chuyển lệnh đến nhân viên trực ngang bằng với việc không có công cụ AI.

---

## 6. Mini AI Spec (Cấu trúc kỹ thuật tổng quan):

Ứng dụng "VinFast Car Recommender" khai thác dòng mô hình xử lý LangGraph đa trình tự với 8 node thực thi chủ lục. Flow chuẩn xử lý qua các bước:
Khởi tạo giao diện chat → Node Router chuyển tiếp (kiêm nhiệm rào chắn Guard từ chối tác vụ Off-topic) → Node Elicitation (làm giàu ngữ cảnh khách hàng) → Profile tổng hợp dữ liệu → Cơ chế Retrieval vector fan-out cho hệ tư vấn → Synthesizer tổng hợp quyết định chung → Response Output trả thẳng về Client → Endpoint thu thập độ tương tác (Feedback).

Nền tảng tri thức (Knowledge Base) sử dụng thông số truy xuất trực tiếp từ cổng điện tử `vinfast.vn` và kho dữ liệu crawl độc quyền trải dài từ YouTube Reviews đến Nhóm Cộng đồng Facebook (tạo sự liên kết định tính khách quan). Hạ tầng chạy nhúng trên nền Vector Search FAISS/ChromaDB đồng thời trang bị khả năng kéo API lấy dữ liệu thực như lịch khuyến mãi theo ngày.

**Nhân sự:**

| Người phụ trách | Hạng mục nhiệm vụ (Task Specification) |
|---|---|
| **Đạt** | Chịu trách nhiệm vị trí AI Backend. Tham gia trực tiếp dựng luồng LangGraph pipeline tiêu chuẩn (8 node độc lập). Nạp mã nguồn cho FastAPI `POST /recommend`. Xử lý lệnh thiết kế prompt tạo luồng dữ liệu cho bộ phận Synthesizer và bảo đảm tích hợp đầu cuối. |
| **Huấn** | Phụ trách Data Crawler (Nguồn YouTube) kết hợp công cụ tra cứu thông tin tĩnh Web Search Tool. Xử lý tập tin nội dung tối thiểu của 5 phương tiện cấu hình tiêu biểu. Tối ưu hóa hàm `search_vectordb(query, top_k)`. |
| **Long** | Làm vai trò Data Crawler (Mạng xã hội FB) và Prompt Engineer. Phân loại cấu trúc và đào sâu các prompt điều phối chuyên biệt cho 2 node đặc thù là Guard & Router. Lập phương thức chốt chặn ngôn ngữ, chịu trách nhiệm cho ra kết quả chỉ định >90% vượt 10 edge case. |
| **Hiếu** | Thiết kế khối Frontend sử dụng cấu trúc nền hộp thoại chat qua chuẩn ứng dụng Next.js phiên bản 15 và thư viện TailwindCSS. Đặc thù tạo luồng hiển thị khối thẻ dữ liệu kết quả đặc tả xe. Ráp nối tương thích với chuẩn Endpoint `/recommend` nội bộ. |
| **Linh** | Đảm nhiệm xử lý kho dữ liệu VinFast.vn, làm đặc tả đầu ra dạng `cars.json` cho hơn 8 loại. Phụ trách luồng nhúng Embedding toàn bộ không gian số (FAISS/ChromaDB). Chuẩn hóa 10 đầu mục bài kiểm tra QA. |
