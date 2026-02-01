import streamlit as st
import graphviz
import json
from streamlit_mic_recorder import mic_recorder
from core.schema import OntologyModel, LayerConfig, AccessLevel
from core.engine import HozoEngine
from core.storage import OntologyStorage

# 1. 初期設定と永続化の準備
storage = OntologyStorage()
st.set_page_config(
    page_title="1216 Hozo AI Architect",
    page_icon="🎙️",
    layout="wide"
)

# 2. セッションステートの初期化
if "model" not in st.session_state:
    loaded_data = storage.load()
    # データが存在する場合のみロード、空の場合は新規作成
    if loaded_data.get("nodes"):
        model = OntologyModel(**loaded_data)
    else:
        # 初期状態のレイヤー定義
        model = OntologyModel()
        model.layers = {
            "Core": LayerConfig(name="Core", access=AccessLevel.LOCKED, description="基本概念層"),
            "Medical": LayerConfig(name="Medical", access=AccessLevel.OPEN, description="医療ドメイン層"),
            "User": LayerConfig(name="User", access=AccessLevel.OPEN, description="自由記述層")
        }
    st.session_state.model = model
    st.session_state.engine = HozoEngine(st.session_state.model)

# --- UI レイアウト ---

st.title("🎙️ Hozo Voice-Driven Ontology Architect")
# 接続中のAIモデル名を表示（デバッグ用）
if hasattr(st.session_state.engine, 'model_id'):
    st.caption(f"🚀 AI Engine: `{st.session_state.engine.model_id}` connected.")
st.markdown("---")

# サイドバー: レイヤー管理とデータエクスポート
with st.sidebar:
    st.header("⚙️ System Control")
    
    st.subheader("Layer Status")
    for l_name, l_cfg in st.session_state.model.layers.items():
        icon = "🔒" if l_cfg.access == AccessLevel.LOCKED else "🔓"
        st.write(f"{icon} **{l_name}**: `{l_cfg.access.value}`")
    
    st.divider()
    
    st.subheader("💾 Data Management")
    if st.button("Save Current Model"):
        # Pydantic V2: dict() を model_dump() に修正
        storage.save(st.session_state.model.model_dump())
        st.success("Saved to data/ontology_model.json")
    
    # JSONプレビューとダウンロード
    # Pydantic V2: dict() を model_dump() に修正
    json_output = json.dumps(st.session_state.model.model_dump(), indent=2, ensure_ascii=False)
    st.download_button(
        label="Download JSON",
        data=json_output,
        file_name="hozo_model.json",
        mime="application/json"
    )

# メインエリア: 入力と可視化
col_input, col_viz = st.columns([1, 2])

with col_input:
    st.subheader("🎤 Command Input")
    
    # 音声入力
    audio = mic_recorder(
        start_prompt="Click to Start Recording",
        stop_prompt="Stop Recording",
        key='recorder'
    )
    
    if audio:
        st.audio(audio['bytes'])
        st.info("Audio captured. Analyzing intent...")
    
    user_input = st.text_area(
        "Voice to Text / Manual Command:",
        placeholder="例：医療レイヤーに、人間から派生する患者というロール概念を追加して",
        height=100
    )
    
    if st.button("Execute Logic", type="primary"):
        if user_input:
            with st.spinner("Gemini is reasoning..."):
                result = st.session_state.engine.execute(user_input)
                
                if result["status"] == "success":
                    st.success(f"Action: {result.get('action', 'ADD')} Success!")
                    st.balloons()
                    
                    # AIからの追加提案を表示
                    if result.get("suggestions"):
                        st.write("💡 **AI Suggestions for expansion:**")
                        for suggestion in result["suggestions"]:
                            st.info(f"• {suggestion}")
                    
                    # 操作のたびに自動保存 (dict -> model_dump)
                    storage.save(st.session_state.model.model_dump())
                else:
                    st.error(f"Error: {result['message']}")
        else:
            st.warning("Please enter a command.")

with col_viz:
    st.subheader("📊 Knowledge Structure Visualization")
    
    # Graphvizによる描画
    dot = graphviz.Digraph()
    dot.attr(rankdir='BT', size='8,8') # Bottom-to-Top (法造の階層順)
    
    if not st.session_state.model.nodes:
        st.info("No nodes yet. Add a concept to start visualizing.")
    else:
        for node_id, node in st.session_state.model.nodes.items():
            # 法造のルール：Basicは青、Roleはオレンジ
            color = "#E1F5FE" if node.type == "basic" else "#FFF3E0"
            edge_color = "#01579B" if node.type == "basic" else "#E65100"
            shape = "ellipse" if node.type == "basic" else "box"
            
            label = f"<<B>{node.label}</B><BR/><FONT POINT-SIZE='10'>({node.type})</FONT>>"
            dot.node(node_id, label, style="filled", fillcolor=color, color=edge_color, shape=shape)
            
            # 親概念へのリンク（isa関係）
            if node.parent_id and node.parent_id in st.session_state.model.nodes:
                dot.edge(node_id, node.parent_id, label="isa", color="#9E9E9E")

        st.graphviz_chart(dot, use_container_width=True)

# 3. デバッグ用エディタ（最下部）
with st.expander("🔍 View Raw Model Schema"):
    # Pydantic V2: dict() を model_dump() に修正
    st.json(st.session_state.model.model_dump())