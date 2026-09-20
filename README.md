# Stock Screening Project for Vietnamese Stocks

Dự án này xây dựng một bộ lọc cổ phiếu Việt Nam theo logic chốt trong hình quy trình đầu tư:

- Xu hướng: EMA/MACD/điểm vào theo xu hướng
- Biên độ: hỗ trợ, kháng cự, trendline
- Sóng: Fibonacci retracement, điểm vào theo vùng giá
- Chu kỳ: MACD, xoay vòng, thời điểm tốt
- Xác nhận: breakout/retest, khối lượng, tín hiệu xác nhận

Mục tiêu: chấm điểm từng cổ phiếu và chỉ giữ lại những mã đạt tiêu chuẩn theo bộ quy tắc định lượng.

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Chạy demo

```bash
python stock_screening.py --demo
```

## Chạy với file CSV

File CSV cần có các cột:

```csv
date,ticker,open,high,low,close,volume
2024-01-02,FPT,100,105,98,103,1000000
```

```bash
python stock_screening.py --csv data/sample_vn_stocks.csv
```

## Kết quả

Sản phẩm sẽ in ra danh sách mã đủ điều kiện theo score, ví dụ:

```text
ticker  score  trend  macd  rsi  vol  fib  decision
FPT     9.0    up     yes   58   yes  yes  PASS
```

## Thay đổi dữ liệu thật

Để sử dụng dữ liệu thị trường thật, bạn có thể thay thế `data/sample_vn_stocks.csv` bằng file dữ liệu đầy đủ từ nguồn của bạn hoặc tích hợp thêm data source như `vnstock`/API của sàn.

## Mô tả logic lọc

- Xu hướng tăng: giá đóng cửa > EMA20 > EMA50
- MACD gợi ý xu hướng tăng: MACD > Signal
- RSI trong vùng trung tính đến tăng: 50-70
- Khối lượng hợp lệ: volume > trung bình 20 phiên
- Vùng giá hợp lý: giá gần vùng hỗ trợ / Fibonacci retracement
- Xác nhận: cổ phiếu phải đạt tối thiểu 6/10 điểm theo các tiêu chí trên

## Tài liệu tham khảo

- Quy trình đầu tư trong hình: các bước xu hướng -> biên độ -> sóng -> chu kỳ -> xác nhận
- Khuyến nghị: luôn kết hợp với phân tích riêng và quản trị rủi ro trước khi đặt lệnh.
