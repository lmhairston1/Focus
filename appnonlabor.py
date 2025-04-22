
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FOCUS_NonLabor", layout="wide")
st.title("💼 FOCUS_NonLabor – Non-Labor Expense Analysis")

uploaded_file = st.sidebar.file_uploader("📂 Upload Non-Labor Detail Report", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df["Vendor Category"] = df["Vendor Name"]
    df.loc[df["Vendor Name"].str.contains("U.S. BANCORP", case=False, na=False), "Vendor Category"] = "Credit Card Purchase"

    divisions = sorted(df["Division"].dropna().unique())
    overview_tab, scenario_tab, *division_tabs = st.tabs(["🏛️ Leadership Overview", "🚀 Scenario Simulator"] + [f"📊 {div}" for div in divisions])

    # Scenario Simulator Tab
    with scenario_tab:
        st.header("🚀 Scenario Simulator")
        categories = sorted(df["Category"].dropna().astype(str).unique())
        vendors = sorted(df["Vendor Category"].dropna().astype(str).unique())
        scenario_type = st.radio("Adjust by Category or Vendor?", ["Category", "Vendor"])
        selected = st.selectbox("Select to Adjust:", categories if scenario_type == "Category" else vendors)
        adjustment_pct = st.slider("Adjustment (%)", -50, 50, 0, step=1)
        st.markdown(f"**Applying {adjustment_pct}% adjustment to {selected}.**")

        scenario_df = df.copy()
        if adjustment_pct != 0:
            factor = 1 + (adjustment_pct / 100)
            if scenario_type == "Category":
                scenario_df.loc[scenario_df["Category"] == selected, "Cum Comm"] *= factor
            else:
                scenario_df.loc[scenario_df["Vendor Category"] == selected, "Cum Comm"] *= factor

        scenario_cat_div_df = scenario_df.groupby(["Division", "Category"])["Cum Comm"].sum().reset_index()
        fig_scenario_stack = px.bar(
            scenario_cat_div_df, x="Division", y="Cum Comm", color="Category",
            title="📊 Scenario: Category Breakdown Across Divisions",
            labels={"Cum Comm": "Cumulative Commitments ($)"}, text_auto=".2s"
        )
        st.plotly_chart(fig_scenario_stack, use_container_width=True)

        baseline_sum = df["Cum Comm"].sum()
        scenario_sum = scenario_df["Cum Comm"].sum()
        diff = scenario_sum - baseline_sum
        summary_df = pd.DataFrame({
            "Metric": ["Baseline Spend", "Scenario Spend", "Net Difference"],
            "Amount": [baseline_sum, scenario_sum, diff]
        })
        summary_df["Amount"] = summary_df["Amount"].apply(lambda x: f"${x:,.0f}")
        st.subheader("🔍 Scenario Comparison Summary")
        st.table(summary_df)

        affected_divisions = scenario_df.groupby("Division")["Cum Comm"].sum() - df.groupby("Division")["Cum Comm"].sum()
        top_division = affected_divisions.abs().idxmax()
        impact_amount = affected_divisions[top_division]
        direction = "increase" if impact_amount > 0 else "decrease"
        st.markdown(
            f"🧠 **Insight:** Applying a {adjustment_pct}% {direction} to {selected} "
            f"results in a {direction} of ${abs(impact_amount):,.0f} in spending for the {top_division} division."
        )

    # Leadership Overview Tab
    with overview_tab:
        st.header("🏛️ Leadership Overview")
        cat_div_df = df.groupby(["Division", "Category"])["Cum Comm"].sum().reset_index()
        fig_stack = px.bar(cat_div_df, x="Division", y="Cum Comm", color="Category",
                           title="📈 Category Breakdown Across Divisions",
                           labels={"Cum Comm": "Cumulative Commitments ($)", "Division": "Division"},
                           text_auto=".2s")
        st.plotly_chart(fig_stack, use_container_width=True)

        st.subheader("🔍 Interactive Vendor Drilldown")
        top_vendors_df = df.groupby("Vendor Category")["Cum Comm"].sum().reset_index().sort_values(by="Cum Comm", ascending=False).head(10)
        selected_vendor = st.selectbox("Click a vendor to filter by:", ["All Vendors"] + top_vendors_df["Vendor Category"].tolist())
        vendor_filter_df = df if selected_vendor == "All Vendors" else df[df["Vendor Category"] == selected_vendor]
        vendor_div_df = vendor_filter_df.groupby("Division")["Cum Comm"].sum().reset_index().sort_values(by="Cum Comm", ascending=False)
        fig_vendor = px.bar(vendor_div_df, x="Division", y="Cum Comm",
                            title=f"Vendor Spend Across Divisions - {selected_vendor}",
                            labels={"Cum Comm": "Cumulative Commitments ($)"}, text_auto=".2s")
        st.plotly_chart(fig_vendor, use_container_width=True)

    # Division Tabs
    for tab, div in zip(division_tabs, divisions):
        with tab:
            div_df = df[df["Division"] == div]
            st.header(f"🔍 {div} Division Overview")
            fund_df = div_df.groupby("Fund Type")["Cum Comm"].sum().reset_index()
            st.subheader("💰 Fund Type Distribution")
            st.plotly_chart(px.pie(fund_df, names="Fund Type", values="Cum Comm"), use_container_width=True)
            cat_df = div_df.groupby("Category")["Cum Comm"].sum().reset_index()
            st.subheader("📊 Commitments by Category")
            st.plotly_chart(px.bar(cat_df, x="Category", y="Cum Comm", text_auto=".2s"), use_container_width=True)
            vendor_df = div_df.groupby("Vendor Category")["Cum Comm"].sum().reset_index().sort_values(by="Cum Comm", ascending=False).head(5)
            vendor_df["Cum Comm"] = vendor_df["Cum Comm"].apply(lambda x: f"${x:,.0f}")
            st.write("🏆 **Top 5 Vendors by Spend**")
            st.dataframe(vendor_df, use_container_width=True)
            total_spend = div_df["Cum Comm"].sum()
            top_vendor = vendor_df.iloc[0]["Vendor Category"]
            top_amount = vendor_df.iloc[0]["Cum Comm"]
            st.markdown(f"<h5>🧠 <b>Summary:</b> {div} Division spent a total of <b>${total_spend:,.0f}</b>, with the highest spend on <b>{top_vendor}</b> ({top_amount}).</h5>", unsafe_allow_html=True)
else:
    st.info("Upload a non-labor detail report to begin.")
