from pyspark.sql import SparkSession
from pyspark.sql.functions import floor
import logging

spark = SparkSession.builder \
    .appName("Simple PySpark Example") \
    .config("spark.network.timeout", "600s") \
    .getOrCreate()

logging.info("start")    

data = [("Alice", 34), ("Bob", 45), ("Catherine", 29), ("David", 25), ("Emily", 34)]
columns = ["Name", "Age"]

df = spark.createDataFrame(data, columns)

df_with_age_group = df.withColumn("AgeGroup", floor(df["Age"] / 10) * 10)

user_count_by_age_group = df_with_age_group.groupBy("AgeGroup").count().orderBy("AgeGroup")

user_count_by_age_group.show()
