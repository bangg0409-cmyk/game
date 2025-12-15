import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 頁面設定 ---
st.set_page_config(page_title="專業排球紀錄系統", page_icon="🏐", layout="wide")

# --- 2. 魔法 CSS (美化網頁的核心) ---
# 這裡定義了計分板的樣式、字體大小和顏色
st.markdown("""
    <style>
    /* 讓整個計分板置中並加上陰影 */
    .scoreboard {
        background-color: #262730;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        color: white;
        text-align: center;
    }
    /* 隊伍名稱 */
    .team-name {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    /* 分數大字體 */
    .score-big {
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
        font-family: 'Arial Black', sans-serif;
    }
    /* 局數顯示 */
    .set-display {
        background-color: #f0f2f6;
        color: #31333F;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }
    /* 強制表格字體黑色 (解決深色模式問題) */
    .dataframe { color: black !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 初始化變數 ---
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=['時間', '局數', '隊伍', '背號', '動作類別', '詳細原因', '結果', '目前比分'])
if 'set_history' not in st.session_state:
    st.session_state.set_history = []
if 'current_set' not in st.session_state:
    st.session_state.current_set = 1
if 'score_a' not in st.session_state:
    st.session_state.score_a = 0
if 'score_b' not in st.session_state:
    st.session_state.score_b = 0

# --- 4. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 球隊設定")
    with st.expander("隊名與名單設定", expanded=True):
        team_a_name = st.text_input("主隊 (Team A)", value="Team A")
        team_a_color = "#3b82f6" # 藍色系
        team_a_roster = st.text_area("A 隊球員 (逗號隔開)", value="1, 2, 3, 4, 5, 6, 12, L").split(',')
        
        st.markdown("---")
        
        team_b_name = st.text_input("客隊 (Team B)", value="Team B")
        team_b_color = "#ef4444" # 紅色系
        team_b_roster = st.text_area("B 隊球員 (逗號隔開)", value="7, 8, 9, 10, 11, 13, L").split(',')

    team_a_players = [x.strip() for x in team_a_roster]
    team_b_players = [x.strip() for x in team_b_roster]

# --- 5. 動作規則定義 ---
action_map = {
    "攻擊 (Attack)": {
        "扣球得分 (Kill)": ("Self", "得分"), "打手出界 (Touch Out)": ("Self", "得分"), 
        "吊球得分 (Tip Kill)": ("Self", "得分"), "攻擊出界 (Out)": ("Opponent", "失誤"), 
        "攻擊掛網 (Net)": ("Opponent", "失誤"), "被攔死 (Blocked)": ("Opponent", "失誤")
    },
    "發球 (Serve)": {
        "發球得分 (Ace)": ("Self", "得分"), "發球出界 (Out)": ("Opponent", "失誤"), 
        "發球掛網 (Net)": ("Opponent", "失誤"), "8秒違例": ("Opponent", "失誤")
    },
    "攔網 (Block)": {
        "攔網得分 (Kill Block)": ("Self", "得分"), "觸網 (Net Touch)": ("Opponent", "失誤")
    },
    "一般失誤 (Faults)": {
        "連擊 (Double)": ("Opponent", "失誤"), "持球 (Catch)": ("Opponent", "失誤"), 
        "觸網 (Net)": ("Opponent", "失誤"), "越界 (Center Line)": ("Opponent", "失誤"), 
        "輪轉錯誤": ("Opponent", "失誤"), "接發球失誤": ("Opponent", "失誤")
    },
    "其他 (Other)": {
        "自訂": ("Self", "得分") 
    }
}

# --- 6. 核心介面：美化版計分板 ---
# 使用 HTML 來繪製漂亮的計分板
score_html = f"""
<div class="scoreboard">
    <div class="set-display">SET {st.session_state.current_set}</div>
    <div style="display: flex; justify-content: space-around; align-items: center;">
        <div style="width: 40%;">
            <div class="team-name" style="color: {team_a_color};">{team_a_name}</div>
            <div class="score-big" style="color: {team_a_color};">{st.session_state.score_a}</div>
        </div>
        <div style="font-size: 2rem; color: #666;">VS</div>
        <div style="width: 40%;">
            <div class="team-name" style="color: {team_b_color};">{team_b_name}</div>
            <div class="score-big" style="color: {team_b_color};">{st.session_state.score_b}</div>
        </div>
    </div>
</div>
"""
st.markdown(score_html, unsafe_allow_html=True)

# 歷史比分顯示
if st.session_state.set_history:
    st.caption(f"📜 歷史局數: {' | '.join(st.session_state.set_history)}")

# 控制按鈕區 (撤銷 & 換局)
col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    if st.button("↩️ 撤銷上一步 (Undo)", use_container_width=True):
        if not st.session_state.logs.empty:
            last_log = st.session_state.logs.iloc[-1]
            if last_log['局數'] == st.session_state.current_set:
                if "得分" in last_log['結果']:
                    if last_log['隊伍'] == team_a_name: st.session_state.score_a -= 1
                    else: st.session_state.score_b -= 1
                elif "失分" in last_log['結果']:
                    if last_log['隊伍'] == team_a_name: st.session_state.score_b -= 1
                    else: st.session_state.score_a -= 1
                st.session_state.logs = st.session_state.logs[:-1]
                st.rerun()
            else:
                st.toast("⚠️ 無法撤銷上一局紀錄", icon="🚫")
        else:
            st.toast("⚠️ 無紀錄可撤銷", icon="🚫")

with col_ctrl2:
    if st.button("🏁 結束本局 (Next Set)", use_container_width=True):
        final_score = f"{st.session_state.score_a}:{st.session_state.score_b}"
        st.session_state.set_history.append(final_score)
        st.session_state.current_set += 1
        st.session_state.score_a = 0
        st.session_state.score_b = 0
        st.rerun()

# --- 7. 紀錄輸入區 (使用 Container 包裹) ---
st.markdown("### 📝 新增紀錄")
with st.container(border=True): # 加上邊框讓視覺更集中
    c1, c2, c3 = st.columns([1.2, 1.2, 1.5])

    with c1:
        st.caption("Step 1: 誰？")
        who_team = st.radio("操作隊伍", [team_a_name, team_b_name], horizontal=True, label_visibility="collapsed")
        
        # 根據隊伍顯示不同顏色的提示
        if who_team == team_a_name:
            st.markdown(f"<span style='color:{team_a_color}'>● {team_a_name} 球員</span>", unsafe_allow_html=True)
            who_player = st.selectbox("背號", team_a_players, key="p_a")
        else:
            st.markdown(f"<span style='color:{team_b_color}'>● {team_b_name} 球員</span>", unsafe_allow_html=True)
            who_player = st.selectbox("背號", team_b_players, key="p_b")

    with c2:
        st.caption("Step 2: 做什麼？")
        category = st.selectbox("動作類別", list(action_map.keys()))
        detail_action = st.selectbox("詳細原因", list(action_map[category].keys()))

    with c3:
        st.caption("Step 3: 特殊狀況 (可選)")
        custom_desc = st.text_input("手動輸入原因", placeholder="輸入後將忽略左側選項")
        custom_result_type = None
        if custom_desc:
            st.warning("👇 請指定判決")
            custom_result_type = st.radio("判決結果", ["得分 (我方+1)", "失誤 (對方+1)"], horizontal=True)

    # 送出按鈕 (紅色顯眼)
    if st.button("確認送出 (Submit)", type="primary", use_container_width=True):
        # 邏輯判斷
        if custom_desc:
            final_reason = custom_desc
            if custom_result_type and "得分" in custom_result_type:
                who_gets_point = "Self"
                result_desc = "得分"
            else:
                who_gets_point = "Opponent"
                result_desc = "失分"
        else:
            final_reason = detail_action
            who_gets_point, result_desc = action_map[category][detail_action]
        
        # 分數計算
        if who_team == team_a_name:
            if who_gets_point == "Self": st.session_state.score_a += 1
            else: st.session_state.score_b += 1
        else: 
            if who_gets_point == "Self": st.session_state.score_b += 1
            else: st.session_state.score_a += 1

        # 寫入紀錄
        new_record = {
            '時間': datetime.now().strftime("%H:%M:%S"),
            '局數': st.session_state.current_set,
            '隊伍': who_team,
            '背號': who_player,
            '動作類別': category if not custom_desc else "自訂",
            '詳細原因': final_reason,
            '結果': f"{result_desc}",
            '目前比分': f"{st.session_state.score_a}:{st.session_state.score_b}"
        }
        st.session_state.logs = pd.concat([pd.DataFrame([new_record]), st.session_state.logs], ignore_index=True)
        st.rerun()

# --- 8. 顯示紀錄表格 ---
st.markdown("---")
st.subheader(f"📊 本局明細 (Set {st.session_state.current_set})")

current_set_logs = st.session_state.logs[st.session_state.logs['局數'] == st.session_state.current_set]

# 定義表格顏色樣式 (包含黑字修正)
def highlight_row(row):
    bg_color = '#ffe6e6' if '失分' in row['結果'] else '#e6ffe6'
    return [f'background-color: {bg_color}; color: black' for _ in row]

if not current_set_logs.empty:
    # 這裡加入 iloc[::-1] 讓顯示時也是新的在上面
    display_df = current_set_logs.iloc[::-1]
    st.dataframe(display_df.style.apply(highlight_row, axis=1), use_container_width=True)
else:
    st.info("尚無紀錄，請輸入第一筆資料")

# --- 9. 下載區 (修正為顛倒順序：舊 -> 新) ---
# 下載時把順序轉正 (時間軸順序)
full_log_download = st.session_state.logs.iloc[::-1] if not st.session_state.logs.empty else st.session_state.logs

csv = full_log_download.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 下載完整比賽紀錄 (CSV)", csv, "match_log.csv", "text/csv", use_container_width=True)
