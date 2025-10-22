


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
    audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
    output_dir = os.path.join("../result", audio_basename)
    os.makedirs(output_dir, exist_ok=True)

    txt_path = os.path.join(output_dir, f"{audio_basename}.txt")
    json_path = os.path.join(output_dir, f"{audio_basename}_result.json")

    print(f"출력 디렉토리: {output_dir}")
    return audio_basename, output_dir, txt_path, json_path


# ------------------------------------------------------------
# ② CLOVA Speech API 호출
# ------------------------------------------------------------
def call_clova_api(audio_path: str, diarization: bool = True):

    print("클로바 스피치 API 요청 중...")
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
    segments = result_json.get("segments", [])
    merged_segments = []

    if not segments and result_json.get("text"):
        merged_segments.append(f"[전체 텍스트]: {result_json['text']}\n")
        return merged_segments

    prev_speaker = None
    prev_start = None
    conf_values = []
    accumulated_text = ""

    for i, seg in enumerate(segments):
        speaker = seg.get("speaker", {}).get("label", "Unknown")
        text = seg.get("text", "").strip()
        start = seg.get("start")
        conf = seg.get("confidence")

        if speaker == prev_speaker:
            accumulated_text += " " + text
            if conf is not None:
                conf_values.append(conf)
        else:
            if prev_speaker is not None:
                avg_conf = sum(conf_values) / len(conf_values) if conf_values else None
                conf_str = f"{avg_conf:.2f}" if avg_conf else "N/A"
                start_str = f"{int(prev_start):08d}" if prev_start else "00000000"
                merged_segments.append(f"{len(merged_segments):04d}:{start_str}:{conf_str}:speaker{prev_speaker}:{accumulated_text.strip()}\n")

            prev_speaker = speaker
            prev_start = start
            accumulated_text = text
            conf_values = [conf] if conf else []

    if prev_speaker is not None:
        avg_conf = sum(conf_values) / len(conf_values) if conf_values else None
        conf_str = f"{avg_conf:.2f}" if avg_conf else "N/A"
        start_str = f"{int(prev_start):08d}" if prev_start else "00000000"
        merged_segments.append(f"{len(merged_segments):04d}:{start_str}:{conf_str}:speaker{prev_speaker}:{accumulated_text.strip()}\n")

    return merged_segments


# ------------------------------------------------------------
# ④ 결과 저장 (TXT + JSON)
# ------------------------------------------------------------
def save_results(txt_lines, txt_path, json_path, json_data):
    with open(txt_path, "w", encoding="utf-8") as f:
        f.writelines(txt_lines)
    print(f"✅ 텍스트 저장 완료 → {txt_path}")

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(json_data, jf, ensure_ascii=False, indent=2)
    print(f"✅ JSON 저장 완료 → {json_path}")


# ------------------------------------------------------------
# ⑤ 메인 실행 함수
# ------------------------------------------------------------
def main(audio_path, diarization=True):
    if not os.path.exists(audio_path):
        print(f"❌ 파일 없음: {audio_path}")
        return

    audio_basename, output_dir, txt_path, json_path = setup_output_paths(audio_path)
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
