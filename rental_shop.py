"""
ระบบร้านเช่าชุด (Costume Rental Shop Management System)
Mini Project - OOP
เวอร์ชัน Streamlit (เว็บแอปที่เขียนด้วย Python ล้วน ไม่ต้องเขียน HTML/CSS/JS เอง)

วิธีรัน:
    pip install streamlit
    streamlit run costume_rental_streamlit.py

ข้อมูลถูกเก็บถาวรใน SQLite (ไฟล์ shop.db ที่จะถูกสร้างขึ้นในโฟลเดอร์เดียวกับไฟล์นี้)
ปิดแอปแล้วเปิดใหม่ ข้อมูลชุด/ลูกค้า/ประวัติการเช่าจะยังอยู่ครบ

สรุปตำแหน่งหลักการ OOP (ใช้พูดตอน present ได้เลย):
- Encapsulation : Costume.__code, __price_per_day ฯลฯ (private) เข้าถึงผ่าน property/setter
- Inheritance   : WeddingCostume, ThaiCostume, PartyCostume สืบทอดจาก Costume (abstract base)
- Polymorphism  : costume.calculate_rental_fee(days) และ costume.category()
                  ถูก override ต่างกันในแต่ละคลาสลูก แต่เรียกผ่าน interface เดียวกัน
                  (ดูจุดเรียกใช้จริงใน RentalShop.rent_costume)
- Persistence   : คลาส Database (แยกหน้าที่จัดการ SQLite ต่างหาก) ถูกเรียกใช้จาก
                  RentalShop ทุกจุดที่ข้อมูลเปลี่ยน (add/remove/rent/return/edit)
"""

import os
import sqlite3
from abc import ABC, abstractmethod

import streamlit as st
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.db")



class Costume(ABC):
    def __init__(self, code, name, size, price_per_day, deposit=0, available=True):
        self.__code = code
        self.__name = name
        self.__size = size
        self.__price_per_day = float(price_per_day)
        self.__deposit = float(deposit)
        self.__available = bool(available)

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



class WeddingCostume(Costume):
    def category(self):
        return "ชุดแต่งงาน"

    def calculate_rental_fee(self, days):
        return self.price_per_day * days



class ThaiCostume(Costume):
    def category(self):
        return "ชุดไทย"

    def calculate_rental_fee(self, days):
        total = self.price_per_day * days
        if days >= 3:
            total *= 0.90  # ลด 10% ถ้าเช่า >= 3 วัน
        return total


class PartyCostume(Costume):
    def category(self):
        return "ชุดปาร์ตี้"

    def calculate_rental_fee(self, days):
        if days <= 0:
            return 0
        return self.price_per_day + (days - 1) * self.price_per_day * 0.5  # วันถัดไปครึ่งราคา


class CustomCostume(Costume):
    def __init__(self, code, name, size, price_per_day, deposit=0, category_name="ชุดอื่นๆ", available=True):
        super().__init__(code, name, size, price_per_day, deposit, available)
        self.__category_name = category_name

    def category(self):
        return self.__category_name

    def calculate_rental_fee(self, days):
        return self.price_per_day * days


COSTUME_CLASSES = {
    "ชุดแต่งงาน": WeddingCostume,
    "ชุดไทย": ThaiCostume,
    "ชุดปาร์ตี้": PartyCostume,
}


def build_costume(code, category, name, size, price_per_day, deposit, available=True):
    """โรงงานสร้าง Costume ที่ถูกคลาส จาก category ที่เก็บไว้ (ใช้ทั้งตอนสร้างใหม่และตอนโหลดจาก DB)"""
    cls = COSTUME_CLASSES.get(category)
    if cls is not None:
        return cls(code, name, size, price_per_day, deposit, available)
    return CustomCostume(code, name, size, price_per_day, deposit, category_name=category, available=available)



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


class Rental:
    def __init__(self, rental_id, customer, costume, days, fee, returned=False):
        self.__rental_id = rental_id
        self.__customer = customer
        self.__costume = costume
        self.__days = days
        self.__fee = fee
        self.__returned = returned

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


class Database:
    def __init__(self, path=DB_PATH):
        self.__conn = sqlite3.connect(path, check_same_thread=False)
        self.__conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        self.__conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS costumes (
                code TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                size TEXT NOT NULL,
                price_per_day REAL NOT NULL,
                deposit REAL NOT NULL,
                available INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rentals (
                rental_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                costume_code TEXT NOT NULL,
                days INTEGER NOT NULL,
                fee REAL NOT NULL,
                returned INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self.__conn.commit()


    def is_seeded(self):
        row = self.__conn.execute("SELECT value FROM meta WHERE key='seeded'").fetchone()
        return row is not None

    def mark_seeded(self):
        self.__conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', '1')")
        self.__conn.commit()

    
    def fetch_costumes(self):
        return self.__conn.execute(
            "SELECT code, category, name, size, price_per_day, deposit, available FROM costumes ORDER BY code"
        ).fetchall()

    def upsert_costume(self, costume):
        self.__conn.execute(
            "INSERT OR REPLACE INTO costumes (code, category, name, size, price_per_day, deposit, available) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                costume.code, costume.category(), costume.name, costume.size,
                costume.price_per_day, costume.deposit, int(costume.available),
            ),
        )
        self.__conn.commit()

    def delete_costume(self, code):
        self.__conn.execute("DELETE FROM costumes WHERE code=?", (code,))
        self.__conn.commit()

   
    def fetch_customers(self):
        return self.__conn.execute(
            "SELECT customer_id, name, phone FROM customers ORDER BY customer_id"
        ).fetchall()

    def upsert_customer(self, customer):
        self.__conn.execute(
            "INSERT OR REPLACE INTO customers (customer_id, name, phone) VALUES (?, ?, ?)",
            (customer.customer_id, customer.name, customer.phone),
        )
        self.__conn.commit()

    def delete_customer(self, customer_id):
        self.__conn.execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))
        self.__conn.commit()

  
    def fetch_rentals(self):
        return self.__conn.execute(
            "SELECT rental_id, customer_id, costume_code, days, fee, returned FROM rentals ORDER BY rental_id"
        ).fetchall()

    def upsert_rental(self, rental):
        self.__conn.execute(
            "INSERT OR REPLACE INTO rentals (rental_id, customer_id, costume_code, days, fee, returned) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                rental.rental_id, rental.customer.customer_id, rental.costume.code,
                rental.days, rental.fee, int(rental.returned),
            ),
        )
        self.__conn.commit()


class RentalShop:
    def __init__(self, name, db: Database):
        self.__name = name
        self.__db = db
        self.__costumes = {}
        self.__customers = {}
        self.__rentals = {}
        self.__next_costume_no = 1
        self.__next_customer_no = 1
        self.__next_rental_no = 1
        self._load_from_db()

    @property
    def name(self):
        return self.__name

  
    def _load_from_db(self):
        for code, category, name, size, price, deposit, available in self.__db.fetch_costumes():
            costume = build_costume(code, category, name, size, price, deposit, bool(available))
            self.__costumes[code] = costume
            self.__next_costume_no = max(self.__next_costume_no, int(code[1:]) + 1)

        for customer_id, name, phone in self.__db.fetch_customers():
            self.__customers[customer_id] = Customer(customer_id, name, phone)
            self.__next_customer_no = max(self.__next_customer_no, int(customer_id[1:]) + 1)

        for rental_id, customer_id, costume_code, days, fee, returned in self.__db.fetch_rentals():
            customer = self.__customers.get(customer_id)
            costume = self.__costumes.get(costume_code)
            if customer is None or costume is None:
                continue  
            self.__rentals[rental_id] = Rental(rental_id, customer, costume, days, fee, bool(returned))
            self.__next_rental_no = max(self.__next_rental_no, int(rental_id[1:]) + 1)

    def custom_categories(self):
        """ประเภทชุดที่ผู้ใช้พิมพ์เพิ่มเอง (ไม่ใช่ 3 ประเภทหลัก) เอาไว้เติมดรอปดาวน์ตอนเปิดแอป"""
        seen = []
        for c in self.__costumes.values():
            cat = c.category()
            if cat not in COSTUME_CLASSES and cat not in seen:
                seen.append(cat)
        return seen

    def add_costume(self, costume_type, name, size, price_per_day, deposit=0):
        code = f"C{self.__next_costume_no:03d}"
        self.__next_costume_no += 1
        costume = build_costume(code, costume_type, name, size, price_per_day, deposit)
        self.__costumes[code] = costume
        self.__db.upsert_costume(costume)  
        return costume

    def persist_costume(self, costume):
        """ใช้เมื่อแก้ไขข้อมูลชุดที่มีอยู่แล้ว (ผ่าน property setter) แล้วต้องการบันทึกลง SQLite"""
        self.__db.upsert_costume(costume)

    def remove_costume(self, code):
        costume = self.__costumes.get(code)
        if costume is None:
            raise ValueError("ไม่พบชุด")
        if not costume.available:
            raise ValueError("ชุดนี้ถูกเช่าอยู่ ลบไม่ได้")
        del self.__costumes[code]
        self.__db.delete_costume(code)

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

  
    def add_customer(self, name, phone):
        cid = f"U{self.__next_customer_no:03d}"
        self.__next_customer_no += 1
        customer = Customer(cid, name, phone)
        self.__customers[cid] = customer
        self.__db.upsert_customer(customer)
        return customer

    def all_customers(self):
        return list(self.__customers.values())

    def search_customers(self, keyword=""):
        keyword = keyword.strip().lower()
        return [
            c for c in self.__customers.values()
            if keyword in c.name.lower() or keyword in c.phone.lower() or keyword in c.customer_id.lower()
        ]

    def remove_customer(self, customer_id):
        customer = self.__customers.get(customer_id)
        if customer is None:
            raise ValueError("ไม่พบลูกค้า")
        has_active_rental = any(
            r.customer.customer_id == customer_id and not r.returned
            for r in self.__rentals.values()
        )
        if has_active_rental:
            raise ValueError("ลูกค้ายังมีชุดที่เช่าอยู่ ลบไม่ได้")
        del self.__customers[customer_id]
        self.__db.delete_customer(customer_id)

    
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

        fee = costume.calculate_rental_fee(days)

        rental_id = f"R{self.__next_rental_no:03d}"
        self.__next_rental_no += 1
        rental = Rental(rental_id, customer, costume, days, fee)
        self.__rentals[rental_id] = rental
        costume.mark_rented()

        self.__db.upsert_rental(rental)
        self.__db.upsert_costume(costume) 
        return rental

    def return_costume(self, rental_id):
        rental = self.__rentals.get(rental_id)
        if rental is None:
            raise ValueError("ไม่พบรายการเช่านี้")
        if rental.returned:
            raise ValueError("รายการนี้คืนไปแล้ว")
        rental.mark_returned()
        rental.costume.mark_returned()

        self.__db.upsert_rental(rental)
        self.__db.upsert_costume(rental.costume) 
        return rental

    def all_rentals(self):
        return list(self.__rentals.values())


def seed_shop(shop: "RentalShop") -> None:
    """เติมข้อมูลตัวอย่าง: ชุด 6 ชิ้น, ลูกค้า 3 คน, ประวัติการเช่า 3 รายการ
    เรียกผ่านเมธอดจริงของ RentalShop ทุกจุด (ไม่ยัดข้อมูลตรงๆ) เพื่อให้ผ่านการ
    ตรวจสอบ/คำนวณเดียวกับตอนผู้ใช้กรอกฟอร์มเป๊ะ ๆ และให้ผลตรงกับเวอร์ชันเว็บ
    เรียกครั้งเดียวตอนฐานข้อมูลยังไม่มีข้อมูลเลยเท่านั้น (ดู is_seeded ในส่วน main)"""
    w1 = shop.add_costume("ชุดแต่งงาน", "ชุดเจ้าสาวขาวลูกไม้", "M", 1800, 3000)
    shop.add_costume("ชุดแต่งงาน", "ชุดเจ้าบ่าวสูทกรมท่า", "L", 1500, 2500)
    shop.add_costume("ชุดไทย", "ชุดไทยจักรีสีทอง", "S", 900, 1000)
    shop.add_costume("ชุดไทย", "ชุดไทยศรีอยุธยาสีชมพู", "M", 850, 1000)
    shop.add_costume("ชุดปาร์ตี้", "ชุดปาร์ตี้เซคควินแดง", "M", 500, 0)
    shop.add_costume("ชุดปาร์ตี้", "ชุดฮาโลวีนแม่มด", "L", 450, 0)

    u1 = shop.add_customer("สมชาย ใจดี", "0891234567")
    u2 = shop.add_customer("วรรณา สุขใจ", "0898765432")
    u3 = shop.add_customer("ธนกร มั่งมี", "0812223333")

    shop.rent_costume(u1.customer_id, "C002", 2)      
    shop.rent_costume(u2.customer_id, "C006", 1)      
    r3 = shop.rent_costume(u3.customer_id, w1.code, 3) 
    shop.return_costume(r3.rental_id)                 



st.set_page_config(page_title="ระบบร้านเช่าชุด", layout="wide")


if "shop" not in st.session_state:
    db = Database()
    shop = RentalShop("ร้านเช่าชุดสวยดี", db)
    if not db.is_seeded():
        
        seed_shop(shop)
        db.mark_seeded()
    st.session_state.shop = shop
shop: RentalShop = st.session_state.shop

CUSTOM_CSS = (
    "<style>"
    ":root{--ink:#201126;--ink-soft:#3a2440;--paper:#faf8fb;--card:#ffffff;--accent:#b3435f;--accent-hover:#94324a;--gold:#caa14b;--muted:#7a7182;--line:#e6dfec;}"
    "html,body,[class*='css']{font-family:'Prompt',sans-serif;color:#241a2b;}"
    ".stApp{background-color:var(--paper);}"
    "div[data-testid='stHeader']{background-color:transparent;}"
    "div[data-testid='stMainBlockContainer']{padding-top:2rem;}"
    "h1{font-family:'Playfair Display',serif;font-weight:700 !important;color:var(--ink);}"
    "h2,h3{font-family:'Playfair Display',serif;font-weight:600 !important;color:var(--ink);}"
    "[data-testid='stCaptionContainer']{letter-spacing:1px;font-size:13px !important;color:var(--muted) !important;font-style:italic;}"
    "button[data-baseweb='tab']{font-family:'Prompt',sans-serif;font-weight:600;font-size:15px;color:var(--muted);padding:0 6px 12px 6px !important;}"
    "button[data-baseweb='tab'][aria-selected='true']{color:var(--accent) !important;font-weight:700;}"
    "div[data-baseweb='tab-highlight']{background-color:var(--accent) !important;height:3px !important;border-radius:3px;}"
    "div[data-baseweb='tab-border']{background-color:var(--line) !important;}"
    ".stButton>button,.stFormSubmitButton>button{background-color:var(--accent);color:#ffffff;border-radius:10px;border:1px solid var(--accent);font-weight:600;letter-spacing:0.2px;padding:0.55rem 1.5rem;box-shadow:0 2px 8px rgba(179,67,95,0.25);}"
    ".stButton>button:hover,.stFormSubmitButton>button:hover{background-color:var(--accent-hover);border-color:var(--accent-hover);box-shadow:0 4px 12px rgba(179,67,95,0.35);}"
    ".stTextInput input,.stNumberInput input,div[data-baseweb='select']>div{border-radius:8px !important;border:1px solid var(--line) !important;font-family:'Prompt',sans-serif;}"
    ".stTextInput input:focus,.stNumberInput input:focus{border-color:var(--accent) !important;box-shadow:0 0 0 1px var(--accent) !important;}"
    ".stTextInput label,.stNumberInput label,.stSelectbox label{font-size:12px !important;font-weight:600 !important;letter-spacing:0.3px;color:var(--muted) !important;}"
    "div[data-testid='stForm']{border:none;border-radius:0;padding:0;background-color:transparent;box-shadow:none;}"
    "div[data-testid='stVerticalBlockBorderWrapper']>div>div[data-testid='stVerticalBlock']{border:1px solid var(--line);border-radius:16px;padding:1.8rem 1.8rem 1.4rem;background-color:var(--card);box-shadow:0 4px 18px rgba(32,17,38,0.06);}"
    "div[data-testid='stAlert']{border-radius:10px;border:1px solid var(--line);background-color:var(--card) !important;}"
    "div[data-testid='stAlert'] p{color:var(--ink) !important;font-weight:500;}"
    "hr{border-color:var(--line) !important;}"
    ".hero{background:linear-gradient(135deg,var(--ink) 0%,var(--ink-soft) 100%);color:#ffffff;padding:2.6rem 2.8rem;margin-bottom:2.2rem;border-radius:20px;box-shadow:0 12px 32px rgba(32,17,38,0.25);}"
    ".hero-mark{display:flex;align-items:center;gap:10px;margin-bottom:1.4rem;}"
    ".hero-mark-text{font-family:'Prompt',sans-serif;font-weight:600;letter-spacing:2px;font-size:12px;text-transform:uppercase;color:var(--gold);}"
    ".hero-eyebrow{letter-spacing:2px;font-size:12px;color:#c9b8d1;margin-bottom:10px;font-style:italic;}"
    ".hero-title{font-family:'Playfair Display',serif;font-weight:700;font-size:2.4rem;line-height:1.25;margin:0 0 .8rem;}"
    ".hero-sub{color:#d8cee0;font-size:15px;max-width:600px;margin:0 0 1.8rem;line-height:1.7;font-weight:300;}"
    ".spec-bar{display:flex;border-top:1px solid rgba(255,255,255,0.15);flex-wrap:wrap;padding-top:1.4rem;}"
    ".spec-item{flex:1;min-width:140px;padding:0 1.4rem;border-right:1px solid rgba(255,255,255,0.15);}"
    ".spec-item:first-child{padding-left:0;}"
    ".spec-item:last-child{border-right:none;}"
    ".spec-label{letter-spacing:0.5px;font-size:11px;color:#b8abc0;margin-bottom:6px;}"
    ".spec-value{font-family:'Playfair Display',serif;font-weight:700;font-size:1.7rem;color:var(--gold);}"
    ".spec-sub{font-size:11px;color:#9a8ea3;margin-top:2px;}"
    "</style>"
)

GOOGLE_FONT_LINK = (
    "<link rel='preconnect' href='https://fonts.googleapis.com'>"
    "<link href='https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap' rel='stylesheet'>"
)
st.markdown(GOOGLE_FONT_LINK + CUSTOM_CSS, unsafe_allow_html=True)


_total_costumes = len(shop.all_costumes())
_available = len(shop.available_costumes())
_rented = _total_costumes - _available
_total_customers = len(shop.all_customers())
_active_rentals = len([r for r in shop.all_rentals() if not r.returned])

HANGER_ICON = (
    "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='white' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
    "<path d='M12 3a2 2 0 1 1 2 2c0 1-2 2-2 3'/><path d='M12 8l9 6H3l9-6z'/><path d='M3 20h18'/>"
    "</svg>"
)

HERO_HTML = (
    "<div class='hero'>"
    "<div class='hero-mark'>" + HANGER_ICON + "<span class='hero-mark-text'>COSTUME RENTAL SHOP</span></div>"
    "<div class='hero-title'>จัดการร้านเช่าชุดอย่างเป็นระบบ</div>"
    "<div class='spec-bar'>"
    f"<div class='spec-item'><div class='spec-label'>ชุดทั้งหมด</div><div class='spec-value'>{_total_costumes}</div><div class='spec-sub'>รายการในคลัง</div></div>"
    f"<div class='spec-item'><div class='spec-label'>ชุดว่าง</div><div class='spec-value'>{_available}</div><div class='spec-sub'>พร้อมให้เช่า</div></div>"
    f"<div class='spec-item'><div class='spec-label'>กำลังเช่าอยู่</div><div class='spec-value'>{_rented}</div><div class='spec-sub'>ชุดที่ถูกยืมออก</div></div>"
    f"<div class='spec-item'><div class='spec-label'>ลูกค้า</div><div class='spec-value'>{_total_customers}</div><div class='spec-sub'>คนในระบบ</div></div>"
    f"<div class='spec-item'><div class='spec-label'>รายการเช่าที่ยังไม่คืน</div><div class='spec-value'>{_active_rentals}</div><div class='spec-sub'>ต้องติดตาม</div></div>"
    "</div>"
    "</div>"
)
st.markdown(HERO_HTML, unsafe_allow_html=True)

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



NEW_TYPE_OPTION = "+ เพิ่มประเภทใหม่..."
ss = st.session_state
ss.setdefault("adding_new_type", False)  # True = ดรอปดาวน์อยู่ในโหมดพิมพ์ได้
if "custom_categories" not in ss:
    
    ss.custom_categories = shop.custom_categories()

# เพิ่งเพิ่มชุดด้วยประเภทใหม่ -> กลับไปโหมดปกติ และเลือกประเภทนั้นไว้ให้
# (ต้องตั้งค่านี้ "ก่อน" สร้าง widget เพราะ Streamlit ห้ามแก้ค่า widget หลังสร้างไปแล้ว)
if "pending_type" in ss:
    ss.costume_type_select = ss.pop("pending_type")
    ss.adding_new_type = False
    ss.pop("new_type_select", None)


def _on_type_change():
    # ผู้ใช้เลือก "+ เพิ่มประเภทใหม่..." -> สลับดรอปดาวน์เป็นโหมดพิมพ์ได้
    if ss.costume_type_select == NEW_TYPE_OPTION:
        ss.adding_new_type = True
        ss.costume_type_select = list(COSTUME_CLASSES)[0]


def _cancel_new_type():
    ss.adding_new_type = False
    ss.pop("new_type_select", None)


with tab_costume:
    st.subheader("เพิ่มชุดใหม่")

    with st.container(border=True):
        type_options = list(COSTUME_CLASSES) + ss.custom_categories

        if ss.adding_new_type:
            # โหมดพิมพ์ได้: accept_new_options=True ให้พิมพ์ค่าใหม่ลงในดรอปดาวน์ได้เลย
            tcol, bcol = st.columns([5, 1], vertical_alignment="bottom")
            costume_type = tcol.selectbox(
                "ประเภท (พิมพ์ชื่อประเภทใหม่แล้วกด Enter)",
                type_options,
                index=None,
                placeholder="พิมพ์ชื่อประเภทใหม่ เช่น ชุดนักเรียน, ชุดราตรี",
                accept_new_options=True,
                key="new_type_select",
            )
            bcol.button("ยกเลิก", on_click=_cancel_new_type)
        else:
            costume_type = st.selectbox(
                "ประเภท",
                type_options + [NEW_TYPE_OPTION],
                key="costume_type_select",
                on_change=_on_type_change,
            )

        # ข้อความสำเร็จที่ฝากไว้ก่อน st.rerun()
        if "costume_msg" in ss:
            st.success(ss.pop("costume_msg"))

        with st.form("add_costume_form", clear_on_submit=True, border=False):
            c2, c3, c4, c5 = st.columns(4)
            name = c2.text_input("ชื่อชุด")
            size = c3.text_input("ขนาด")
            price = c4.number_input("ราคา/วัน", min_value=0.0, step=50.0)
            deposit = c5.number_input("มัดจำ", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("เพิ่มชุด")
            if submitted:
                try:
                    if not name or not size:
                        raise ValueError("กรอกชื่อและขนาดให้ครบ")
                    final_type = (costume_type or "").strip()
                    if not final_type or final_type == NEW_TYPE_OPTION:
                        raise ValueError("พิมพ์ชื่อประเภทใหม่ในช่องประเภท แล้วกด Enter ก่อน")

                    shop.add_costume(final_type, name, size, price, deposit)  # บันทึกลง SQLite ในตัวแล้ว

                    # ประเภทใหม่ -> เพิ่มเข้าไปในดรอปดาวน์
                    if final_type not in COSTUME_CLASSES and final_type not in ss.custom_categories:
                        ss.custom_categories.append(final_type)

                    ss.pending_type = final_type
                    ss.costume_msg = f"เพิ่มชุดสำเร็จ (ประเภท: {final_type})"
                    st.rerun()
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
                    shop.remove_costume(del_code)  # ลบออกจาก SQLite ในตัวแล้ว
                    st.success(f"ลบชุด {del_code} แล้ว")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    # ---- แก้ไขชุดที่มีอยู่แล้ว (แก้ได้แม้กำลังถูกเช่าอยู่ เช่น แก้ราคา/ชื่อที่พิมพ์ผิด) ----
    with st.expander("แก้ไขชุดที่มีอยู่แล้ว"):
        all_codes = [c.code for c in shop.all_costumes()]
        edit_code = st.selectbox("เลือกรหัสชุดที่จะแก้ไข", [""] + all_codes, key="edit_costume_select")
        if edit_code:
            costume_obj = next(c for c in shop.all_costumes() if c.code == edit_code)
            with st.form(f"edit_costume_form_{edit_code}"):
                ec1, ec2, ec3, ec4 = st.columns(4)
                new_name = ec1.text_input("ชื่อชุด", value=costume_obj.name)
                new_size = ec2.text_input("ขนาด", value=costume_obj.size)
                new_price = ec3.number_input("ราคา/วัน", min_value=0.0, step=50.0, value=costume_obj.price_per_day)
                new_deposit = ec4.number_input("มัดจำ", min_value=0.0, step=100.0, value=costume_obj.deposit)
                if st.form_submit_button("บันทึกการแก้ไข"):
                    try:
                        # ใช้ setter ของคลาส Costume ตรงๆ (มี validation อยู่แล้ว เช่น ราคาห้ามติดลบ)
                        costume_obj.name = new_name
                        costume_obj.size = new_size
                        costume_obj.price_per_day = new_price
                        costume_obj.deposit = new_deposit
                        shop.persist_costume(costume_obj)  # บันทึกการแก้ไขลง SQLite
                        st.success(f"แก้ไขชุด {edit_code} สำเร็จ")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))


# ---------------- แท็บ: ลูกค้า ----------------
with tab_customer:
    with st.form("add_customer_form", clear_on_submit=True):
        st.subheader("เพิ่มลูกค้า")
        c1, c2 = st.columns(2)
        cust_name = c1.text_input("ชื่อ")
        cust_phone = c2.text_input("เบอร์โทร", placeholder="0891234567", max_chars=10)
        submitted = st.form_submit_button("เพิ่มลูกค้า")
        if submitted:
            if not cust_name or not cust_phone:
                st.error("กรอกชื่อและเบอร์โทรให้ครบ")
            elif not cust_phone.isdigit() or len(cust_phone) != 10:
                st.error("เบอร์โทรต้องเป็นตัวเลข 10 หลักเท่านั้น เช่น 0891234567")
            else:
                shop.add_customer(cust_name, cust_phone)  # บันทึกลง SQLite ในตัวแล้ว
                st.success("เพิ่มลูกค้าสำเร็จ")

    cust_keyword = st.text_input("ค้นหาชื่อ / เบอร์โทร / รหัสลูกค้า", key="search_customer")
    filtered_customers = shop.search_customers(cust_keyword) if cust_keyword else shop.all_customers()

    customers_df = pd.DataFrame([
        {"รหัสลูกค้า": c.customer_id, "ชื่อ": c.name, "เบอร์โทร": c.phone}
        for c in filtered_customers
    ])
    st.dataframe(customers_df, width='stretch', hide_index=True)

    if filtered_customers:
        cust_codes = [c.customer_id for c in filtered_customers]
        del_cust_id = st.selectbox("เลือกรหัสลูกค้าที่จะลบ", [""] + cust_codes)
        if st.button("ลบลูกค้าที่เลือก") and del_cust_id:
            try:
                shop.remove_customer(del_cust_id)  # ลบออกจาก SQLite ในตัวแล้ว
                st.success(f"ลบลูกค้า {del_cust_id} แล้ว")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


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
                rental = shop.rent_costume(  # บันทึกลง SQLite ในตัวแล้ว
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
                shop.return_costume(return_id)  # บันทึกลง SQLite ในตัวแล้ว
                st.success(f"คืนชุดของรายการ {return_id} แล้ว")
                st.rerun()
            except ValueError as e:
                st.error(str(e))