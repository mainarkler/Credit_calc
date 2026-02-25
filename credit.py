import streamlit as st
import pandas as pd

# =========================
# Кэширование расчета
# =========================
@st.cache_data
def calculate_schedule(
    principal,
    annual_rate,
    months,
    payment_type,
    interest_type,
    extra_payment_type=None,
    extra_payment_amount=0,
    extra_payment_frequency=1
):
    r = annual_rate / 100 / 12
    n = months
    balance = principal
    schedule = []

    # Расчет базового платежа
    if payment_type == "annuity":
        payment = balance * r / (1 - (1 + r) ** -n) if r != 0 else balance / n
    else:
        principal_part = balance / n

    for month in range(1, n + 1):
        if balance <= 0:
            break

        # Проценты
        interest = balance * r if interest_type == "compound" else principal * r

        # Основной платеж
        if payment_type == "annuity":
            principal_payment = payment - interest
        else:
            principal_payment = principal_part
            payment = principal_payment + interest

        # Доп. платеж
        extra_payment = 0
        if extra_payment_type == "one_time" and month == 1:
            extra_payment = extra_payment_amount
        elif extra_payment_type == "periodic" and month % extra_payment_frequency == 0:
            extra_payment = extra_payment_amount

        total_principal_payment = principal_payment + extra_payment
        if total_principal_payment > balance:
            total_principal_payment = balance

        balance -= total_principal_payment

        schedule.append([
            month,
            round(payment + extra_payment, 2),
            round(interest, 2),
            round(total_principal_payment, 2),
            round(max(balance, 0), 2)
        ])

    df = pd.DataFrame(
        schedule,
        columns=["Месяц", "Платеж", "Проценты", "Погашение долга", "Остаток долга"]
    )
    return df


# =========================
# UI Streamlit
# =========================
st.set_page_config(
    page_title="Кредитный калькулятор",
    page_icon="💳",
    layout="wide"
)
st.title("💳 Кредитный калькулятор (Web-версия)")

# ========== Вводные параметры ==========
col1, col2 = st.columns(2)
with col1:
    principal = st.number_input(
        "Сумма кредита",
        min_value=0,
        value=1_000_000,
        step=10000,
        help="Введите сумму кредита (например: 1_000_000)"
    )
    annual_rate = st.number_input(
        "Годовая ставка (%)",
        min_value=0.0,
        value=12.0,
        step=0.1,
        help="Процентная ставка (например: 12%)"
    )
    months = st.number_input(
        "Срок (месяцев)",
        min_value=1,
        value=36,
        step=1,
        help="Введите срок кредита в месяцах (например: 36)"
    )

with col2:
    payment_type = st.selectbox(
        "Тип платежа",
        ["annuity", "diff"],
        index=0,
        format_func=lambda x: "Аннуитетный" if x == "annuity" else "Дифференцированный"
    )
    interest_type = st.selectbox(
        "Тип начисления процентов",
        ["compound", "simple"],
        index=0,
        format_func=lambda x: "Сложные" if x == "compound" else "Простые"
    )

# ===== Дополнительные платежи =====
st.subheader("Дополнительные платежи")
extra_payment_type = st.selectbox(
    "Тип доп. платежа",
    ["none", "one_time", "periodic"],
    format_func=lambda x: {
        "none": "Нет",
        "one_time": "Единоразовый (1 месяц)",
        "periodic": "Периодический"
    }[x]
)

extra_payment_amount = 0
extra_payment_frequency = 1
if extra_payment_type != "none":
    extra_payment_amount = st.number_input(
        "Размер доп. платежа",
        min_value=0,
        value=50_000,
        step=10000,
        help="Введите сумму дополнительного платежа"
    )
if extra_payment_type == "periodic":
    extra_payment_frequency = st.number_input(
        "Периодичность (каждые N месяцев)",
        min_value=1,
        value=3,
        step=1,
        help="Каждые N месяцев будет доп. платеж"
    )

# ===== Кнопка рассчитать =====
if st.button("Рассчитать"):

    # Без доп. платежей
    df_base = calculate_schedule(
        principal, annual_rate, months, payment_type, interest_type
    )
    total_payment_base = df_base["Платеж"].sum()
    total_interest_base = df_base["Проценты"].sum()

    # С доп. платежами
    if extra_payment_type == "none":
        df_extra = df_base.copy()
        total_payment_extra = total_payment_base
        total_interest_extra = total_interest_base
    else:
        df_extra = calculate_schedule(
            principal, annual_rate, months, payment_type, interest_type,
            extra_payment_type, extra_payment_amount, extra_payment_frequency
        )
        total_payment_extra = df_extra["Платеж"].sum()
        total_interest_extra = df_extra["Проценты"].sum()

    # ===== Итоги =====
    st.subheader("Итоговые показатели")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### С выбранными параметрами")
        st.metric("Полная стоимость кредита", f"{total_payment_extra:,.2f}")
        st.metric("Переплата (проценты)", f"{total_interest_extra:,.2f}")

    with col2:
        if extra_payment_type != "none":
            st.markdown("### Без доп. платежей")
            st.markdown(f"<span style='color:gray'>Полная стоимость: {total_payment_base:,.2f}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:gray'>Переплата: {total_interest_base:,.2f}</span>", unsafe_allow_html=True)
            st.success(f"Экономия по процентам: {total_interest_base - total_interest_extra:,.2f}")

    # ===== Таблица =====
    st.subheader("График платежей")
    st.dataframe(df_extra, use_container_width=True)

    # ===== График =====
    st.subheader("Динамика остатка долга")
    chart_df = pd.DataFrame({
        "Без доп. платежей": df_base.set_index("Месяц")["Остаток долга"],
        "С доп. платежами": df_extra.set_index("Месяц")["Остаток долга"]
    })
    st.line_chart(chart_df)
