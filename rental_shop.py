"""
ระบบร้านเช่าชุด (Costume Rental Shop Management System)
Mini Project - OOP
เวอร์ชัน Streamlit (เว็บแอปที่เขียนด้วย Python ล้วน ไม่ต้องเขียน HTML/CSS/JS เอง)

วิธีรัน:
    pip install streamlit
    streamlit run costume_rental_streamlit.py

สรุปตำแหน่งหลักการ OOP (ใช้พูดตอน present ได้เลย):
- Encapsulation : Costume.__code, __price_per_day ฯลฯ (private) เข้าถึงผ่าน property/setter
- Inheritance   : WeddingCostume, ThaiCostume, PartyCostume สืบทอดจาก Costume (abstract base)
- Polymorphism  : costume.calculate_rental_fee(days) และ costume.category()
                  ถูก override ต่างกันในแต่ละคลาสลูก แต่เรียกผ่าน interface เดียวกัน
                  (ดูจุดเรียกใช้จริงใน RentalShop.rent_costume)
"""

from abc import ABC, abstractmethod
import streamlit as st
import pandas as pd


# ==========================================================
# 1) Costume (Abstract base class)
# ==========================================================
class Costume(ABC):
    def __init__(self, code, name, size, price_per_day, deposit=0):
        self.__code = code
        self.__name = name
        self.__size = size
        self.__price_per_day = float(price_per_day)
        self.__deposit = float(deposit)
        self.__available = True

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        if not value:
            raise ValueError("ชื่อชุดห้ามว่าง")
        self.__name = value

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        self.__size = value

    @property
    def price_per_day(self):
        return self.__price_per_day

    @price_per_day.setter
    def price_per_day(self, value):
        if float(value) < 0:
            raise ValueError("ราคาต้องไม่ติดลบ")
        self.__price_per_day = float(value)

    @property
    def deposit(self):
        return self.__deposit

    @deposit.setter
    def deposit(self, value):
        self.__deposit = float(value)

    @property
    def available(self):
        return self.__available

    def mark_rented(self):
        self.__available = False

    def mark_returned(self):
        self.__available = True

    @abstractmethod
    def category(self):
        raise NotImplementedError

    @abstractmethod
    def calculate_rental_fee(self, days):
        raise NotImplementedError

    def __str__(self):
        return (
            f"[{self.category()}] {self.name} ({self.size}) "
            f"- {self.price_per_day:.0f} บาท/วัน"
        )


# ==========================================================
# 2) WeddingCostume  (Inheritance + Polymorphism)
# ==========================================================
class WeddingCostume(Costume):
    def category(self):
        return "ชุดแต่งงาน"

    def calculate_rental_fee(self, days):
        return self.price_per_day * days


# ==========================================================
# 3) ThaiCostume  (Inheritance + Polymorphism)
# ==========================================================
class ThaiCostume(Costume):
    def category(self):
        return "ชุดไทย"

    def calculate_rental_fee(self, days):
        total = self.price_per_day * days
        if days >= 3:
            total *= 0.90  # ลด 10% ถ้าเช่า >= 3 วัน
        return total


# ==========================================================
# 4) PartyCostume  (Inheritance + Polymorphism)
# ==========================================================
class PartyCostume(Costume):
    def category(self):
        return "ชุดปาร์ตี้"

    def calculate_rental_fee(self, days):
        if days <= 0:
            return 0
        return self.price_per_day + (days - 1) * self.price_per_day * 0.5  # วันถัดไปครึ่งราคา


COSTUME_CLASSES = {
    "ชุดแต่งงาน": WeddingCostume,
    "ชุดไทย": ThaiCostume,
    "ชุดปาร์ตี้": PartyCostume,
}


# ==========================================================
# 5) Customer
# ==========================================================
class Customer:
    def __init__(self, customer_id, name, phone):
        self.__id = customer_id
        self.__name = name
        self.__phone = phone

    @property
    def customer_id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def phone(self):
        return self.__phone


# ==========================================================
# 6) Rental (1 รายการเช่า)
# ==========================================================
class Rental:
    def __init__(self, rental_id, customer, costume, days, fee):
        self.__rental_id = rental_id
        self.__customer = customer
        self.__costume = costume
        self.__days = days
        self.__fee = fee
        self.__returned = False

    @property
    def rental_id(self):
        return self.__rental_id

    @property
    def customer(self):
        return self.__customer

    @property
    def costume(self):
        return self.__costume

    @property
    def days(self):
        return self.__days

    @property
    def fee(self):
        return self.__fee

    @property
    def returned(self):
        return self.__returned

    def mark_returned(self):
        self.__returned = True


# ==========================================================
# 7) RentalShop (ตรรกะหลักของระบบทั้งหมด)
# ==========================================================
class RentalShop:
    def __init__(self, name):
        self.__name = name
        self.__costumes = {}
        self.__customers = {}
        self.__rentals = {}
        self.__next_costume_no = 1
        self.__next_customer_no = 1
        self.__next_rental_no = 1

    @property
    def name(self):
        return self.__name

    # ---------- Costume ----------
    def add_costume(self, costume_type, name, size, price_per_day, deposit=0):
        cls = COSTUME_CLASSES[costume_type]
        code = f"C{self.__next_costume_no:03d}"
        self.__next_costume_no += 1
        costume = cls(code, name, size, price_per_day, deposit)
        self.__costumes[code] = costume
        return costume

    def remove_costume(self, code):
        costume = self.__costumes.get(code)
        if costume is None:
            raise ValueError("ไม่พบชุด")
        if not costume.available:
            raise ValueError("ชุดนี้ถูกเช่าอยู่ ลบไม่ได้")
        del self.__costumes[code]

    def search_costumes(self, keyword=""):
        keyword = keyword.strip().lower()
        return [
            c for c in self.__costumes.values()
            if keyword in c.name.lower()
            or keyword in c.category().lower()
            or keyword in c.code.lower()
        ]

    def all_costumes(self):
        return list(self.__costumes.values())

    def available_costumes(self):
        return [c for c in self.__costumes.values() if c.available]

    # ---------- Customer ----------
    def add_customer(self, name, phone):
        cid = f"U{self.__next_customer_no:03d}"
        self.__next_customer_no += 1
        customer = Customer(cid, name, phone)
        self.__customers[cid] = customer
        return customer

    def all_customers(self):
        return list(self.__customers.values())

    # ---------- Rental (เช่า/คืน) ----------
    def rent_costume(self, customer_id, costume_code, days):
        customer = self.__customers.get(customer_id)
        if customer is None:
            raise ValueError("ไม่พบลูกค้า")

        costume = self.__costumes.get(costume_code)
        if costume is None:
            raise ValueError("ไม่พบชุด")
        if not costume.available:
            raise ValueError("ชุดนี้ถูกเช่าอยู่แล้ว")

        days = int(days)
        if days <= 0:
            raise ValueError("จำนวนวันต้องมากกว่า 0")

        # POLYMORPHISM: costume คนละคลาสกัน แต่เรียก method เดียวกัน
        fee = costume.calculate_rental_fee(days)

        rental_id = f"R{self.__next_rental_no:03d}"
        self.__next_rental_no += 1
        rental = Rental(rental_id, customer, costume, days, fee)
        self.__rentals[rental_id] = rental
        costume.mark_rented()
        return rental

    def return_costume(self, rental_id):
        rental = self.__rentals.get(rental_id)
        if rental is None:
            raise ValueError("ไม่พบรายการเช่านี้")
        if rental.returned:
            raise ValueError("รายการนี้คืนไปแล้ว")
        rental.mark_returned()
        rental.costume.mark_returned()
        return rental

    def all_rentals(self):
        return list(self.__rentals.values())


# ==========================================================
# 8) ส่วนหน้าจอ Streamlit
# ==========================================================
st.set_page_config(page_title="ระบบร้านเช่าชุด", page_icon="👗", layout="wide")

# เก็บ RentalShop ไว้ใน session_state เพื่อให้ข้อมูลไม่หายตอน Streamlit รันซ้ำ
if "shop" not in st.session_state:
    st.session_state.shop = RentalShop("ร้านเช่าชุดสวยดี")
shop: RentalShop = st.session_state.shop

# ---------- ธีมสี (ขาว-ดำ-เหลี่ยม ให้เข้าชุดกับเวอร์ชันเว็บ) ----------
st.markdown(
    """
    <style>
    .stApp { background-color: #f4f3f0; }
    div[data-testid="stHeader"] { background-color: transparent; }
    h1, h2, h3 { font-weight: 800 !important; }
    .stButton>button {
        background-color: #111111; color: #ffffff; border-radius: 0;
        border: 1px solid #111111; font-weight: 700;
    }
    .stButton>button:hover { background-color: #3a3a3a; color: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("👗 ระบบร้านเช่าชุด")
st.caption("Costume Rental Shop Management System · OOP Mini Project · Streamlit")

tab_costume, tab_customer, tab_rental = st.tabs(["คลังชุด", "ลูกค้า", "เช่า / คืนชุด"])


def costumes_dataframe(costumes):
    return pd.DataFrame([
        {
            "รหัส": c.code, "ประเภท": c.category(), "ชื่อชุด": c.name,
            "ขนาด": c.size, "ราคา/วัน": c.price_per_day, "มัดจำ": c.deposit,
            "สถานะ": "ว่าง" if c.available else "ถูกเช่าอยู่",
        }
        for c in costumes
    ])


# ---------------- แท็บ: คลังชุด ----------------
with tab_costume:
    with st.form("add_costume_form", clear_on_submit=True):
        st.subheader("เพิ่มชุดใหม่")
        c1, c2, c3, c4, c5 = st.columns(5)
        costume_type = c1.selectbox("ประเภท", list(COSTUME_CLASSES.keys()))
        name = c2.text_input("ชื่อชุด")
        size = c3.text_input("ขนาด")
        price = c4.number_input("ราคา/วัน", min_value=0.0, step=50.0)
        deposit = c5.number_input("มัดจำ", min_value=0.0, step=100.0)
        submitted = st.form_submit_button("+ เพิ่มชุด")
        if submitted:
            try:
                if not name or not size:
                    raise ValueError("กรอกชื่อและขนาดให้ครบ")
                shop.add_costume(costume_type, name, size, price, deposit)
                st.success("เพิ่มชุดสำเร็จ")
            except ValueError as e:
                st.error(str(e))

    keyword = st.text_input("ค้นหาชื่อ / ประเภท / รหัสชุด", key="search_costume")
    costumes = shop.search_costumes(keyword) if keyword else shop.all_costumes()
    st.dataframe(costumes_dataframe(costumes), width='stretch', hide_index=True)

    if costumes:
        codes = [c.code for c in shop.all_costumes() if c.available]
        if codes:
            del_code = st.selectbox("เลือกรหัสชุดที่จะลบ (เฉพาะชุดว่าง)", [""] + codes)
            if st.button("ลบชุดที่เลือก") and del_code:
                try:
                    shop.remove_costume(del_code)
                    st.success(f"ลบชุด {del_code} แล้ว")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


# ---------------- แท็บ: ลูกค้า ----------------
with tab_customer:
    with st.form("add_customer_form", clear_on_submit=True):
        st.subheader("เพิ่มลูกค้า")
        c1, c2 = st.columns(2)
        cust_name = c1.text_input("ชื่อ")
        cust_phone = c2.text_input("เบอร์โทร")
        submitted = st.form_submit_button("+ เพิ่มลูกค้า")
        if submitted:
            if not cust_name or not cust_phone:
                st.error("กรอกชื่อและเบอร์โทรให้ครบ")
            else:
                shop.add_customer(cust_name, cust_phone)
                st.success("เพิ่มลูกค้าสำเร็จ")

    customers_df = pd.DataFrame([
        {"รหัสลูกค้า": c.customer_id, "ชื่อ": c.name, "เบอร์โทร": c.phone}
        for c in shop.all_customers()
    ])
    st.dataframe(customers_df, width='stretch', hide_index=True)


# ---------------- แท็บ: เช่า / คืนชุด ----------------
with tab_rental:
    st.subheader("ทำรายการเช่าชุด")
    customer_options = {f"{c.customer_id} - {c.name}": c.customer_id for c in shop.all_customers()}
    costume_options = {f"{c.code} - {c.name} ({c.category()})": c.code for c in shop.available_costumes()}

    with st.form("rent_form"):
        c1, c2, c3 = st.columns(3)
        customer_label = c1.selectbox("ลูกค้า", [""] + list(customer_options.keys()))
        costume_label = c2.selectbox("ชุด (เฉพาะที่ว่าง)", [""] + list(costume_options.keys()))
        days = c3.number_input("จำนวนวัน", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("ยืนยันเช่า")
        if submitted:
            try:
                if not customer_label or not costume_label:
                    raise ValueError("กรุณาเลือกลูกค้าและชุด")
                rental = shop.rent_costume(
                    customer_options[customer_label], costume_options[costume_label], days
                )
                st.success(
                    f"{rental.rental_id}: {rental.customer.name} เช่า {rental.costume.name} "
                    f"{rental.days} วัน = {rental.fee:.0f} บาท"
                )
            except ValueError as e:
                st.error(str(e))

    st.divider()
    rentals = shop.all_rentals()
    rentals_df = pd.DataFrame([
        {
            "รหัสเช่า": r.rental_id, "ลูกค้า": r.customer.name, "ชุด": r.costume.name,
            "จำนวนวัน": r.days, "ค่าเช่า": r.fee,
            "สถานะ": "คืนแล้ว" if r.returned else "กำลังเช่า",
        }
        for r in rentals
    ])
    st.dataframe(rentals_df, width='stretch', hide_index=True)

    active_ids = [r.rental_id for r in rentals if not r.returned]
    if active_ids:
        return_id = st.selectbox("เลือกรหัสเช่าที่จะคืน", [""] + active_ids)
        if st.button("คืนชุด") and return_id:
            try:
                shop.return_costume(return_id)
                st.success(f"คืนชุดของรายการ {return_id} แล้ว")
                st.rerun()
            except ValueError as e:
                st.error(str(e))