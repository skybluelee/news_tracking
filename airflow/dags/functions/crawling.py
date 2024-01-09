from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import time
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import logging
import numpy as np


# 날짜가 바뀌는 경우의 링크 수집 함수
# checkpoint 사용 X
def get_link_init(driver, date):
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001&date=" + date + "&page="

    link_list = [] # 링크를 담을 리스트
    page_num = 0   # 값을 증가시켜 각 페이지의 기사 링크 수집
    use_link_list = []
    
    # 날짜 변경 후 최대 페이지 확인 작업
    # driver.get(url + str(1))
    # container = driver.find_element(By.CLASS_NAME, "container")
    # content = container.find_element(By.CLASS_NAME, "content")
    # paging = container.find_element(By.CLASS_NAME, "paging")
    # last_page = len(paging.find_elements(By.TAG_NAME, 'a'))

    # 페이지 이상을 검색해도 오류가 발생하지 않음!
    # for page_num in range(last_page + 1):
    print("link init")
    print("link search start")
    for page_num in range(100):
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
                pub = j.find_element(By.CLASS_NAME, "writing").text
                link_list.append(href)
                if pub in ["SBS", "KBS", "MBC", "국민일보", "세계일보", "뉴시스", "YTN", "MBN", "JTBC"]:
                    use_link_list.append(href)
                    print("pub: ", pub, 'href: ', href)
 
    print("link search end")
    # 바뀐 날짜에 대해 checkpoint 설정
    checkpoint = link_list[:3]
    with open('/opt/airflow/dags/checkpoint.txt', 'w') as file:
        for item in checkpoint:
            file.write(f"{item}\n")
    
    return use_link_list

def get_link_normal(driver, date):
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=001&date=" + date + "&page="

    # checkpoint를 사용하여 크롤링 중단
    with open('/opt/airflow/dags/checkpoint.txt', 'r') as file:
        checkpoint = [str(line.strip()) for line in file.readlines()]

    link_list = [] # 링크를 담을 리스트
    use_link_list = []
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
                pub = j.find_element(By.CLASS_NAME, "writing").text
                if pub in ["SBS", "KBS", "MBC", "국민일보", "세계일보", "뉴시스", "YTN", "MBN", "JTBC"]:
                    use_link_list.append(href)
                    print("pub: ", pub, 'href: ', href)

            temp = link_list[-15:]
            count = sum(1 for elem in checkpoint if elem in temp) # checkpoint와 겹치는 링크의 개수
            
            # 링크 중복 발생
            if count >= 2:
                init = False # while 탈출

    # 최초 3개의 링크를 checkpoint로 사용하기 위해 저장
    checkpoint = link_list[:3]
    with open('/opt/airflow/dags/checkpoint.txt', 'w') as file:
        for item in checkpoint:
            file.write(f"{item}\n")
    
    return use_link_list    

def get_article(driver, link_list):
    df = pd.DataFrame(columns=["title", "link", "article", "input_time", "pub", "reporter"])
    print("len(link_list):", len(link_list))

    for link in link_list:
        try:
            driver.get(link)
            time.sleep(0.3)
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
        except:
            pass

        # # 특정 언론사의 기사만 저장(데이터 양에 대한 비용과 Lambda 비용 문제)
        # if pub in ["SBS", "KBS", "MBC", "국민일보", "세계일보"]:
        #     if len(df) // 10 == 0:
        #         print(pub)
        #         print(len(df))
        data = {
            "title": title,
            "link": link,
            "article": article,
            "input_time": input_time,
            "pub": pub,
            "reporter": reporter  # 값이 없을 수 있는 필드
        }    
        print(data["pub"], ": ", data["title"])
        df_add = pd.DataFrame([data])
        df = pd.concat([df, df_add], ignore_index=True)
    df_no_duplicates = df.drop_duplicates()
    
    path = "/opt/airflow/dags/news_1_raw_data.csv"
    df_no_duplicates.to_csv(path, index=False)

def konlpy(df):
    logging.info("start") 
    articles = df['article'].tolist()

    print(articles[0])
    # 엔터를 삭제하는 함수
    def remove_newline(text):
        # 정규표현식을 사용하여 엔터(\n) 삭제
        cleaned_text = re.sub(r'\n+', ' ', text)
        return cleaned_text

    # 토큰화와 어간 추출을 포함한 전처리 함수
    def preprocess(text):
        tokens = tokenizer.pos(text)  # 형태소 분석
        stems = [token[0] for token in tokens if token[1] in ['Noun', 'Verb', 'Adjective']]  # 명사, 동사, 형용사 추출
        return ' '.join(stems)

    # 불용어 처리 함수
    def remove_stopwords(text, stop_words):
        tokens = text.split()
        filtered_tokens = [token for token in tokens if token not in stop_words]
        return ' '.join(filtered_tokens)

    logging.info("okt") 

    # KoNLPy의 형태소 분석기 선택 (Okt 사용)
    tokenizer = Okt()

    # 토큰화 함수
    def tokenize(text):
        tokens = tokenizer.pos(text)
        stems = [token[0] for token in tokens if token[1] in ['Noun', 'Verb', 'Adjective']]
        return stems
    logging.info("enter") 

    # 엔터 삭제        
    for idx in range(len(articles)):
        if type(articles[idx]) == float:
            articles[idx] = "내용 없음"
        elif type(articles[idx]) == str:        
            articles[idx] = remove_newline(articles[idx])
    logging.info("tokenize") 

    # 토큰화와 어간 추출
    lemmatized_articles = [preprocess(article) for article in articles]
    logging.info("stop_words") 

    # 불용어 제거
    stop_words = ['아', '가', '16일']
    processed_articles = [remove_stopwords(article, stop_words) for article in lemmatized_articles]
    
    # TF-IDF 벡터화
    # tokenizer=tokenize로 할지 빈칸(기본값)으로 할지는 추후 결정
    logging.info("vectorizer") 
    vectorizer = TfidfVectorizer(tokenizer=tokenize)
    tfidf_matrix = vectorizer.fit_transform(processed_articles)

    logging.info("vector nomarlize") 
    # 단어 수에 따른 문장 길이 정규화
    normalized_tfidf_matrix = tfidf_matrix / tfidf_matrix.sum(axis=1)
    
    # 벡터 간 코사인 유사도 계산
    logging.info("cos") 
    cosine_similarities = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # 0에서 1로 정규화하여 백분율로 변환
    logging.info("cos %") 
    normalized_cosine_similarities = (cosine_similarities + 1) / 2 * 100

    # 결과 출력
    print("Original Articles:")
    for i, article in enumerate(articles):
        print(f"Article {i + 1}: {article}")

    print("\nLemmatized Articles:")
    for i, lemmatized_article in enumerate(lemmatized_articles):
        print(f"Lemmatized Article {i + 1}: {lemmatized_article}")

    print("\nNormalized Cosine Similarities (%):")
    print(normalized_cosine_similarities)    

    np.save('/opt/airflow/dags/cos_similarity.npy', normalized_cosine_similarities)

def get_representative_value():
    def find_clusters(matrix, threshold=70):
        clusters = []
        visited = set()

        for i in range(matrix.shape[0]):
            if i not in visited:
                cluster = [i]
                visited.add(i)

                stack = [i]

                while stack:
                    current = stack.pop()

                    neighbors = np.where(matrix[current] >= threshold)[0]

                    for neighbor in neighbors:
                        if neighbor not in visited:
                            stack.append(neighbor)
                            visited.add(neighbor)
                            cluster.append(neighbor)

                clusters.append(cluster)

        return clusters

    def merge_overlapping_clusters(clusters):
        merged_clusters = []

        for cluster in clusters:
            merged = False

            for existing_cluster in merged_clusters:
                if any(value in existing_cluster for value in cluster):
                    existing_cluster.update(cluster)
                    merged = True
                    break

            if not merged:
                merged_clusters.append(set(cluster))

        return [list(cluster) for cluster in merged_clusters]

    def get_representative_value(matrix, merged_clusters, threshold=70, determinant="median"):
        print(matrix)
        print(merged_clusters)
        # 대표값 측정에 사용하는 변수
        cluster_num = 0
        determinant_value = 0
        
        # 매핑용 딕셔너리
        representative_dict = {}
        
        for cluster in merged_clusters:
            for value in cluster: # value=4
                above_threshold_values = matrix[value][(matrix[value] >= threshold) & (matrix[value] <= 101)]
                # 각 클러스터에 대한 대표값 설정
                
                # 유사도가 높은 기사가 다수 존재하는 경우를 우선시
                if len(above_threshold_values) > cluster_num:     
                    cluster_num = len(above_threshold_values)
                    # 대표값을 중간값을 사용하여 구하는 경우
                    if determinant == "median":
                        determinant_value = np.median(above_threshold_values)
                        representative_value = value
                        # 대표값을 평균을 사용하여 구하는 경우
                    elif determinant == "mean":
                        determinant_value = np.mean(above_threshold_values)
                        representative_value = value   
                
                # 기존 대표값의 유사도가 높은 기사의 개수가 일치하는 경우
                elif len(above_threshold_values) == cluster_num:
                    cluster_num = len(above_threshold_values)
                    # 대표값을 중간값을 사용하여 구하는 경우
                    if determinant == "median" and determinant_value < np.median(above_threshold_values):
                        determinant_value = np.median(above_threshold_values)
                        representative_value = value
                    # 대표값을 평균을 사용하여 구하는 경우
                    elif determinant == "mean" and determinant_value < np.mean(above_threshold_values):
                        determinant_value = np.mean(above_threshold_values)
                        representative_value = value   
            
            for value in cluster:
                representative_dict[value] = representative_value
            
            # 대표값 측정 후 초기화
            cluster_num = 0
            determinant_value = 0
                        
        return representative_dict

    matrix = np.load('/opt/airflow/dags/cos_similarity.npy')
    df = pd.read_csv('/opt/airflow/dags/news_1_raw_data.csv')
    initial_clusters = find_clusters(matrix, threshold=70)
    merged_clusters = merge_overlapping_clusters(initial_clusters)
    representative_dict = get_representative_value(matrix, merged_clusters, threshold=70, determinant="median")
    representative_titles = [df.loc[representative_dict[index], 'title'] for index in df.index]
    df['representative_title'] = representative_titles

    path = "/opt/airflow/dags/news_2_representative_data.csv"
    df.to_csv(path, index=False)

    indices_to_extract = [index for index, rep_index in representative_dict.items() if index == rep_index]
    latest_representative_df = df.loc[indices_to_extract, ['title', 'article']]
    path = "/opt/airflow/dags/news_latest_representative.csv"
    latest_representative_df.to_csv(path, index=False)

def add_track_field_to_documents(search, representative_title, track):
    track_value = track  # 업데이트할 값 설정
    search.update_by_query(index='test', body={
        "script": {
            "source": """
                if (ctx._source.containsKey('track')) {
                    if (ctx._source.track == null) {
                        ctx._source.track = params.track_value;
                    }
                } else {
                    ctx._source['track'] = params.track_value;
                }
            """,
            "lang": "painless",
            "params": {
                "track_value": track_value
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"match": {"representative_title": representative_title}}
                ]
            }
        }
    })    

def track_update(search):
    if 'track.keyword' in search.indices.get(index='test')['test']['mappings']['properties']:
        response = search.search(
            index='test',
            body={
                "size": 0,
                "aggs": {
                    "tracks": {
                        "terms": {
                            "field": "track.keyword",
                            "size": 10000  # 유니크한 track 값이 많을 경우에는 적절한 크기로 설정
                        },
                        "aggs": {
                            "articles": {
                                "terms": {
                                    "field": "article.keyword",
                                    "size": 10000  # 유니크한 article 값이 많을 경우에는 적절한 크기로 설정
                                }
                            }
                        }
                    }
                }
            }
        )
        # 집계 결과에서 'tracks' 집계의 버킷을 추출
        tracks_buckets = response['aggregations']['tracks']['buckets']

        # 가장 최신의 대표값이 있는 csv 파일 로드
        df = pd.read_csv("/opt/airflow/dags/news_latest_representative.csv")
        latest_article = df['article'].tolist()
        print('최근의 대표 기사만 df로 만듦')

        # 각 버킷에서 'articles' 집계의 버킷을 추출하고 article 값을 출력
        for bucket in tracks_buckets:
            track_value = bucket['key']
            article_buckets = bucket['articles']['buckets']
            articles = [article_bucket['key'] for article_bucket in article_buckets]

            articles_fianl = latest_article + articles
            print("articles_fianl", articles_fianl)
            df = pd.DataFrame({'article': articles_fianl})
            matrix = konlpy(df)
            for i in range(len(latest_article)):
                for num in matrix[i][len(latest_article):]:
                    if num > 70:
                        title = df.loc[i, 'title']
                        add_track_field_to_documents(search, 'test', title, track_value)
                        break
    else:
        print("추적할 뉴스 없음.")