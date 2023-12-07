from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta
from pytz import timezone
import json

service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 날짜 변경시 작동 - 날짜 변경, 디렉토리 생성 추가!
# 매일 한번 실행
def change_date():
    korea_tz = timezone('Asia/Seoul')
    korea_time = datetime.now(korea_tz)
    next_day = korea_time + timedelta(days=1)
    next_day_str = next_day.strftime('%Y%m%d')
    with open('D:\\news_trend\\news_crawling\\date.txt', 'w') as file:
        file.write(next_day_str)

# 날짜가 바뀌는 경우의 링크 수집 함수
# checkpoint 사용 X
def get_link_init(driver):
    with open('D:\\news_trend\\news_crawling\\date.txt', 'r') as file:
        date = file.read()

    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001&date=" + date + "&page="

    link_list = [] # 링크를 담을 리스트
    page_num = 0   # 값을 증가시켜 각 페이지의 기사 링크 수집
    
    # 날짜 변경 후 최대 페이지 확인 작업
    driver.get(url + str(1))
    container = driver.find_element(By.CLASS_NAME, "container")
    content = container.find_element(By.CLASS_NAME, "content")
    paging = container.find_element(By.CLASS_NAME, "paging")
    last_page = len(paging.find_elements(By.TAG_NAME, 'a'))

    # 페이지 이상을 검색해도 오류가 발생하지 않음!
    for page_num in range(last_page + 1):
        page_num += 1
        driver.get(url + str(page_num))
        container = driver.find_element(By.CLASS_NAME, "container")
        content = container.find_element(By.CLASS_NAME, "content")
        list_body = content.find_element(By.CLASS_NAME, "list_body.newsflash_body")
        ul = list_body.find_elements(By.TAG_NAME, "ul") # 링크는 2개의 ul 태그로 구성
        for i in ul:
            li = i.find_elements(By.TAG_NAME, "li")
            for j in li:
                tag_a = j.find_elements(By.TAG_NAME, 'a')
                href = tag_a[-1].get_attribute("href")
                link_list.append(href)
 
    # 바뀐 날짜에 대해 checkpoint 설정
    checkpoint = link_list[:3]
    with open('D:\\news_trend\\news_crawling\\checkpoint.txt', 'w') as file:
        for item in checkpoint:
            file.write(f"{item}\n")

    return link_list


def get_link_normal(driver):
    with open('D:\\news_trend\\news_crawling\\date.txt', 'r') as file:
        date = file.read()

    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001&date=" + date + "&page="

    # checkpoint를 사용하여 크롤링 중단
    with open('D:\\news_trend\\news_crawling\\checkpoint.txt', 'r') as file:
        checkpoint = [str(line.strip()) for line in file.readlines()]

    link_list = [] # 링크를 담을 리스트
    page_num = 0
    init = True
    while(init):
        page_num += 1
        driver.get(url + str(page_num))
        container = driver.find_element(By.CLASS_NAME, "container")
        content = container.find_element(By.CLASS_NAME, "content")
        list_body = content.find_element(By.CLASS_NAME, "list_body.newsflash_body")
        ul = list_body.find_elements(By.TAG_NAME, "ul") # 링크는 2개의 ul 태그로 구성
        for i in ul:
            li = i.find_elements(By.TAG_NAME, "li")
            for j in li:
                tag_a = j.find_elements(By.TAG_NAME, 'a')
                href = tag_a[-1].get_attribute("href")
                link_list.append(href)

            temp = link_list[-12:]
            count = sum(1 for elem in checkpoint if elem in temp) # checkpoint와 겹치는 링크의 개수
            
            # 링크 중복 발생
            if count >= 2:
                # 중복 링크 제거
                try:
                    idx = temp.index(checkpoint[1])
                    idx = temp.index(checkpoint[0])
                except:
                    pass

                link_list = link_list[:-12 + idx]

                init = False # while 탈출


    # 최초 3개의 링크를 checkpoint로 사용하기 위해 저장
    checkpoint = link_list[:3]
    with open('D:\\news_trend\\news_crawling\\checkpoint.txt', 'w') as file:
        for item in checkpoint:
            file.write(f"{item}\n")

    return link_list      

# 디렉토리를 생성하고 json을 저장하도록 수정!
def main(driver, link_list):
    for link in link_list:
        driver.get(link)
        time.sleep(1)
        total = driver.find_element(By.CLASS_NAME, "end_container")
        title_area = total.find_element(By.CLASS_NAME, "newsct_wrapper._GRID_TEMPLATE_COLUMN._STICKY_CONTENT")
        title_info = title_area.find_element(By.CLASS_NAME, "media_end_head_title")
        title = title_info.text
        pub_info = title_area.find_element(By.CLASS_NAME, "media_end_head_top")
        pub = pub_info.find_element(By.CSS_SELECTOR, "img").get_attribute("title")
        article_info = title_area.find_element(By.ID, "dic_area")
        article = article_info.text
        input_area = title_area.find_element(By.CLASS_NAME, "media_end_head_info_datestamp")
        input_area2 = input_area.find_element(By.CLASS_NAME, "media_end_head_info_datestamp_bunch")
        input_time = input_area2.find_element(By.CSS_SELECTOR, "span").get_attribute("data-date-time")
        # input_time = datetime.strftime(input_time, '%Y-%m-%d %H:%M:%S')
        try:
            rep_info = title_area.find_element(By.CLASS_NAME, "media_end_head_journalist")
            reporter = rep_info.text
        except:
            reporter = None

        # 특정 언론사의 기사만 저장(데이터 양에 대한 비용과 Lambda 비용 문제)
        if pub in ["SBS", "KBS", "MBC", "국민일보", "세계일보"]:
            data = {
                "title": title,
                "link": link,
                "article": article,
                "input_time": input_time,
                "pub": pub,
                "reporter": reporter  # 값이 없을 수 있는 필드
            }

            # JSON으로 변환
            json_data = json.dumps(data, indent=2)

            # 파일에 쓰기
            file_path = 'D:\\news_trend\\news_crawling\\data.json'
            with open(file_path, 'w') as json_file:
                json_file.write(json_data)

link_list = get_link_init(driver)
main(driver, link_list)