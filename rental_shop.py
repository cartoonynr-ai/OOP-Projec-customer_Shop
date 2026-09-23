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


# ==========================================================
# 1) Costume (Abstract base class)
# ==========================================================
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


# ==========================================================
# 4.5) CustomCostume (Inheritance + Polymorphism)
# รองรับ "ประเภทชุด" ที่ผู้ใช้พิมพ์เพิ่มเองนอกเหนือ 3 ประเภทหลัก
# ใช้สูตรราคามาตรฐาน (ไม่มีส่วนลด/โปรโมชันพิเศษแบบ 3 คลาสด้านบน)
# ==========================================================
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

    @name.setter
    def name(self, value):
        if not value:
            raise ValueError("ชื่อลูกค้าห้ามว่าง")
        self.__name = value

    @property
    def phone(self):
        return self.__phone

    @phone.setter
    def phone(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("เบอร์โทรต้องเป็นตัวเลข 10 หลักเท่านั้น เช่น 0891234567")
        self.__phone = value


# ==========================================================
# 6) Rental (1 รายการเช่า)
# ==========================================================
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


# ==========================================================
# 7) Database (SQLite persistence layer)
# แยกหน้าที่ "คุยกับ SQLite" ออกจาก RentalShop โดยเฉพาะ
# RentalShop ไม่รู้เรื่อง SQL เลย แค่เรียก method ของ Database เป็น CRUD ธรรมดา
# ==========================================================
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

    # ---------- meta (ใช้เช็คว่าเคยเติมข้อมูลตัวอย่างไปแล้วหรือยัง) ----------
    def is_seeded(self):
        row = self.__conn.execute("SELECT value FROM meta WHERE key='seeded'").fetchone()
        return row is not None

    def mark_seeded(self):
        self.__conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', '1')")
        self.__conn.commit()

    # ---------- costumes ----------
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

    # ---------- customers ----------
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

    # ---------- rentals ----------
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


# ==========================================================
# 8) RentalShop (ตรรกะหลักของระบบทั้งหมด)
# ทุก method ที่ทำให้ข้อมูลเปลี่ยน จะเรียก self.__db ให้บันทึกลง SQLite ทันที
# ==========================================================
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

    # ---------- โหลดข้อมูลเดิมจาก SQLite ตอนเปิดแอป ----------
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
                continue  # ข้อมูลกำพร้า (ถูกลบไปแล้ว) -> ข้าม
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

    # ---------- Costume ----------
    def add_costume(self, costume_type, name, size, price_per_day, deposit=0):
        code = f"C{self.__next_costume_no:03d}"
        self.__next_costume_no += 1
        costume = build_costume(code, costume_type, name, size, price_per_day, deposit)
        self.__costumes[code] = costume
        self.__db.upsert_costume(costume)  # บันทึกลง SQLite ทันที
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

    # ---------- Customer ----------
    def add_customer(self, name, phone):
        cid = f"U{self.__next_customer_no:03d}"
        self.__next_customer_no += 1
        customer = Customer(cid, name, phone)
        self.__customers[cid] = customer
        self.__db.upsert_customer(customer)
        return customer

    def persist_customer(self, customer):
        """ใช้เมื่อแก้ไขข้อมูลลูกค้าที่มีอยู่แล้ว (ผ่าน property setter) แล้วต้องการบันทึกลง SQLite"""
        self.__db.upsert_customer(customer)

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

        self.__db.upsert_rental(rental)
        self.__db.upsert_costume(costume)  # อัปเดตสถานะ available=False ลง SQLite
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
        self.__db.upsert_costume(rental.costume)  # อัปเดตสถานะ available=True ลง SQLite
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

    shop.rent_costume(u1.customer_id, "C002", 2)      # กำลังเช่าอยู่
    shop.rent_costume(u2.customer_id, "C006", 1)       # กำลังเช่าอยู่
    r3 = shop.rent_costume(u3.customer_id, w1.code, 3)  # จะคืนด้านล่าง
    shop.return_costume(r3.rental_id)                  # คืนแล้ว (โชว์ประวัติ)


# ==========================================================
# 9) ส่วนหน้าจอ Streamlit
# ==========================================================
st.set_page_config(page_title="ระบบร้านเช่าชุด", layout="wide")

# เก็บ RentalShop ไว้ใน session_state เพื่อให้ข้อมูลไม่หายตอน Streamlit รันซ้ำ
# ข้อมูลจริงอยู่ใน SQLite (shop.db) แล้ว -> ปิด/เปิดแอปใหม่ หรือรีสตาร์ทเซิร์ฟเวอร์ ข้อมูลก็ยังอยู่
if "shop" not in st.session_state:
    db = Database()
    shop = RentalShop("ร้านเช่าชุดสวยดี", db)
    if not db.is_seeded():
        # เปิดแอปครั้งแรกสุด (ยังไม่มีไฟล์ shop.db มาก่อน) -> เติมข้อมูลตัวอย่างให้อัตโนมัติ
        seed_shop(shop)
        db.mark_seeded()
    st.session_state.shop = shop
shop: RentalShop = st.session_state.shop

# ---------- Modern colorful UI theme ----------
CUSTOM_CSS = (
    "<style>"
    ":root{--ink:#182033;--muted:#667085;--line:#e4e7ec;--card:#ffffff;--indigo:#5b5ce2;--indigo-dark:#4444c7;--violet:#8b5cf6;--pink:#ec4899;--cyan:#06b6d4;--teal:#14b8a6;--green:#22a06b;--amber:#f59e0b;--red:#dc4c64;--shadow:0 12px 34px rgba(38,45,77,.09);}"
    "html,body,[class*='css']{font-family:'Noto Sans Thai','Prompt',sans-serif;color:var(--ink);}"
    ".stApp{background:radial-gradient(circle at 8% 2%,rgba(139,92,246,.16),transparent 30%),radial-gradient(circle at 92% 10%,rgba(6,182,212,.14),transparent 28%),linear-gradient(180deg,#f2f0ff 0,#f8fbff 32%,#f6f7fb 100%);background-attachment:fixed;}"
    "div[data-testid='stHeader']{background:rgba(248,249,253,.78);backdrop-filter:blur(18px);border-bottom:1px solid rgba(228,231,236,.75);}"
    "#MainMenu,footer{visibility:hidden;}"
    "div[data-testid='stMainBlockContainer']{padding-top:1.4rem;padding-bottom:4.5rem;max-width:1360px;}"
    "h1,h2,h3{font-family:'Noto Sans Thai','Prompt',sans-serif;color:var(--ink);letter-spacing:-.025em;}"
    "h3{font-weight:800 !important;font-size:1.18rem !important;margin:.15rem 0 .8rem !important;}"
    "[data-testid='stCaptionContainer']{color:var(--muted) !important;}"

    ".hero{position:relative;overflow:hidden;background:linear-gradient(125deg,#1d2550 0%,#4f46e5 48%,#7c3aed 100%);color:#fff;padding:2.15rem 2.2rem 1.85rem;margin-bottom:1.25rem;border-radius:26px;box-shadow:0 18px 50px rgba(79,70,229,.24);}"
    ".hero:before{content:'';position:absolute;width:280px;height:280px;border-radius:50%;right:-90px;top:-130px;background:rgba(255,255,255,.14);filter:blur(2px);}"
    ".hero:after{content:'';position:absolute;width:190px;height:190px;border-radius:50%;right:180px;bottom:-130px;background:rgba(34,211,238,.18);}"
    ".hero>*{position:relative;z-index:1;}"
    ".hero-mark{display:flex;align-items:center;gap:10px;margin-bottom:.55rem;}"
    ".hero-mark-text{font-size:11px;font-weight:800;letter-spacing:2px;color:#ddd6fe;}"
    ".hero-title{font-family:'Noto Sans Thai','Prompt',sans-serif;font-size:2rem;font-weight:850;line-height:1.35;margin:0 0 1.3rem;color:#fff;letter-spacing:-.035em;}"
    ".spec-bar{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:11px;}"
    ".spec-item{position:relative;overflow:hidden;background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.17);border-radius:15px;padding:1rem 1rem .9rem;backdrop-filter:blur(8px);}"
    ".spec-item:before{content:'';position:absolute;left:0;top:0;width:100%;height:3px;background:#a5b4fc;}"
    ".spec-item:nth-child(2):before{background:#5eead4}.spec-item:nth-child(3):before{background:#fbbf24}.spec-item:nth-child(4):before{background:#67e8f9}.spec-item:nth-child(5):before{background:#f9a8d4}"
    ".spec-label{font-size:11px;font-weight:700;color:#dbe3ff;margin-bottom:6px;}"
    ".spec-value{font-size:1.65rem;font-weight:850;line-height:1;color:#fff;}"
    ".spec-sub{font-size:10.5px;color:#c9d2ff;margin-top:7px;}"

    "div[data-testid='stTabs'] div[data-baseweb='tab-list'],div[data-baseweb='tab-list']{gap:7px;background:rgba(255,255,255,.82);border:1px solid rgba(200,205,222,.95);padding:6px;border-radius:15px;box-shadow:0 8px 24px rgba(48,56,92,.08);margin-bottom:.5rem;}"
    "div[data-testid='stTabs'] button[role='tab'],button[data-baseweb='tab']{font-family:'Noto Sans Thai','Prompt',sans-serif;font-size:14px;font-weight:750;color:#374151 !important;padding:11px 22px !important;border-radius:10px;margin:0 !important;transition:.18s ease;}"
    "div[data-testid='stTabs'] button[role='tab'] p,div[data-testid='stTabs'] button[role='tab'] span,button[data-baseweb='tab'] p,button[data-baseweb='tab'] span{color:#374151 !important;font-weight:750 !important;}"
    "div[data-testid='stTabs'] button[role='tab']:hover,button[data-baseweb='tab']:hover{background:#ede9fe !important;color:#4f46e5 !important;}"
    "div[data-testid='stTabs'] button[role='tab']:hover p,div[data-testid='stTabs'] button[role='tab']:hover span,button[data-baseweb='tab']:hover p,button[data-baseweb='tab']:hover span{color:#4f46e5 !important;}"
    "div[data-testid='stTabs'] button[role='tab'][aria-selected='true'],button[data-baseweb='tab'][aria-selected='true']{background:linear-gradient(135deg,#5b5ce2,#7c3aed) !important;color:#ffffff !important;box-shadow:0 6px 16px rgba(91,92,226,.22);}"
    "div[data-testid='stTabs'] button[role='tab'][aria-selected='true'] p,div[data-testid='stTabs'] button[role='tab'][aria-selected='true'] span,button[data-baseweb='tab'][aria-selected='true'] p,button[data-baseweb='tab'][aria-selected='true'] span{color:#ffffff !important;}"
    "div[data-testid='stTabs'] div[data-baseweb='tab-highlight'],div[data-testid='stTabs'] div[data-baseweb='tab-border'],div[data-baseweb='tab-highlight'],div[data-baseweb='tab-border']{display:none !important;}"

    ".section-head{display:flex;align-items:center;justify-content:space-between;gap:18px;margin:1.45rem 0 .75rem;padding:0 .2rem;}"
    ".section-title-wrap{display:flex;align-items:center;gap:12px;}"
    ".section-accent{width:9px;height:34px;border-radius:10px;background:linear-gradient(180deg,#5b5ce2,#8b5cf6);box-shadow:0 5px 12px rgba(91,92,226,.2);}"
    ".section-head.teal .section-accent{background:linear-gradient(180deg,#06b6d4,#14b8a6)}"
    ".section-head.pink .section-accent{background:linear-gradient(180deg,#ec4899,#8b5cf6)}"
    ".section-title{font-weight:850;font-size:1.12rem;color:var(--ink);line-height:1.25;}"
    ".section-sub{font-size:12px;color:#7b8496;margin-top:3px;}"
    ".section-tag{font-size:11px;font-weight:800;padding:6px 10px;border-radius:999px;background:#eeedff;color:#5956c9;border:1px solid #dcdbff;white-space:nowrap;}"
    ".section-head.teal .section-tag{background:#e9fbf8;color:#0f8f7a;border-color:#c9f2e9}.section-head.pink .section-tag{background:#fff0f7;color:#c43b7a;border-color:#ffd6e9}"

    "div[data-testid='stVerticalBlockBorderWrapper']>div>div[data-testid='stVerticalBlock']{border:1px solid rgba(222,226,237,.96);border-radius:18px;padding:1.35rem 1.4rem 1.2rem;background:rgba(255,255,255,.94);box-shadow:var(--shadow);}"
    "div[data-testid='stForm']{border:1px solid #e1e5ee;border-radius:16px;padding:1.2rem 1.25rem;background:linear-gradient(180deg,#fff 0%,#fcfcff 100%);box-shadow:0 8px 22px rgba(48,56,92,.055);}"
    "div[data-testid='stExpander']{border:1px solid #e1e5ee !important;border-radius:15px !important;overflow:hidden;background:#fff;box-shadow:0 7px 20px rgba(48,56,92,.05);}"
    "div[data-testid='stExpander'] details summary{font-weight:800;color:var(--ink);padding:.2rem .3rem;}"

    ".stTextInput input,.stNumberInput input,div[data-baseweb='select']>div{background:#fff !important;border:1px solid #d7dce7 !important;border-radius:11px !important;min-height:45px;font-family:'Noto Sans Thai','Prompt',sans-serif;box-shadow:0 1px 2px rgba(16,24,40,.02);transition:.15s ease;}"
    ".stTextInput input:hover,.stNumberInput input:hover,div[data-baseweb='select']>div:hover{border-color:#a9adff !important;}"
    ".stTextInput input:focus,.stNumberInput input:focus{border-color:var(--indigo) !important;box-shadow:0 0 0 3px rgba(91,92,226,.12) !important;}"
    ".stTextInput label,.stNumberInput label,.stSelectbox label{font-size:12.5px !important;font-weight:750 !important;color:#50596c !important;}"

    ".stButton>button,.stFormSubmitButton>button{background:linear-gradient(135deg,#5b5ce2,#7056e8);color:#fff;border:0;border-radius:11px;font-family:'Noto Sans Thai','Prompt',sans-serif;font-weight:800;padding:.58rem 1.3rem;min-height:43px;box-shadow:0 6px 16px rgba(91,92,226,.2);transition:.16s ease;}"
    ".stButton>button:hover,.stFormSubmitButton>button:hover{background:linear-gradient(135deg,#4d4ed0,#6545df);color:#fff;transform:translateY(-1px);box-shadow:0 9px 20px rgba(91,92,226,.26);}"
    ".stButton>button:focus,.stFormSubmitButton>button:focus{box-shadow:0 0 0 4px rgba(91,92,226,.14) !important;}"
    "div[data-testid='stAlert']{border-radius:12px;border:1px solid rgba(220,224,234,.9);box-shadow:0 5px 14px rgba(48,56,92,.045);}"
    "div[data-testid='stDataFrame']{background:#fff;border:1px solid #e1e5ee;border-radius:16px;overflow:hidden;box-shadow:0 10px 28px rgba(48,56,92,.065);margin:.35rem 0 1rem;}"
    "hr{border-color:#e2e6ef !important;margin:1.7rem 0 !important;}"
    ".soft-note{background:linear-gradient(135deg,#eeedff,#f5f3ff);border:1px solid #dfddff;border-radius:14px;padding:.8rem 1rem;color:#5a5c7c;font-size:12px;margin:.35rem 0 .8rem;}"

    "/* Robust tab contrast fix for newer Streamlit DOM */"
    "[role='tablist']{gap:8px !important;background:rgba(255,255,255,.94) !important;border:1px solid #d9deea !important;padding:7px !important;border-radius:16px !important;box-shadow:0 8px 24px rgba(48,56,92,.08) !important;}"
    "[role='tab']{background:#f4f5ff !important;border:1px solid #dde1f3 !important;border-radius:11px !important;color:#1f2937 !important;opacity:1 !important;padding:11px 22px !important;font-weight:800 !important;transition:.18s ease !important;}"
    "[role='tab'] *{color:#1f2937 !important;opacity:1 !important;-webkit-text-fill-color:#1f2937 !important;text-shadow:none !important;font-weight:800 !important;}"
    "[role='tab']:hover{background:#e9e7ff !important;border-color:#b9b7ff !important;color:#4338ca !important;}"
    "[role='tab']:hover *{color:#4338ca !important;-webkit-text-fill-color:#4338ca !important;}"
    "[role='tab'][aria-selected='true']{background:linear-gradient(135deg,#5355dc,#7c3aed) !important;border-color:#5355dc !important;color:#ffffff !important;box-shadow:0 7px 18px rgba(83,85,220,.24) !important;}"
    "[role='tab'][aria-selected='true'] *{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;opacity:1 !important;}"
    "[role='tablist'] [data-baseweb='tab-highlight'],[role='tablist'] [data-baseweb='tab-border']{display:none !important;}"
    ".balanced-panel{display:none;}"
    "div[data-testid='stColumn']:has(.balanced-panel) div[data-testid='stVerticalBlockBorderWrapper']>div>div[data-testid='stVerticalBlock']{min-height:245px;height:100%;display:flex;flex-direction:column;}"
    "div[data-testid='stColumn']:has(.balanced-panel) .stButton>button{width:100%;}"
    "div[data-testid='stColumn']:has(.balanced-panel) h3{margin-top:0 !important;margin-bottom:.9rem !important;}"
    ".panel-help{font-size:12px;color:#7b8496;line-height:1.6;margin:-.25rem 0 .8rem;}"
    ".return-panel-title{display:flex;align-items:center;gap:10px;font-size:1.05rem;font-weight:850;color:#182033 !important;margin:0 0 .3rem;line-height:1.35;}"
    ".return-panel-title:before{content:\'\';display:block;width:7px;height:26px;border-radius:999px;background:linear-gradient(180deg,#ec4899,#8b5cf6);box-shadow:0 4px 10px rgba(139,92,246,.18);}"
    ".return-panel-desc{font-size:12px;color:#667085 !important;line-height:1.6;margin:0 0 1rem;}"
    ".return-summary-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:.7rem;}"
    ".return-stat{background:linear-gradient(180deg,#fafaff 0%,#f2f1ff 100%);border:1px solid #dedcff;border-radius:14px;padding:1rem .85rem;text-align:center;box-shadow:0 6px 16px rgba(79,70,229,.06);}"
    ".return-stat:nth-child(2){background:linear-gradient(180deg,#fffaf0 0%,#fff3d7 100%);border-color:#f7dfaa;}"
    ".return-stat:nth-child(3){background:linear-gradient(180deg,#effcf7 0%,#e3f8ef 100%);border-color:#c8eadc;}"
    ".return-stat-label{font-size:11.5px;font-weight:750;color:#667085 !important;margin-bottom:7px;white-space:nowrap;}"
    ".return-stat-value{font-size:1.7rem;font-weight:900;color:#4f46e5 !important;line-height:1;}"
    ".return-stat:nth-child(2) .return-stat-value{color:#d97706 !important;}"
    ".return-stat:nth-child(3) .return-stat-value{color:#16845f !important;}"
    ".return-tip{margin-top:1rem;background:#f8f9ff;border:1px solid #e4e5f5;border-radius:12px;padding:.8rem .9rem;font-size:11.5px;color:#697386 !important;line-height:1.55;}"
    ".return-panel-marker{display:none;}"
    "div[data-testid=\'stColumn\']:has(.return-panel-marker) div[data-testid=\'stVerticalBlockBorderWrapper\']>div>div[data-testid=\'stVerticalBlock\']{min-height:275px !important;background:#ffffff !important;border:1px solid #e2e4ef !important;box-shadow:0 10px 28px rgba(48,56,92,.075) !important;}"
    "@media(max-width:900px){div[data-testid='stMainBlockContainer']{padding-left:1rem;padding-right:1rem}.hero{padding:1.55rem 1.25rem;border-radius:20px}.hero-title{font-size:1.58rem}.spec-bar{grid-template-columns:repeat(2,minmax(0,1fr))}.spec-item:last-child{grid-column:1/-1}div[data-baseweb='tab-list']{overflow-x:auto}button[data-baseweb='tab']{white-space:nowrap;padding:10px 14px !important}.section-head{align-items:flex-start}.section-tag{display:none}}"
    ".stTextInput input,.stNumberInput input{color:#111111 !important;}"".stTextInput input::placeholder,.stNumberInput input::placeholder{color:#9ca3af !important;opacity:1 !important;}"".section-title{color:#182033 !important;-webkit-text-fill-color:#182033 !important;opacity:1 !important;}"".section-sub{color:#667085 !important;-webkit-text-fill-color:#667085 !important;opacity:1 !important;}"".stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{color:#182033 !important;-webkit-text-fill-color:#182033 !important;opacity:1 !important;}"".panel-help{color:#667085 !important;-webkit-text-fill-color:#667085 !important;opacity:1 !important;}"".stTextInput label,.stNumberInput label,.stSelectbox label{color:#374151 !important;-webkit-text-fill-color:#374151 !important;opacity:1 !important;}""div[data-testid='stAlert'] p{color:#263244 !important;-webkit-text-fill-color:#263244 !important;opacity:1 !important;}""</style>"
)
GOOGLE_FONT_LINK = (
    "<link rel='preconnect' href='https://fonts.googleapis.com'>"
    "<link href='https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700;800&family=Prompt:wght@400;500;600;700&display=swap' rel='stylesheet'>"
)
st.markdown(GOOGLE_FONT_LINK + CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Hero section: live dashboard ----------
_total_costumes = len(shop.all_costumes())
_available = len(shop.available_costumes())
_rented = _total_costumes - _available
_total_customers = len(shop.all_customers())
_active_rentals = len([r for r in shop.all_rentals() if not r.returned])

HANGER_ICON = (
    "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' stroke='white' "
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
    "</div></div>"
)
st.markdown(HERO_HTML, unsafe_allow_html=True)

tab_costume, tab_customer, tab_rental = st.tabs(["คลังชุด", "ลูกค้า", "เช่า / คืนชุด"])


def section_heading(title, subtitle, tag, tone="indigo"):
    tone_class = "" if tone == "indigo" else tone
    st.markdown(
        f"<div class='section-head {tone_class}'>"
        "<div class='section-title-wrap'><div class='section-accent'></div><div>"
        f"<div class='section-title'>{title}</div><div class='section-sub'>{subtitle}</div>"
        "</div></div>"
        f"<div class='section-tag'>{tag}</div></div>",
        unsafe_allow_html=True,
    )


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
NEW_TYPE_OPTION = "+ เพิ่มประเภทใหม่..."
ss = st.session_state
ss.setdefault("adding_new_type", False)
if "custom_categories" not in ss:
    ss.custom_categories = shop.custom_categories()

if "pending_type" in ss:
    ss.costume_type_select = ss.pop("pending_type")
    ss.adding_new_type = False
    ss.pop("new_type_select", None)


def _on_type_change():
    if ss.costume_type_select == NEW_TYPE_OPTION:
        ss.adding_new_type = True
        ss.costume_type_select = list(COSTUME_CLASSES)[0]


def _cancel_new_type():
    ss.adding_new_type = False
    ss.pop("new_type_select", None)


with tab_costume:
    section_heading("เพิ่มชุดใหม่", "เพิ่มรายการชุดเข้าสู่คลังและกำหนดราคาเช่า", "ADD COSTUME")
    with st.container(border=True):
        type_options = list(COSTUME_CLASSES) + ss.custom_categories

        if ss.adding_new_type:
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

                    shop.add_costume(final_type, name, size, price, deposit)
                    if final_type not in COSTUME_CLASSES and final_type not in ss.custom_categories:
                        ss.custom_categories.append(final_type)
                    ss.pending_type = final_type
                    ss.costume_msg = f"เพิ่มชุดสำเร็จ (ประเภท: {final_type})"
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    section_heading("คลังชุด", "ค้นหาและตรวจสอบสถานะชุดทั้งหมดในระบบ", "INVENTORY", "teal")
    keyword = st.text_input("ค้นหาชื่อ / ประเภท / รหัสชุด", key="search_costume", placeholder="พิมพ์คำค้นหา...")
    costumes = shop.search_costumes(keyword) if keyword else shop.all_costumes()
    st.dataframe(costumes_dataframe(costumes), width='stretch', hide_index=True)

    section_heading("จัดการข้อมูลชุด", "แก้ไขรายละเอียดหรือลบชุดที่ว่างออกจากระบบ", "MANAGE", "pink")
    manage_left, manage_right = st.columns(2, gap="large")
    with manage_left:
        with st.container(border=True):
            st.markdown("<span class='balanced-panel'></span>", unsafe_allow_html=True)
            st.subheader("ลบชุด")
            st.markdown("<div class='panel-help'>ลบได้เฉพาะชุดที่มีสถานะว่างและไม่ได้ถูกเช่าอยู่</div>", unsafe_allow_html=True)
            if costumes:
                codes = [c.code for c in shop.all_costumes() if c.available]
                if codes:
                    del_code = st.selectbox("เลือกรหัสชุดที่จะลบ (เฉพาะชุดว่าง)", [""] + codes)
                    if st.button("ลบชุดที่เลือก", use_container_width=True) and del_code:
                        try:
                            shop.remove_costume(del_code)
                            st.success(f"ลบชุด {del_code} แล้ว")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                else:
                    st.info("ขณะนี้ไม่มีชุดว่างที่สามารถลบได้")
            else:
                st.info("ยังไม่มีรายการชุด")

    with manage_right:
        with st.container(border=True):
            st.markdown("<span class='balanced-panel'></span>", unsafe_allow_html=True)
            st.subheader("แก้ไขชุด")
            st.markdown("<div class='panel-help'>เลือกรหัสชุดเพื่อแก้ไขชื่อ ขนาด ราคาเช่า และเงินมัดจำ</div>", unsafe_allow_html=True)
            if "clear_edit_costume" in ss:
                ss.edit_costume_select = ""
                del ss["clear_edit_costume"]
            if "edit_costume_msg" in ss:
                st.success(ss.pop("edit_costume_msg"))

            all_codes = [c.code for c in shop.all_costumes()]
            edit_code = st.selectbox("เลือกรหัสชุดที่จะแก้ไข", [""] + all_codes, key="edit_costume_select")
            if edit_code:
                costume_obj = next(c for c in shop.all_costumes() if c.code == edit_code)
                with st.form(f"edit_costume_form_{edit_code}"):
                    ec1, ec2 = st.columns(2)
                    ec3, ec4 = st.columns(2)
                    new_name = ec1.text_input("ชื่อชุด", value=costume_obj.name)
                    new_size = ec2.text_input("ขนาด", value=costume_obj.size)
                    new_price = ec3.number_input("ราคา/วัน", min_value=0.0, step=50.0, value=costume_obj.price_per_day)
                    new_deposit = ec4.number_input("มัดจำ", min_value=0.0, step=100.0, value=costume_obj.deposit)
                    if st.form_submit_button("บันทึกการแก้ไข", use_container_width=True):
                        try:
                            costume_obj.name = new_name
                            costume_obj.size = new_size
                            costume_obj.price_per_day = new_price
                            costume_obj.deposit = new_deposit
                            shop.persist_costume(costume_obj)
                            ss.edit_costume_msg = f"แก้ไขชุด {edit_code} สำเร็จ"
                            ss.clear_edit_costume = True
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
            else:
                st.info("เลือกรหัสชุดด้านบนเพื่อเปิดแบบฟอร์มแก้ไข")


# ---------------- แท็บ: ลูกค้า ----------------
with tab_customer:
    section_heading("เพิ่มลูกค้า", "บันทึกข้อมูลลูกค้าใหม่เข้าสู่ระบบ", "NEW CUSTOMER")
    with st.container(border=True):
        with st.form("add_customer_form", clear_on_submit=True, border=False):
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
                    shop.add_customer(cust_name, cust_phone)
                    st.success("เพิ่มลูกค้าสำเร็จ")

    section_heading("รายชื่อลูกค้า", "ค้นหาจากชื่อ เบอร์โทร หรือรหัสลูกค้า", "CUSTOMERS", "teal")
    cust_keyword = st.text_input("ค้นหาชื่อ / เบอร์โทร / รหัสลูกค้า", key="search_customer", placeholder="พิมพ์คำค้นหา...")
    filtered_customers = shop.search_customers(cust_keyword) if cust_keyword else shop.all_customers()

    customers_df = pd.DataFrame([
        {"รหัสลูกค้า": c.customer_id, "ชื่อ": c.name, "เบอร์โทร": c.phone}
        for c in filtered_customers
    ])
    st.dataframe(customers_df, width='stretch', hide_index=True)

    section_heading("จัดการข้อมูลลูกค้า", "แก้ไขข้อมูลหรือลบลูกค้าที่ไม่มีรายการเช่าค้างอยู่", "MANAGE", "pink")
    cust_left, cust_right = st.columns(2, gap="large")
    with cust_left:
        with st.container(border=True):
            st.markdown("<span class='balanced-panel'></span>", unsafe_allow_html=True)
            st.subheader("ลบลูกค้า")
            st.markdown("<div class='panel-help'>ลบได้เฉพาะลูกค้าที่ไม่มีรายการเช่าค้างอยู่ในระบบ</div>", unsafe_allow_html=True)
            if filtered_customers:
                cust_codes = [c.customer_id for c in filtered_customers]
                del_cust_id = st.selectbox("เลือกรหัสลูกค้าที่จะลบ", [""] + cust_codes)
                if st.button("ลบลูกค้าที่เลือก", use_container_width=True) and del_cust_id:
                    try:
                        shop.remove_customer(del_cust_id)
                        st.success(f"ลบลูกค้า {del_cust_id} แล้ว")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            else:
                st.info("ไม่พบลูกค้าที่ตรงกับคำค้นหา")

    with cust_right:
        with st.container(border=True):
            st.markdown("<span class='balanced-panel'></span>", unsafe_allow_html=True)
            st.subheader("แก้ไขลูกค้า")
            st.markdown("<div class='panel-help'>เลือกรหัสลูกค้าเพื่อแก้ไขชื่อและเบอร์โทรศัพท์</div>", unsafe_allow_html=True)
            if "clear_edit_customer" in ss:
                ss.edit_customer_select = ""
                del ss["clear_edit_customer"]
            if "edit_customer_msg" in ss:
                st.success(ss.pop("edit_customer_msg"))

            all_cust_ids = [c.customer_id for c in shop.all_customers()]
            edit_cust_id = st.selectbox("เลือกรหัสลูกค้าที่จะแก้ไข", [""] + all_cust_ids, key="edit_customer_select")
            if edit_cust_id:
                customer_obj = next(c for c in shop.all_customers() if c.customer_id == edit_cust_id)
                with st.form(f"edit_customer_form_{edit_cust_id}"):
                    ecu1, ecu2 = st.columns(2)
                    new_cust_name = ecu1.text_input("ชื่อ", value=customer_obj.name)
                    new_cust_phone = ecu2.text_input("เบอร์โทร", value=customer_obj.phone, max_chars=10)
                    if st.form_submit_button("บันทึกการแก้ไข", use_container_width=True):
                        try:
                            customer_obj.name = new_cust_name
                            customer_obj.phone = new_cust_phone
                            shop.persist_customer(customer_obj)
                            ss.edit_customer_msg = f"แก้ไขลูกค้า {edit_cust_id} สำเร็จ"
                            ss.clear_edit_customer = True
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
            else:
                st.info("เลือกรหัสลูกค้าด้านบนเพื่อเปิดแบบฟอร์มแก้ไข")


# ---------------- แท็บ: เช่า / คืนชุด ----------------
with tab_rental:
    section_heading("ทำรายการเช่าชุด", "เลือกลูกค้า ชุดที่ว่าง และจำนวนวันที่ต้องการเช่า", "NEW RENTAL")
    customer_options = {f"{c.customer_id} - {c.name}": c.customer_id for c in shop.all_customers()}
    costume_options = {f"{c.code} - {c.name} ({c.category()})": c.code for c in shop.available_costumes()}

    with st.container(border=True):
        with st.form("rent_form", border=False):
            c1, c2, c3 = st.columns([1.1, 1.7, .7])
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

    section_heading("รายการเช่าทั้งหมด", "ตรวจสอบประวัติและสถานะของรายการเช่า", "RENTAL HISTORY", "teal")
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

    section_heading("คืนชุด", "เลือกรายการเช่าที่ยังไม่คืนเพื่อบันทึกการคืนชุด", "RETURN", "pink")
    active_ids = [r.rental_id for r in rentals if not r.returned]
    returned_count = len([r for r in rentals if r.returned])
    rental_left, rental_right = st.columns(2, gap="large")

    with rental_left:
        with st.container(border=True):
            st.markdown("<span class='balanced-panel return-panel-marker'></span>", unsafe_allow_html=True)
            st.markdown(
                "<div class='return-panel-title'>บันทึกการคืนชุด</div>"
                "<div class='return-panel-desc'>เลือกรหัสเช่าที่ยังไม่คืน แล้วกดยืนยันเพื่อคืนชุดเข้าคลัง</div>",
                unsafe_allow_html=True,
            )
            if active_ids:
                return_id = st.selectbox(
                    "เลือกรหัสเช่าที่จะคืน",
                    [""] + active_ids,
                    key="return_rental_select",
                )
                if st.button("คืนชุด", use_container_width=True, key="return_costume_button") and return_id:
                    try:
                        shop.return_costume(return_id)
                        st.success(f"คืนชุดของรายการ {return_id} แล้ว")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
            else:
                st.info("ไม่มีรายการเช่าที่รอคืนในขณะนี้")

    with rental_right:
        with st.container(border=True):
            st.markdown("<span class='balanced-panel return-panel-marker'></span>", unsafe_allow_html=True)
            st.markdown(
                "<div class='return-panel-title'>สรุปสถานะการเช่า</div>"
                "<div class='return-panel-desc'>ภาพรวมรายการเช่าจากข้อมูลที่มีอยู่ในระบบ</div>"
                "<div class='return-summary-grid'>"
                f"<div class='return-stat'><div class='return-stat-label'>รายการทั้งหมด</div><div class='return-stat-value'>{len(rentals)}</div></div>"
                f"<div class='return-stat'><div class='return-stat-label'>กำลังเช่า</div><div class='return-stat-value'>{len(active_ids)}</div></div>"
                f"<div class='return-stat'><div class='return-stat-label'>คืนแล้ว</div><div class='return-stat-value'>{returned_count}</div></div>"
                "</div>"
                "<div class='return-tip'>สถานะจะอัปเดตทันทีหลังบันทึกการคืนชุดสำเร็จ</div>",
                unsafe_allow_html=True,
            )
