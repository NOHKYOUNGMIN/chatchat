# -*- coding: utf-8 -*-
"""
app.py — 생성형 AI(ChatGPT API) 미니 챗앱 (Streamlit)
- API 키는 프로젝트 루트의 .env에 보관: OPENAI_API_KEY=...
- 캐릭터(시스템 프롬프트) 선택, 대화 히스토리 유지, 수동 내보내기 제공
- 자동 저장 기능 없음 (요청 반영)

실행 전:
  1) 가상환경 만들기
     - Windows:  .\create_venv_windows.ps1
     - macOS:    bash create_venv_mac.sh
  2) .env에 OPENAI_API_KEY 채우기
  3) 실행: streamlit run app.py
"""

import os
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# 0) .env 로드 (API 키는 코드에 직접 쓰지 않기)
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    st.set_page_config(page_title="나만의 AI 챗봇", page_icon="🤖")
    st.error(
        "OPENAI_API_KEY가 없어요.\n"
        "프로젝트 루트에 .env 파일을 만들고 아래처럼 적어주세요:\n"
        "OPENAI_API_KEY=sk-..."
    )
    st.stop()

# OpenAI Python SDK v1 — 환경변수에서 키 자동 인식
client = OpenAI()

# 1) 캐릭터 프롬프트 (블로그 스타일 참고)
character_prompts = {
    "친근한_멘토": """당신은 친근하고 따뜻한 개발 멘토입니다.
짧고 실용하며, 복잡한 용어는 풀어서 설명하고,
필요하면 한 줄 예시 코드를 먼저 제시하세요.""",
    "90년대_감성": """당신은 90년대 감성의 재치 있는 친구입니다.
밝고 유쾌하지만 정보는 정확하게,
문장 끝에 가벼운 추임새를 한 번씩 첨가하세요(과하지 않게).""",
    "차분한_사서": """당신은 차분하고 신뢰감 있는 사서입니다.
정보의 출처/근거를 간략히 덧붙이고,
항상 요약 → 핵심 목록 → 다음 행동을 제안하세요."""
}

# 2) Streamlit 페이지/사이드바
st.set_page_config(page_title="나만의 AI 챗봇", page_icon="🤖", layout="wide")
st.title("🤖 나만의 AI 챗봇")

with st.sidebar:
    st.subheader("⚙️ 설정")

    model = st.selectbox(
        "모델",
        options=["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
        index=0,
        help="계정마다 사용 가능 모델이 다를 수 있어요.",
    )
    temperature = st.slider("창의성(temperature)", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("응답 최대 토큰", 64, 4096, 1024, 64)

    selected_character = st.selectbox(
        "캐릭터 선택", list(character_prompts.keys()), index=0
    )
    st.caption("💡 캐릭터는 시스템 프롬프트로 구현됩니다.")

    # 대화 초기화
    if st.button("🧹 대화 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 3) 세션 상태 준비
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []
if "character" not in st.session_state:
    st.session_state.character = selected_character

# 캐릭터가 바뀌면 히스토리 초기화(스타일 일관성)
if st.session_state.character != selected_character:
    st.session_state.character = selected_character
    st.session_state.messages = []

# 4) 기존 히스토리 렌더링
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 5) 입력 → 스트리밍 응답
prompt = st.chat_input("메시지를 입력하세요")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        try:
            # 최근 N개만 전달
            N = 20
            history = st.session_state.messages[-N:]
            system_prompt = character_prompts[st.session_state.character]

            stream = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[{"role": "system", "content": system_prompt}] + history,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and getattr(delta, "content", None):
                    full_text += delta.content
                    placeholder.markdown(full_text)

        except Exception as e:
            placeholder.error(f"오류: {type(e).__name__} — {e}")

    st.session_state.messages.append({"role": "assistant", "content": full_text})

# 6) 간단 대시(메시지/추정 토큰)
with st.sidebar:
    total_msgs = len(st.session_state.messages)
    user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
    st.metric("총 메시지", total_msgs)
    st.metric("사용자 메시지", user_msgs)

# 7) 수동 내보내기 (자동 저장 없음)
if st.session_state.messages:
    st.download_button(
        label="⬇️ 대화 내보내기 (markdown)",
        data="\n\n".join(
            [f"**{m['role']}**: {m['content']}" for m in st.session_state.messages]
        ),
        file_name="chat_history.md",
        mime="text/markdown",
        use_container_width=True,
    )
