


import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

CLOVASPEECH_API_KEY = os.getenv("CLOVASPEECH_API")
CLOVASPEECH_URL = os.getenv("CLOVASPEECH_INVOKE_URL")



class ClovaSpeechClient:
    # Clova Speech invoke URL
    invoke_url = CLOVASPEECH_URL
    # Clova Speech secret key
    secret = CLOVASPEECH_API_KEY

    def req_url( # 외부 파일 인식 (url)
        self,
        url,
        completion,
        callback=None,
        userdata=None,
        forbiddens=None,
        boostings=None,
        wordAlignment=True,
        fullText=True,
        diarization=True,
        sed=None,
    ):
        '''
            NAVER Clova Speech의 **URL 기반 인식** 엔드포인트(`/recognizer/url`)를 호출합니다.
            로컬 업로드 없이, **외부에 접근 가능한 미디어 파일의 URL**을 넘겨 음성 → 텍스트(STT)를 수행합니다.

            [언제 쓰나요?]
            - 파일이 이미 CDN, S3/OBS 퍼블릭 링크, 웹 서버 등 **외부 URL**로 제공될 때
            - 대용량 파일을 업로드하지 않고 빠르게 요청만 던지고 싶을 때

            [요청 본문 주요 필드 설명]
            - url (str, 필수): 인식 대상 미디어의 절대 URL
            - completion (str, 필수): 응답 방식. 일반적으로 'sync' | 'async'
            - 'sync'  : 요청-응답 한 번에 결과를 받는 블로킹 방식 (짧은 파일에 적합)
            - 'async' : 비동기 처리. callback/resultToObs 등과 함께 사용 (긴 파일에 적합)
            - callback (str | None): completion='async'일 때 결과가 완료되면 **POST**로 통지받을 콜백 URL
            - userdata (dict | str | None): 호출자가 임의로 첨부하는 메타데이터(응답에 그대로 되돌려줌)
            - forbiddens (str | list[str] | None): 금칙어(비식별/마스킹용). 형식은 도메인 설정/문서에 따름(불확실)
            - boostings (list[dict] | None): **키워드 부스팅** 목록. 특정 단어 인식률 향상용(스킴은 문서에 따름)
            - wordAlignment (bool): 단어 단위 타임스탬프/정렬 정보 포함 여부 (기본 True)
            - fullText (bool): 분할 결과 외에 **전체 텍스트**를 함께 반환할지 (기본 True)
            - diarization (bool | dict | None): 화자 분리. True/False 또는 {enable: bool, speakerCountMin/Max: int} 형태(문서 버전별 상이할 수 있어 불확실)
            - sed (bool | dict | None): SED(Sound Event Detection) 이벤트 탐지 설정. 문서 스킴에 따름(불확실)

            [반환값]
            - requests.Response: HTTP 상태코드/헤더/본문을 포함한 응답 객체
            - 200 OK: 성공. 본문에 인식 결과(JSON)가 포함되거나(동기) 토큰/상태가 포함(비동기)
            - 그 외: 오류. 응답 본문에 에러 메시지 및 코드가 포함될 수 있음

            [예시]
            >>> client = ClovaSpeechClient()
            >>> resp = client.req_url(
            ...     url="https://example.com/audio/sample.wav",
            ...     completion="sync",
            ...     diarization=True,
            ...     wordAlignment=True,
            ...     fullText=True,
            ... )
            >>> resp.status_code, resp.text

            [주의/팁]
            - URL은 **서버에서 직접 접근 가능**해야 합니다(사설망/인증 필요한 URL은 실패 가능).
            - 비동기('async') 사용 시에는 보통 callback 또는 resultToObs(이 클래스에는 필드 노출 X)를 함께 설정해야 합니다.
            - 대용량/장시간 파일은 'sync'에서 타임아웃/실패 가능성이 높으므로 'async' 권장.
        '''

        request_body = {
            "url": url,
            "language": "ko-KR",
            "completion": completion,
            "callback": callback,
            "userdata": userdata,
            "wordAlignment": wordAlignment,
            "fullText": fullText,
            "forbiddens": forbiddens,
            "boostings": boostings,
            "diarization": diarization,
            "sed": sed,
        }
        headers = {
            "Accept": "application/json;UTF-8",
            "Content-Type": "application/json;UTF-8",
            "X-CLOVASPEECH-API-KEY": self.secret,
        }
        return requests.post(
            headers=headers,
            url=self.invoke_url + "/recognizer/url",
            data=json.dumps(request_body).encode("UTF-8"),
        )

    def req_object_storage( # Naver Cloud Object Storage에 저장된 파일 인식
        self,
        data_key,
        completion,
        callback=None,
        userdata=None,
        forbiddens=None,
        boostings=None,
        wordAlignment=True,
        fullText=True,
        diarization=None,
        sed=None,
    ):
        '''
            NAVER Cloud **Object Storage(OBS)**에 저장된 파일을 대상으로 인식을 수행하는
            엔드포인트(`/recognizer/object-storage`)를 호출합니다.

            [언제 쓰나요?]
            - 이미 **NCP Object Storage**에 업로드되어 있고, 도메인/버킷과 연동된 **dataKey**로 접근할 수 있을 때
            - 외부 URL 공개 없이 **사내/NCP 환경**에서 안전하게 처리하고 싶을 때

            [요청 본문 주요 필드 설명]
            - data_key (str, 필수): OBS 상의 파일 경로 키. 도메인 생성 시 설정한 **인식 대상 저장 경로** 기준의 상대 경로
            - 예: 인식 루트가 '/data'이고 실제 경로가 '/data/sample.wav'라면 dataKey는 '/sample.wav'
            - completion (str, 필수): 'sync' | 'async' (용도는 req_url과 동일)
            - callback / userdata / forbiddens / boostings / wordAlignment / fullText / diarization / sed:
            - 의미 및 타입은 req_url과 동일. 문서 버전에 따라 세부 스킴은 다를 수 있음(불확실)

            [반환값]
            - requests.Response: HTTP 상태코드/헤더/본문을 포함
            - 동기(sync): 인식 결과가 바로 본문(JSON)으로 반환될 수 있음
            - 비동기(async): 토큰/상태 정보 반환 후, 콜백/별도 조회로 결과 수신

            [예시]
            >>> client = ClovaSpeechClient()
            >>> resp = client.req_object_storage(
            ...     data_key="/meetings/2025-10-22/session01.wav",
            ...     completion="async",
            ...     diarization={"enable": True, "speakerCountMin": 2, "speakerCountMax": 6},
            ... )
            >>> resp.json()

            [주의/팁]
            - **도메인에 등록된 인식 대상 저장 경로** 하위만 접근 가능합니다.
            - 권한/리전/버킷 설정이 잘못되면 4xx/5xx가 발생할 수 있으니 NCP 콘솔 설정을 확인하세요.
            - 장시간 파일은 비동기 권장. 콜백 서버는 **공개 접근 가능**하고, 인증/서명 등 필요 시 구현해야 합니다.
        '''
        request_body = {
            "dataKey": data_key,
            "language": "ko-KR",
            "completion": completion,
            "callback": callback,
            "userdata": userdata,
            "wordAlignment": wordAlignment,
            "fullText": fullText,
            "forbiddens": forbiddens,
            "boostings": boostings,
            "diarization": diarization,
            "sed": sed,
        }
        headers = {
            "Accept": "application/json;UTF-8",
            "Content-Type": "application/json;UTF-8",
            "X-CLOVASPEECH-API-KEY": self.secret,
        }
        return requests.post(
            headers=headers,
            url=self.invoke_url + "/recognizer/object-storage",
            data=json.dumps(request_body).encode("UTF-8"),
        )

    def req_upload( # 로컬 파일 직접 업로드
        self,
        file,
        completion,
        callback=None,
        userdata=None,
        forbiddens=None,
        boostings=None,
        wordAlignment=True,
        fullText=True,
        diarization=None,
        sed=None,
    ):
        '''
            로컬(또는 임시) 파일을 **직접 업로드**하여 인식을 수행하는 엔드포인트(`/recognizer/upload`)를 호출합니다.
            멀티파트 업로드를 사용해 바이너리와 파라미터를 함께 전송합니다.

            [언제 쓰나요?]
            - 파일이 로컬 디스크에만 있고, URL/OBS로 올리기 번거로울 때
            - 빠르게 한 번만 테스트하거나 내부 배치에서 즉시 처리하고 싶을 때

            [요청 멀티파트 필드 구성]
            - files["media"]: 열어둔 파일 핸들 (예: open(file, "rb"))
            - files["params"]: JSON 직렬화된 설정(예: ('params', b'{"language":"ko-KR", ...}', 'application/json'))

            [요청 본문 주요 필드 설명]
            - language (str): 언어 코드. 예: 'ko-KR'
            - completion (str, 필수): 'sync' | 'async'
            - 'sync'는 파일 길이에 제한이 있을 수 있음(정확 한도는 버전/과금플랜/문서에 따라 **불확실**)
            - 긴 파일/대용량은 'async' 권장
            - callback (str | None): completion='async'일 때 결과 통지용 콜백 URL
            - userdata (dict | str | None): 호출자 임의 메타데이터
            - wordAlignment (bool): 단어 정렬/타임스탬프 포함 여부(기본 True)
            - fullText (bool): 전체 텍스트 포함 여부(기본 True)
            - forbiddens / boostings / diarization / sed: 의미는 req_url과 동일(세부 스킴은 문서에 따라 **불확실**)

            [반환값]
            - requests.Response: 업로드 및 처리 요청에 대한 서버 응답
            - 200/202 등: 요청 수락. 동기라면 결과 JSON, 비동기라면 토큰/상태
            - 실패 시 상태코드와 에러 메시지 확인

            [예시]
            >>> client = ClovaSpeechClient()
            >>> resp = client.req_upload(
            ...     file="data/input/meeting.wav",
            ...     completion="async",
            ...     diarization=True,
            ...     wordAlignment=True,
            ... )
            >>> resp.status_code

            [주의/팁]
            - 파일 핸들을 열 때는 **예외 처리**와 함께 `with open(file, "rb") as f:` 패턴을 사용하는 것이 안전합니다.
            - 대용량 업로드 시 네트워크/타임아웃 이슈가 있을 수 있으므로 `requests.post`의 `timeout`/재시도 로직을 고려하세요.
            - 서비스 플랜/도메인 정책에 따라 **최대 파일 크기/길이 제한**이 있을 수 있습니다(정확치는 문서/콘솔 기준, 불확실).
        '''
        request_body = {
            "language": "ko-KR", ### 언어
            "completion": completion, ### 응답방식 [동기 / 비동기]
            "callback": callback, # 비동기 방식일 경우 callback, resultToObs 중 하나 필수 입력
            "userdata": userdata, # 사용자 데이터 세부 정보
            "wordAlignment": wordAlignment, # 인식 결과의 음성과 텍스트 정렬 출력 여부
            "fullText": fullText, # 전체 인식 결과 텍스트 출력 기본 true
            "forbiddens": forbiddens,
            # noiseFiltering : 노이즈 필터링 여부 기본값 true
            "boostings": boostings, ### 키워드 부스팅, 음성 인식률을 높일 수 있는 키워드 목록으로 사용
            "diarization": diarization, ### 화자 인식
            "sed": sed,
        }
        headers = {
            "Accept": "application/json;UTF-8",
            "X-CLOVASPEECH-API-KEY": self.secret,
        }
        print(json.dumps(request_body, ensure_ascii=False).encode("UTF-8"))
        files = {
            "media": open(file, "rb"),
            "params": (
                None,
                json.dumps(request_body, ensure_ascii=False).encode("UTF-8"),
                "application/json",
            ),
        }
        response = requests.post(
            headers=headers, url=self.invoke_url + "/recognizer/upload", files=files
        )
        return response


# ------------------------------------------------------------
# ① 출력 경로 및 폴더 세팅
# ------------------------------------------------------------
def setup_output_paths(audio_path: str):
    # 오디오 경로를 받아서 해당 오디오의 파일명(확장자 제외)를 사용해서 만들어질 파일명을 정함.
    # 이것도 json이랑 txt로 나눠서 폴더를 만들 수 있게 하는게 좋아보임.
    # 오디오파일명
    audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
    # output을 넣을 폴더 경로와 폴더명 정의
    output_dir = os.path.join("../result", audio_basename)
    # 실제 폴더 생성.
    os.makedirs(output_dir, exist_ok=True)

    # 생성된 폴더에 생성할 파일명 정의
    txt_path = os.path.join(output_dir, f"{audio_basename}.txt")
    json_path = os.path.join(output_dir, f"{audio_basename}_result.json")

    print(f"출력 디렉토리: {output_dir}")
    # 파일명 return
    return txt_path, json_path

# ------------------------------------------------------------
# ② CLOVA Speech API 호출
# ------------------------------------------------------------
def call_clova_api(audio_path: str, diarization: bool = True):
    # 단순히 Clova Speech API를 호출하는 코드
    # file: 오디오 경로 필요 (필수)
    # diarization: 화자 분리 기능
    # completion(sync/async) 동기 비동기 방식인데 오디오 길이가 클수록 들어가는 시간이 많아져 비동기 방식을 권장. 단 테스트에는 동기방식으로 통일
    print("클로바 스피치 API 요청 중...")
    # HTTP 통신의 상태 코드, 헤더, 본문(JSON 등)을 모두 포함하는 구조를 반환.
    res = ClovaSpeechClient().req_upload(
        file=audio_path,
        completion="sync",
        diarization={"enable": diarization}
    )

    if res.status_code != 200:
        print(f"❌ API 실패 ({res.status_code})")
        print(res.text)
        return None
    else:
        print("✅ API 응답 수신 완료")
        return res.json()


# ------------------------------------------------------------
# ③ 세그먼트 병합 및 화자별 텍스트 정리
# ------------------------------------------------------------
def process_segments(result_json: dict):
    # 수정할 예정
    # 오로지 txt파일을 만들기위한 메소드
    # 기본적으로 나오는 json파일의 segments의 값을 가져와서 그 내용으로 txt를 하나씩 append함.   
    
    # 아래 코드의 쓰임새가 지금만 봤을때는 불분명함.
    # json에 segments는 없지만 text만 있는경우 실행되는 코드지만. json에 segments가 없는 경우는 없다고 생각
    # if not segments and result_json.get("text"):
    #     merged_segments.append(f"[전체 텍스트]: {result_json['text']}\n")
    #     return merged_segments

    segments = result_json.get("segments", [])
    merged = []
    current = None

    for seg in segments:
        speaker = seg.get("speaker", {}).get("label", "Unknown")
        text = seg.get("text", "").strip()
        start = seg.get("start")
        conf = seg.get("confidence")

        # 🔹 새로운 화자면 이전 구간 저장
        if current and speaker != current["speaker"]:
            merged.append(format_segment(current))
            current = None

        # 🔹 현재 화자 구간 갱신
        if not current:
            current = {"speaker": speaker, "start": start, "texts": [], "confs": []}

        current["texts"].append(text)
        if conf is not None:
            current["confs"].append(conf)

    # 🔹 마지막 화자 구간 처리
    if current:
        merged.append(format_segment(current))

    return merged

def format_segment(seg):
    avg_conf = sum(seg["confs"]) / len(seg["confs"]) if seg["confs"] else None
    conf_str = f"{avg_conf:.2f}" if avg_conf is not None else "N/A"
    start_str = f"{int(seg['start']):08d}" if seg["start"] else "00000000"
    text = " ".join(seg["texts"]).strip()
    idx = len(text)  # (선택사항) or global counter
    return f"{start_str}:{conf_str}:speaker{seg['speaker']}:{text}\n"


# ------------------------------------------------------------
# ④ 결과 저장 (TXT + JSON)
# ------------------------------------------------------------
def save_results(txt_lines, txt_path, json_path, json_data):#
    with open(txt_path, "w", encoding="utf-8") as f:
        f.writelines(txt_lines)
    print(f"✅ 텍스트 저장 완료 → {txt_path}")

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, ensure_ascii=False, indent=2)
    print(f"✅ JSON 저장 완료 → {json_path}")
    
def save_text_result(txt_lines, path):
    pass
def save_json_result(path, data):
    pass


# ------------------------------------------------------------
# ⑤ 메인 실행 함수
# ------------------------------------------------------------
def main(audio_path, diarization=True):
    # 경로에 실제 오디오 파일이 있는지 확인(메소드화)
    if not os.path.exists(audio_path):
        print(f"❌ 파일 없음: {audio_path}")
        return
    
    txt_path, json_path = setup_output_paths(audio_path)
    result_json = call_clova_api(audio_path, diarization)

    if not result_json:
        print("❌ API 결과 없음. 종료합니다.")
        return

    txt_lines = process_segments(result_json)
    save_results(txt_lines, txt_path, json_path, result_json)
    print("🎉 모든 과정 완료!")


# ------------------------------------------------------------
# 실행
# ------------------------------------------------------------
if __name__ == "__main__":
    AUDIO_FILE_PATH = input("🎧 변환할 오디오 파일 경로를 입력하세요: ").strip()
    DIARIZATION = True
    main(AUDIO_FILE_PATH, DIARIZATION)
