"""
ระบบร้านเช่าชุด (Costume Rental Shop Management System)
Mini Project - OOP

"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, messagebox


# ==========================================================
# 1) Costume
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
# 2) WeddingCostume
# ==========================================================
class WeddingCostume(Costume):
    def category(self):
        return "ชุดแต่งงาน"

    def calculate_rental_fee(self, days):
        return self.price_per_day * days

    def __str__(self):
        return f"{super().__str__()} | มัดจำ {self.deposit:.0f} บาท"


# ==========================================================
# 3) ThaiCostume
# ==========================================================
class ThaiCostume(Costume):
    def category(self):
        return "ชุดไทย"

    def calculate_rental_fee(self, days):
        total = self.price_per_day * days
        if days >= 3:
            total *= 0.90
        return total

    def __str__(self):
        return f"{super().__str__()} | ลด 10% ถ้าเช่า >= 3 วัน"


# ==========================================================
# 4) PartyCostume
# ==========================================================
class PartyCostume(Costume):
    def category(self):
        return "ชุดปาร์ตี้"

    def calculate_rental_fee(self, days):
        if days <= 0:
            return 0
        return self.price_per_day + (days - 1) * self.price_per_day * 0.5

    def __str__(self):
        return f"{super().__str__()} | วันถัดไปลดครึ่งราคา"


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

    def __str__(self):
        return f"{self.customer_id} | {self.name} | {self.phone}"


# ==========================================================
# 6) RentalShop (เฉพาะฟังก์ชันพื้นฐาน)
# ==========================================================
class RentalShop:
    def __init__(self, name):
        self.__name = name
        self.__costumes = {}
        self.__customers = {}
        self.__next_costume_no = 1
        self.__next_customer_no = 1

    @property
    def name(self):
        return self.__name

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

    def add_customer(self, name, phone):
        cid = f"U{self.__next_customer_no:03d}"
        self.__next_customer_no += 1
        customer = Customer(cid, name, phone)
        self.__customers[cid] = customer
        return customer

    def all_customers(self):
        return list(self.__customers.values())


# ==========================================================
# 7) RentalApp (GUI พื้นฐาน)
# ==========================================================
class RentalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ระบบร้านเช่าชุด")
        self.root.geometry("900x550")
        self.shop = RentalShop("ร้านเช่าชุดสวยดี")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_costume = ttk.Frame(notebook)
        self.tab_customer = ttk.Frame(notebook)
        notebook.add(self.tab_costume, text="คลังชุด")
        notebook.add(self.tab_customer, text="ลูกค้า")

        self.build_costume_tab()
        self.build_customer_tab()
        self.refresh_all()

    def build_costume_tab(self):
        form = ttk.LabelFrame(self.tab_costume, text="เพิ่มชุดใหม่")
        form.pack(fill="x", padx=10, pady=8)

        ttk.Label(form, text="ประเภท").grid(row=0, column=0, padx=5, pady=5)
        self.cb_type = ttk.Combobox(
            form, values=list(COSTUME_CLASSES.keys()),
            state="readonly", width=15
        )
        self.cb_type.current(0)
        self.cb_type.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="ชื่อชุด").grid(row=0, column=2, padx=5, pady=5)
        self.ent_name = ttk.Entry(form, width=18)
        self.ent_name.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="ไซซ์").grid(row=0, column=4, padx=5, pady=5)
        self.ent_size = ttk.Entry(form, width=8)
        self.ent_size.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(form, text="ราคา/วัน").grid(row=1, column=0, padx=5, pady=5)
        self.ent_price = ttk.Entry(form, width=12)
        self.ent_price.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="มัดจำ").grid(row=1, column=2, padx=5, pady=5)
        self.ent_deposit = ttk.Entry(form, width=12)
        self.ent_deposit.insert(0, "0")
        self.ent_deposit.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(
            form, text="เพิ่มชุด", command=self.on_add_costume
        ).grid(row=1, column=5, padx=5, pady=5)

        search = ttk.Frame(self.tab_costume)
        search.pack(fill="x", padx=10)
        self.ent_search = ttk.Entry(search, width=25)
        self.ent_search.pack(side="left")
        ttk.Button(
            search, text="ค้นหา", command=self.on_search
        ).pack(side="left", padx=5)
        ttk.Button(
            search, text="แสดงทั้งหมด", command=self.refresh_costumes
        ).pack(side="left")
        ttk.Button(
            search, text="ลบชุด", command=self.on_delete
        ).pack(side="right")

        cols = ("code", "type", "name", "size", "price", "deposit")
        self.tree_costume = ttk.Treeview(
            self.tab_costume, columns=cols, show="headings", height=15
        )
        headers = ["รหัส", "ประเภท", "ชื่อชุด", "ไซซ์", "ราคา/วัน", "มัดจำ"]
        for col, title in zip(cols, headers):
            self.tree_costume.heading(col, text=title)
            self.tree_costume.column(col, width=130, anchor="center")
        self.tree_costume.pack(fill="both", expand=True, padx=10, pady=8)

    def build_customer_tab(self):
        form = ttk.LabelFrame(self.tab_customer, text="เพิ่มลูกค้า")
        form.pack(fill="x", padx=10, pady=8)

        ttk.Label(form, text="ชื่อ").grid(row=0, column=0, padx=5, pady=5)
        self.ent_customer_name = ttk.Entry(form, width=25)
        self.ent_customer_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="เบอร์โทร").grid(row=0, column=2, padx=5, pady=5)
        self.ent_phone = ttk.Entry(form, width=20)
        self.ent_phone.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(
            form, text="เพิ่มลูกค้า", command=self.on_add_customer
        ).grid(row=0, column=4, padx=5, pady=5)

        cols = ("id", "name", "phone")
        self.tree_customer = ttk.Treeview(
            self.tab_customer, columns=cols, show="headings", height=18
        )
        for col, title in zip(cols, ["รหัสลูกค้า", "ชื่อ", "เบอร์โทร"]):
            self.tree_customer.heading(col, text=title)
            self.tree_customer.column(col, width=180, anchor="center")
        self.tree_customer.pack(fill="both", expand=True, padx=10, pady=8)

    def on_add_costume(self):
        try:
            name = self.ent_name.get().strip()
            size = self.ent_size.get().strip()
            price = float(self.ent_price.get())
            deposit = float(self.ent_deposit.get() or 0)
            if not name or not size:
                raise ValueError("กรอกชื่อและไซซ์ให้ครบ")

            self.shop.add_costume(
                self.cb_type.get(), name, size, price, deposit
            )
            self.ent_name.delete(0, tk.END)
            self.ent_size.delete(0, tk.END)
            self.ent_price.delete(0, tk.END)
            self.refresh_all()
        except ValueError as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))

    def on_search(self):
        self.fill_costumes(
            self.shop.search_costumes(self.ent_search.get())
        )

    def on_delete(self):
        selected = self.tree_costume.selection()
        if not selected:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกชุด")
            return

        code = self.tree_costume.item(selected[0])["values"][0]
        try:
            self.shop.remove_costume(code)
            self.refresh_all()
        except ValueError as e:
            messagebox.showerror("ข้อผิดพลาด", str(e))

    def on_add_customer(self):
        name = self.ent_customer_name.get().strip()
        phone = self.ent_phone.get().strip()
        if not name or not phone:
            messagebox.showerror("ข้อผิดพลาด", "กรอกข้อมูลให้ครบ")
            return

        self.shop.add_customer(name, phone)
        self.ent_customer_name.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.refresh_all()

    def fill_costumes(self, costumes):
        self.tree_costume.delete(*self.tree_costume.get_children())
        for c in costumes:
            self.tree_costume.insert(
                "", tk.END,
                values=(
                    c.code, c.category(), c.name, c.size,
                    f"{c.price_per_day:.0f}", f"{c.deposit:.0f}"
                )
            )

    def refresh_costumes(self):
        self.fill_costumes(self.shop.all_costumes())

    def refresh_customers(self):
        self.tree_customer.delete(*self.tree_customer.get_children())
        for c in self.shop.all_customers():
            self.tree_customer.insert(
                "", tk.END,
                values=(c.customer_id, c.name, c.phone)
            )

    def refresh_all(self):
        self.refresh_costumes()
        self.refresh_customers()


def main():
    root = tk.Tk()
    RentalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
