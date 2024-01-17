from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, FloatType
from pyspark.sql.functions import udf, lit
from pyspark.ml.feature import HashingTF, IDF
from konlpy.tag import Okt
import re
import numpy as np

# 엔터 제거 함수
def remove_newline(text):
    return re.sub(r'\n+', ' ', text)

# 토큰화와 어간 추출을 포함한 전처리 함수
def preprocess(text):
    tokens = tokenizer.pos(text)  # 형태소 분석
    stems = [token[0] for token in tokens if token[1] in ['Noun', 'Verb', 'Adjective']]  # 명사, 동사, 형용사 추출
    return ' '.join(stems)

# 불용어 목록
stop_words = [] 

# 불용어 제거 함수 정의
def remove_stopwords(text, stopwords):
    words = text.split()
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)

# Spark 세션 생성
spark = SparkSession.builder \
    .appName("Article Similarity") \
    .getOrCreate()

# tokenizer는 Okt 모델 사용
tokenizer = Okt()

# DataFrame 스키마 정의
schema = StructType([
    StructField("title", StringType(), True),
    StructField("link", StringType(), True),
    StructField("article", StringType(), True),
    StructField("input_time", StringType(), True),  # 여기서는 StringType으로 가정합니다.
    StructField("pub", StringType(), True),
    StructField("reporter", StringType(), True)
])

# 로컬 파일에서 DataFrame 로드 (파일 경로는 실제 환경에 맞게 수정 필요)
df = spark.read \
    .option("header", "true") \
    .schema(schema) \
    .csv("opt/airflow/dags/news_1_raw_data.csv")

# "article" 컬럼만 선택
df = df.select("article")

# UDF 등록
remove_newline_udf = udf(remove_newline, StringType())
preprocess_udf = udf(preprocess, StringType())
remove_stopwords_udf = udf(remove_stopwords, StringType())  

df = df.withColumn("cleaned_text", remove_newline_udf("text"))
df = df.withColumn("processed_text", preprocess_udf("cleaned_text"))
df = df.withColumn("stop_removed_text", remove_stopwords_udf("processed_text", lit(stop_words))) 

# HashingTF 및 IDF 설정 및 적용
hashingTF = HashingTF(inputCol="tokenized_text", outputCol="rawFeatures", numFeatures=20)
featurized_data = hashingTF.transform(df)

idf = IDF(inputCol="rawFeatures", outputCol="features")
idf_model = idf.fit(featurized_data)
tfidf_data = idf_model.transform(featurized_data)

# 코사인 유사도 계산
dot_udf = F.udf(lambda x, y: float(np.dot(x, y)), FloatType())
cross_join_df = tfidf_data.alias("a").crossJoin(tfidf_data.alias("b"))

similarity_matrix = cross_join_df.withColumn("similarity", dot_udf("a.features", "b.features")) \
    .select("a.id", "b.id", "similarity") \
    .groupBy("a.id").pivot("b.id").agg(F.first("similarity"))

# DataFrame을 배열 형태로 변환
similarity_array = np.array(similarity_matrix.select("*").toPandas().iloc[:, 1:])

# 배열 출력 및 저장
print(similarity_array)
np.save('/opt/airflow/dags/cos_similarity.npy', similarity_array)

# Spark 세션 종료
spark.stop()
