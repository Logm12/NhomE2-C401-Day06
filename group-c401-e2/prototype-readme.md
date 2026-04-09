# Prototype — VinFast Car Recommender

## Mô tả
Hệ thống tư vấn đóng vai trò trợ lý cá nhân, tương tác qua biểu mẫu tin nhắn nhằm đánh giá nhu cầu khách hàng qua các câu hỏi trọng tâm. Nhiệm vụ chính là đề xuất danh sách 3 mẫu xe VinFast phù hợp nhất kèm theo luận điểm đối chiếu đặc tả kỹ thuật, giúp tiết kiệm thời gian tra cứu. Hệ thống tích hợp cơ chế phân luồng thông tin để đảm bảo phản hồi đúng giới hạn nghiệp vụ.

## Level: MVP Prototype
- Áp dụng kiến trúc LangGraph đa trình tự với 8 node thực thi.
- Giao diện hộp thoại Next.js tương tác với luồng xử lý API độc lập.
- Đường dẫn thao tác chính: Tiếp nhận truy vấn → Phân luồng (Router/Guard) → Thu thập thêm dữ liệu (Elicitation) → Truy xuất cơ sở dữ liệu (Retrieval) → Tổng hợp quyết định (Synthesizer).

## Links
- Github: https://github.com/Logm12/NhomE2-C401-Day06

## Tools
- Giao diện người dùng: Next.js 15, TailwindCSS
- Dịch vụ máy chủ: FastAPI
- Điều phối khối xử lý: LangGraph, LLM Inference API
- Lưu trữ dữ liệu và truy xuất vector: FAISS / ChromaDB
- Quy trình thu thập dữ liệu: Crawler đa nền tảng (YouTube, Facebook, Web Search)

## Phân công
| Thành viên | Phần nhiệm vụ | Output dự kiến |
|---|---|---|
| Đạt | Lập trình Backend, tích hợp LangGraph pipeline tiêu chuẩn, triển khai FastAPI, thiết kế khối lệnh Synthesizer. | Luồng Endpoint `/recommend` tích hợp LLM |
| Huấn | Thu thập dữ liệu đa phương tiện (YouTube) và cấu hình Web Search Tool, tối ưu hóa truy xuất dữ liệu `search_vectordb`. | Tập dữ liệu 5 phương tiện, mã nguồn truy xuất |
| Long | Thu thập dữ liệu mạng xã hội (Facebook), thiết kế khối lệnh đặc thù cho các khâu Guard và Router. | Hệ thống lọc từ khóa, tệp kiểm thử chuyên dụng (vượt &gt;90% edge cases) |
| Hiếu | Phát triển nền tảng giao diện người dùng cấu trúc hộp thoại, phát triển thẻ hiển thị thông số. | Khối Frontend bằng Next.js 15 và TailwindCSS |
| Linh | Tổng hợp và biên soạn thông tin không gian kiến thức số VinFast.vn, đảm nhiệm nhúng Embedding. | Tập tin `cars.json` cho 8 mẫu xe, 10 đầu mục bài kiểm tra QA |