import os
import json
import streamlit as st
from google import genai
from google.genai import types

# ページ設定
st.set_page_config(page_title="なぞなぞジェネレーター", page_icon="🤔")

# タイトル
st.title("🤔 なぞなぞジェネレーター")
st.write("テキストを入力すると、AIが入力をテーマにしたなぞなぞ（問題と答え）を作成します")

# テキスト入力
input_text = st.text_area(
    "テキストを入力してください",
    placeholder="例: 夏（'夏' と入力すると夏に関するなぞなぞを作成します）",
    height=100,
)

# 生成ボタン
if st.button("なぞなぞを生成", type="primary"):
    if not input_text:
        st.warning("テキストを入力してください")
    else:
        with st.spinner("なぞなぞを作成中..."):
            try:
                # APIキー取得
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("GEMINI_API_KEYが設定されていません")
                    st.stop()

                # クライアント初期化
                client = genai.Client(api_key=api_key)

                # プロンプト作成（入力内容をテーマとしてなぞなぞを作成する）
                # JSONの中括弧やダブルクオートはf文字列内でリテラルにしたいため、トリプルクオート＆中括弧を二重にして逃がす
                prompt = f'''
次のテキストをテーマとして、そのテーマに関連する日本語のなぞなぞ（問題と答え）を作成してください。
テーマ: {input_text}。
出力はJSONのみで、形式は{{"riddle": "問題文", "answer": "答え", "category": "任意のカテゴリー"}}としてください。他の説明や余分なテキストは含めないでください。
'''

                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)],
                    )
                ]

                # API呼び出し
                response = client.models.generate_content(
                    model="gemini-flash-lite-latest",
                    contents=contents,
                    config=types.GenerateContentConfig(),
                )

                # レスポンスの整形（コードブロック対応）
                response_text = response.text.strip()
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    if lines and lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    response_text = "\n".join(lines)

                # JSONパース
                try:
                    riddle_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # もしJSONパースに失敗したら、ユーザーに生レスポンスを見せる
                    st.error("JSONパースエラーが発生しました。生成されたテキストを確認してください。")
                    st.code(response_text)
                    raise

                riddle = riddle_data.get("riddle", "")
                answer = riddle_data.get("answer", "")
                category = riddle_data.get("category", "不明")

                # 結果表示
                st.success("なぞなぞの生成が完了しました！")
                if category and category != "":
                    st.markdown(f"**カテゴリ:** {category}")
                st.markdown(
                    f'<div style="background-color: #f7fbff; padding: 18px; border-radius: 8px;">'
                    f'<h3 style="margin:0; color:#111">{riddle}</h3>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # 答えは折りたたみで表示
                with st.expander("答えを見る"):
                    st.write(answer)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

