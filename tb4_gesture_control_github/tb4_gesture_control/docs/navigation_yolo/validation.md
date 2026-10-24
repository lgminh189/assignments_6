# Kiểm chứng Navigation + YOLO

Workspace dùng ROS 2 Jazzy/Gazebo Harmonic, TurtleBot 4 standard trong world warehouse. Dùng bản đồ tuần trước tại `src/tb4_assignment/maps/final_map.yaml` cùng `final_map.pgm` (605 × 975, 0.05 m/pixel), không tạo lại bản đồ.

## Điều hướng đã chạy trong Gazebo

Chạy `navigation.launch.py rviz:=false gui:=false auto_undock:=true`, sau đó node `navigate_goals.py` với `use_sim_time:=true`. Ba điểm chọn trên vùng trống của bản đồ, kiểm tra khoảng cách tới ô không phải free trên ảnh PGM lần lượt khoảng 2.23 m, 1.97 m và 2.00 m. Nav2 chạy tuần tự và trả kết quả:

| Goal | x | y | yaw (rad) | Kết quả |
| --- | --- | --- | --- | --- |
| 1 | -5.0 | 1.0 | 1.5708 | SUCCEEDED |
| 2 | -5.0 | 6.0 | 0.0 | SUCCEEDED |
| 3 | 3.0 | 6.0 | 0.0 | SUCCEEDED |

Không gửi goal bằng chuột hoặc teleop trong nhiệm vụ. Log đầy đủ: [navigation.log](navigation.log). Các điểm đã lưu ở `config/goals.yaml` và được dùng mặc định bởi node. Chỉ tái sử dụng khi dùng đúng map/world; vẫn kiểm tra localization trước mỗi phiên.

## Camera và YOLO đã chạy trong Gazebo

- Kiểm tra nhận được `/map`, `/scan` (640 tia), `/amcl_pose` và RGB 320 × 240.
- Node nhận ảnh `rgb8` từ `/oakd/rgb/preview/image_raw`, đổi sang BGR bằng `cv_bridge`, chạy YOLOv8n CPU và publish `/yolo/annotated_image` (`bgr8`).
- Thêm mô hình Casual Female vào world tại `(5.0, 5.5, 0.0)`, yaw pi, ngoài tuyến goal. Khi robot tiến tới Goal 3, YOLO nhận diện `person`; mẫu lưu có confidence **0.8793**.
- Dữ liệu kết quả: [detection.json](detection.json). Đây là tọa độ bbox pixel, không phải tọa độ vật thể trong map.
- Ảnh camera: [rgb_image.png](rgb_image.png); ảnh kết quả: [annotated_image.png](annotated_image.png). Ảnh và JSON lấy từ cùng phiên chạy, có thể khác frame.

Các phiên bản đã dùng: Ultralytics 8.4.178, PyTorch 2.14.1+cpu, torchvision 0.29.1+cpu, NumPy 1.26.4, OpenCV 4.11.0. Môi trường `.venv-yolo` đọc được thư viện ROS hệ thống và dùng `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` thống nhất với simulation.

## Build và kiểm thử

`colcon build --symlink-install --packages-select tb4_assignment` thành công. `python3 -m pytest -q src/tb4_assignment/test/test_navigation.py`: **14 passed**. Kiểm thử bao gồm thứ tự goal, quaternion, dừng khi thất bại/từ chối/hủy, timeout và lưu tọa độ từ RViz đúng frame/yaw.

Đã khởi chạy RViz bằng `view_assignment.launch.py` với map, RobotModel, scan, RGB và ảnh YOLO. RViz có ghi lỗi shader OpenGL của display Map lúc khởi động và thông báo bỏ một số scan cũ; chưa xác nhận trực quan toàn bộ cửa sổ RViz. Cần kiểm tra các display trên màn hình của máy trước khi chụp bằng chứng nộp bài. Kết quả action và nhận diện nêu trên được kiểm chứng qua ROS, không suy ra từ ảnh RViz.

Chưa ghi video toàn tuyến hoặc đo độc lập khoảng cách va chạm; SUCCEEDED là kết quả do Nav2 báo. Các tài liệu báo cáo DOCX/PDF cũ của bài SLAM chưa được cập nhật cho bài YOLO này.
