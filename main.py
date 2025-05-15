# -*- coding: utf-8 -*-
import os
import time
from random import randint
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, WebDriverException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from exceptions import InvalidStationNameError, InvalidDateError, InvalidDateFormatError, InvalidTimeFormatError
from validation import station_list

chromedriver_path = r'C:\workspace\chromedriver.exe'

import subprocess
import platform
import dotenv

dotenv.load_dotenv()

class SRT:
    def __init__(self, dpt_stn, arr_stn, dpt_dt, dpt_tm, adult_num, child_num, num_trains_to_check=2, want_reserve=False):
        """
        :param dpt_stn: SRT 출발역
        :param arr_stn: SRT 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param adult_num: 성인 인원 수
        :param child_num: 어린이 인원 수
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        """
        self.login_id = None
        self.login_psw = None

        self.dpt_stn = dpt_stn
        self.arr_stn = arr_stn
        self.dpt_dt = dpt_dt
        self.dpt_tm = dpt_tm
        self.adult_num = adult_num
        self.child_num = child_num

        self.num_trains_to_check = num_trains_to_check
        self.want_reserve = want_reserve
        self.driver = None

        self.is_booked = False  # 예약 완료 되었는지 확인용
        self.cnt_refresh = 0  # 새로고침 회수 기록

        self.check_input()

        self.phone_number = os.getenv('SRT_PHONE_NUMBER')  # Add this line to store the user's phone number

    def check_input(self):
        if self.dpt_stn not in station_list:
            raise InvalidStationNameError(f"출발역 오류. '{self.dpt_stn}' 은/는 목록에 없습니다.")
        if self.arr_stn not in station_list:
            raise InvalidStationNameError(f"도착역 오류. '{self.arr_stn}' 은/는 목록에 없습니다.")
        if not str(self.dpt_dt).isnumeric():
            raise InvalidDateFormatError("날짜는 숫자로만 이루어져야 합니다.")
        try:
            datetime.strptime(str(self.dpt_dt), '%Y%m%d')
        except ValueError:
            raise InvalidDateError("날짜가 잘못 되었습니다. YYYYMMDD 형식으로 입력해주세요.")

    def set_log_info(self, login_id, login_psw):
        self.login_id = login_id
        self.login_psw = login_psw

    def run_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
        options.add_argument("lang=ko_KR")
        
        # Use webdriver_manager to automatically download and manage ChromeDriver
        if platform.system() == "Darwin":  # macOS
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        else:
            # For other operating systems, you might want to keep the original implementation
            self.driver = webdriver.Chrome('C:\\workspace\\chromedriver.exe', options=options)

    def login(self):
        self.driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')
        self.driver.implicitly_wait(15)
        self.driver.find_element(By.ID, 'srchDvNm01').send_keys(str(self.login_id))
        self.driver.find_element(By.ID, 'hmpgPwdCphd01').send_keys(str(self.login_psw))
        self.driver.find_element(By.XPATH, '//*[@id="login-form"]/fieldset/div[1]/div[1]/div[2]/div/div[2]/input').click()
        self.driver.implicitly_wait(5)
        return self.driver

    def check_login(self):
        menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
        if "환영합니다" in menu_text:
            return True
        else:
            return False

    def go_search(self):
        # 기차 조회 페이지로 이동
        self.driver.get('https://etk.srail.kr/hpg/hra/01/selectScheduleList.do')
        self.driver.implicitly_wait(5)

        # 출발지 입력
        elm_dpt_stn = self.driver.find_element(By.ID, 'dptRsStnCdNm')
        elm_dpt_stn.clear()
        elm_dpt_stn.send_keys(self.dpt_stn)

        # 도착지 입력
        elm_arr_stn = self.driver.find_element(By.ID, 'arvRsStnCdNm')
        elm_arr_stn.clear()
        elm_arr_stn.send_keys(self.arr_stn)

        # 출발 날짜 입력
        elm_dpt_dt = self.driver.find_element(By.ID, "dptDt")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_dt)
        Select(self.driver.find_element(By.ID, "dptDt")).select_by_value(self.dpt_dt)

        # 출발 시간 입력
        elm_dpt_tm = self.driver.find_element(By.ID, "dptTm")
        self.driver.execute_script("arguments[0].setAttribute('style','display: True;')", elm_dpt_tm)
        Select(self.driver.find_element(By.ID, "dptTm")).select_by_visible_text(self.dpt_tm)

        # 인원 정보 입력
        select_adult = Select(self.driver.find_element(By.ID, "psgInfoPerPrnb1"))
        select_adult.select_by_value(str(int(self.adult_num)))

        select_child = Select(self.driver.find_element(By.ID, "psgInfoPerPrnb5"))
        select_child.select_by_value(str(int(self.child_num)))

        print("기차를 조회합니다")
        print(f"출발역:{self.dpt_stn} , 도착역:{self.arr_stn}\n날짜:{self.dpt_dt}, 시간: {self.dpt_tm}시 이후\n{self.num_trains_to_check}개의 기차 중 예약")
        print(f"예약 대기 사용: {self.want_reserve}")

        self.driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
        self.driver.implicitly_wait(5)
        time.sleep(1)

    def book_ticket(self, standard_seat, i):
        if "예약하기" in standard_seat:
            print("예약 가능 클릭")

            try:
                # Try to click the reservation button
                self.driver.find_element(By.CSS_SELECTOR,
                                         f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7) > a").click()
                
                # Wait for and handle any alert that might appear
                try:
                    WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                    alert = self.driver.switch_to.alert
                    print(f"Alert message: {alert.text}")
                    alert.accept()
                except TimeoutException:
                    print("No alert appeared.")

                # Check if the reservation was successful
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'isFalseGotoMain')))
                
                self.is_booked = True
                print("예약 성공")
                # Send SMS
                if self.phone_number:
                    message = f"SRT ticket booked successfully!\nFrom: {self.dpt_stn}\nTo: {self.arr_stn}\nDate: {self.dpt_dt}\nTime: {self.dpt_tm}"
                    self.send_sms(self.phone_number, message)
                return self.driver

            except UnexpectedAlertPresentException as e:
                print(f"Unexpected alert appeared: {e.alert_text}")
                self.driver.switch_to.alert.accept()
                self.driver.back()
                self.driver.implicitly_wait(5)
            except Exception as e:
                print(f"예약 실패: {str(e)}")
                self.driver.back()
                self.driver.implicitly_wait(5)

        return None

    def refresh_result(self):
        submit = self.driver.find_element(By.XPATH, "//input[@value='조회하기']")
        self.driver.execute_script("arguments[0].click();", submit)
        self.cnt_refresh += 1
        print(f"새로고침 {self.cnt_refresh}회")
        self.driver.implicitly_wait(10)
        time.sleep(0.5)

    def reserve_ticket(self, reservation, i):
        if "신청하기" in reservation:
            print("예약 대기 완료")
            self.driver.find_element(By.CSS_SELECTOR,
                                     f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").click()
            self.is_booked = True
            return self.is_booked

    def check_result(self):
        while True:
            for i in range(1, self.num_trains_to_check+1):
                try:
                    standard_seat = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7)").text
                    reservation = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8)").text
                except StaleElementReferenceException:
                    standard_seat = "매진"
                    reservation = "매진"

                if self.book_ticket(standard_seat, i):
                    return self.driver

                if self.want_reserve:
                    self.reserve_ticket(reservation, i)

            if self.is_booked:
                return self.driver

            else:
                time.sleep(randint(2, 4))
                self.refresh_result()

    def set_phone_number(self, phone_number):
        self.phone_number = phone_number

    def send_sms(self, phone_number, message):
        """
        Send an SMS using iMessage on macOS, or print a message on other platforms.
        
        :param phone_number: The recipient's phone number
        :param message: The message to send
        """
        if platform.system() == 'Darwin':  # Darwin is the system name for macOS
            apple_script = f'''
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{phone_number}" of targetService
                send "{message}" to targetBuddy
            end tell
            '''
            
            try:
                subprocess.run(['osascript', '-e', apple_script], check=True)
                print(f"SMS sent successfully to {phone_number}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to send SMS: {e}")
        else:
            print(f"SMS sending is only supported on macOS. Message content: {message}")

    def run(self, login_id, login_psw, phone_number):
        self.run_driver()
        self.set_log_info(login_id, login_psw)
        self.set_phone_number(phone_number)
        self.login()
        self.go_search()
        self.check_result()

#
# if __name__ == "__main__":
#     srt_id = os.environ.get('srt_id')
#     srt_psw = os.environ.get('srt_psw')
#
#     srt = SRT("동탄", "동대구", "20220917", "08")
#     srt.run(srt_id, srt_psw)
