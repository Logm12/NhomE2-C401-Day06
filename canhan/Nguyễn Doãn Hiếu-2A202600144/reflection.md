# Individual reflection — Nguyễn Doãn Hiếu (2A202600144)

## 1. Role
Frontend developer + AI integration engineer. Phụ trách hoàn thiện giao diện chatbot web, kết nối Next.js với Python AI service, và đảm bảo trải nghiệm chat mượt với tiếng Việt.

## 2. Đóng góp cụ thể
- Xây dựng giao diện chat chính bằng Next.js, gồm luồng tạo cuộc trò chuyện mới, gửi tin nhắn, hiển thị lịch sử chat và sidebar quản lý hội thoại.
- Tích hợp frontend với Python AI service qua API stream, giúp phản hồi được hiển thị theo thời gian thực thay vì chờ trả về một lần.
- Hoàn thiện các tính năng hỗ trợ trải nghiệm người dùng như upload file, paste ảnh, gợi ý hành động ban đầu và lưu nội dung input tạm thời bằng local storage.
- Bổ sung xử lý các tình huống lỗi thực tế như timeout từ AI service, vượt giới hạn số tin nhắn trong ngày, hoặc mất kết nối để người dùng vẫn nhận được phản hồi thân thiện.

## 3. SPEC mạnh/yếu
- Mạnh nhất: luồng sử dụng end-to-end khá rõ, từ đăng nhập/guest mode đến chat, lưu lịch sử, xóa hội thoại và đồng bộ lại UI khi trạng thái thay đổi.
- Mạnh nhất nữa là nhóm có nghĩ đến reliability chứ không chỉ demo happy path, thể hiện qua rate limit, fallback message khi AI timeout, và cơ chế stream response.
- Yếu nhất: system prompt và domain behavior của AI còn khá generic, nên sản phẩm hiện mạnh về platform/chat experience hơn là chiều sâu nghiệp vụ.
- Yếu nữa là phần đặc tả đánh giá chất lượng AI chưa nổi bật trong repo; có test giao diện nhưng chưa thấy rõ bộ tiêu chí đo chất lượng câu trả lời hoặc benchmark cho model.

## 4. Đóng góp khác
- Việt hóa khá nhiều thông điệp trên giao diện để chatbot gần gũi hơn với người dùng trong nước.
- Tham gia chỉnh lại các trạng thái UI như loading, upload queue, stop generation và đồng bộ lại màn hình khi người dùng back/forward trình duyệt.
- Hỗ trợ kết nối phần web app với backend AI riêng thay vì chỉ dùng cấu hình mẫu ban đầu.

## 5. Điều học được
Trước khi làm project, mình nghĩ chatbot chủ yếu là phần prompt và model. Sau khi triển khai mới thấy chất lượng sản phẩm phụ thuộc rất nhiều vào luồng hệ thống xung quanh: stream có ổn định không, lỗi có được xử lý tử tế không, lịch sử chat có lưu đúng không, và người dùng có hiểu hệ thống đang ở trạng thái nào không. Với AI product, UX và reliability gần như quan trọng ngang với bản thân mô hình.

## 6. Nếu làm lại
Mình sẽ tách phần đặc tả AI behavior và evaluation sớm hơn. Hiện tại phần app và integration khá đầy đủ, nhưng nếu có rubric đánh giá câu trả lời, bộ test prompt và các failure cases ngay từ đầu thì nhóm sẽ tối ưu được chất lượng AI tốt hơn thay vì chủ yếu hoàn thiện platform trước.

## 7. AI giúp gì / AI sai gì
- **Giúp:** AI hỗ trợ rất tốt khi đọc nhanh code mẫu, gợi ý cách tổ chức luồng streaming, xử lý upload và sửa các lỗi integration giữa frontend với backend.
- **Giúp:** AI cũng hữu ích trong việc gợi ý wording cho thông báo lỗi, placeholder và các text tiếng Việt trên giao diện.
- **Sai/mislead:** Một số gợi ý của AI thiên về thêm nhiều tính năng "hay" như artifact editor hoặc mở rộng tool use, nhưng không phải phần nào cũng cần cho phạm vi bài lab.
- **Bài học:** AI giúp tăng tốc rất mạnh ở mức implementation, nhưng mình vẫn phải bám sát mục tiêu môn học và chủ động cắt bớt những phần vượt scope.
