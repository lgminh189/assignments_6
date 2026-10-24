# Kiểm chứng điều khiển bằng cử chỉ

Cập nhật nhận diện Wave: giữ lịch sử qua gián đoạn ngắn, dùng thêm hình học lòng bàn tay, đo từ cực trị từng lượt vẫy, ngưỡng 6% chiều rộng ảnh trong 3 giây. Webcam có chỉ báo tiến độ 0/3 và nhãn AI gốc. Build thành công; **58 kiểm tra đạt**, gồm các trường hợp mất nhãn ngắn, quét một chiều, đảo chiều chậm và Wave → chọn → xác nhận. Chưa kiểm chứng cải thiện bằng thao tác tay thật của người dùng.

Cập nhật hành vi ghi nhớ: sau xác nhận, `No_Hand` duy trì heartbeat của camera/AI và robot chạy hết hành vi dù đã hạ tay. Lỗi `Camera_Error` hoặc mất bản tin vẫn dừng robot. Build lại thành công và **48 kiểm tra đạt** với `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`. Bộ kiểm tra logic đã được bổ sung để hoàn thành cả 3 quỹ đạo với `No_Hand` sau xác nhận; script kiểm tra Gazebo cũng dùng `No_Hand` trong khi chạy. Log/JSON Gazebo bên dưới được thu **trước cập nhật ghi nhớ**, khi còn giữ `Thumb_Up`; chưa thu lại log Gazebo cho chế độ hạ tay.

Đã build package trên ROS 2 Jazzy, chạy Gazebo `gesture_arena`, undock thành công và chuyển dock tới (4, 4). Webcam laptop mở được bằng OpenCV, đọc ảnh 640 × 480; MediaPipe 0.10.21 nạp model `.task`, suy luận VIDEO trên ảnh và node publish `No_Hand` khi không có cử chỉ hợp lệ. Launch control khởi động hai node, hiển thị cửa sổ và thoát sạch khi SIGINT. Đã thử cho recognizer thoát riêng: launch tự dừng behavior controller sạch; [log vòng đời](launch_lifecycle.log).

Ở lần kiểm tra trước cập nhật ghi nhớ, `python3 -m pytest -q src/tb4_assignment/test`: **40 passed**, gồm 26 kiểm tra gesture/behavior và 14 kiểm tra navigation hiện có. Các kiểm tra mới bao gồm trạng thái chờ xác nhận, lọc nhiễu, không lặp lệnh, timeout, dừng/hủy, 4 chu kỳ tiến–lùi, vòng tròn, chào, tốc độ quay giới hạn, LiDAR lỗi/vật cản và quét phía sau khi lùi.

Kiểm tra tích hợp dùng **nhãn cử chỉ tự động**, scan/odom thật từ Gazebo và `/cmd_vel` thật; không phải bằng chứng người đã biểu diễn đủ cử chỉ trước webcam. Tốc độ mô phỏng trên máy khoảng 0.5 lần thời gian thực, nên thời lượng dưới đây là thời gian thực.

| Thử nghiệm | Kết quả |
| --- | --- |
| Chọn mà chưa xác nhận | Không tạo kế hoạch chuyển động |
| Pointing Up + Thumb Up | Hoàn thành 4 chu kỳ; khoảng 48.35 s; lệch vị trí đầu khoảng 8.4 mm |
| Victory + Thumb Up | Hoàn thành 1 vòng; khoảng 63.03 s; lệch vị trí đầu khoảng 6.9 mm |
| Wave + Thumb Up | Hoàn thành chuỗi quay trái/phải và trở lại gần hướng đầu; xem dữ liệu đo |
| Giữ Thumb Up sau khi xong | Không khởi động lại |
| Open Palm | Xóa kế hoạch; vận tốc cuối bằng zero trong lần kiểm tra sau 0.15–0.16 s |
| Closed Fist | Về chờ, vận tốc cuối bằng zero |
| Ngừng publish cử chỉ | Watchdog xóa kế hoạch, vận tốc cuối bằng zero; kiểm tra sau khoảng 1.1 s |

Dữ liệu pose/thời lượng: [simulation_results.json](simulation_results.json). Log tiến–lùi/vòng tròn: [trajectories.log](trajectories.log). Log chào/dừng đã chạy lại với duy nhất một behavior controller: [wave_stop_recheck.log](wave_stop_recheck.log). Thời gian kiểm tra dừng là thời điểm lấy mẫu để xác nhận, không phải phép đo latency nhỏ nhất. Pose và hoàn thành kế hoạch chưa phải kiểm chứng tiếp xúc vật lý độc lập; demo thực tế vẫn cần quan sát không va chạm.

Chạy lại kiểm tra tích hợp sau khi thực hiện bước chuẩn bị simulation trong README. **Dừng `gesture_control.launch.py`, Nav2, teleop và mọi node phát vận tốc khác trước**. Script tự điều khiển mô phỏng và ghi đè JSON kết quả; đây là kiểm thử kỹ thuật, không phải demo điều khiển bằng webcam:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
python3 docs/gesture_control/validate_sim.py
```

Còn cần người dùng biểu diễn trực tiếp 5 cử chỉ tĩnh và Wave, thu video và đánh giá khả năng phân biệt Wave/Open Palm trong ánh sáng thực tế. Không suy ra độ chính xác nhận diện cả 6 cử chỉ từ các bài kiểm tra logic hoặc nhãn tự động.
