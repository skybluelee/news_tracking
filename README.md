# 뉴스 검색과 추적 기능이 있는 웹 서비스 개발
## **개요**

> **프로젝트:** News Tracking
>
> **기획 및 제작:** 이상민
>
> **분류:** 개인 프로젝트
>
> **작업 기간:** 2023.12.12 ~ 2024.01.09
>
> **주요 기능:** 데이터 파이프라인 구축, 웹 서비스 구축
>
> **사용 기술:** Python, AWS, Docker, Airflow, Spark, S3, Lambda, OpenSearch, Django

## **프로젝트 요약**
Docker에서 Airflow를 사용하여 뉴스를 수집하고 Spark에서 기사 내용간의 유사도를 판별후 대표값을 추가한 상태로 S3에 저장. 

S3에 저장된 뉴스는 Lambda를 통해 OpenSearch로 데이터 전송.

Django를 통해 OpenSearch의 데이터를 사용하여 검색 기능과 추적 기능이 있는 웹 서비스 구현.

## **상태도**
<img src="https://github.com/skybluelee/news_tracking/assets/107929903/52a70277-b80b-4458-ba33-0d9ba9d9afa9.png" width="900" height="700"/>

## **결과**
<img src="https://github.com/skybluelee/news_tracking/assets/107929903/52ae3fe8-5657-4c1e-b8b0-8f64cbd1ce34.png" width="800" height="700"/>

위는 초기 화면으로 날짜와 시간, 검색 내용을 포함하여 검색할 수 있다.

<img src="https://github.com/skybluelee/news_tracking/assets/107929903/d5735363-08cb-4058-ae45-78c72b5cefd4.png" width="600" height="700"/>

검색 결과는 유사한 기사가 많은 순서대로 보여준다. 

해당 타이틀을 클릭하면 유사 기사의 내용을 확인할 수 있으며, 후속 기사가 궁금하다면 '해당 뉴스 추적' 버튼을 눌러 뉴스를 추적한다.

<img src="https://github.com/skybluelee/news_tracking/assets/107929903/13f22605-e4fd-4565-858d-213043de50be.png" width="500" height="500"/>

추적 버튼을 누르면 기존 기사에 track 필드와 값을 추가한다.

이후 Airflow로 뉴스를 수집한 후에 track 필드의 뉴스들과 유사도를 비교하고 track 값을 입력하는 방식으로 유사한 뉴스를 추가한다.

<img src="https://github.com/skybluelee/news_tracking/assets/107929903/a2ae7e2b-118e-4b65-9670-1c5642b9b0db.png" width="250" height="500"/>

추적 뉴스는 화면의 track 바를 클릭하여 들어갈 수 있으며, 최신순으로 뉴스를 정렬한다.


## **프로젝트 상세**
### **Docker를 사용하여 Airflow, Spark, Selenium 이미지 사용**
Airflow에서 Spark와 연동하고 사용하기 위해서는 [Provider packages](https://airflow.apache.org/docs/#providers-packages-docs-apache-airflow-providers-index-html)에서 Spark에 사용하는 모듈과 Java open-jdk가 필요하다. Dockefile 참조.

Spark과 Konlpy를 사용하기 위해서는 호환되는 [JPype](https://github.com/jpype-project/jpype/releases) 버전이 필요하다. Airflow와 연동하기 전에 사용가능한 Spark 버전과 JPype를 찾아야 한다.
`docker exec -it <spark_container_name>`으로 들어간 컨테이너에서는 `wget` 명령어를 사용할 수 없다. `docker-compose.yaml`에서 `volume`위치를 적절히 저장하고 ubuntu 상에서 `wget`으로 JPype을 다운받고 컨테이너 내에서 `pip install`을 사용해야 한다.

적절한 Spark 이미지를 찾았다면 Spark에서 사용하는 Python 버전을 확인한다. Spark에서 사용하는 파이썬 버전과 Airflow의 파이썬 버전이 동일해야 SparkSubmitOperator를 사용하여 Spark job을 넘길 수 있다.
Spark Python 버전은 `docker exec -it <spark_container_name>`으로 컨테이너에 들어가서 `python --version`으로 확인한다.

적절한 Airflow 이미지를 찾았다면 필요한 모듈을 추가한채로 extend한 이미지를 빌드, 실행한 후 컨테이너의 상태를 확인한다. 
만약 컨테이너의 상태가 health: starting 상태에서 멈춰있다면(이때 `docker logs <container_name>`을 확인하면 `airflow db update`라고 쓰여있을 가능성이 높다) 해당 이미지는 포기하고 다른 이미지를 찾아야 한다.

Selenium 상태 확인 용 DAG를 하나 생성한다. 가끔씩 동작하지 않는 경우가 있는데 `docker restart`를 사용해서 정상 상태로 만들어 줘야 한다.

`SparkSubmitOperator`를 사용하기 위해서는 Connection에서 Spark에 대해 추가한다. Connection Id는 본인이 `SparkSubmitOperator`에서 사용할 connection과 이름과 동일하게 설정하면 된다. Connection Type은 Spark이다(뭔가 다양한데 Spark 사용하면 됨).
Host의 경우 `spark://Spark 컨테이너의 이름`이다. 컨테이너를 재시작할 때마다 바꿔주어야 하는데 `docker-compose.yaml`에서 host를 미리 설정하면 바꿀 필요 없으니 웬만하면 미리 설정하자.
포트는 본인이 바꾸지 않았다면 7077이다.

S3에 업로드하기 위해서는 aws access key와 secret key가 필요하다. IAM 사용자를 생성하고 S3에 대한 접근 권한을 추가한다. 사용자가 생성되면 키를 csv파일로 제공한다.
### **S3 -> Lambda -> OpenSearch**
S3에 업로드 된것을 Lambda에서 인식하기 위해서는 트리거를 S3로 두고 PUT에 대해 동작하게 만들면 된다.

Lambda를 생성하면 IAM 역할이 새로 생긴 것을 확인할 수 있다. 본인의 의도에 맞게 역할을 제거, 추가한다.

트리거와 달리 목적지는 항상 사용할 필요는 없다. 코드 내에서 처리가 가능하다면 굳이 설정하지 않아도 된다.

Lambda에서 모듈을 찾을 수 없다는 오류가 발생하면(오류는 CloudWatch에서 확인할 수 있다) 해당 모듈을 layer에 추가해야 한다.

Lambda는 파일 이름이 숫자로 되어있으면 이를 제대로 처리하지 못하니 첫 글자는 항상 영어를 사용한다.

OpenSearch의 경우 IAM 사용자가 필요하다. 보안 구성 편집 -> IAM ARN을 마스터 사용자로 설정 으로 들어가 본인이 사용할 IAM 사용자를 지정한다.
이와 같이 하는 이유는 access key와 secret key를 사용하여 OpenSearch에 접근할 때 사용자 이름은 `arn:aws:iam::` 형식인데, OpenSearch에서 사용자를 추가할 때 `:`를 사용하지 못하기 때문이다.

### **Django를 사용한 웹 서비스 구현**
> `views.py`: PUT, POST, GET, DELETE 등의 명령을 주로 여기서 처리한다.
>
> `settings.py`: ALLOWED_HOSTS에 본인 혹은 전체에 접속 권한을 추가한다.
> 템플릿 위치를 지정한다. 나의 경우 `os.path.join(BASE_DIR)`를 TEMPLATES 'DIRS'에 추가하였다.
>
> `urls.py`: 본인이 사용할 엔드포인트와 사용할 함수를 설정한다.

가상 환경은 어디까지나 해당 인스턴스에서 다른 작업을 하는 경우, 혹은 할 예정인 경우에만 사용하면 된다.

사용할 함수(주로 views.py에 있는)는 값과 html을 리턴한다. 이때 해당 html에서는 해당 값에 접근할 수 있다. 딕셔너리와 리스트 그리고 리스트 안에 여러 딕셔너리를 넣을 수도 있으니 잘 활용해보자.
