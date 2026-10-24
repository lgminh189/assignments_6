# Điều khiển TurtleBot 4 bằng cử chỉ tay — ROS 2 và MediaPipe

Dự án sử dụng webcam laptop, OpenCV và MediaPipe Gesture Recognizer để điều khiển TurtleBot 4 trong Gazebo. Robot ghi nhớ hành vi đã chọn, chỉ thực hiện sau khi được xác nhận và tự hoàn thành hành vi khi người dùng hạ tay.

Môi trường phát triển: **Ubuntu 24.04, ROS 2 Jazzy, Gazebo Sim Harmonic, Python 3.12**. Các launch trong repository dành cho Jazzy; không dùng trực tiếp cho ROS 2 Humble/Ubuntu 22.04.

## 1. Chức năng và kiến trúc

```text
Webcam laptop
    │ OpenCV + MediaPipe Tasks + theo dõi chuyển động bàn tay
    ▼
gesture_recognition_node
    │ /detected_gesture (std_msgs/msg/String)
    ▼
robot_behavior_node ◄── /scan và /odom
    │ /cmd_vel (geometry_msgs/msg/TwistStamped)
    ▼
TurtleBot 4 trong Gazebo
```

`gesture_recognition_node` hiển thị ảnh webcam, landmarks, nhãn AI/confidence, tiến độ vẫy tay và trạng thái robot. `robot_behavior_node` lọc lệnh nhiễu, quản lý chọn/xác nhận, đo quãng đường/góc quay bằng odometry và dừng khi có lỗi hoặc vật cản.

| Cử chỉ | Nhãn trên topic | Hành vi |
| --- | --- | --- |
| Vẫy tay | `Wave` | Chọn chào: robot quay trái–phải rồi trở về gần hướng đầu |
| Giơ một ngón | `Pointing_Up` | Chọn tiến 0.35 m, lùi 0.35 m, lặp **4 chu kỳ** |
| Giơ hai ngón | `Victory` | Chọn chạy **1 vòng tròn**, bán kính 0.6 m |
| Giơ ngón cái | `Thumb_Up` | Xác nhận và thực hiện hành vi đã chọn |
| Xòe tay tĩnh | `Open_Palm` | Dừng ngay và xóa lựa chọn/hành vi |
| Nắm tay | `Closed_Fist` | Hủy hành vi, trở về chờ |

Năm cử chỉ tĩnh dùng model có sẵn của MediaPipe. `Wave` được suy ra từ chuyển động tâm lòng bàn tay qua nhiều khung hình, kết hợp landmarks; không phải class có sẵn hoặc model Wave tự huấn luyện.

## 2. Cấu trúc repository

```text
README.md
requirements-gesture.txt
.gitignore
src/tb4_assignment/
├── package.xml
├── CMakeLists.txt
├── scripts/
│   ├── gesture_recognition_node.py  # Webcam, AI và publish cử chỉ
│   ├── robot_behavior_node.py       # Chọn/xác nhận và điều khiển vận tốc
│   └── gesture_logic.py             # Lọc cử chỉ, phát hiện Wave, máy trạng thái
├── launch/
│   ├── gesture_sim.launch.py        # Gazebo + TurtleBot 4
│   ├── gesture_control.launch.py    # Hai node nhận diện/điều khiển
│   └── gz_ogre2.launch.py           # Gazebo server và GUI dùng Ogre2
├── worlds/gesture_arena.sdf         # Sân trống có tường bao 10 × 10 m
└── test/test_gesture_behavior.py
docs/gesture_control/               # Hướng dẫn kiểm chứng, script, log và kết quả
```

Package còn giữ các node/launch, config và map của bài SLAM/Navigation/YOLO trước. Chúng không được khởi chạy trong demo cử chỉ; hướng dẫn riêng tại [docs/README_navigation_yolo.md](docs/README_navigation_yolo.md).

## 3. Cài đặt

### 3.1. Dependency hệ thống

Cài ROS 2 Jazzy và Gazebo Harmonic trước. Sau đó cài các gói sau; một số gói navigation được giữ để đáp ứng dependency của package hiện có:

```bash
sudo apt update
sudo apt install \
  git curl python3-venv python3-pytest python3-opencv python3-yaml \
  python3-colcon-common-extensions python3-rosdep \
  ros-jazzy-rmw-fastrtps-cpp \
  ros-jazzy-turtlebot4-gz-bringup \
  ros-jazzy-turtlebot4-navigation \
  ros-jazzy-slam-toolbox \
  ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-simple-commander \
  ros-jazzy-cv-bridge
```

Máy cần webcam laptop, quyền truy cập `/dev/video*` và màn hình đồ họa để hiển thị Gazebo/OpenCV. Đóng các ứng dụng khác đang chiếm webcam trước khi chạy.

### 3.2. Tải source code

Clone repository Public của bạn, thay `YOUR_USERNAME` và `YOUR_REPOSITORY` bằng thông tin thực tế:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git ~/tb4_slam_ws
cd ~/tb4_slam_ws
```

Nếu dùng ZIP, giải nén và đặt source vào `~/tb4_slam_ws`, sao cho có đường dẫn `~/tb4_slam_ws/src/tb4_assignment/package.xml`. Các lệnh bên dưới giả định workspace ở vị trí này.

### 3.3. Build ROS 2 package

Với máy mới, khởi tạo rosdep một lần bằng `sudo rosdep init` nếu chưa khởi tạo. Sau đó:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select tb4_assignment
source install/setup.bash
```

### 3.4. Cài MediaPipe trong venv

Dùng Python hệ thống cùng phiên bản với ROS và `--system-site-packages` để import được `rclpy`. Venv này dành riêng cho cử chỉ:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
python3 -m venv --system-site-packages .venv-gesture
.venv-gesture/bin/python -m pip install -r requirements-gesture.txt
.venv-gesture/bin/python -c \
  "import rclpy, cv2, mediapipe; print('Imports OK')"
```

Các phiên bản được giới hạn trong `requirements-gesture.txt`: MediaPipe 0.10.21, NumPy dưới 2 và OpenCV dưới 4.12. Không cần cài YOLO để chạy bài cử chỉ.

### 3.5. Tải model Gesture Recognizer

Model không được đóng gói trong repository; tải sau khi clone:

```bash
cd ~/tb4_slam_ws
mkdir -p models
curl -fL \
  https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task \
  -o models/gesture_recognizer.task
```

## 4. Khởi chạy demo — dùng 3 terminal

Dừng phiên ROS/Gazebo/Navigation/teleop cũ trước khi chạy. Mỗi khối dưới đây đã có phần thiết lập môi trường. Không chạy đồng thời node điều hướng, teleop hoặc publisher vận tốc khác trong demo này.

### Terminal 1 — Gazebo và TurtleBot 4

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment gesture_sim.launch.py gui:=true
```

World `gesture_arena` có sân trống 10 × 10 m và tường bao. Robot bắt đầu trên dock; chưa chạy node điều khiển ở bước này.

### Terminal 2 — Undock và chuẩn bị khu vực di chuyển

Đợi khoảng 20–30 giây để mô phỏng/controller sẵn sàng, rồi chạy:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
```

**Chờ kết quả `SUCCEEDED`**. Nếu goal bị từ chối vì robot chưa sẵn sàng, đợi thêm rồi chạy lại. Sau khi undock thành công, chuyển dock ra góc sân để không cản quỹ đạo robot:

```bash
gz service -s /world/gesture_arena/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'name: "standard_dock", position: {x: 4.0, y: 4.0, z: 0.0}'
```

Kết quả phải có `data: true`. Undock và chuyển dock là bước chuẩn bị trước demo; không chạy undock đồng thời với behavior controller.

Kiểm tra giao tiếp ROS:

```bash
ros2 topic info /cmd_vel -v
ros2 topic echo /scan --once --field range_min
ros2 topic echo /odom --once --field pose.pose.position
```

`/cmd_vel` phải có kiểu `geometry_msgs/msg/TwistStamped` và subscriber `motion_control`. Kiểm tra robot thật sự nhận vận tốc bằng cử chỉ sau khi mở Terminal 3: quan sát robot di chuyển trong Gazebo và pose trên `/odom` thay đổi.

### Kiểm tra riêng webcam — tùy chọn, trước Terminal 3

Dùng terminal đã source ROS/workspace:

```bash
cd ~/tb4_slam_ws
.venv-gesture/bin/python src/tb4_assignment/scripts/gesture_recognition_node.py \
  --ros-args -p webcam_only:=true
```

Chế độ này chỉ hiển thị ảnh OpenCV, không suy luận AI; publish `Camera_Error` để không duy trì điều khiển robot. Đóng cửa sổ để nhả webcam trước khi chạy nhận diện đầy đủ.

### Terminal 3 — Nhận diện cử chỉ và điều khiển robot

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment gesture_control.launch.py \
  python_executable:="$PWD/.venv-gesture/bin/python" \
  model_path:="$PWD/models/gesture_recognizer.task" \
  camera_index:=0
```

Launch mở cả hai node. Recognizer chạy bằng Python trong venv, behavior controller chạy bằng Python ROS hệ thống. Nếu một node thoát, launch dừng node còn lại.

Trong cửa sổ webcam:

- Dòng đầu: kết quả điều khiển và `AI: <nhãn gốc> <confidence>`.
- Dòng trạng thái: `IDLE`, `SELECTED: ...`, `RUNNING: ...` hoặc lý do dừng.
- Dòng Wave: số lượt vẫy `0/3`, `1/3`, `2/3` và thông báo đã nhận Wave.

Khi sửa code hoặc cập nhật phiên bản, dừng Terminal 3 bằng Ctrl+C rồi chạy lại lệnh launch để node nạp code mới.

## 5. Cách thao tác bằng tay

Chỉ dùng **một tay**, hướng lòng bàn tay về camera, ánh sáng đủ và cả bàn tay nằm trong khung hình. Không dùng bàn phím để điều khiển robot trong demo.

### Chọn, xác nhận và hạ tay

1. Giơ một ngón hoặc hai ngón khoảng 0.4 giây, chờ `SELECTED`.
2. Giơ ngón cái khoảng 1 giây, chờ `RUNNING`.
3. Hạ tay. Robot ghi nhớ và tự thực hiện hết hành vi, không cần giữ ngón tay.

Lựa chọn hết hạn sau 8 giây nếu chưa xác nhận. Giơ ngón cái khi chưa chọn hành vi không tạo lệnh chuyển động. Sau khi kết thúc, robot đứng yên; giữ nguyên ngón cái không làm chạy lại.

### Vẫy tay để robot chào

1. Xòe bàn tay, di chuyển cả bàn tay ngang trái → phải → trái → phải trong khoảng 2–3 giây, biên độ nên khoảng 1/5 chiều rộng ảnh.
2. Theo dõi bộ đếm `Wave: 1/3 → 2/3`; khi đủ 3 lượt, cửa sổ báo `Wave OK`.
3. Giữ tay xòe yên khoảng 0.5 giây, chờ `SELECTED: Wave`.
4. Giơ ngón cái khoảng 1 giây để xác nhận, rồi hạ tay khi thấy `RUNNING`.

Xòe tay tĩnh ban đầu phát lệnh dừng là bình thường. Chỉ khi đủ chuyển động luân phiên, recognizer mới chọn Wave. Chỉ lắc các ngón hoặc quét một chiều có thể không đủ. Ngưỡng mặc định là 6% chiều rộng ảnh/lượt trong cửa sổ 3 giây; bộ phát hiện giữ lịch sử qua mất nhận diện ngắn dưới 0.35 giây và dùng thêm hình học lòng bàn tay.

Có thể thêm vào cuối lệnh launch nếu cần vẫy chậm hoặc biên độ nhỏ hơn:

```text
wave_amplitude:=0.05 wave_window:=3.5
```

### Dừng, hủy và chạy lại

- **Xòe tay tĩnh:** dừng ngay và xóa hành vi đang chạy.
- **Nắm tay:** hủy và về trạng thái chờ.
- Muốn chạy lại: chọn cử chỉ rồi xác nhận lại bằng ngón cái. Robot bắt đầu hành vi từ đầu, không tiếp tục đoạn đang dở.

## 6. Chống nhiễu và điều kiện dừng

Lệnh tĩnh cần confidence ≥ 0.65, nhãn ổn định ≥ 0.25 giây và cooldown 0.7 giây. Giữ nguyên một cử chỉ không phát lặp lệnh. Open Palm và Closed Fist bỏ qua thời gian giữ để dừng ngay khi có nhận diện hợp lệ.

`No_Hand` nghĩa là camera/AI vẫn xử lý được ảnh nhưng không thấy cử chỉ hợp lệ: robot giữ lựa chọn hoặc tiếp tục hành vi đã xác nhận. Che ống kính vẫn có thể tạo ảnh hợp lệ, không được coi là mất kết nối.

Robot dừng, xóa hành vi và phát vận tốc zero khi:

- Nhận `Open_Palm`, `Closed_Fist` hoặc lỗi `Camera_Error`.
- Không nhận bản tin recognizer quá 0.8 giây.
- `/scan` hoặc `/odom` cũ quá 0.8 giây, hoặc dữ liệu dùng cho điều khiển không hợp lệ.
- LiDAR thấy vật cản gần hơn 0.55 m theo hướng di chuyển; khi quay/chạy cong kiểm tra toàn vòng.
- Chuyển động vượt thời gian cho phép.

Watchdog dùng đồng hồ monotonic và timer steady; không phụ thuộc việc đồng hồ mô phỏng có tiếp tục chạy hay không. Vận tốc được publish ở 20 Hz; mặc định tiến/lùi 0.12 m/s, chào quay 0.35 rad/s. Robot không tự resume sau khi bị dừng. Chức năng hiện tại dừng trước vật cản, chưa lập kế hoạch đường né vật cản như Nav2.

## 7. Kiểm tra và nghiệm thu

### Quan sát topic

Trong terminal đã source ROS/workspace và export Fast DDS, chạy mỗi lệnh echo ở một terminal riêng:

```bash
ros2 topic echo /detected_gesture
ros2 topic echo /robot_behavior/state
ros2 topic echo /cmd_vel
ros2 topic echo /odom --field pose.pose.position
```

Khi chọn nhưng chưa xác nhận, vận tốc phải bằng zero. Sau xác nhận, vận tốc khác zero và pose thay đổi kể cả khi đã hạ tay. Khi dừng/hủy hoặc recognizer ngừng gửi tín hiệu, vận tốc phải về zero.

### Kiểm tra tự động

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
python3 -m pytest -q src/tb4_assignment/test
```

Kết quả đã chạy: **58 kiểm tra đạt**, gồm lọc nhiễu, chọn/xác nhận, ghi nhớ khi hạ tay, chống lặp, phát hiện Wave, dừng/hủy, timeout và các kiểm tra navigation cũ. Package đã build thành công.

Đã kiểm tra webcam đọc ảnh 640 × 480 và MediaPipe nạp model. Log Gazebo sẵn có ghi nhận tiến–lùi 4 chu kỳ, vòng tròn, chào và dừng/hủy bằng nhãn tự động. Log này được thu trước các cập nhật ghi nhớ/Wave mới; chưa phải bằng chứng nghiệm thu đầy đủ với tay thật của người dùng. Xem chi tiết và script chạy lại tại [docs/gesture_control/validation.md](docs/gesture_control/validation.md).

Video nghiệm thu cần thể hiện 5 cử chỉ tĩnh và Wave, robot đứng yên trước xác nhận, tự chạy khi hạ tay, 4 chu kỳ tiến–lùi, một vòng tròn, chào, dừng/hủy và mất kết nối; quan sát không va chạm dock/tường. Video chưa được đóng gói trong repository.

## 8. Xử lý sự cố

| Hiện tượng | Cách kiểm tra |
| --- | --- |
| Không mở được webcam | Đóng ứng dụng đang chiếm camera; kiểm tra `/dev/video*`; thử `camera_index:=2`. `/dev/video1` có thể là thiết bị metadata. |
| Không import được MediaPipe | Cài `requirements-gesture.txt`, truyền đúng `python_executable` trong venv. |
| Không import được rclpy | Source ROS, dùng Python hệ thống để tạo venv với `--system-site-packages`. |
| Robot không chạy sau cử chỉ | Kiểm tra có `SELECTED`, xác nhận bằng ngón cái khoảng 1 giây, xem lý do dừng trên cửa sổ/log. |
| `STOPPED: obstacle or stale/invalid sensors` | Kiểm tra `/scan`, `/odom`, dock đã chuyển ra góc và đường đi đủ trống. Sau khi xử lý phải chọn/xác nhận lại. |
| Wave không tăng bộ đếm | Xòe cả bàn tay, di chuyển ngang đủ rộng, giảm tốc độ vẫy, xem nhãn AI và landmarks; dùng các tham số Wave ở mục 5 nếu cần. |
| Node vẫn chạy hành vi cũ sau sửa code | Dừng và khởi động lại Terminal 3. |
| Gazebo lỗi cửa sổ đồ họa | Có thể dùng `gui:=false` để kiểm tra server; để quay demo cần môi trường đồ họa hoạt động. |
| ROS không tìm thấy package/topic | Source `/opt/ros/jazzy/setup.bash` và `install/setup.bash`, dùng cùng `RMW_IMPLEMENTATION=rmw_fastrtps_cpp` ở mọi terminal. |

Để kết thúc phiên: Ctrl+C Terminal 3 trước, sau đó Ctrl+C Terminal 1. Terminal undock đã hoàn tất thì không cần dừng.

## 9. Đưa source lên GitHub Public

Giải nén ZIP và tải **nội dung bên trong thư mục dự án** lên repository để `README.md`, `requirements-gesture.txt` và `src/` nằm ở gốc repository. Không chỉ upload nguyên file ZIP. Tạo repository trên GitHub, chọn **Public**, rồi dùng giao diện Add file → Upload files hoặc Git.

Ví dụ dùng Git trong thư mục đã giải nén, thay tên tài khoản/repository thực tế. Với cách này nên tạo repository Public trống trước:

```bash
git init
git add README.md .gitignore requirements-gesture.txt requirements-yolo.txt src docs
git commit -m "Add TurtleBot 4 hand gesture control with ROS 2 and MediaPipe"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

File ZIP chứa source, launch, world, cấu hình/map dùng bởi package, dependency Python và tài liệu. Không chứa `build/`, `install/`, `log/`, venv, model `.task`/`.pt`, cache IDE/Python hoặc các báo cáo/ZIP cũ. Model được tải bằng lệnh ở mục 3.5.

## 10. Tài liệu tham khảo

- [MediaPipe Gesture Recognizer — Python](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer/python)
- [MediaPipe Gesture Recognizer — model và các nhãn có sẵn](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer)
- [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/)
