# Individual reflection — Bùi Hữu Huấn (2A202600353)

## 1. Role

AI Data Engineer + Retrieval Engineer. Phụ trách crawl dữ liệu từ YouTube và xây dựng hệ thống retrieval (vector search + web search).

---

## 2. Đóng góp cụ thể

* Xây dựng pipeline crawl YouTube:

  * Search video theo từng mẫu xe (≥ 5 mẫu)
  * Lấy transcript (ưu tiên subtitle, fallback sang Whisper GPU)
  * Lưu dữ liệu vào CSV (incremental save, tránh mất dữ liệu)
* Tối ưu crawl:

  * Dùng multi-thread (ThreadPoolExecutor)
  * Thêm random delay để tránh bị block
  * Xử lý lỗi download và transcript fallback
* Xây dựng hệ thống retrieval:

  * Convert data → embedding (sentence-transformers)
  * Build vector database bằng Qdrant
  * Implement QdrantVectorStore có `search(query, top_k,...)` 
* Tích hợp web search:

  * Viết tool lấy dữ liệu realtime (giá, chính sách, thông tin mới)
  * Combine vector search + web search thành 1 tool dùng trong pipeline
* Test hệ thống:

  * Chạy test với nhiều query khác nhau (xe rẻ, xe gia đình, xe đi phố)
  * Kiểm tra độ relevance của kết quả top_k

---

## 3. SPEC mạnh/yếu

### Mạnh nhất: Data pipeline thực tế

* Crawl từ nguồn thật (YouTube review)
* Có fallback (subtitle → Whisper) giúp tăng coverage
* Có chunking + embedding → tăng chất lượng retrieval
* Kết hợp thêm web search giúp bổ sung thông tin realtime

### Yếu nhất: Data quality & consistency

* Transcript từ YouTube có nhiều noise (quảng cáo, lan man)
* Chưa có bước filtering hoặc cleaning sâu (ví dụ: chỉ giữ đoạn liên quan đến xe)
* Một số query trả về kết quả chưa đúng model (overlap giữa các xe)

---

## 4. Đóng góp khác

* Hỗ trợ team debug lỗi Qdrant (import conflict, path issues)
* Chuẩn hóa format dữ liệu để các thành viên khác dùng chung (cars.json, CSV schema)
* Viết test script để mọi người có thể kiểm tra retrieval độc lập
* Hỗ trợ tích hợp với pipeline của Đạt (LangGraph node)

---

## 5. Điều học được

Trước đây nghĩ retrieval chỉ là “search embedding đơn giản”.
Sau khi làm mới hiểu:

* Data quality quan trọng hơn model
* Chunking + metadata ảnh hưởng rất lớn đến kết quả
* Retrieval không chỉ là kỹ thuật, mà là product decision:

  * Top_k bao nhiêu là đủ?
  * Có nên ưu tiên precision hay recall?
  * Có cần kết hợp nhiều nguồn (vector + web)?

Ngoài ra học được cách build pipeline gần với production:

* xử lý lỗi
* retry
* incremental save
* tránh bị block khi crawl

---

## 6. Nếu làm lại

* Sẽ làm bước cleaning + filtering data sớm hơn
  (loại bỏ đoạn không liên quan, chỉ giữ insight về xe)
* Sẽ thiết kế schema tốt hơn từ đầu (metadata rõ ràng hơn: price, segment…)
* Sẽ thêm evaluation sớm:

  * đo precision@k
  * test với nhiều query edge case hơn
* Sẽ chunk transcript thông minh hơn (theo sentence thay vì fixed length)

---

## 7. AI giúp gì / AI sai gì

### Giúp:

* Dùng AI để generate code base nhanh (Qdrant, embedding, search)
* Gợi ý cách thiết kế retrieval pipeline (vector + web search)
* Hỗ trợ debug lỗi (import, path, Docker, etc.)
* Gợi ý best practices (chunking, batching, fallback)

### Sai/mislead:

* Một số gợi ý over-engineer (dùng quá nhiều tool không cần thiết cho MVP)
* Có lúc đề xuất architecture phức tạp hơn scope hackathon
* Nếu không kiểm soát dễ bị:
  → viết nhiều code nhưng không focus vào core problem

👉 Bài học:
AI rất mạnh trong coding và idea, nhưng không hiểu constraint thực tế của project.
Cần luôn kiểm soát scope và ưu tiên MVP.
