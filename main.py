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
    def __init__(self, dpt_stn, arr_stn, dpt_dt, dpt_tm, adult_num, child_num, num_trains_to_check=4, want_reserve=False, want_train='none'):
        """
        :param dpt_stn: SRT 출발역
        :param arr_stn: SRT 도착역
        :param dpt_dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
        :param dpt_tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
        :param adult_num: 성인 인원 수
        :param child_num: 어린이 인원 수
        :param num_trains_to_check: 검색 결과 중 예약 가능 여부 확인할 기차의 수 ex) 2일 경우 상위 2개 확인
        :param want_reserve: 예약 대기가 가능할 경우 선택 여부
        :param want_train: 예약 대기 기차 선택 여부
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
        self.want_train = want_train
        
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
        max_login_attempts = 3
        attempt = 0
        
        while attempt < max_login_attempts:
            try:
                print(f"Attempting login ({attempt+1}/{max_login_attempts})...")
                
                # Navigate to login page
                self.driver.get('https://etk.srail.co.kr/cmc/01/selectLoginForm.do')
                
                # Wait for login form to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, 'srchDvNm01'))
                )
                
                # Input credentials
                id_field = self.driver.find_element(By.ID, 'srchDvNm01')
                id_field.clear()
                id_field.send_keys(str(self.login_id))
                
                pwd_field = self.driver.find_element(By.ID, 'hmpgPwdCphd01')
                pwd_field.clear()
                pwd_field.send_keys(str(self.login_psw))
                
                # Click login button using class name
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'loginSubmit'))
                )
                login_button.click()
                
                # Wait a moment for login to process
                time.sleep(2)
                
                # Check if login was successful
                if self.check_login():
                    print("Login successful")
                    return self.driver
                else:
                    # Try to capture any error messages on the page
                    try:
                        error_msg = self.driver.find_element(By.CSS_SELECTOR, ".alert, .error, #login-form .txt_warn").text
                        print(f"Login error message: {error_msg}")
                    except:
                        print("Login failed, incorrect credentials or website structure changed")

                    print(f"Current URL: {self.driver.current_url}")
                    attempt += 1
                    
            except (TimeoutException, WebDriverException, StaleElementReferenceException) as e:
                print(f"Login error: {str(e)}")
                attempt += 1
                
                if attempt < max_login_attempts:
                    print(f"Retrying login... Attempt {attempt+1}/{max_login_attempts}")
                    time.sleep(3)  # Wait before retrying
                    
        print("Failed to login after multiple attempts")
        raise Exception("Login failed after multiple attempts")

    def check_login(self):
        try:
            menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
            if "환영합니다" in menu_text:
                return True
            else:
                # Check for alternative login indicators
                try:
                    # Check if we're on the main page after login
                    if "selectScheduleList" in self.driver.current_url or "main" in self.driver.current_url:
                        return True
                except:
                    pass
                return False
        except Exception as e:
            print(f"Error checking login status: {str(e)}")
            return False

    def go_search(self):
        max_search_attempts = 3
        attempt = 0
        
        while attempt < max_search_attempts:
            try:
                # 기차 조회 페이지로 이동
                self.driver.get('https://etk.srail.kr/hpg/hra/01/selectScheduleList.do')
                self.driver.implicitly_wait(5)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'dptRsStnCdNm'))
                )

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
                if self.want_train != 'none':
                    print(f"예약 대기 기차: {self.want_train}")
                else:
                    print("예약 대기 기차: 없음")
                if self.want_reserve:
                    print("예약 대기 사용: 예")
                else:
                    print("예약 대기 사용: 아니오")
                print(f"성인 인원 수: {self.adult_num}, 어린이 인원 수: {self.child_num}")

                # Click the search button and wait for results
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value='조회하기']"))
                )
                self.driver.execute_script("arguments[0].click();", search_button)
                
                # Wait for search results to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#result-form fieldset table tbody tr"))
                )
                
                self.driver.implicitly_wait(5)
                time.sleep(1)
                
                # If we reach this point, the search was successful
                return
                
            except (TimeoutException, WebDriverException, StaleElementReferenceException) as e:
                attempt += 1
                print(f"Error during search attempt {attempt}: {str(e)}")
                
                if attempt >= max_search_attempts:
                    print("Maximum search attempts reached. Restarting browser...")
                    self.restart_browser()
                    return
                else:
                    print(f"Retrying search... Attempt {attempt+1} of {max_search_attempts}")
                    time.sleep(3)  # Wait before retrying

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
        try:
            # Find the search button with a more robust wait
            submit = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='조회하기']"))
            )
            
            # Click using JavaScript for more reliable clicks
            self.driver.execute_script("arguments[0].click();", submit)
            
            # Wait for results to update
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#result-form fieldset table tbody tr"))
                )
            except TimeoutException:
                print("Search results not appearing, may need to retry...")
                
            self.cnt_refresh += 1
            print(f"새로고침 {self.cnt_refresh}회")
            self.driver.implicitly_wait(10)
            time.sleep(0.5)
            
            return True
            
        except (TimeoutException, WebDriverException, StaleElementReferenceException) as e:
            print(f"Error during refresh: {str(e)}")
            # If refresh fails, try to recover
            try:
                # Check if we're still on the search page
                if "selectScheduleList" not in self.driver.current_url:
                    print("Not on search page, navigating back...")
                    self.go_search()
                return False
            except Exception as inner_e:
                print(f"Error recovering from refresh failure: {str(inner_e)}")
                return False

    def reserve_ticket(self, reservation, i):
        if "신청하기" in reservation:
            print("예약 대기 완료")
            self.driver.find_element(By.CSS_SELECTOR,
                                     f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8) > a").click()
            self.is_booked = True
            return self.is_booked

    def check_result(self):
        max_retries = 5
        retry_count = 0

        while True:
            try:
                for i in range(1, self.num_trains_to_check+1):
                    try:
                        train_num = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(3)").text.strip()
                        premium_seat = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(6)").text.strip()
                        standard_seat = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(7)").text.strip()
                        reservation = self.driver.find_element(By.CSS_SELECTOR, f"#result-form > fieldset > div.tbl_wrap.th_thead > table > tbody > tr:nth-child({i}) > td:nth-child(8)").text.strip()
                    except (StaleElementReferenceException, Exception):
                        train_num = "알 수 없음"
                        premium_seat = "매진"
                        standard_seat = "매진"
                        reservation = "매진"

                    print(f"기차번호: {train_num} / 프리미엄석: {premium_seat} / 일반석: {standard_seat} / 예약 대기: {reservation}")
                    # want_train이 있고 예약 대기 기차와 같을 경우 예약 진행
                    if self.want_train and self.want_train != 'none' and self.want_train.strip() == train_num:
                        print(f"지정 기차 발견: {train_num}")
                        if "매진" not in premium_seat:
                            self.book_ticket(premium_seat, i)
                            return self.driver
                        elif "매진" not in standard_seat:
                            self.book_ticket(standard_seat, i)
                            return self.driver
                        elif "매진" not in reservation and self.want_reserve:
                            self.reserve_ticket(reservation, i)
                            return self.driver
                    elif not self.want_train or self.want_train == 'none':
                        if "매진" not in premium_seat:
                            print("예약 클릭")
                            self.book_ticket(premium_seat, i)
                            return self.driver
                        elif "매진" not in standard_seat:
                            print("예약 클릭")
                            self.book_ticket(standard_seat, i)
                            return self.driver
                        elif "매진" not in reservation and self.want_reserve:
                            print("예약 클릭")
                            self.reserve_ticket(reservation, i)
                            return self.driver

                    if self.is_booked:
                        return self.driver

                time.sleep(randint(2, 4))
                self.refresh_result()
                    
            except (WebDriverException, TimeoutException, ElementClickInterceptedException) as e:
                retry_count += 1
                print(f"Error occurred: {str(e)}")
                print(f"Retry attempt {retry_count} of {max_retries}")
                
                if retry_count >= max_retries:
                    print("Maximum retries reached. Restarting the driver...")
                    self.restart_browser()
                    retry_count = 0
                else:
                    time.sleep(5)  # Wait before retrying
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
            
    def restart_browser(self):
        """
        Restart the browser session if it crashes or becomes unresponsive
        """
        print("Restarting browser session...")
        try:
            # Close the current driver if it exists
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"Error closing browser: {str(e)}")
            
            # Wait a moment before starting a new session
            time.sleep(3)
            
            # Start a new driver session
            self.run_driver()
            
            # Log back in and return to the search page
            self.login()
            
            # Return to the search page
            self.go_search()
            
            print("Browser successfully restarted")
            
        except Exception as e:
            print(f"Failed to restart browser: {str(e)}")
            # If we can't restart, wait and try again
            time.sleep(10)
            self.driver = None  # Set driver to None to ensure a fresh start

    def run(self, login_id, login_psw, phone_number):
        max_run_attempts = 3
        attempt = 0
        
        while attempt < max_run_attempts and not self.is_booked:
            try:
                print(f"Starting booking attempt {attempt+1} of {max_run_attempts}")
                
                if self.driver is None:
                    self.run_driver()
                    
                self.set_log_info(login_id, login_psw)
                self.set_phone_number(phone_number)
                
                # Check if we're already logged in, if not, log in
                if not self.check_login_status():
                    self.login()
                    
                self.go_search()
                self.check_result()
                
                # If we reach here without booking, increment attempt counter
                if not self.is_booked:
                    attempt += 1
                    print(f"Booking attempt {attempt} unsuccessful")
                    
            except (WebDriverException, TimeoutException) as e:
                print(f"Critical error in run process: {str(e)}")
                attempt += 1
                
                if attempt < max_run_attempts:
                    print(f"Restarting the entire process. Attempt {attempt+1} of {max_run_attempts}")
                    try:
                        if self.driver:
                            self.driver.quit()
                    except Exception:
                        pass
                    
                    self.driver = None
                    time.sleep(10)  # Wait before restarting
            
        if self.is_booked:
            print("Ticket successfully booked!")
        else:
            print(f"Failed to book ticket after {max_run_attempts} attempts")
            
        return self.driver
        
    def check_login_status(self):
        """Check if we're logged in without attempting a new login"""
        try:
            menu_text = self.driver.find_element(By.CSS_SELECTOR, "#wrap > div.header.header-e > div.global.clear > div").text
            return "환영합니다" in menu_text
        except Exception:
            return False

#
# if __name__ == "__main__":
#     srt_id = os.environ.get('srt_id')
#     srt_psw = os.environ.get('srt_psw')
#
#     srt = SRT("동탄", "동대구", "20220917", "08")
#     srt.run(srt_id, srt_psw)
