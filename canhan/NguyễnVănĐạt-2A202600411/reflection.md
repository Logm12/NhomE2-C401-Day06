# Sprint Reflection — Nguyễn Văn Đạt

**Vai trò:** AI Backend Engineer · Project Coordinator

---

## Số liệu

| Hạng mục | Kết quả |
|---|---|
| Node pipeline | 6 |
| API endpoint | 1 (`POST /recommend`) |
| Test coverage | E2E |
| Thành viên nhóm | 4–5 người |

---

## Đóng góp chính

### Quản lý dự án

- **Tìm & chọn đề tài:** Nghiên cứu, đề xuất và chốt đề tài phù hợp năng lực nhóm và xu hướng AI hiện tại.
- **Lên kế hoạch thực hiện:** Lập roadmap, xác định milestone và phân bổ thời gian cho từng giai đoạn trong sprint.
- **Phân chia công việc nhóm:** Giao task cho 4–5 thành viên theo năng lực, đảm bảo không bị bottleneck và tiến độ đồng đều.

### AI Backend

- **LangGraph pipeline:** Dựng StateGraph tiêu chuẩn với 6 node độc lập, định tuyến có điều kiện qua `route_next`.
- **FastAPI integration:** Nạp mã nguồn endpoint `POST /recommend`, kết nối `recommender_graph` vào API layer.

### Prompt Engineering

- **Synthesizer prompt design:** Thiết kế luồng dữ liệu và prompt cho node `synthesizer` — tổng hợp output từ retrieval.

### Testing

- **Kiểm thử tích hợp đầu cuối:** Xác minh từng node hoạt động đúng, chạy test toàn luồng agent từ input đến output cuối cùng.

---

## Kiến trúc pipeline

```
create_graph()

router ──→ off_topic   ──→ END
       ├─→ elicitation ──→ END
       └─→ rewrite ──→ retrieval ──→ synthesizer ──→ END
```

---

## Kỹ năng & công nghệ

`LangGraph` `StateGraph` `FastAPI` `Prompt Engineering` `RAG Pipeline` `Python` `Integration Testing` `Project Planning` `Task Management` `Team Coordination`

---

## Nhận xét bản thân

Trong sprint này tôi đảm nhận cả hai vai trò: điều phối nhóm và triển khai kỹ thuật AI backend. Từ việc chọn đề tài, lên kế hoạch, phân công task cho đến tự tay dựng LangGraph pipeline và tích hợp API — điều này giúp tôi nắm toàn bộ bức tranh của dự án.

Thách thức lớn nhất là cân bằng giữa quản lý tiến độ nhóm và đảm bảo chất lượng kỹ thuật, đặc biệt khi tinh chỉnh prompt cho synthesizer qua nhiều vòng thử nghiệm. Đây là kinh nghiệm thực chiến có giá trị về xây dựng hệ thống AI production-ready lẫn kỹ năng dẫn dắt nhóm.
