import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from textblob import TextBlob
import pyttsx3
from reportlab.pdfgen import canvas
from datetime import datetime
import numpy as np

# ================= PAGE =================
st.set_page_config(page_title="AI Business Intelligence", layout="wide")

# ================= VOICE =================
engine = pyttsx3.init()

def speak(text, language="English"):
    try:
        voices = engine.getProperty('voices')
        if language == "English":
            engine.setProperty('voice', voices[0].id)
        elif len(voices) > 1:
            engine.setProperty('voice', voices[1].id)
        engine.say(text)
        engine.runAndWait()
    except:
        pass

# ================= STYLE =================
st.markdown("""
<style>
.stApp {background: linear-gradient(white,#1f4037,#99f2c8);}
.login-box {
border-radius:18px;width:420px;margin:auto;
box-shadow:0px 8px 25px rgba(0,0,0,0.2);text-align:center;}
.card {
border-radius:15px;
box-shadow:0px 6px 18px rgba(0,0,0,0.15);}
.title {
text-align:center;font-size:36px;font-weight:700;margin-bottom:20px;}
.logout {position:fixed;right:30px;top:20px;}
</style>
""", unsafe_allow_html=True)

# ================= USERS =================
if not os.path.exists("users.csv"):
    pd.DataFrame(columns=["username","password"]).to_csv("users.csv", index=False)

users = pd.read_csv("users.csv")

if "logged" not in st.session_state:
    st.session_state.logged=False

# =====================================================
# LOGIN
# =====================================================
if not st.session_state.logged:

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("## 👋 Welcome")

    option = st.radio("",["Login","Register"],horizontal=True)

    if option=="Register":
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        if st.button("Create Account"):
            if u in users.username.values:
                st.error("User exists")
            else:
                users.loc[len(users)] = [u,p]
                users.to_csv("users.csv", index=False)
                st.success("Registered")

    if option=="Login":
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        if st.button("Login"):
            if not users[(users.username==u)&(users.password==p)].empty:
                st.session_state.logged=True
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =====================================================
# DASHBOARD
# =====================================================
st.markdown('<div class="logout">', unsafe_allow_html=True)
if st.button("Logout"):
    st.session_state.logged=False
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="title">AI Business Intelligence Dashboard</div>', unsafe_allow_html=True)

# ================= LANGUAGE =================
lang = st.selectbox("Language",["English","Tamil","Hindi","Telugu","Kannada"])

# ================= AI ASSISTANT =================
st.sidebar.title("🤖 AI Assistant")
q=st.sidebar.text_input("Ask anything")
if q:
    r="This platform analyzes sentiment drivers and predicts demand."
    st.sidebar.success(r)
    speak(r,lang)

# ================= PDF =================
def create_pdf(title,lines):
    file="report.pdf"
    c=canvas.Canvas(file)
    y=800
    c.setFont("Helvetica-Bold",14)
    c.drawString(100,y,"AI Business Intelligence Report")
    y-=20
    c.setFont("Helvetica",10)
    c.drawString(100,y,"Generated:"+str(datetime.now()))
    y-=30
    c.drawString(100,y,title)
    y-=20
    for line in lines:
        c.drawString(100,y,str(line))
        y-=15
    c.save()
    return file

# ================= HELPERS =================
def find_text_column(df):
    for c in df.columns:
        if df[c].dtype=="object":
            return c
    return df.columns[0]

def find_numeric_column(df):
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return df.columns[0]

# =====================================================
# SENTIMENT
# =====================================================
col1,col2=st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Customer Sentiment Intelligence")

    file=st.file_uploader("Upload reviews file")

    if file:
        df=pd.read_csv(file)
        text_col=find_text_column(df)

        # general sentiment
        df["polarity"]=df[text_col].astype(str).apply(lambda x: TextBlob(x).sentiment.polarity)

        pos=len(df[df.polarity>0])
        neg=len(df[df.polarity<0])
        neu=len(df[df.polarity==0])

        st.write("Positive:",pos)
        st.write("Negative:",neg)
        st.write("Neutral:",neu)

        # aspect sentiment
        aspects=["price","quality","delivery","service","packaging"]
        aspect_scores={a:[] for a in aspects}

        for review in df[text_col].astype(str):
            for a in aspects:
                if a in review.lower():
                    aspect_scores[a].append(TextBlob(review).sentiment.polarity)

        aspect_avg={a:(np.mean(v) if v else 0) for a,v in aspect_scores.items()}
        st.write("Aspect Scores:",aspect_avg)

        # plot
        fig=plt.figure()
        plt.bar(aspect_avg.keys(),aspect_avg.values())
        st.pyplot(fig)

        # insight
        worst=min(aspect_avg,key=aspect_avg.get)
        best=max(aspect_avg,key=aspect_avg.get)
        insight=f"Negative driver: {worst} | Positive driver: {best}"
        st.success(insight)
        speak(insight,lang)

        if st.button("Download Sentiment Report"):
            lines=[f"Positive:{pos}",f"Negative:{neg}",f"Neutral:{neu}"]
            for k,v in aspect_avg.items():
                lines.append(f"{k}:{round(v,2)}")
            lines.append(insight)
            pdf=create_pdf("Sentiment Analysis",lines)
            st.download_button("Download",open(pdf,"rb"),"sentiment.pdf")

    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# FORECASTING
# =====================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Sentiment-Integrated Demand Forecast")

    file=st.file_uploader("Upload sales data")

    if file:
        df=pd.read_csv(file)
        num_col=find_numeric_column(df)

        st.line_chart(df[num_col])

        trend=df[num_col].pct_change().mean()
        sentiment_factor=0.1
        forecast=df[num_col].iloc[-1]*(1+trend+sentiment_factor)

        st.write("Forecast Demand:",int(forecast))

        inventory=st.number_input("Current Inventory",value=100)

        if forecast>inventory:
            st.error("Stockout risk")
        else:
            st.success("Inventory safe")

        change=st.slider("Improve sentiment %",-20,20,5)
        new_forecast=forecast*(1+change/100)
        st.write("What-if Forecast:",int(new_forecast))

        if st.button("Download Forecast Report"):
            lines=[
                f"Forecast:{int(forecast)}",
                f"Inventory:{inventory}",
                f"What-if change:{change}%",
                f"New forecast:{int(new_forecast)}"
            ]
            pdf=create_pdf("Demand Forecast",lines)
            st.download_button("Download",open(pdf,"rb"),"forecast.pdf")

    st.markdown('</div>', unsafe_allow_html=True)