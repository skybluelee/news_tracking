FROM apache/airflow:2.7.0-python3.11

# Install OpenJDK-11
# Spark을 사용하기 위해서 openjdk가 필요함
USER root
RUN apt update && \
    apt-get install -y openjdk-11-jdk && \
    apt-get install -y ant && \
    apt-get clean;

USER airflow

# Set JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/
RUN export JAVA_HOME

# requirements.txt 파일 복사 및 패키지 설치
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt