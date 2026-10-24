# TurtleBot 4 — SLAM, Navigation và YOLO (bài trước)

Tài liệu cho các chức năng cũ được giữ trong package. Với bài cử chỉ tay, dùng [README chính](../README.md).

## Chạy lại bài Navigation + YOLO — sao chép theo từng terminal

Dùng mục này cho workspace hiện tại đã build và cài YOLO. **Mở 5 terminal riêng**, sao chép toàn bộ khối lệnh tương ứng; mỗi khối đã có đầy đủ phần thiết lập môi trường. Không chạy thêm phiên simulation/localization khác từ các mục hướng dẫn chi tiết bên dưới.

### Terminal 1 — Gazebo + Localization + Nav2

Khởi chạy đúng world warehouse và nạp final_map mặc định. Giữ terminal này chạy.

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment navigation.launch.py \
  world:=warehouse model:=standard \
  gui:=true rviz:=false auto_undock:=true
```

### Terminal 2 — RViz: robot, map, LiDAR, camera RGB và YOLO

Dùng cấu hình assignment.rviz đã sửa topic ảnh. Hai khung ảnh nằm trong RViz; ảnh YOLO xuất hiện sau khi Terminal 4 chạy.

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment view_assignment.launch.py
```

### Terminal 3 — Thêm người để nhận diện

Chạy sau khi Gazebo đã tải xong world; chỉ chạy một lần trong mỗi phiên mô phỏng. Lệnh tự kết thúc sau khi thêm mô hình.

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment demo_objects.launch.py \
  world:=warehouse x:=5.0 y:=5.5
```

### Terminal 4 — Nhận diện YOLO từ camera

Giữ terminal này chạy. Ảnh RGB và ảnh YOLO hiển thị trong RViz. Muốn thêm cửa sổ OpenCV riêng, thêm -p show_window:=true vào cuối lệnh.

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

.venv-yolo/bin/python src/tb4_assignment/scripts/yolo_detector.py \
  --ros-args -p use_sim_time:=true \
  -p image_topic:=/oakd/rgb/preview/image_raw \
  -p model:="$HOME/tb4_slam_ws/yolov8n.pt" \
  -p confidence:=0.45 -p inference_rate:=2.0 -p device:=cpu
```

### Terminal 5 — Tự động di chuyển qua 3 goal

Chờ ít nhất khoảng 30 giây từ khi khởi động mô phỏng, robot đã rời dock và Nav2 sẵn sàng. Kiểm tra LiDAR khớp tường; nếu lệch, dùng 2D Pose Estimate trước. Lệnh dùng 3 goal warehouse đã kiểm tra trong config/goals.yaml.

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 run tb4_assignment navigate_goals.py \
  --ros-args -p use_sim_time:=true
```

Khi robot đang đi, không dùng teleop hoặc đặt Nav2 Goal bằng chuột. Kết quả mong đợi: lần lượt `Goal 1 SUCCEEDED`, `Goal 2 SUCCEEDED`, `Goal 3 SUCCEEDED`; khi người vào khung hình, terminal YOLO in `person` cùng confidence.

Để dừng phiên, nhấn **Ctrl-C** trong các terminal còn chạy, ưu tiên dừng node điều hướng trước rồi YOLO, RViz và simulation. Terminal thêm người đã tự thoát thì không cần dừng.

## Nội dung repository

- `src/tb4_assignment/launch/`: launch mapping, localization, navigation và Gazebo Ogre2.
- `src/tb4_assignment/config/`: tham số SLAM Toolbox, Nav2/AMCL và mẫu cấu hình goal.
- `src/tb4_assignment/scripts/`: ghi goal, chạy tuần tự ít nhất 3 goal và nhận diện YOLO.
- `requirements-yolo.txt`: thư viện Python nhận diện, cài trong venv riêng.
- `src/tb4_assignment/maps/final_map.yaml` và `final_map.pgm`: bản đồ warehouse đã lưu (605 × 975 pixel, độ phân giải 0.05 m/pixel).

## Yêu cầu

- Ubuntu 24.04, ROS 2 Jazzy và Gazebo Sim/Harmonic.
- TurtleBot 4 ROS 2 packages và các dependency của chúng.
- SLAM Toolbox, Nav2, `teleop_twist_keyboard`, `colcon`.

Cài các package ROS cần dùng nếu chưa có:

```bash
sudo apt update
sudo apt install \
  ros-jazzy-turtlebot4-gz-bringup \
  ros-jazzy-turtlebot4-navigation \
  ros-jazzy-slam-toolbox \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-simple-commander \
  ros-jazzy-cv-bridge \
  python3-venv \
  ros-jazzy-teleop-twist-keyboard \
  python3-colcon-common-extensions
```

Máy hiện tại dùng **Jazzy**, vì vậy không cài các gói `ros-humble-*` vào workspace này. Đề bài dùng Humble/Ubuntu 22.04 thì cần môi trường riêng và launch Ignition tương ứng; các launch Gazebo Harmonic trong repository này dành cho Jazzy.

### Cài YOLO trong môi trường Python riêng

Dùng Python hệ thống cùng phiên bản với ROS để import được `rclpy`/`cv_bridge`. Cài PyTorch CPU trước để tránh tải các thư viện CUDA khi máy không cần GPU:

```bash
cd ~/tb4_slam_ws
python3 -m venv --system-site-packages .venv-yolo
source .venv-yolo/bin/activate
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-yolo.txt
python -c "import rclpy, cv_bridge, cv2; from ultralytics import YOLO; print('Imports OK')"
```

Trên máy hiện tại, thiếu `ensurepip` và sudo yêu cầu mật khẩu. Nếu chưa cài `python3-venv`, có thể dùng cách bootstrap đã áp dụng cho workspace này:

```bash
python3 -m venv --system-site-packages --without-pip .venv-yolo
curl -fL https://bootstrap.pypa.io/pip/pip.pyz -o /tmp/tb4-pip.pyz
.venv-yolo/bin/python /tmp/tb4-pip.pyz install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv-yolo/bin/python /tmp/tb4-pip.pyz install -r requirements-yolo.txt
```

`requirements-yolo.txt` giữ NumPy dưới 2 và OpenCV dưới 4.12 để tương thích với `cv_bridge` hệ thống. Model `yolov8n.pt` tải lần đầu nên cần Internet; có thể truyền đường dẫn weights cục bộ. Venv/weights không đưa lên Git.

## Clone và build

Repository này là ROS 2 workspace hoàn chỉnh; clone repository vào thư mục workspace:

```bash
git clone <URL_REPOSITORY_PUBLIC> ~/tb4_slam_ws
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Mỗi terminal ROS mới cần source môi trường:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

## Mapping bằng SLAM Toolbox

Khởi chạy Gazebo warehouse, TurtleBot 4, RViz2 và SLAM:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment sim_mapping.launch.py \
  world:=warehouse model:=standard rviz:=true gui:=true
```

Launch dùng renderer Ogre2; Gazebo server và GUI chạy tách riêng để lỗi render GUI không nhất thiết làm dừng physics/sensor server. Robot được spawn tại pose mặc định và launch mapping tự gửi yêu cầu undock; chờ undock hoàn tất trước khi lái.

Kiểm tra LiDAR/odometry và điều khiển teleop trong terminal khác:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 topic hz /scan
ros2 topic hz /odom
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true -p use_sim_time:=true -r cmd_vel:=/cmd_vel
```

Khảo sát các hành lang/khu vực có thể đi qua ở tốc độ chậm; nên quay lại gần các vùng đã quét để SLAM Toolbox đóng loop. Theo dõi `/map`, `/scan` và TF trên RViz2. Khi hoàn tất, lưu map vào thư mục package:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 run nav2_map_server map_saver_cli \
  -f "$HOME/tb4_slam_ws/src/tb4_assignment/maps/final_map"
```

Lệnh này cập nhật `final_map.yaml` và `final_map.pgm`; kiểm tra map trước khi commit/push. Muốn giữ bản hiện tại, lưu dưới tên khác thay vì ghi đè.

## Localization

Dừng phiên mapping, khởi chạy lại trong cùng world với map đã lưu:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment localization.launch.py \
  world:=warehouse model:=standard rviz:=true \
  map:="$(ros2 pkg prefix tb4_assignment)/share/tb4_assignment/maps/final_map.yaml"
```

Trong RViz2, dùng **2D Pose Estimate** để chỉ initial pose nếu AMCL chưa định vị được. Xác nhận robot hiển thị đúng vị trí so với Gazebo và TF `map -> odom` được publish. Localization launch cũng tự gửi yêu cầu undock sau khi khởi động.

## Autonomous navigation với Nav2

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment navigation.launch.py \
  world:=warehouse model:=standard rviz:=true gui:=true \
  map:="$(ros2 pkg prefix tb4_assignment)/share/tb4_assignment/maps/final_map.yaml"
```

`auto_undock` mặc định là `false`. Nếu robot còn trên dock và cần rời dock, bật tùy chọn này và chờ undock hoàn tất trước khi đặt goal:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment navigation.launch.py \
  world:=warehouse model:=standard rviz:=true gui:=true auto_undock:=true \
  map:="$(ros2 pkg prefix tb4_assignment)/share/tb4_assignment/maps/final_map.yaml"
```

Chờ Nav2 khởi động (launch trì hoãn 25 giây). Dùng **2D Pose Estimate** nếu cần, kiểm tra `/scan` trùng tường và vị trí robot khớp Gazebo. Đây là bước chuẩn bị; khi chạy node điều hướng, không teleop và không dùng **Nav2 Goal**.

### Khảo sát và ghi ít nhất 3 mục tiêu

Trong RViz2, đặt **Fixed Frame = map**. Chọn các điểm thuộc những khu vực khác nhau, trong vùng trắng đã quét và cách xa tường/vật cản. Khởi chạy bộ ghi:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 run tb4_assignment record_goals.py --ros-args \
  -p use_sim_time:=true -p output:="$HOME/tb4_slam_ws/goals.yaml" -p count:=3
```

Dùng công cụ **Publish Point** bấm Goal 1, Goal 2, Goal 3 theo thứ tự. Bộ ghi tự thoát khi đủ điểm và lưu `goals.yaml`. Bộ ghi không gửi lệnh chuyển động; file đã tồn tại sẽ không bị ghi đè khi bắt đầu phiên mới.

Publish Point chỉ có x/y, không có hướng. Yaw mặc định 0 rad (hướng +X của `map`); đặt hướng cho từng điểm **trước khi bấm** trong terminal khác:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 param set /goal_recorder yaw 1.5708
ros2 topic echo /clicked_point
# Hoặc đọc pose hiện tại để lấy x/y và quaternion:
ros2 topic echo /amcl_pose --once
```

Nếu lấy hướng từ quaternion `(qx, qy, qz, qw)`, tính `yaw = atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))`. Có thể sửa yaw trong YAML sau khi ghi. Cấu trúc file:

```yaml
frame_id: map
goals:
  - {x: 1.0, y: 2.0, yaw: 0.0}
  - {x: 3.0, y: 4.0, yaw: 1.5708}
  - {x: 5.0, y: 6.0, yaw: 3.1416}
```

**Các số trên chỉ minh họa cú pháp, chưa đo trên warehouse.** File `config/goals.yaml` cung cấp 3 tọa độ warehouse đã chạy thử thành công; node vẫn từ chối các file có ít hơn 3 điểm. Khi tự khảo sát, dùng file thực tế đã ghi từ RViz, không sao chép tọa độ minh họa ở trên. Kiểm tra lại thứ tự và ghi bảng `(x, y, yaw)` vào báo cáo.

### Chạy chương trình điều hướng

Có thể chạy ngay bộ tọa độ đã kiểm tra trong `config/goals.yaml` khi dùng đúng `warehouse` + `final_map`:

| Goal | x (m) | y (m) | yaw (rad) |
| --- | --- | --- | --- |
| 1 | -5.0 | 1.0 | 1.5708 |
| 2 | -5.0 | 6.0 | 0.0 |
| 3 | 3.0 | 6.0 | 0.0 |

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 run tb4_assignment navigate_goals.py --ros-args -p use_sim_time:=true
```

Hoặc sau khi robot đã rời dock, AMCL ổn định và đã ghi bộ goal riêng:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 run tb4_assignment navigate_goals.py --ros-args \
  -p use_sim_time:=true \
  -p goals_file:="$HOME/tb4_slam_ws/goals.yaml" \
  -p goal_timeout:=180.0
```

`navigate_goals.py` là ROS 2 node dùng `BasicNavigator`: đợi pose AMCL và Nav2 active, tạo `PoseStamped` trong `map`, chuyển yaw sang quaternion và gọi `goToPose()` lần lượt. Chỉ khi nhận `SUCCEEDED` mới gửi goal tiếp theo; feedback khoảng cách in mỗi 2 giây. Goal bị từ chối, thất bại, hủy hoặc quá thời gian thì dừng nhiệm vụ. Timeout tính theo thời gian thực; Ctrl-C yêu cầu hủy action hiện tại. Node không thay pose ban đầu đã thiết lập trên RViz. `localization_timeout` mặc định 120 giây; bước đợi lifecycle Nav2 active tiếp tục chờ nếu stack chưa sẵn sàng.

### Nhận diện YOLO song song

Mở terminal khác và sao chép toàn bộ khối lệnh sau. Chạy **bằng Python trong venv** để chắc chắn thấy Ultralytics; executable `ros2 run` có thể dùng Python hệ thống theo shebang:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

.venv-yolo/bin/python src/tb4_assignment/scripts/yolo_detector.py --ros-args \
  -p use_sim_time:=true \
  -p image_topic:=/oakd/rgb/preview/image_raw \
  -p model:="$HOME/tb4_slam_ws/yolov8n.pt" \
  -p confidence:=0.45 -p inference_rate:=2.0 -p device:=cpu
```

Node subscribe `sensor_msgs/Image` với QoS best effort, dùng `CvBridge` đổi sang BGR, suy luận YOLO, vẽ bounding box/tên class/confidence, rồi publish:

- `/yolo/annotated_image` (`sensor_msgs/Image`): ảnh nhận diện, giữ stamp/frame của ảnh gốc.
- `/yolo/detections` (`std_msgs/String`): JSON gồm stamp/frame, class, confidence và bbox pixel.
- Terminal: danh sách vật thể/confidence mỗi 2 giây; có thông báo khi không phát hiện.

Chỉ xử lý ảnh mới nhất, mặc định tối đa 2 lần/giây để giảm tải CPU. Thêm `-p show_window:=true` nếu muốn cửa sổ OpenCV. Có `perception.launch.py` để dùng khi Python hệ thống của executable đã import được Ultralytics.

Model COCO mặc định nhận diện người, xe, ghế...; không có class bình chữa cháy. Muốn nhận diện bình chữa cháy cần weights huấn luyện riêng hoặc tích hợp YOLO-World với bộ nhãn phù hợp. Khả năng nhận diện phụ thuộc hình dạng/texture vật thể mô phỏng. Có thể thêm người bằng launch sau (sau khi Gazebo đã chạy; lần đầu cần Internet nếu mesh chưa cache):

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment demo_objects.launch.py world:=warehouse x:=5.0 y:=5.5
```

Tọa độ chèn vật thể là hệ **world của Gazebo**, khác hệ `map` của goal. Launch thêm mô hình Casual Female từ Gazebo Fuel, có collision; chỉ chạy một lần cho mỗi phiên. Có thể thêm người/ghế qua GUI và chọn vị trí không chặn hoàn toàn hành lang. YOLO cung cấp nhận diện; Nav2 tránh vật cản dựa trên LiDAR/costmap, bbox ảnh chưa được chiếu thành vị trí vật thể trong `map`.

### Quan sát trên RViz2 và nghiệm thu

Có sẵn cấu hình hiển thị đầy đủ. Khi khởi động simulation với `rviz:=false`, mở RViz bằng:

```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch tb4_assignment view_assignment.launch.py
```

Hoặc trong RViz hiện có, mở `src/tb4_assignment/config/assignment.rviz`. Cấu hình gồm các display sau:

| Display | Topic/cấu hình |
| --- | --- |
| RobotModel | Description `/robot_description`, TF hợp lệ |
| Map | `/map`, durability **Transient Local**, Fixed Frame `map` |
| LaserScan | `/scan`, reliability **Best Effort** |
| Image (RGB) | `/oakd/rgb/preview/image_raw`, **Best Effort** |
| Image (YOLO) | `/yolo/annotated_image`, **Best Effort** |
| Path | `/plan` để xem đường đi Nav2 |

Chụp ảnh/video thể hiện map + robot + scan khớp tường, camera RGB và ảnh nhận diện. Lưu terminal có lần lượt `Goal 1 SUCCEEDED`, `Goal 2 SUCCEEDED`, `Goal 3 SUCCEEDED` cùng log tên vật thể/confidence. Bằng chứng chạy thử sẵn có tại [docs/navigation_yolo](navigation_yolo/validation.md): cả 3 goal SUCCEEDED và nhận diện person trên camera Gazebo. Khi thay map/goal, cần thu lại bằng chứng; việc build thành công không chứng minh robot đã tới đích hoặc không va chạm.

Kiểm tra logic chương trình:

```bash
source /opt/ros/jazzy/setup.bash
python3 -m pytest -q src/tb4_assignment/test/test_navigation.py
```

## Tài liệu tham khảo

- [TurtleBot 4 Navigator (chọn tab Jazzy cho workspace này)](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html)
- [Nav2 Simple Commander API](https://docs.nav2.org/commander_api/index.html)
- [Ultralytics Predict: ảnh OpenCV, kết quả và bounding boxes](https://docs.ultralytics.com/modes/predict/)

## Kiểm tra nhanh / xử lý sự cố

Nếu hai khung Image báo **No Image**, mở thuộc tính display và kiểm tra **Topic** cùng **Reliability Policy = Best Effort**. Trong file `.rviz` của Jazzy, khóa cấu hình là `Topic`, không phải `Image Topic`. Sau khi cập nhật cấu hình, mở lại `view_assignment.launch.py` hoặc dùng **File → Open Config** để nạp lại `assignment.rviz`.


```bash
cd ~/tb4_slam_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 topic list | grep -E '^/(scan|odom|map|cmd_vel)$'
ros2 topic echo /amcl_pose --once
ros2 action list | grep navigate
ros2 run tf2_ros tf2_echo map base_link
```

- Không có `/scan`: kiểm tra Gazebo server còn chạy và đúng ROS environment/DDS.
- RobotModel báo thiếu TF: kiểm tra `/tf`, `/tf_static` và frame `base_link`; không khởi chạy nhiều phiên mô phỏng cũ cùng lúc.
- RViz không hiện map: kiểm tra `map:=...` và YAML có tham chiếu đúng `final_map.pgm`.
- Nếu GUI Gazebo gặp lỗi OpenGL, thử `gui:=false`; server mô phỏng vẫn có thể chạy không cửa sổ. Tránh bật software rendering nếu nó làm Gazebo crash trên máy.

## Đưa lên GitHub Public

Tạo repository Public trên GitHub, sau đó chạy từ thư mục workspace:

```bash
git init
git add README.md .gitignore src/tb4_assignment
git commit -m "Add TurtleBot 4 SLAM and Nav2 assignment"
git branch -M main
git remote add origin <URL_REPOSITORY_PUBLIC>
git push -u origin main
```

Không đưa `build/`, `install/`, `log/` hoặc cache IDE lên repository.
