```
PUT /news
{
  "mappings": {
    "properties": {
      "input_time": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss"
      },
      "link": {
        "type": "text"
      },
      "reporter": {
        "type": "text"
      },
      "representative_title": {
        "type": "text"
      },
      "title": {
        "type": "text"
      },
      "pub": {
        "type": "text"
      },
      "article": {
        "type": "text"
      }
    }
  }
}
```

데이터에서 수집한 뉴스 시간의 경우 OpenSearch에서 바로 인식할 수 없는 형태이므로,
미리 지정해야 한다.
