10/22 작업완료
vs코드에서 실행시 ctrl + shift + v 하면 미리보기 창으로 보임

## 📁 프로젝트 폴더 구조 및 사용법 (README.md)

이 문서는 프로젝트의 폴더 구조와 **`clova.py`** 스크립트 사용법을 설명합니다.

-----

### 📂 폴더 구조

<pre>
project_root/
├── data/
│   ├── 생성/
│   │   ├── 오디오/
│   │   └── 텍스트/
│   └── 수집/
│       ├── 오디오/
│       └── 텍스트/
├── result/
│   └── 오디오파일명/
│       ├── 오디오파일명.txt
│       └── 오디오파일명_result.json
└── scripts/
    ├── clova.py
    └── clova.ipynb
</pre>


-----

### 💻 `clova.py` 사용법

#### 1\. 필수 라이브러리 설치

가상환경 (venv, conda 등)을 활성화한 후, 필요한 라이브러리를 설치합니다.

```bash
pip install requests python-dotenv
```

⚠️ **주의**: API 인증 정보(Secret Key 등)는 보안을 위해 **`.env` 파일**에 설정해야 합니다.

**`.env` 파일**은 `scripts/` 또는 프로젝트 루트`(Clova_Test/)`에 위치해야 하며, 아래와 같은 내용을 포함해야 합니다:

```bash
CLOVASPEECH_API=발급받은_Secret_Key
CLOVASPEECH_INVOKE_URL=https://clovaspeech-gw.ncloud.com/external/v2/앱ID
```

#### 2\. 스크립트 실행

터미널에서 `clova.py` 스크립트를 실행합니다.

```bash
python clova.py
```

#### 3\. 오디오 파일 경로 입력

아래 메시지가 출력되면 변환을 원하는 오디오 파일의 경로를 입력합니다.

```
🎧 변환할 오디오 파일 경로를 입력하세요:
```

#### 4\. 실행 예시 및 출력

경로 입력 후, 스크립트가 API 요청 및 결과 저장 과정을 진행합니다.

**입력 예시:**
`data/수집/오디오/test.wav`

**출력 예시:**

```
출력 디렉토리: ../result\test
클로바 스피치 API 요청 중...
b'{"language": "ko-KR", "completion": "sync", "callback": null, "userdata": null, "wordAlignment": true, "fullText": true, "forbiddens": null, "boostings": null, "diarization": {"enable": true}, "sed": null}'
✅ API 응답 수신 완료
✅ 텍스트 저장 완료 → ../result\test\test.txt
✅ JSON 저장 완료 → ../result\test\test_result.json
🎉 모든 과정 완료!
```

변환된 텍스트 및 JSON 결과는 **`result/`** 디렉토리 내에 입력된 오디오 파일명으로 된 폴더에 저장됩니다.