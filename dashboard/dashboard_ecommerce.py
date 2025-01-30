import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime as dt
from babel.numbers import format_currency
sns.set(style='dark')

def create_demografi_df(df):
    bycity_df = df.groupby(by="customer_city").customer_id.nunique().reset_index()
    bycity_df.rename(columns={
    "customer_id": "customer_count"

    }, inplace=True)
    bycity = bycity_df.sort_values(by="customer_count", ascending=False).head(8)
    
    return bycity

def create_delivery_time_df(df):
    # Pastikan kolom datetime sudah dalam format datetime
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'], errors='coerce')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')

    # Mengonversi shipping_limit_date menjadi datetime dengan penanganan kesalahan
    df['shipping_limit_date'] = pd.to_datetime(df['shipping_limit_date'], errors='coerce')
    
    # Memeriksa tipe data kolom untuk memastikan berhasil konversi
    print(df['shipping_limit_date'].dtype)  # Menampilkan tipe data kolom shipping_limit_date

    # Memeriksa beberapa nilai pertama setelah konversi untuk memastikan hasilnya benar
    print(df['shipping_limit_date'].head())  # Menampilkan beberapa nilai pertama

    # Menghitung delivery_time
    delivery_time = df['order_delivered_customer_date'] - df['order_purchase_timestamp']
    delivery_time = delivery_time.apply(lambda x: x.total_seconds() if pd.notna(x) else 0)
    df['delivery_time'] = round(delivery_time / 86400)  # Mengonversi detik ke hari

    Q1 = df['delivery_time'].quantile(0.25)
    Q3 = df['delivery_time'].quantile(0.75)
    IQR = Q3 - Q1

    # Tentukan batas bawah dan atas untuk outlier
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Memfilter outlier
    df = df[(df['delivery_time'] >= lower_bound) & (df['delivery_time'] <= upper_bound)]
    
    # Mengisi nilai delivery_time negatif dengan nilai median
    median_value = df[df['delivery_time'] >= 0]['delivery_time'].median()
    df['delivery_time'] = df['delivery_time'].apply(lambda x: median_value if x < 0 else x)
    
    # Mengambil tahun dan bulan dari shipping_limit_date
    df["shipping_month"] = df["shipping_limit_date"].dt.strftime('%B')
    df["shipping_year"] = df["shipping_limit_date"].dt.year
    monthly_delivery_time = df.groupby(["shipping_year", "shipping_month"])["delivery_time"].mean().reset_index()
    
    return monthly_delivery_time


def create_top_category_df(df):
    start_date = "2017-01-01"
    end_date = "2018-12-31"

    filtered_df = df[
    (df['shipping_limit_date'] >= start_date)&
    (df['shipping_limit_date'] <= end_date)
    ]
    
    top_products_seller_per_category = filtered_df.groupby(['product_category_name', 'product_id']).size()\
    .reset_index(name='count')\
    .sort_values(by=["product_category_name", "count"],ascending=[True, False])

    top_10_products = top_products_seller_per_category.sort_values(by="count", ascending=False).head(10)
    return top_10_products

def create_revenue_df(df):
    latest_date = df['order_purchase_timestamp'].max()
    months = 3
    cutoff_date = latest_date - pd.DateOffset(months=months)
    recent_transactions = df[df["order_purchase_timestamp"] >= cutoff_date]
    recent_revenue = recent_transactions.groupby("customer_unique_id")["price"].sum().reset_index()
    recent_revenue = recent_revenue.sort_values(by="price", ascending=False)

    return recent_revenue

def create_clustering_df(df):
    def categorize_price(price):
        if price < 50:
            return "Murah"
        elif 50 <= price <= 200:
            return "Menengah"
        else:
            return "Mahal"

    df["price_category"] = df["price"].apply(categorize_price)
    price_distribution = df["price_category"].value_counts()
    return price_distribution

all_df = pd.read_csv("all_data.csv")

datetime_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
all_df.reset_index(inplace=True)


for columns in datetime_columns:
    all_df[columns] = pd.to_datetime(all_df[columns], errors='coerce')

demografi_df = create_demografi_df(all_df)
clustering_df = create_clustering_df(all_df)
delivery_time_df = create_delivery_time_df(all_df)
category_df = create_top_category_df(all_df)
revenue_df = create_revenue_df(all_df)

#===============#

st.header("E-Commerce Public Dataset Dashboard - Dicoding Task :sparkles:")
st.text("Raden Dika Natakusumah -- Dicoding Code : dika1804 -- E-mail : Kenasyah12@gmail.com")
st.subheader('Customers Demografi')

col1, col2 = st.columns(2)

with col1:
    demografi_cust = demografi_df['customer_count'].sum()
    st.metric("Total customers", value=demografi_cust)  
    
with col2:
    top_city = demografi_df.iloc[0]
    top_city_name = top_city['customer_city']
    top_city_count = top_city['customer_count']

    st.metric(f"Total Customers in {top_city_name}", value=top_city_count)
    
demografi_df_sorted = demografi_df.sort_values(by='customer_count', ascending=True)

fig, ax = plt.subplots(figsize=(16, 8))
ax.barh(demografi_df_sorted['customer_city'], demografi_df_sorted['customer_count'], color="#90CAF9")
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=15)
ax.set_xlabel('Number of Customers', fontsize=18)
ax.set_ylabel('City', fontsize=18)
ax.set_title('Total Customers per City', fontsize=20)
st.pyplot(fig)

#===========================#

st.subheader('Delivery Time')

month_order = ["January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"]
delivery_time_df["shipping_month"] = pd.Categorical(delivery_time_df["shipping_month"], categories=month_order, ordered=True)
delivery_time_df_sorted = delivery_time_df.sort_values(["shipping_year", "shipping_month"])

plt.figure(figsize=(14, 7))
sns.lineplot(
    x="shipping_month", 
    y="delivery_time", 
    hue="shipping_year", 
    data=delivery_time_df_sorted,
    marker="o",
    linewidth=2,
    palette="tab10"
)
plt.title("Rata-rata Waktu Pengiriman per Bulan dan Tahun", fontsize=16)
plt.xlabel("Bulan", fontsize=12)
plt.ylabel("Rata-rata Waktu Pengiriman (hari)", fontsize=12)
plt.xticks(rotation=45) 
plt.legend(title="Tahun") 
plt.grid(True)

st.pyplot(plt)

st.subheader("Top 10 Best-Selling Product Categories (2017-2018)")

colors = ["#72BCD4"] + ["#D3D3D3"] * 9  

plt.figure(figsize=(10, 5))
sns.barplot(
    y="product_category_name", 
    x="count",
    data=category_df, 
    palette=colors
)

plt.title("Top 10 Best-Selling Product Categories in 2017-2018", loc="center", fontsize=15)
plt.xlabel("Number of Products Sold", fontsize=12)
plt.ylabel("Product Category", fontsize=12)
plt.tick_params(axis='x', labelsize=12)
plt.tick_params(axis='y', labelsize=12)
plt.grid(axis="x", linestyle="--", alpha=0.7)


st.pyplot(plt)

#===============#

st.subheader("Top 10 Customers by Revenue in the Last 3 Months")

latest_date = all_df['order_purchase_timestamp'].max()
months = 3
cutoff_date = latest_date - pd.DateOffset(months=months)
recent_transactions = all_df[all_df["order_purchase_timestamp"] >= cutoff_date]
recent_revenue = recent_transactions.groupby("customer_unique_id")["price"].sum().reset_index()
recent_revenue = recent_revenue.sort_values(by="price", ascending=False).head(10)

colors_ = ["#72BCD4"] + ["#D3D3D3"] * 9  

plt.figure(figsize=(10, 5))
sns.barplot(
    x="customer_unique_id",
    y="price",
    data=recent_revenue,
    palette=colors_
)

plt.title("Top 10 Customers by Revenue (Last 3 Months)", fontsize=15)
plt.ylabel("Total Revenue (Price)", fontsize=12)
plt.xlabel(None)
plt.xticks(rotation=45, ha='right', fontsize=10)  
plt.tick_params(axis='y', labelsize=12)
plt.grid(axis="y", linestyle="--", alpha=0.7)

st.pyplot(plt)


#===================#

st.subheader("Product Price Clustering")

price_distribution_df = clustering_df.reset_index()
price_distribution_df.columns = ["Price Category", "Count"]

fig1, ax1 = plt.subplots(figsize=(7, 5))
colors = ["#72BCD4", "#FFDD57", "#FF6B6B"]

st.subheader("Product Count by Price Category")
plt.figure(figsize=(8, 5))
sns.barplot(
    x=price_distribution_df["Price Category"], 
    y=price_distribution_df["Count"], 
    palette=colors
)

plt.title("Product Count per Price Category", fontsize=15)
plt.xlabel("Price Category", fontsize=12)
plt.ylabel("Number of Products", fontsize=12)
plt.grid(axis="y", linestyle="--", alpha=0.7)

st.pyplot(plt)

st.caption("@Dikta2025")