# Python program for booking SRT ticket.


매진된 SRT 표의 예매를 도와주는 파이썬 프로그램입니다.  
원하는 표가 나올 때 까지 새로고침하여 예약을 시도합니다.

```python
## requirements
pip install -r requirements.txt
```

## Arguments
    dpt: SRT 출발역
    arr: SRT 도착역
    dt: 출발 날짜 YYYYMMDD 형태 ex) 20220115
    tm: 출발 시간 hh 형태, 반드시 짝수 ex) 06, 08, 14, ...
    num: 검색 결과 중 예약 가능 여부 확인할 기차의 수 (default : 2)
    reserve: 예약 대기가 가능할 경우 선택 여부 (default : False)

    station_list = ["수서", "동탄", "평택지제", "천안아산", "오송", "대전", "김천(구미)", "동대구",
    "신경주", "울산(통도사)", "부산", "공주", "익산", "정읍", "광주송정", "나주", "목포", "창원중앙"]



## 간단 사용법
    .env에 파일에 회원번호, 비밀번호, 휴대폰 번호를 입력합니다.
```python
    SRT_LOGIN_ID=123456789
    SRT_LOGIN_PASSWORD=000000
    SRT_PHONE_NUMBER=01012345678


```cmd
python quickstart.py --dpt 수서 --arr 창원중앙 --dt 20241027 --tm 06
```

**Optional**  
예약대기 사용 및 검색 결과 상위 3개의 예약 가능 여부 확인
```cmd
python quickstart.py --dpt 동탄 --arr 동대구 --dt 20220117 --tm 08 --num 3 --reserve True
```
