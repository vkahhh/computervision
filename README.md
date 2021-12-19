# Nhóm 05: Hệ thống điểm danh nhận diện khuôn mặt

  ![Gui Application View](icon/aufr.jpg?raw=true "PyQt GUI")

## Các thuật toán xử lý ảnh được triển khai
  - Eigenfaces
  - Localbinary Pattern Histograms[LBPH]
  - Fisherfaces

# Hướng dẫn sử dụng
 1. Thiết lập môi trường và các công cụ liên quan.
 2. Triển khai chương trình.

### 1. Thiết lập môi trường và các công cụ
 1. Cài đặt Python 
- ```sudo apt install python```
 2. Cài đặt OpenCV và công cụ PyQt5.
- ```pip3 install --user pyqt5```
- ```sudo apt-get install python3-pyqt5```
- ```sudo apt-get install pyqt5-dev-tools```
- ```sudo apt-get install qttools5-dev-tools```
- ```sudo pip install opencv-contrib-python```   
### 2. Triển khai chương trình
 - Chạy chương trình qua lệnh  ```$ python main.py```

  1. Nhập tên và khóa của mỗi sinh viên.
  2. Chọn thuật toán xử lý ảnh.
  3. Chọn Recognize Face (Nhận diện khuôn mặt).
  4. Chọn Attendance để xuất danh sách điểm danh.

## Các tài liệu liên quan
  - [OpenCV](https://docs.opencv.org/2.4/modules/contrib/doc/facerec/facerec_tutorial.html)
  - [PyQt5](http://pyqt.sourceforge.net/Docs/PyQt5/)
