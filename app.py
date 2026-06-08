import streamlit as st
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

# Cấu hình giao diện rộng rãi, hiện đại
st.set_page_config(page_title="Hệ Hỗ Trợ Ra Quyết Định Menu Bánh (DSS)", layout="wide")

# ==========================================
# 1. ĐỌC VÀ CHUẨN HÓA DỮ LIỆU TỪ EXCEL 2 TAB
# ==========================================
@st.cache_data
def load_data():
    file_excel = "data dss.xlsx" 
    
    # Đọc dữ liệu từ 2 tab (sheet) của file Excel chung
    df_data = pd.read_excel(file_excel, sheet_name="data")
    df_recipe = pd.read_excel(file_excel, sheet_name="recipe")
    
    # Dùng Regex trích xuất lấy con số đầu tiên (Khắc phục triệt để lỗi lệch dấu cách/ký tự ẩn)
    df_data['Muc_Do_Ngot'] = df_data['Độ ngọt/Độ béo (1-5)'].astype(str).str.extract(r'(\d+)').astype(int)
    df_recipe['Muc_Do_Ngot'] = df_recipe['Adjustment_Note'].astype(str).str.extract(r'(\d+)').astype(int)
    
    return df_data, df_recipe

try:
    df_data, df_recipe = load_data()
except Exception as e:
    st.error(f"❌ Không tìm thấy file 'data dss.xlsx' hoặc cấu trúc file bị sai! Hãy chắc chắn file Excel nằm chung thư mục với file app.py. Chi tiết: {e}")
    st.stop()

# ==========================================
# 2. HÀM CHẠY THUẬT TOÁN APRIORI THEO VÙNG MIỀN
# ==========================================
def run_apriori_for_location(df_location):
    if df_location.empty or df_location['ORDER_ID'].nunique() < 2:
        return pd.DataFrame()
        
    try:
        # Tạo ma trận Giỏ hàng cho riêng vùng miền này
        basket = (df_location.groupby(['ORDER_ID', 'Sản phẩm'])['Sản phẩm']
                  .count().unstack().reset_index().fillna(0)
                  .set_index('ORDER_ID'))
        
        basket_sets = basket.applymap(lambda x: x > 0)
        
        # Chạy thuật toán tìm tập mục phổ biến
        frequent_itemsets = apriori(basket_sets, min_support=0.01, use_colnames=True)
        
        if frequent_itemsets.empty:
            return pd.DataFrame()
            
        # Tạo hệ luật kết hợp
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.01)
        return rules
    except:
        return pd.DataFrame()

# ==========================================
# 3. GIAO DIỆN CHÍNH CỦA ỨNG DỤNG WEB (STREAMLIT UI)
# ==========================================
st.title("🍰 HỆ HỖ TRỢ QUYẾT ĐỊNH (DSS) - TỐI ƯU MENU TIỆM BÁNH")
st.markdown("---")

# Thiết kế Thanh bên trái (Sidebar) để người dùng chọn thông số đầu vào
st.sidebar.header("⚙️ Khu vực Nhập Liệu")
selected_city = st.sidebar.selectbox("1. Chọn Thành phố muốn tối ưu Menu:", df_data['Vùng miền'].unique())
selected_cake = st.sidebar.selectbox("2. Chọn Loại bánh cần hiệu chỉnh:", df_data['Sản phẩm'].unique())

st.sidebar.markdown("---")
st.sidebar.caption("Dự án Hệ thống hỗ trợ ra quyết định nhóm Jolista - MIS VNU")

# 📊 PHẦN BIỂU ĐỒ ĐỘNG ĐƯỢC ĐƯA THẲNG LÊN TRANG CHỦ ĐỂ THEO DÕI TỔNG QUAN
st.header(f"📊 Báo Cáo Phân Tích Dữ Liệu Khảo Sát tại {selected_city}")

# Lọc nhanh tập dữ liệu theo thành phố đang được chọn để vẽ biểu đồ tổng quan vùng
df_filtered_city = df_data[df_data['Vùng miền'] == selected_city]

# Tạo 2 cột để đặt 2 biểu đồ nằm ngang nhau
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("🔹 Biểu đồ sản phẩm bán chạy (Lượng đơn)")
    # Đếm số lượng đơn của từng loại bánh tại thành phố được chọn
    cake_counts = df_filtered_city['Sản phẩm'].value_counts().reset_index()
    cake_counts.columns = ['Tên Sản Phẩm', 'Số Lượng Đơn Bán Ra']
    # Vẽ biểu đồ cột bằng Streamlit
    st.bar_chart(data=cake_counts, x='Tên Sản Phẩm', y='Số Lượng Đơn Bán Ra', color="#FF4B4B")

with chart_col2:
    st.subheader(f"🔹 Phân bổ phản hồi độ ngọt của bánh '{selected_cake}'")
    # Lọc riêng phản hồi của loại bánh đang chọn tại thành phố đó
    df_specific_cake_city = df_filtered_city[df_filtered_city['Sản phẩm'] == selected_cake]
    
    if not df_specific_cake_city.empty:
        # Chuẩn hóa đếm số lượng phiếu khảo sát cho từng mức ngọt
        sweet_counts = df_specific_cake_city['Độ ngọt/Độ béo (1-5)'].value_counts().reset_index()
        sweet_counts.columns = ['Mức Độ Khảo Sát', 'Số Lượng Bình Chọn']
        # Sắp xếp theo thứ tự từ mức 1 đến mức 5
        sweet_counts = sweet_counts.sort_values(by='Mức Độ Khảo Sát')
        # Vẽ biểu đồ cột đứng hiển thị tỷ lệ phản hồi trực quan thay thế cho biểu đồ tròn
        st.bar_chart(data=sweet_counts, x='Mức Độ Khảo Sát', y='Số Lượng Bình Chọn', color="#00C0F2")
    else:
        st.info(f"Chưa có dữ liệu phản hồi độ ngọt cho bánh {selected_cake} tại khu vực này.")

st.markdown("---")

# 🧠 PHẦN KHAI PHÁ LOGIC ĐỂ RA QUYẾT ĐỊNH KINH DOANH VÀ KHUYẾN NGHỊ CÔNG THỨC
st.header("🧠 Kết Quả Xử Lý Thuật Toán & Khuyến Nghị Quyết Định")

# Tạo 2 cột lớn hiển thị kết quả Khuyến nghị công thức và Combo mua kèm
col1, col2 = st.columns([1, 1])

# --------------------------------------------------
# CỘT 1: PHÂN TÍCH KHẢO SÁT VỊ GIÁC VÀ CÔNG THỨC SỬA ĐỔI
# --------------------------------------------------
with col1:
    st.subheader("📋 Đề Xuất Công Thức Sản Xuất")
    
    if not df_specific_cake_city.empty:
        # Tìm mức phản hồi xuất hiện nhiều nhất (Mode) từ khảo sát trải nghiệm công thức gốc của vùng đó
        most_common_feedback = df_specific_cake_city['Muc_Do_Ngot'].mode()[0]
        
        # Tính toán tỷ lệ phần trăm số đông phản hồi
        total_votes = len(df_specific_cake_city)
        matching_votes = len(df_specific_cake_city[df_specific_cake_city['Muc_Do_Ngot'] == most_common_feedback])
        percentage = round((matching_votes / total_votes) * 100, 1)
        
        # Khởi tạo mô tả trạng thái phản hồi của khách hàng
        feedback_desc = ""
        action_desc = ""
        if most_common_feedback == 5:
            feedback_desc = "Mức 5 - Rất ngọt (Quá ngọt so với khẩu vị địa phương)"
            action_desc = "Tự động kích hoạt công thức Giảm 50% lượng đường (-50% Sweet)"
        elif most_common_feedback == 4:
            feedback_desc = "Mức 4 - Ngọt (Hơi đậm đường so với khẩu vị địa phương)"
            action_desc = "Tự động kích hoạt công thức Giảm 30% lượng đường (-30% Sweet)"
        elif most_common_feedback == 3:
            feedback_desc = "Mức 3 - Vừa (Vừa vặn với khẩu vị địa phương)"
            action_desc = "Giữ nguyên Công thức gốc của tiệm (Original Recipe)"
        else:
            feedback_desc = f"Mức {most_common_feedback} - Nhạt/Hơi nhạt so với khẩu vị địa phương"
            action_desc = "Tự động kích hoạt công thức Tăng thêm lượng đường (+30% Sweet)"
        
        # Hiển thị lập luận DSS mang tính khoa học quản lý
        st.warning(f"📢 **Tình trạng phản hồi:** Phần lớn khách hàng trải nghiệm sản phẩm thử nghiệm tại **{selected_city}** đều phản hồi bánh đang ở **{feedback_desc}** (Chiếm tỷ lệ **{percentage}%** tổng số phiếu khảo sát vùng).")
        st.success(f"💡 **Quyết định tối ưu hóa (DSS):** {action_desc} để ra sản phẩm phù hợp hoàn toàn với thị trường này.")
        
        # TRUY VẤN CÔNG THỨC: Khớp đồng thời Tên bánh, Điểm số phản hồi VÀ Vùng miền (Location)
        recipe_row = df_recipe[
            (df_recipe['Product_name'] == selected_cake) & 
            (df_recipe['Muc_Do_Ngot'] == most_common_feedback) &
            (df_recipe['Location'] == selected_city)
        ]
        
        # Dự phòng: Nếu không tìm thấy công thức riêng biệt cho thành phố đó, bốc công thức chung của mức ngọt đó
        if recipe_row.empty:
            recipe_row = df_recipe[
                (df_recipe['Product_name'] == selected_cake) & 
                (df_recipe['Muc_Do_Ngot'] == most_common_feedback)
            ]
        
        if not recipe_row.empty:
            st.write(f"**Chi tiết nguyên liệu sản xuất riêng cho chi nhánh {selected_city}:**")
            st.caption(f"**Ghi chú hệ thống định danh:** `{recipe_row['Adjustment_Note'].values[0]}`")
            st.text_area(label="Hàm lượng thành phần chi tiết:", value=recipe_row['Recipe'].values[0], height=250)
        else:
            st.error("⚠️ Không tìm thấy dòng công thức hiệu chỉnh phù hợp tương ứng trong sheet `recipe`.")
    else:
        st.warning(f"Chưa ghi nhận dữ liệu phản hồi khảo sát cho bánh **{selected_cake}** tại **{selected_city}**.")

# --------------------------------------------------
# CỘT 2: CHIẾN LƯỢC COMBO (APRIORI CHẠY RIÊNG CHO KHU VỰC)
# --------------------------------------------------
with col2:
    st.subheader("🤝 Gợi Ý Chiến Lược Combo Tối Ưu Quầy Kệ")
    st.write(f"Món đề xuất sắp xếp bán cùng hoặc làm combo giảm giá với bánh '{selected_cake}':")
    
    # CHẠY APRIORI LOCAL: Chỉ truyền vào dữ liệu đơn hàng của riêng thành phố đang chọn thôi
    rules_local = run_apriori_for_location(df_filtered_city)
    
    # Kiểm tra nếu bảng rules tồn tại và không rỗng
    if (rules_local is not None) and (not rules_local.empty) and ('antecedents' in rules_local.columns):
        # Tạo cột chuỗi từ frozenset để thực hiện tìm kiếm lọc tên bánh
        rules_local['antecedents_str'] = rules_local['antecedents'].apply(lambda x: ', '.join(list(x)))
        rules_local['consequents_str'] = rules_local['consequents'].apply(lambda x: ', '.join(list(x)))
        
        # Lọc luật kết hợp: Tìm xem ở thành phố này, khi mua selected_cake thì họ hay mua kèm bánh nào nhất
        matched_rules = rules_local[rules_local['antecedents_str'] == selected_cake].sort_values(by='confidence', ascending=False)
        
        if not matched_rules.empty:
            for idx, row in matched_rules.head(2).iterrows():
                addon_item = row['consequents_str']
                confidence_percent = round(row['confidence'] * 100, 1)
                
                st.warning(f"🧁 **Gợi ý thiết lập Combo:** Nên bán kèm với món **{addon_item}**")
                st.markdown(f"* **Độ tin cậy tại địa phương (Confidence):** **{confidence_percent}%** (Có nghĩa là cứ {confidence_percent}% số lượng đơn hàng mua bánh *{selected_cake}* tại riêng khu vực *{selected_city}* thì khách sẽ chốt mua thêm bánh *{addon_item}*).")
            st.caption(f"ℹ️ *Hệ thống tự động khai phá (Data Mining) hành vi giỏ hàng độc lập của người tiêu dùng tại {selected_city} để thiết lập ưu đãi, tối ưu hóa doanh thu tổng.*")
        else:
            st.info(f"❌ Dựa trên hành vi mua sắm độc lập tại khu vực **{selected_city}**, chưa có món bánh nào có tỷ lệ mua kèm đủ lớn với bánh **{selected_cake}** để lập combo.")
    else:
        st.info(f"❌ Dữ liệu lịch sử giỏ hàng tại riêng khu vực **{selected_city}** chưa đủ điều kiện cấu thành luật kết hợp Apriori.")