"""
대화 로직 관리 - LangGraph 기반 구직 상담 플로우
9개 필수 질문을 통해 사용자 정보를 수집하고 검증합니다.
"""

import asyncio
from schemas.ConversationState import ConversationState
from schemas.ValidationResponse import ValidationResponse
from schemas.ElderlyUser import ElderlyUser
import yaml
from dotenv import load_dotenv
import os
import json
import subprocess
import time

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain.schema.messages import HumanMessage, SystemMessage
from VoiceToText import VoiceToText
from client import TwilioClient


class conversation_logic:
    """구직 상담 대화를 관리하는 클래스"""
    
    def __init__(self, call_sid: str, client_instance: TwilioClient):
        # YAML 설정 파일 로드
        question_config = yaml.safe_load(
            open("./configs/essential_question_prompts.yaml", "r", encoding="utf-8")
        )
        validation_config = yaml.safe_load(
            open("./configs/validation_prompts.yaml", "r", encoding="utf-8")
        )
        output_config = yaml.safe_load(
            open("./configs/output_format_prompt.yaml", "r", encoding="utf-8")
        )
        load_dotenv()

        self.client = client_instance
        self.call_sid = call_sid

        # 질문 리스트
        self.question_list = [
            question_config["essential_question1"],
            question_config["essential_question2"],
            question_config["essential_question3"],
            question_config["essential_question4"],
            question_config["essential_question5"],
            question_config["essential_question6"],
            question_config["essential_question7"],
            question_config["essential_question8"],
            question_config["essential_question9"],
        ]

        # 각 질문별 검증 프롬프트
        self.validation_list = [
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
            validation_config["validation_question1"],
        ]

        # LLM 모델 초기화
        self.output_prompt = output_config["output_format"]
        self.gpt = ChatOpenAI(
            model="gpt-4o-mini",
        )
        self.valid_gpt = self.gpt.with_structured_output(ValidationResponse)  # 답변 검증용
        self.valid_gpt_output = self.gpt.with_structured_output(ElderlyUser)  # 최종 데이터 추출용
        self.vtt = VoiceToText()  # 음성-텍스트 변환 인스턴스

    # ---------------------------NODES--------------------------- #

    async def initialize(self, state: ConversationState) -> ConversationState:
        """대화 시작 시 인사말 출력"""
        print("initialize start")
        call_sid = state["call_sid"]

        msg1 = (
            "안녕하세요. 어르신의 구직을 도와드리기 위해 몇 가지 질문을 드리겠습니다."
        )
        msg2 = "질문에 대한 답변은 가능한 구체적으로 말씀해주실 수록 최적의 구직 정보를 제공받으실 수 있습니다."
        msg3 = "그럼 시작하겠습니다."

        await self.client.say(call_sid, msg1)
        await self.client.say(call_sid, msg2)
        await self.client.say(call_sid, msg3)

        # 초기화 메시지들을 history에 추가
        init_history = [f"[AI] : {msg1}", f"[AI] : {msg2}", f"[AI] : {msg3}"]

        return {"history": init_history}

    async def conversation(self, state: ConversationState) -> ConversationState:
        """질문 출력 및 사용자 답변 수집"""
        phase = state["phase"]
        call_sid = state["call_sid"]
        AIquestion = self.question_list[phase]

        # TTS로 질문 음성 출력
        tts_start = time.time()
        await self.client.say(call_sid, AIquestion)
        tts_time = time.time() - tts_start
        print(f"[TIMING] Phase {phase} - TTS: {tts_time:.2f}초")

        # 사용자 음성 녹음 및 다운로드
        listen_start = time.time()
        wav_file_path = await self.client.listen(call_sid, phase=phase)
        listen_time = time.time() - listen_start
        print(f"[TIMING] Phase {phase} - 녹음+다운로드: {listen_time:.2f}초")

        # 녹음 파일을 STT 처리
        print("오디오 경로 :", wav_file_path)
        human_answer = None
        if wav_file_path:
            stt_start = time.time()
            human_answer = await asyncio.to_thread(self.vtt.listen, wav_file_path)
            stt_time = time.time() - stt_start
            print(f"[TIMING] Phase {phase} - STT+정제: {stt_time:.2f}초")

        # 녹음 실패 또는 STT 실패 시
        if (
            human_answer is None
            or "[녹음 실패]" in human_answer
            or "[녹음된 음성이 없습니다]" in human_answer
        ):
            await self.client.say(
                call_sid,
                "죄송합니다. 음성이 잘 들리지 않았어요. 다시 한 번 천천히 말씀해주시겠어요?",
            )
            return await self.retry(state)

        # 정상 응답 처리
        print(f"[USER] {human_answer}")
        past_history = state["history"]
        new_history = past_history + [f"[AI] : {AIquestion}"]
        new_history = new_history + [f"[USER] : {human_answer}"]

        return {"history": new_history, "last_response": human_answer}

    async def is_valid(self, state: ConversationState) -> str:
        """답변의 유효성을 검증하고 다음 단계 결정"""
        phase = state["phase"]
        call_sid = state["call_sid"]
        AIquestion = self.question_list[phase]
        validation_prompt = self.validation_list[phase]
        human_answer = state["last_response"]

        # GPT를 사용한 답변 유효성 검증
        validation_input = [
            SystemMessage(validation_prompt),
            HumanMessage(f"질문: {AIquestion} \n답변: {human_answer}"),
        ]
        validation_start = time.time()
        justification = await self.valid_gpt.ainvoke(validation_input)
        validation_time = time.time() - validation_start
        print(f"[TIMING] Phase {phase} - 답변검증: {validation_time:.2f}초")

        # 답변이 유효한 경우
        if justification.is_valid:
            if state["phase"] == len(self.question_list) - 1:  # 마지막 질문인 경우
                await self.client.say(
                    call_sid,
                    "모든 질문에 대한 답변이 끝났습니다. 어르신의 답변을 바탕으로 최적의 구직 정보를 빠른 시일 내에 메세지로 전달해드리겠습니다. 감사합니다.",
                )
                return "End"
            else:  # 다음 질문으로 진행
                return "Next"
        else:  # 답변이 불충분한 경우 재질문
            common_prefix = "어르신, 말씀주신 내용이 충분하지 않은 것 같아요."
            ai_prefix = justification.message
            text = f"{common_prefix} {ai_prefix}"
            await self.client.say(call_sid, text)
            return "Retry"

    async def before_next(self, state: ConversationState) -> ConversationState:
        call_sid = state["call_sid"]
        next_tts_start = time.time()
        await self.client.say(call_sid, "감사합니다. 다음 질문으로 넘어가겠습니다.")
        next_tts_time = time.time() - next_tts_start
        print(f"[TIMING] Phase {state['phase']} - 다음질문 TTS: {next_tts_time:.2f}초")

        return {
            "phase": state["phase"] + 1,
        }

    async def before_end(self, state: ConversationState) -> ConversationState:
        call_sid = state["call_sid"]
        end_msg = "어르신, 대화가 종료되었습니다."
        await self.client.say(call_sid, end_msg)
        await self.client.hangup(call_sid)
        return {
            "history": state["history"] + [f"[AI] : {end_msg}"],
        }

    async def retry(self, state: ConversationState) -> ConversationState:
        new_history = state["history"][:-2]
        return {"history": new_history}

    # ---------------------------WORKFLOW --------------------------- #

    def compose_workflow(self):
        """LangGraph 워크플로우 구성"""
        workflow = StateGraph(ConversationState)

        # 워크플로우 노드들 추가
        workflow.add_node(self.initialize, "initialize")
        workflow.add_node(self.conversation, "conversation")
        workflow.add_node(self.is_valid, "is_valid")
        workflow.add_node(self.retry, "retry")
        workflow.add_node(self.before_next, "before_next")
        workflow.add_node(self.before_end, "before_end")

        # 워크플로우 엣지(연결) 정의
        workflow.add_edge(START, "initialize")  # 시작 → 초기화
        workflow.add_edge("initialize", "conversation")  # 초기화 → 대화
        workflow.add_edge("retry", "conversation")  # 재시도 → 대화
        workflow.add_conditional_edges(  # 대화 후 조건부 분기
            "conversation",
            self.is_valid,
            {"Next": "before_next", "Retry": "retry", "End": "before_end"},
        )
        workflow.add_edge("before_end", END)  # 종료 전 → 종료
        workflow.add_edge("before_next", "conversation")  # 다음 질문 전 → 대화
        
        # 그래프 컴파일 및 재귀 제한 설정
        graph = workflow.compile()
        graph.recursion_limit = 200
        self.graph = graph

    async def _run(self):
        dummy_input = {
            "phase": 0,
            "history": [],
            "last_response": "",
            "ai_prefix": "",
            "call_sid": self.call_sid,
        }

        result = await self.graph.ainvoke(dummy_input)

        return result

    async def run(self):
        """대화 워크플로우 실행 및 최종 데이터 추출"""
        result = await self._run()
        history = result["history"]
        
        # 대화 내용을 구조화된 데이터로 변환
        validation_input = [
            SystemMessage(self.output_prompt),
            HumanMessage(f"대화 내용 : {history}"),
        ]

        # GPT를 사용하여 최종 사용자 정보 추출
        output = await self.valid_gpt_output.ainvoke(validation_input)
        # Sample
        # INFO:     54.209.203.118:59782 - "POST /voice HTTP/1.1" 200 OK
        # 최종 output: {'name': '김영종', 'age': 76, 'location': '경기도 용인시 수지구',
        # 'available_time': '오전 9시부터 오후 6시까지', 'license': '환경 미화원 자격증',
        # 'preferred_field': '청소', 'health_condition': '다리가 조금 아픕니다',
        # 'career': '어렸을 때부터 청소 일을 했고, 삼성 아파트에서 청소원으로 근무했다',
        #  'education': '낙생 초등학교, 낙원 중학교, 낙생 고등학교 졸업; 대학교는 졸업하지 않음'}

        # 통화 종료 후 파일 자동 생성
        await self._generate_files(history, output)

        return output

    async def _generate_files(self, history, user_data):
        """통화 종료 후 transcript, metadata.json 생성 및 추천 시스템 실행"""
        session_dir = self.client.session_dir

        # 1. transcript.txt 생성
        transcript_path = os.path.join(session_dir, "transcript.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            for line in history:
                if line.strip():  # 빈 줄 제거
                    f.write(f"{line}\n")
        print(f"Transcript saved to: {transcript_path}")

        # 2. metadata.json 생성
        metadata_path = os.path.join(session_dir, "metadata.json")
        # ElderlyUser 객체를 dict로 변환
        if hasattr(user_data, "dict"):
            metadata = user_data.dict()
        else:
            metadata = (
                user_data.__dict__
                if hasattr(user_data, "__dict__")
                else dict(user_data)
            )

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"Metadata saved to: {metadata_path}")

        # 3. 추천 시스템 실행
        try:
            print("Running recommendation system...")
            result = subprocess.run(
                ["python", "recommendation/main.py", session_dir],
                capture_output=True,
                text=True,
                timeout=180,  # timeout: 3분
                cwd=os.getcwd(),  # 현재 디렉토리에서 실행
            )
            if result.returncode == 0:
                print("Recommendation system completed successfully")
                if result.stdout:
                    print(result.stdout)
            else:
                print(
                    f"Recommendation system failed (return code: {result.returncode})"
                )
                if result.stderr:
                    print(f"Error details: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("Recommendation system timed out (3분 초과)")
        except FileNotFoundError:
            print("Error: recommendation/main.py 파일을 찾을 수 없습니다")
        except Exception as e:
            print(f"Error running recommendation system: {e}")
