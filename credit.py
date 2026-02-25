import streamlit as st
import pandas as pd

# =========================
# Функция расчёта кредита
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

    if payment_type == "annuity":
        payment = balance * r / (1 - (1 + r) ** -n) if r != 0 else balance / n
    else:
        principal_part = balance / n

    for month in range(1, n + 1):
        if balance <= 0:
            break
        interest = balance * r if interest_type == "compound" else principal * r
        if payment_type == "annuity":
            principal_payment = payment - interest
        else:
            principal_payment = principal_part
            payment = principal_payment + interest

        # Доп платеж
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
# UI
# =========================
st.set_page_config(page_title="Кредитный калькулятор", page_icon="💳", layout="wide")
st.title("💳 Кредитный калькулятор (Web)")

# ===== Ввод через text_input/text_area с placeholder =====
col1, col2 = st.columns(2)
with col1:
    principal_input = st.text_input(
        "Сумма кредита",
        placeholder="1000000",
        help="Введите сумму кредита"
    )
    annual_rate_input = st.text_input(
        "Годовая ставка (%)",
        placeholder="12",
        help="Процентная ставка"
    )
    months_input = st.text_input(
        "Срок (месяцев)",
        placeholder="36",
        help="Срок кредита"
    )

with col2:
    payment_type = st.selectbox(
        "Тип платежа",
        ["Аннуитетный", "Дифференцированный"]
    )
    interest_type = st.selectbox(
        "Тип начисления процентов",
        ["Сложные", "Простые"]
    )

# ===== Доп платежи =====
st.subheader("Дополнительные платежи")
extra_payment_type = st.selectbox(
    "Тип доп. платежа",
    ["Нет", "Единоразовый (1 месяц)", "Периодический"]
)

extra_payment_amount_input = ""
extra_payment_frequency_input = "1"

if extra_payment_type != "Нет":
    extra_payment_amount_input = st.text_input(
        "Размер доп. платежа",
        placeholder="50000"
    )
if extra_payment_type == "Периодический":
    extra_payment_frequency_input = st.text_input(
        "Периодичность (каждые N месяцев)",
        placeholder="3"
    )

# ===== Кнопка рассчитать =====
if st.button("Рассчитать"):
    try:
        principal = float(principal_input)
        annual_rate = float(annual_rate_input)
        months = int(months_input)
        extra_payment_amount = float(extra_payment_amount_input) if extra_payment_amount_input else 0
        extra_payment_frequency = int(extra_payment_frequency_input) if extra_payment_frequency_input else 1
        payment_type_code = "annuity" if payment_type == "Аннуитетный" else "diff"
        interest_type_code = "compound" if interest_type == "Сложные" else "simple"
        extra_payment_type_code = None
        if extra_payment_type == "Единоразовый (1 месяц)":
            extra_payment_type_code = "one_time"
        elif extra_payment_type == "Периодический":
            extra_payment_type_code = "periodic"

        # ===== Расчёт графиков =====
        df_base = calculate_schedule(principal, annual_rate, months, payment_type_code, interest_type_code)
        total_payment_base = df_base["Платеж"].sum()
        total_interest_base = df_base["Проценты"].sum()

        if extra_payment_type_code is None:
            df_extra = df_base.copy()
            total_payment_extra = total_payment_base
            total_interest_extra = total_interest_base
        else:
            df_extra = calculate_schedule(principal, annual_rate, months, payment_type_code,
                                          interest_type_code, extra_payment_type_code, extra_payment_amount, extra_payment_frequency)
            total_payment_extra = df_extra["Платеж"].sum()
            total_interest_extra = df_extra["Проценты"].sum()

        # ===== Итоги =====
        st.subheader("Итоговые показатели")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Полная стоимость кредита", f"{total_payment_extra:,.2f}")
            st.metric("Переплата (проценты)", f"{total_interest_extra:,.2f}")
        with col2:
            if extra_payment_type_code is not None:
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

    except ValueError:
        st.error("Пожалуйста, введите корректные числовые значения в полях.")
