import cv2
import os
import sys
import numpy as np
import datetime
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt
import csv
import face_recognition


class USER(QDialog):  # Dialog box for entering name and key of new dataset.
    """USER Dialog """

    def __init__(self):
        super(USER, self).__init__()
        loadUi("user_info.ui", self)

    def get_name_key(self):
        name = self.name_label.text()
        key = int(self.key_label.text())
        return name, key


class AUFR(QMainWindow):  # Main application
    """Main Class"""

    def __init__(self):
        super(AUFR, self).__init__()
        loadUi("mainwindow.ui", self)
        self.setWindowTitle("Hệ thống điểm danh dựa trên nhận diện khuôn mặt - Nhóm 05")
        # Classifiers, frontal face, eyes and smiles.
        self.face_classifier = cv2.CascadeClassifier("classifiers/haarcascade_frontalface_default.xml")
        self.eye_classifier = cv2.CascadeClassifier("classifiers/haarcascade_eye.xml")
        self.smile_classifier = cv2.CascadeClassifier("classifiers/haarcascade_smile.xml")

        # date and time
        now = QDate.currentDate()
        current_date = now.toString('ddd dd MMMM yyyy')
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.date_label.setText(current_date)
        self.time_label.setText(current_time)

        self.image = None

        # Variables
        self.camera_id = 0  # can also be a url of Video
        self.dataset_per_subject = 50
        self.ret = False
        self.trained_model = 0

        self.image = cv2.imread("icon/app_icon.jpg", 1)
        self.modified_image = self.image.copy()

        self.display()
        # Actions
        self.generate_dataset_btn.setCheckable(True)
        self.train_model_btn.setCheckable(True)
        self.recognize_face_btn.setCheckable(True)
        # Menu
        self.about_menu = self.menu_bar.addAction("About")
        self.help_menu = self.menu_bar.addAction("Help")
        self.about_menu.triggered.connect(self.about_info)
        self.help_menu.triggered.connect(self.help_info)
        # Algorithms
        self.algo_radio_group.buttonClicked.connect(self.algorithm_radio_changed)
        # Recangle
        self.face_rect_radio.setChecked(True)
        self.eye_rect_radio.setChecked(False)
        self.smile_rect_radio.setChecked(False)
        # Events
        self.generate_dataset_btn.clicked.connect(self.generate)
        self.train_model_btn.clicked.connect(self.train)
        self.recognize_face_btn.clicked.connect(self.recognize)
        self.checkin_btn.clicked.connect(self.attendance)
        self.checkout_btn.clicked.connect(self.attendance)
        self.video_recording_btn.clicked.connect(self.save_video)
        # Recognizers
        self.update_recognizer()
        self.assign_algorithms()

    def start_timer(self):  # start the timeer for execution.
        self.capture = cv2.VideoCapture(self.camera_id)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.timer = QtCore.QTimer()
        path = 'ImagesAttendance'
        if not os.path.exists(path):
            os.mkdir(path)
        # known face encoding and known face name list
        images = []
        self.class_names = []
        self.encode_list = []
        self.TimeList1 = []
        self.TimeList2 = []
        attendance_list = os.listdir(path)
        if self.generate_dataset_btn.isChecked():
            self.timer.timeout.connect(self.save_dataset)
        elif self.recognize_face_btn.isChecked():
            self.timer.timeout.connect(self.update_image)
        self.timer.start(5)

    def stop_timer(self):  # stop timer or come out of the loop.
        self.timer.stop()
        self.ret = False
        self.capture.release()

    def update_image(self):  # update canvas every time according to time set in the timer.
        if self.recognize_face_btn.isChecked():
            self.ret, self.image = self.capture.read()
            self.image = cv2.flip(self.image, 1)
            faces = self.get_faces()
            self.draw_rectangle(faces)
        if self.video_recording_btn.isChecked():
            self.recording()
        self.display()

    def attendance(self, roi_gray):
        faces = self.get_faces()
        for (x, y, w, h) in faces:
            roi_gray_original = self.get_gray_image()[y:y + h, x:x + w]
            roi_gray = self.resize_image(roi_gray_original, 92, 112)
            roi_color = self.image[y:y + h, x:x + w]
            predicted, confidence = self.face_recognizer.predict(roi_gray)
            name = self.get_all_key_name_pairs().get(str(predicted))  # Save image captured using the save button.
            if self.checkin_btn.isChecked():
                self.checkin_btn.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                    if (name != 'Unknown'):

                        buttonReply = QMessageBox.question(self, 'Welcome', 'Are you Check In?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n {name},{date_time_string},Checked In')
                            self.checkin_btn.setChecked(False)
                            self.name_label.setText(str(name))
                            self.id_label.setText('Check In')

                            self.Time1 = datetime.datetime.now()
                            # print(self.Time1)
                            self.checkin_btn.setEnabled(True)
                        else:
                            print('Not clicked.')
                            self.checkin_btn.setEnabled(True)
            elif self.checkout_btn.isChecked():

                self.checkout_btn.setEnabled(False)
                with open('Attendance.csv', 'a') as f:
                    if (name != 'Unknown'):
                        buttonReply = QMessageBox.question(self, 'Good Bye ', 'Are you Clocking Out?',
                                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n{name},{date_time_string},Clock Out')
                            self.checkout_btn.setChecked(False)

                            self.name_label.setText(str(name))
                            self.id_label.setText('Checkin Out')
                            self.Time2 = datetime.datetime.now()
                            # print(self.Time2)

                            self.ElapseList(name)
                            self.TimeList2.append(datetime.datetime.now())
                            CheckInTime = self.Time1
                            CheckOutTime = self.Time2
                            self.ElapseHours = (CheckOutTime - CheckInTime)
                            self.min_label.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60) % 60) + 'm')
                            self.hour_label.setText(
                                "{:.0f}".format(abs(self.ElapseHours.total_seconds() / 60 ** 2)) + 'h')
                            self.checkout_btn.setEnabled(True)
                        else:
                            print('Not clicked.')
                            self.checkout_btn.setEnabled(True)

    def ElapseList(self, name):
        with open('Attendance.csv', "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 2

            Time1 = datetime.datetime.now()
            Time2 = datetime.datetime.now()
            for row in csv_reader:
                for field in row:
                    if field in row:
                        if field == 'Clock In':
                            if row[0] == name:
                                # print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time1 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList1.append(Time1)
                        if field == 'Clock Out':
                            if row[0] == name:
                                # print(f'\t ROW 0 {row[0]}  ROW 1 {row[1]} ROW2 {row[2]}.')
                                Time2 = (datetime.datetime.strptime(row[1], '%y/%m/%d %H:%M:%S'))
                                self.TimeList2.append(Time2)
                                # print(Time2)

    def save_dataset(self):  # Save images of new dataset generated using generate dataset button.
        location = os.path.join(self.current_path, str(self.dataset_per_subject) + ".jpg")

        if self.dataset_per_subject < 1:
            QMessageBox().about(self, "Dataset Generated",
                                "Your response is recorded now you can train the Model \n or Generate New Dataset.")
            self.generate_dataset_btn.setText("Generate Dataset")
            self.generate_dataset_btn.setChecked(False)
            self.stop_timer()
            self.dataset_per_subject = 50  # again setting max datasets

        if self.generate_dataset_btn.isChecked():
            self.ret, self.image = self.capture.read()
            self.image = cv2.flip(self.image, 1)
            faces = self.get_faces()
            self.draw_rectangle(faces)
            if len(faces) is not 1:
                self.draw_text("Only One Person at a time")
            else:
                for (x, y, w, h) in faces:
                    cv2.imwrite(location, self.resize_image(self.get_gray_image()[y:y + h, x:x + w], 92, 112))
                    self.draw_text("/".join(location.split("/")[-3:]), 20, 20 + self.dataset_per_subject)
                    self.dataset_per_subject -= 1
                    self.progress_bar_generate.setValue(100 - self.dataset_per_subject * 2 % 100)
        if self.video_recording_btn.isChecked():
            self.recording()

        self.display()

    def display(self):  # Display in the canvas, video feed.
        pixImage = self.pix_image(self.image)
        self.video_feed.setPixmap(QtGui.QPixmap.fromImage(pixImage))
        self.video_feed.setScaledContents(True)

    def pix_image(self, image):  # Converting image from OpenCv to PyQT compatible image.
        qformat = QtGui.QImage.Format_RGB888  # only RGB Image
        if len(image.shape) >= 3:
            r, c, ch = image.shape
        else:
            r, c = image.shape
            qformat = QtGui.QImage.Format_Indexed8
        pixImage = QtGui.QImage(image, c, r, image.strides[0], qformat)
        return pixImage.rgbSwapped()

    def generate(self):  # Envoke user dialog and enter name and key.
        if self.generate_dataset_btn.isChecked():
            try:
                user = USER()
                user.exec_()
                name, key = user.get_name_key()
                self.current_path = os.path.join(os.getcwd(), "datasets", str(key) + "-" + name)
                os.makedirs(self.current_path, exist_ok=True)
                self.start_timer()
                self.generate_dataset_btn.setText("Generating")
            except:
                msg = QMessageBox()
                msg.about(self, "User Information", '''Provide Information Please! \n name[string]\n key[integer]''')
                self.generate_dataset_btn.setChecked(False)

    def algorithm_radio_changed(
            self):  # When radio button change, either model is training or recognizing in respective algorithm.
        self.assign_algorithms()  # 1. update current radio button
        self.update_recognizer()  # 2. update face Recognizer
        self.read_model()  # 3. read trained data of recognizer set in step 2
        if self.train_model_btn.isChecked():
            self.train()

    def update_recognizer(self):  # whenever algoritm radio buttons changes this function need to be invoked.
        if self.eigen_algo_radio.isChecked():
            self.face_recognizer = cv2.face.EigenFaceRecognizer_create()
        elif self.fisher_algo_radio.isChecked():
            self.face_recognizer = cv2.face.FisherFaceRecognizer_create()
        else:
            self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()

    def assign_algorithms(self):  # Assigning anyone of algorithm to current woring algorithm.
        if self.eigen_algo_radio.isChecked():
            self.algorithm = "EIGEN"
        elif self.fisher_algo_radio.isChecked():
            self.algorithm = "FISHER"
        else:
            self.algorithm = "LBPH"

    def read_model(self):  # Reading trained model.
        if self.recognize_face_btn.isChecked():
            try:  # Need to to invoked when algoritm radio button change
                self.face_recognizer.read("training/" + self.algorithm.lower() + "_trained_model.yml")
            except Exception as e:
                self.print_custom_error("Unable to read Trained Model due to")
                print(e)

    def save_model(self):  # Save anyone model.
        try:
            self.face_recognizer.save("training/" + self.algorithm.lower() + "_trained_model.yml")
            msg = self.algorithm + " model trained, stop training or train another model"
            self.trained_model += 1
            self.progress_bar_train.setValue(self.trained_model)
            QMessageBox().about(self, "Training Completed", msg)
        except Exception as e:
            self.print_custom_error("Unable to save Trained Model due to")
            print(e)

    def train(self):  # When train button is clicked.
        if self.train_model_btn.isChecked():
            button = self.algo_radio_group.checkedButton()
            button.setEnabled(False)
            self.train_model_btn.setText("Stop Training")
            os.makedirs("training", exist_ok=True)
            labels, faces = self.get_labels_and_faces()
            try:
                msg = self.algorithm + " model training started"
                QMessageBox().about(self, "Training Started", msg)

                self.face_recognizer.train(faces, np.array(labels))
                self.save_model()
            except Exception as e:
                self.print_custom_error("Unable To Train the Model Due to: ")
                print(e)
        else:
            self.eigen_algo_radio.setEnabled(True)
            self.fisher_algo_radio.setEnabled(True)
            self.lbph_algo_radio.setEnabled(True)
            self.train_model_btn.setChecked(False)
            self.train_model_btn.setText("Train Model")

    def recognize(self):  # When recognized button is called.
        if self.recognize_face_btn.isChecked():
            self.start_timer()
            self.recognize_face_btn.setText("Stop Recognition")
            self.read_model()
        else:
            self.recognize_face_btn.setText("Recognize Face")
            self.stop_timer()

    def get_all_key_name_pairs(self):  # Get all (key, name) pair of datasets present in datasets.
        return dict(
            [subfolder.split('-') for _, folders, _ in os.walk(os.path.join(os.getcwd(), "datasets")) for subfolder in
             folders], )

    def absolute_path_generator(self):  # Generate all path in dataset folder.
        separator = "-"
        for folder, folders, _ in os.walk(os.path.join(os.getcwd(), "datasets")):
            for subfolder in folders:
                subject_path = os.path.join(folder, subfolder)
                key, _ = subfolder.split(separator)
                for image in os.listdir(subject_path):
                    absolute_path = os.path.join(subject_path, image)
                    yield absolute_path, key

    def get_labels_and_faces(self):  # Get label and faces.
        labels, faces = [], []
        for path, key in self.absolute_path_generator():
            faces.append(cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY))
            labels.append(int(key))
        return labels, faces

    def get_gray_image(self):  # Convert BGR image to GRAY image.
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def get_faces(self):  # Get all faces in a image.
        # variables
        scale_factor = 1.1
        min_neighbors = 8
        min_size = (100, 100)

        faces = self.face_classifier.detectMultiScale(
            self.get_gray_image(),
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size)

        return faces

    def get_smiles(self, roi_gray):  # Get all smiles in a image.
        scale_factor = 1.7
        min_neighbors = 22
        min_size = (25, 25)
        # window_size = (200, 200)

        smiles = self.smile_classifier.detectMultiScale(
            roi_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size
        )

        return smiles

    def get_eyes(self, roi_gray):  # Get all eyes in a image.
        scale_factor = 1.1
        min_neighbors = 6
        min_size = (30, 30)

        eyes = self.eye_classifier.detectMultiScale(
            roi_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            # minSize = min_size
        )

        return eyes

    def draw_rectangle(self, faces):  # Draw rectangle either in face, eyes or smile.
        for (x, y, w, h) in faces:
            roi_gray_original = self.get_gray_image()[y:y + h, x:x + w]
            roi_gray = self.resize_image(roi_gray_original, 92, 112)
            roi_color = self.image[y:y + h, x:x + w]
            if self.recognize_face_btn.isChecked():
                try:
                    predicted, confidence = self.face_recognizer.predict(roi_gray)
                    name = self.get_all_key_name_pairs().get(str(predicted))
                    self.draw_text("Recognizing using: " + self.algorithm, 70, 50)
                    if self.lbph_algo_radio.isChecked():
                        if confidence > 105:
                            msg = "Unknown"
                        else:
                            confidence = "{:.2f}".format(100 - confidence)
                            msg = name
                        self.progress_bar_recognize.setValue(float(confidence))
                    else:
                        msg = name
                        self.progress_bar_recognize.setValue(int(confidence % 100))
                        confidence = "{:.2f}".format(confidence)

                    self.draw_text(msg, x - 5, y - 5)
                except Exception as e:
                    self.print_custom_error("Unable to Pridict due to")
                    print(e)

            if self.eye_rect_radio.isChecked():  # If eye radio button is checked.
                eyes = self.get_eyes(roi_gray_original)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            elif self.smile_rect_radio.isChecked():  # If smile radio button is checked.
                smiles = self.get_smiles(roi_gray_original)
                for (sx, sy, sw, sh) in smiles:
                    cv2.rectangle(roi_color, (sx, sy), (sx + sw, sy + sh), (0, 255, 0), 2)
            else:  # If face radio button is checked.
                cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    def time(self):  # Get current time.
        return datetime.now().strftime("%d-%b-%Y:%I-%M-%S")

    def draw_text(self, text, x=20, y=20, font_size=2,
                  color=(0, 255, 0)):  # Draw text in current image in particular color.
        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.6, color, font_size)

    def resize_image(self, image, width=280, height=280):  # Resize image before storing.
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)

    def print_custom_error(self, msg):  # Print custom error message/
        print("=" * 100)
        print(msg)
        print("=" * 100)

    def recording(self):  # Record Video when either recognizing or generating.
        if self.ret:
            self.video_output.write(self.image)

    def save_video(self):  # Saving video.
        if self.video_recording_btn.isChecked() and self.ret:
            self.video_recording_btn.setText("Stop")
            try:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                output_file_name = self.time() + '.avi'
                path = os.path.join(os.getcwd(), "recordings")
                os.makedirs(path, exist_ok=True)
                self.video_output = cv2.VideoWriter(os.path.join(path, output_file_name), fourcc, 20.0, (640, 480))
            except Exception as e:
                self.print_custom_error("Unable to Record Video Due to")
                print(e)
        else:
            self.video_recording_btn.setText("Record")
            self.video_recording_btn.setChecked(False)
            if self.ret:
                QMessageBox().about(self, "Recording Complete",
                                    "Video clip successfully recorded into current recording folder")
            else:
                QMessageBox().about(self, "Information", '''Start either datasets generation or recognition First!  ''')

    # Main Menu

    def about_info(self):  # Menu Information of info button of application.
        msg_box = QMessageBox()
        msg_box.setText('''
            Face Recognition Attendance System
            Cảm ơn sự giúp đỡ của thầy đã giúp chúng em hoàn thành bài tập này
        ''')
        msg_box.setInformativeText('''
            Học Viện Kỹ Thuật Mật Mã
            Thị giác máy tính trên nền nhúng - C2N02
            Giáo viên hướng dẫn: Lê Đức Thuận
                                  Nhóm 05: 
            Hoàng Trung Kiên 
            Nguyễn Vân Khanh
            Mạc Văn Nam 
            ''')
        msg_box.setWindowTitle("About")
        msg_box.exec_()

    def help_info(self):  # Menu Information of help button of application.
        msg_box = QMessageBox()
        msg_box.setText('''
            Phần mềm này có khả năng tạo tập dữ liệu, tạo mô hình, nhận diện các khuôn mặt.
            Phần mềm cũng bao gồm các chức năng nhận diện khuôn mặt, đôi mắt, khóe miệng cười.
        ''')
        msg_box.setInformativeText('''
            Làm theo các bước sau để sử dụng phần mềm
            1. Tạo ít nhất hai bộ dữ liệu.
            2. Huấn luyện tất cả các mô hình xử lý ảnh bằng cách sử dụng 3 nút radio đã cho.
            3. Nhận diện khuôn mặt.

            ''')
        msg_box.setWindowTitle("Help")
        msg_box.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = AUFR()  # Running application loop.
    ui.show()
    sys.exit(app.exec_())  # Exit application.