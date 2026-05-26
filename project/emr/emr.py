# mini_emr_v3.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import calendar
import os
import hashlib

DB_NAME = "emr_v3.db"


# ------------------------------ Utils ------------------------------
def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------ Auth (Login) ------------------------------
def hash_password(password: str, salt: bytes) -> str:
    # PBKDF2-HMAC-SHA256
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return dk.hex()


def ensure_default_user(conn):
    """users 테이블이 비어있으면 기본 계정 1개 생성"""
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        username = "admin"
        password = "admin123"  # 필요하면 바꿔
        salt = os.urandom(16)
        pw_hash = hash_password(password, salt)
        conn.execute(
            "INSERT INTO users(username, pw_hash, salt, created_at) VALUES(?,?,?,?)",
            (username, pw_hash, salt.hex(), now_ts())
        )
        conn.commit()


def verify_login(conn, username: str, password: str) -> bool:
    cur = conn.execute("SELECT pw_hash, salt FROM users WHERE username=?", (username.strip(),))
    row = cur.fetchone()
    if not row:
        return False
    pw_hash, salt_hex = row
    salt = bytes.fromhex(salt_hex)
    return hash_password(password, salt) == pw_hash


class LoginWindow(tk.Toplevel):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        self.ok = False

        self.title("로그인")
        self.geometry("320x170")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        ttk.Label(self, text="아이디").place(x=20, y=20)
        self.ent_user = ttk.Entry(self)
        self.ent_user.place(x=90, y=18, width=200)

        ttk.Label(self, text="비밀번호").place(x=20, y=55)
        self.ent_pw = ttk.Entry(self, show="*")
        self.ent_pw.place(x=90, y=53, width=200)

        ttk.Label(self, text="기본계정: admin / admin123").place(x=20, y=85)

        ttk.Button(self, text="로그인", command=self.on_login).place(x=90, y=115, width=90)
        ttk.Button(self, text="취소", command=self.on_close).place(x=200, y=115, width=90)

        self.ent_user.focus_set()

        # modal
        self.update_idletasks()
        self.transient(parent)
        self.grab_set()

                # --- 강제로 화면 중앙 + 앞으로 가져오기 ---
        w, h = 320, 170
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(250, lambda: self.attributes("-topmost", False))


    def on_login(self):
        u = self.ent_user.get().strip()
        p = self.ent_pw.get()
        if not u or not p:
            messagebox.showwarning("입력", "아이디/비밀번호를 입력하세요.")
            return
        if verify_login(self.conn, u, p):
            self.ok = True
            self.destroy()
        else:
            messagebox.showerror("실패", "아이디 또는 비밀번호가 틀렸습니다.")

    def on_close(self):
        self.ok = False
        self.destroy()


# ------------------------------ DB ------------------------------
def db_connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")

    # users (로그인)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            pw_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # patients
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            birth TEXT,
            phone TEXT,
            memo TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # visits
    conn.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,              -- YYYY-MM-DD
            chief_complaint TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)

    # drugs master (코드/가격 관리)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drugs (
            code TEXT PRIMARY KEY,                 -- 약물코드 (예: D001)
            name TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,      -- 원 단위
            created_at TEXT NOT NULL
        )
    """)

    # prescriptions (환자별 처방 헤더)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            rx_date TEXT NOT NULL,                 -- YYYY-MM-DD
            created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)

    # prescription items (처방 상세)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prescription_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL,
            drug_code TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            directions TEXT,                       -- 복용법/지시
            note TEXT,
            unit_price INTEGER NOT NULL DEFAULT 0,  -- 저장 당시 가격 스냅샷
            FOREIGN KEY(prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE,
            FOREIGN KEY(drug_code) REFERENCES drugs(code) ON DELETE RESTRICT
        )
    """)

    conn.commit()
    return conn


# ----- patients
def db_insert_patient(conn, name, birth, phone, memo):
    conn.execute(
        "INSERT INTO patients(name,birth,phone,memo,created_at) VALUES(?,?,?,?,?)",
        (name, birth, phone, memo, now_ts())
    )
    conn.commit()


def db_update_patient(conn, pid, name, birth, phone, memo):
    conn.execute(
        "UPDATE patients SET name=?, birth=?, phone=?, memo=? WHERE id=?",
        (name, birth, phone, memo, pid)
    )
    conn.commit()


def db_delete_patient(conn, pid):
    conn.execute("DELETE FROM patients WHERE id=?", (pid,))
    conn.commit()


def db_fetch_patients(conn):
    cur = conn.execute("""
        SELECT id, name, birth, phone, memo, created_at
        FROM patients
        ORDER BY id DESC
    """)
    return cur.fetchall()


def db_fetch_patient_one(conn, pid):
    cur = conn.execute("""
        SELECT id, name, birth, phone, memo, created_at
        FROM patients WHERE id=?
    """, (pid,))
    return cur.fetchone()


# ----- visits
def db_insert_visit(conn, patient_id, visit_date, chief_complaint, note):
    conn.execute(
        "INSERT INTO visits(patient_id, visit_date, chief_complaint, note, created_at) VALUES(?,?,?,?,?)",
        (patient_id, visit_date, chief_complaint, note, now_ts())
    )
    conn.commit()


def db_update_visit(conn, vid, visit_date, chief_complaint, note):
    conn.execute(
        "UPDATE visits SET visit_date=?, chief_complaint=?, note=? WHERE id=?",
        (visit_date, chief_complaint, note, vid)
    )
    conn.commit()


def db_delete_visit(conn, vid):
    conn.execute("DELETE FROM visits WHERE id=?", (vid,))
    conn.commit()


def db_fetch_visits_by_patient(conn, patient_id):
    cur = conn.execute("""
        SELECT id, visit_date, chief_complaint, created_at
        FROM visits
        WHERE patient_id=?
        ORDER BY id DESC
    """, (patient_id,))
    return cur.fetchall()


def db_fetch_visit_one(conn, vid):
    cur = conn.execute("""
        SELECT id, visit_date, chief_complaint, note, created_at
        FROM visits WHERE id=?
    """, (vid,))
    return cur.fetchone()


# ----- drugs
def db_insert_drug(conn, code, name, price):
    conn.execute(
        "INSERT INTO drugs(code,name,price,created_at) VALUES(?,?,?,?)",
        (code.strip(), name.strip(), int(price), now_ts())
    )
    conn.commit()


def db_update_drug(conn, code, name, price):
    conn.execute(
        "UPDATE drugs SET name=?, price=? WHERE code=?",
        (name.strip(), int(price), code.strip())
    )
    conn.commit()


def db_delete_drug(conn, code):
    conn.execute("DELETE FROM drugs WHERE code=?", (code.strip(),))
    conn.commit()


def db_fetch_drugs(conn, keyword=""):
    keyword = (keyword or "").strip()
    if keyword:
        cur = conn.execute("""
            SELECT code, name, price, created_at
            FROM drugs
            WHERE code LIKE ? OR name LIKE ?
            ORDER BY code ASC
        """, (f"%{keyword}%", f"%{keyword}%"))
    else:
        cur = conn.execute("""
            SELECT code, name, price, created_at
            FROM drugs
            ORDER BY code ASC
        """)
    return cur.fetchall()


def db_fetch_drug_one(conn, code):
    cur = conn.execute("""
        SELECT code, name, price, created_at
        FROM drugs WHERE code=?
    """, (code.strip(),))
    return cur.fetchone()


# ----- prescriptions
def db_create_prescription(conn, patient_id, rx_date, items):
    """
    items: list of dict {drug_code, qty, directions, note}
    가격은 drugs.price를 스냅샷(unit_price)로 저장
    """
    cur = conn.execute(
        "INSERT INTO prescriptions(patient_id, rx_date, created_at) VALUES(?,?,?)",
        (patient_id, rx_date, now_ts())
    )
    rx_id = cur.lastrowid

    for it in items:
        drug = db_fetch_drug_one(conn, it["drug_code"])
        if not drug:
            raise ValueError(f"약물코드 없음: {it['drug_code']}")
        unit_price = int(drug[2])

        conn.execute("""
            INSERT INTO prescription_items(prescription_id, drug_code, qty, directions, note, unit_price)
            VALUES(?,?,?,?,?,?)
        """, (rx_id, it["drug_code"], int(it["qty"]), it.get("directions", ""), it.get("note", ""), unit_price))

    conn.commit()
    return rx_id


def db_fetch_prescriptions_by_patient(conn, patient_id):
    cur = conn.execute("""
        SELECT p.id, p.rx_date, p.created_at,
               COALESCE(SUM(i.qty * i.unit_price), 0) AS total_price
        FROM prescriptions p
        LEFT JOIN prescription_items i ON i.prescription_id = p.id
        WHERE p.patient_id=?
        GROUP BY p.id
        ORDER BY p.id DESC
    """, (patient_id,))
    return cur.fetchall()


def db_fetch_prescription_items(conn, rx_id):
    cur = conn.execute("""
        SELECT i.id, i.drug_code, d.name, i.qty, i.unit_price,
               (i.qty * i.unit_price) AS line_total, i.directions, i.note
        FROM prescription_items i
        JOIN drugs d ON d.code = i.drug_code
        WHERE i.prescription_id=?
        ORDER BY i.id ASC
    """, (rx_id,))
    return cur.fetchall()


# ------------------------------ UI ------------------------------
class MiniEMRv3(tk.Tk):
    def __init__(self, conn):
        super().__init__()
        self.title("mini_emr_v3")
        self.geometry("1100x650")
        self.resizable(False, False)

        # 같은 DB 연결을 그대로 사용(로그인과 공유)
        self.conn = conn

        self.current_patient_id = None
        self.current_patient_name = ""

        self.nb = ttk.Notebook(self)
        self.nb.place(x=10, y=10, width=1080, height=630)

        self.tab_patients = ttk.Frame(self.nb)
        self.tab_clinic = ttk.Frame(self.nb)

        self.nb.add(self.tab_patients, text="환자관리")
        self.nb.add(self.tab_clinic, text="진료")

        self._build_patients_tab()
        self._build_clinic_tab()

        self.refresh_patients()

    # ---------- Patients tab ----------
    def _build_patients_tab(self):
        # (2) 우측상단 달력
        self._build_calendar_widget(parent=self.tab_patients, x=740, y=10)

        form = ttk.LabelFrame(self.tab_patients, text="환자 정보")
        form.place(x=10, y=10, width=420, height=590)

        ttk.Label(form, text="이름*").place(x=10, y=20)
        self.ent_name = ttk.Entry(form)
        self.ent_name.place(x=120, y=18, width=270)

        ttk.Label(form, text="생년월일").place(x=10, y=55)
        self.ent_birth = ttk.Entry(form)
        self.ent_birth.place(x=120, y=53, width=270)
        self.ent_birth.insert(0, "YYYY-MM-DD")

        ttk.Label(form, text="연락처").place(x=10, y=90)
        self.ent_phone = ttk.Entry(form)
        self.ent_phone.place(x=120, y=88, width=270)

        ttk.Label(form, text="메모").place(x=10, y=125)
        self.txt_memo = tk.Text(form, wrap="word")
        self.txt_memo.place(x=120, y=125, width=270, height=120)

        self.lbl_patient_id = ttk.Label(form, text="선택된 환자 ID: 없음")
        self.lbl_patient_id.place(x=10, y=260)

        btn_y = 295
        ttk.Button(form, text="신규", command=self.clear_patient_form).place(x=10, y=btn_y, width=90)
        ttk.Button(form, text="추가", command=self.on_add_patient).place(x=110, y=btn_y, width=90)
        ttk.Button(form, text="수정", command=self.on_update_patient).place(x=210, y=btn_y, width=90)
        ttk.Button(form, text="삭제", command=self.on_delete_patient).place(x=310, y=btn_y, width=90)

        ttk.Label(form, text="Tip: 환자리스트 더블클릭 → 진료 탭 이동").place(x=10, y=340)

        listf = ttk.LabelFrame(self.tab_patients, text="환자 리스트")
        listf.place(x=450, y=10, width=280, height=590)

        cols = ("id", "name", "birth")
        self.tree_patients = ttk.Treeview(listf, columns=cols, show="headings", height=23)
        self.tree_patients.heading("id", text="ID")
        self.tree_patients.heading("name", text="이름")
        self.tree_patients.heading("birth", text="생년월일")
        self.tree_patients.column("id", width=60, anchor="center")
        self.tree_patients.column("name", width=100, anchor="w")
        self.tree_patients.column("birth", width=100, anchor="center")
        self.tree_patients.place(x=10, y=10, width=255, height=520)

        self.tree_patients.bind("<<TreeviewSelect>>", self.on_select_patient)
        # (1) 더블클릭 → 환자 선택 + 진료탭 이동
        self.tree_patients.bind("<Double-1>", self.on_patient_double_click)

        ttk.Button(listf, text="새로고침", command=self.refresh_patients).place(x=10, y=540, width=255)

    def _build_calendar_widget(self, parent, x, y):
        calf = ttk.LabelFrame(parent, text="오늘 날짜 / 달력")
        calf.place(x=x, y=y, width=330, height=210)

        today = date.today()
        self.lbl_today = ttk.Label(
            calf,
            text=f"오늘: {today.strftime('%Y-%m-%d')} ({calendar.day_name[today.weekday()]})"
        )
        self.lbl_today.place(x=10, y=10)

        self.txt_calendar = tk.Text(calf, borderwidth=0)
        self.txt_calendar.place(x=10, y=40, width=310, height=150)
        self.txt_calendar.configure(state="disabled", font=("Consolas", 10))

        self.render_month_calendar(today.year, today.month)

    def render_month_calendar(self, year, month):
        cal = calendar.TextCalendar(firstweekday=6)  # 일요일 시작
        s = cal.formatmonth(year, month)

        self.txt_calendar.configure(state="normal")
        self.txt_calendar.delete("1.0", "end")
        self.txt_calendar.insert("1.0", s)
        self.txt_calendar.configure(state="disabled")

    def get_patient_form(self):
        name = self.ent_name.get().strip()
        birth = self.ent_birth.get().strip().replace("YYYY-MM-DD", "").strip()
        phone = self.ent_phone.get().strip()
        memo = self.txt_memo.get("1.0", "end").strip()
        return name, birth, phone, memo

    def clear_patient_form(self):
        self.ent_name.delete(0, "end")
        self.ent_birth.delete(0, "end")
        self.ent_birth.insert(0, "YYYY-MM-DD")
        self.ent_phone.delete(0, "end")
        self.txt_memo.delete("1.0", "end")

        self.current_patient_id = None
        self.current_patient_name = ""
        self.lbl_patient_id.config(text="선택된 환자 ID: 없음")
        self.update_current_patient_label()
        self.refresh_visits()
        self.refresh_prescriptions()

    def refresh_patients(self):
        for x in self.tree_patients.get_children():
            self.tree_patients.delete(x)

        rows = db_fetch_patients(self.conn)
        for pid, name, birth, phone, memo, created in rows:
            self.tree_patients.insert("", "end", values=(pid, name, birth))

    def on_add_patient(self):
        name, birth, phone, memo = self.get_patient_form()
        if not name:
            messagebox.showwarning("필수", "이름은 필수입니다.")
            return
        db_insert_patient(self.conn, name, birth, phone, memo)
        self.refresh_patients()
        self.clear_patient_form()
        messagebox.showinfo("완료", "환자 추가 완료")

    def on_update_patient(self):
        if not self.current_patient_id:
            messagebox.showwarning("선택", "수정할 환자를 선택하세요.")
            return
        name, birth, phone, memo = self.get_patient_form()
        if not name:
            messagebox.showwarning("필수", "이름은 필수입니다.")
            return
        db_update_patient(self.conn, self.current_patient_id, name, birth, phone, memo)
        self.refresh_patients()
        messagebox.showinfo("완료", "환자 수정 완료")

    def on_delete_patient(self):
        if not self.current_patient_id:
            messagebox.showwarning("선택", "삭제할 환자를 선택하세요.")
            return
        if messagebox.askyesno("확인", "정말 삭제할까요? (진료/처방 기록도 함께 삭제됩니다)"):
            db_delete_patient(self.conn, self.current_patient_id)
            self.refresh_patients()
            self.clear_patient_form()
            messagebox.showinfo("완료", "삭제 완료")

    def on_select_patient(self, _evt=None):
        sel = self.tree_patients.selection()
        if not sel:
            return
        pid = int(self.tree_patients.item(sel[0])["values"][0])
        row = db_fetch_patient_one(self.conn, pid)
        if not row:
            return

        self.current_patient_id = row[0]
        self.current_patient_name = row[1]
        self.lbl_patient_id.config(text=f"선택된 환자 ID: {self.current_patient_id}")

        self.ent_name.delete(0, "end")
        self.ent_name.insert(0, row[1] or "")
        self.ent_birth.delete(0, "end")
        self.ent_birth.insert(0, row[2] or "")
        self.ent_phone.delete(0, "end")
        self.ent_phone.insert(0, row[3] or "")
        self.txt_memo.delete("1.0", "end")
        self.txt_memo.insert("1.0", row[4] or "")

        self.update_current_patient_label()
        self.refresh_visits()
        self.refresh_prescriptions()

    def on_patient_double_click(self, _evt=None):
        self.on_select_patient()
        if self.current_patient_id:
            self.nb.select(self.tab_clinic)

    # ---------- Clinic tab ----------
    def _build_clinic_tab(self):
        # (2) 우측상단 달력
        self._build_calendar_widget(parent=self.tab_clinic, x=740, y=10)

        top = ttk.LabelFrame(self.tab_clinic, text="현재 선택된 환자")
        top.place(x=10, y=10, width=720, height=70)

        self.lbl_current_patient = ttk.Label(top, text="없음 (환자관리 탭에서 환자를 먼저 선택하세요)")
        self.lbl_current_patient.place(x=10, y=20)

        # (3) 하위 탭: 진료기록 / 처방
        self.subnb = ttk.Notebook(self.tab_clinic)
        self.subnb.place(x=10, y=90, width=720, height=510)

        self.sub_visits = ttk.Frame(self.subnb)
        self.sub_rx = ttk.Frame(self.subnb)
        self.subnb.add(self.sub_visits, text="진료기록")
        self.subnb.add(self.sub_rx, text="처방")

        self._build_visits_subtab()
        self._build_rx_subtab()

    def update_current_patient_label(self):
        if self.current_patient_id:
            self.lbl_current_patient.config(text=f"환자: {self.current_patient_name} (ID: {self.current_patient_id})")
        else:
            self.lbl_current_patient.config(text="없음 (환자관리 탭에서 환자를 먼저 선택하세요)")

    # ---------- Visits subtab ----------
    def _build_visits_subtab(self):
        form = ttk.LabelFrame(self.sub_visits, text="진료기록 입력")
        form.place(x=10, y=10, width=330, height=480)

        ttk.Label(form, text="진료일").place(x=10, y=20)
        self.ent_visit_date = ttk.Entry(form)
        self.ent_visit_date.place(x=110, y=18, width=200)
        self.ent_visit_date.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Label(form, text="주호소").place(x=10, y=55)
        self.txt_cc = tk.Text(form, wrap="word")
        self.txt_cc.place(x=110, y=55, width=200, height=80)

        ttk.Label(form, text="노트").place(x=10, y=145)
        self.txt_note = tk.Text(form, wrap="word")
        self.txt_note.place(x=110, y=145, width=200, height=160)

        self.lbl_visit_id = ttk.Label(form, text="선택된 기록 ID: 없음")
        self.lbl_visit_id.place(x=10, y=320)

        ttk.Button(form, text="신규", command=self.clear_visit_form).place(x=10, y=360, width=70)
        ttk.Button(form, text="추가", command=self.on_add_visit).place(x=90, y=360, width=70)
        ttk.Button(form, text="수정", command=self.on_update_visit).place(x=170, y=360, width=70)
        ttk.Button(form, text="삭제", command=self.on_delete_visit).place(x=250, y=360, width=70)

        listf = ttk.LabelFrame(self.sub_visits, text="진료기록 리스트")
        listf.place(x=350, y=10, width=350, height=480)

        cols = ("id", "visit_date", "chief_complaint", "created_at")
        self.tree_visits = ttk.Treeview(listf, columns=cols, show="headings", height=20)
        self.tree_visits.heading("id", text="ID")
        self.tree_visits.heading("visit_date", text="진료일")
        self.tree_visits.heading("chief_complaint", text="주호소")
        self.tree_visits.heading("created_at", text="생성일시")
        self.tree_visits.column("id", width=50, anchor="center")
        self.tree_visits.column("visit_date", width=90, anchor="center")
        self.tree_visits.column("chief_complaint", width=120, anchor="w")
        self.tree_visits.column("created_at", width=80, anchor="center")
        self.tree_visits.place(x=10, y=10, width=325, height=420)

        self.tree_visits.bind("<<TreeviewSelect>>", self.on_select_visit)
        ttk.Button(listf, text="새로고침", command=self.refresh_visits).place(x=10, y=440, width=325)

        self.selected_visit_id = None

    def clear_visit_form(self):
        self.ent_visit_date.delete(0, "end")
        self.ent_visit_date.insert(0, date.today().strftime("%Y-%m-%d"))
        self.txt_cc.delete("1.0", "end")
        self.txt_note.delete("1.0", "end")
        self.selected_visit_id = None
        self.lbl_visit_id.config(text="선택된 기록 ID: 없음")

    def refresh_visits(self):
        for x in self.tree_visits.get_children():
            self.tree_visits.delete(x)
        if not self.current_patient_id:
            return
        rows = db_fetch_visits_by_patient(self.conn, self.current_patient_id)
        for vid, vdate, cc, created in rows:
            self.tree_visits.insert("", "end", values=(vid, vdate, (cc or "")[:10], created.split(" ")[0]))

    def get_visit_form(self):
        vdate = self.ent_visit_date.get().strip() or date.today().strftime("%Y-%m-%d")
        cc = self.txt_cc.get("1.0", "end").strip()
        note = self.txt_note.get("1.0", "end").strip()
        return vdate, cc, note

    def on_add_visit(self):
        if not self.current_patient_id:
            messagebox.showwarning("선택", "환자를 먼저 선택하세요.")
            return
        vdate, cc, note = self.get_visit_form()
        db_insert_visit(self.conn, self.current_patient_id, vdate, cc, note)
        self.refresh_visits()
        self.clear_visit_form()
        messagebox.showinfo("완료", "진료기록 추가 완료")

    def on_update_visit(self):
        if not self.selected_visit_id:
            messagebox.showwarning("선택", "수정할 기록을 선택하세요.")
            return
        vdate, cc, note = self.get_visit_form()
        db_update_visit(self.conn, self.selected_visit_id, vdate, cc, note)
        self.refresh_visits()
        messagebox.showinfo("완료", "진료기록 수정 완료")

    def on_delete_visit(self):
        if not self.selected_visit_id:
            messagebox.showwarning("선택", "삭제할 기록을 선택하세요.")
            return
        if messagebox.askyesno("확인", "정말 삭제할까요?"):
            db_delete_visit(self.conn, self.selected_visit_id)
            self.refresh_visits()
            self.clear_visit_form()
            messagebox.showinfo("완료", "삭제 완료")

    def on_select_visit(self, _evt=None):
        sel = self.tree_visits.selection()
        if not sel:
            return
        vid = int(self.tree_visits.item(sel[0])["values"][0])
        row = db_fetch_visit_one(self.conn, vid)
        if not row:
            return
        _id, vdate, cc, note, created = row

        self.selected_visit_id = _id
        self.lbl_visit_id.config(text=f"선택된 기록 ID: {self.selected_visit_id}")

        self.ent_visit_date.delete(0, "end")
        self.ent_visit_date.insert(0, vdate or "")
        self.txt_cc.delete("1.0", "end")
        self.txt_cc.insert("1.0", cc or "")
        self.txt_note.delete("1.0", "end")
        self.txt_note.insert("1.0", note or "")

    # ---------- Rx subtab ----------
    def _build_rx_subtab(self):
        # (4) 약물/처방 DB 저장 + 코드/가격 관리
        drugf = ttk.LabelFrame(self.sub_rx, text="약물 마스터 (코드/가격 관리)")
        drugf.place(x=10, y=10, width=330, height=480)

        ttk.Label(drugf, text="검색").place(x=10, y=20)
        self.ent_drug_search = ttk.Entry(drugf)
        self.ent_drug_search.place(x=70, y=18, width=170)
        ttk.Button(drugf, text="조회", command=self.refresh_drugs).place(x=250, y=16, width=60)

        cols = ("code", "name", "price")
        self.tree_drugs = ttk.Treeview(drugf, columns=cols, show="headings", height=10)
        self.tree_drugs.heading("code", text="코드")
        self.tree_drugs.heading("name", text="이름")
        self.tree_drugs.heading("price", text="가격")
        self.tree_drugs.column("code", width=70, anchor="center")
        self.tree_drugs.column("name", width=140, anchor="w")
        self.tree_drugs.column("price", width=80, anchor="e")
        self.tree_drugs.place(x=10, y=50, width=305, height=220)
        self.tree_drugs.bind("<<TreeviewSelect>>", self.on_select_drug)

        ttk.Label(drugf, text="코드").place(x=10, y=285)
        self.ent_drug_code = ttk.Entry(drugf)
        self.ent_drug_code.place(x=70, y=283, width=110)

        ttk.Label(drugf, text="이름").place(x=10, y=320)
        self.ent_drug_name = ttk.Entry(drugf)
        self.ent_drug_name.place(x=70, y=318, width=245)

        ttk.Label(drugf, text="가격").place(x=10, y=355)
        self.ent_drug_price = ttk.Entry(drugf)
        self.ent_drug_price.place(x=70, y=353, width=110)
        ttk.Label(drugf, text="원").place(x=185, y=355)

        ttk.Button(drugf, text="신규", command=self.clear_drug_form).place(x=10, y=400, width=70)
        ttk.Button(drugf, text="추가", command=self.on_add_drug).place(x=90, y=400, width=70)
        ttk.Button(drugf, text="수정", command=self.on_update_drug).place(x=170, y=400, width=70)
        ttk.Button(drugf, text="삭제", command=self.on_delete_drug).place(x=250, y=400, width=70)

        rxf = ttk.LabelFrame(self.sub_rx, text="처방 (환자별 저장)")
        rxf.place(x=350, y=10, width=350, height=480)

        ttk.Label(rxf, text="처방일").place(x=10, y=20)
        self.ent_rx_date = ttk.Entry(rxf)
        self.ent_rx_date.place(x=80, y=18, width=120)
        self.ent_rx_date.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Label(rxf, text="선택약물").place(x=10, y=55)
        self.lbl_selected_drug = ttk.Label(rxf, text="없음")
        self.lbl_selected_drug.place(x=80, y=55)

        ttk.Label(rxf, text="수량").place(x=10, y=85)
        self.ent_rx_qty = ttk.Entry(rxf)
        self.ent_rx_qty.place(x=80, y=83, width=60)
        self.ent_rx_qty.insert(0, "1")

        ttk.Label(rxf, text="복용지시").place(x=10, y=115)
        self.ent_rx_dir = ttk.Entry(rxf)
        self.ent_rx_dir.place(x=80, y=113, width=250)

        ttk.Label(rxf, text="비고").place(x=10, y=145)
        self.ent_rx_note = ttk.Entry(rxf)
        self.ent_rx_note.place(x=80, y=143, width=250)

        ttk.Button(rxf, text="항목추가", command=self.on_add_rx_item_temp).place(x=10, y=175, width=90)
        ttk.Button(rxf, text="항목삭제", command=self.on_remove_rx_item_temp).place(x=110, y=175, width=90)
        ttk.Button(rxf, text="DB저장", command=self.on_save_prescription).place(x=210, y=175, width=120)

        cols = ("code", "name", "qty", "unit_price", "line_total")
        self.tree_rx_temp = ttk.Treeview(rxf, columns=cols, show="headings", height=8)
        for c, t, w, a in [
            ("code", "코드", 60, "center"),
            ("name", "약명", 100, "w"),
            ("qty", "수량", 50, "e"),
            ("unit_price", "단가", 60, "e"),
            ("line_total", "합계", 60, "e"),
        ]:
            self.tree_rx_temp.heading(c, text=t)
            self.tree_rx_temp.column(c, width=w, anchor=a)
        self.tree_rx_temp.place(x=10, y=215, width=325, height=155)

        list2 = ttk.LabelFrame(rxf, text="저장된 처방")
        list2.place(x=10, y=380, width=325, height=90)

        self.cmb_rx_list = ttk.Combobox(list2, state="readonly")
        self.cmb_rx_list.place(x=10, y=10, width=200)
        ttk.Button(list2, text="조회", command=self.on_load_prescription).place(x=220, y=8, width=90)

        self.lbl_rx_total = ttk.Label(list2, text="총액: 0원")
        self.lbl_rx_total.place(x=10, y=40)

        self.selected_drug_code = None
        self.selected_drug_name = ""
        self.temp_rx_items = []

        self.refresh_drugs()
        self.refresh_prescriptions()

    def refresh_drugs(self):
        keyword = self.ent_drug_search.get().strip() if hasattr(self, "ent_drug_search") else ""
        for x in self.tree_drugs.get_children():
            self.tree_drugs.delete(x)
        rows = db_fetch_drugs(self.conn, keyword=keyword)
        for code, name, price, created in rows:
            self.tree_drugs.insert("", "end", values=(code, name, price))

    def clear_drug_form(self):
        self.ent_drug_code.delete(0, "end")
        self.ent_drug_name.delete(0, "end")
        self.ent_drug_price.delete(0, "end")
        self.selected_drug_code = None
        self.selected_drug_name = ""
        self.lbl_selected_drug.config(text="없음")

    def on_select_drug(self, _evt=None):
        sel = self.tree_drugs.selection()
        if not sel:
            return
        code, name, price = self.tree_drugs.item(sel[0])["values"]
        self.ent_drug_code.delete(0, "end")
        self.ent_drug_code.insert(0, code)
        self.ent_drug_name.delete(0, "end")
        self.ent_drug_name.insert(0, name)
        self.ent_drug_price.delete(0, "end")
        self.ent_drug_price.insert(0, str(price))

        self.selected_drug_code = code
        self.selected_drug_name = name
        self.lbl_selected_drug.config(text=f"{code} / {name}")

    def on_add_drug(self):
        code = self.ent_drug_code.get().strip()
        name = self.ent_drug_name.get().strip()
        price = self.ent_drug_price.get().strip() or "0"
        if not code or not name:
            messagebox.showwarning("필수", "코드/이름은 필수입니다.")
            return
        try:
            db_insert_drug(self.conn, code, name, int(price))
            self.refresh_drugs()
            messagebox.showinfo("완료", "약물 추가 완료")
        except sqlite3.IntegrityError:
            messagebox.showerror("오류", "이미 존재하는 코드입니다.")
        except ValueError:
            messagebox.showerror("오류", "가격은 숫자여야 합니다.")

    def on_update_drug(self):
        code = self.ent_drug_code.get().strip()
        name = self.ent_drug_name.get().strip()
        price = self.ent_drug_price.get().strip() or "0"
        if not code:
            messagebox.showwarning("선택", "수정할 약물을 선택하세요.")
            return
        try:
            db_update_drug(self.conn, code, name, int(price))
            self.refresh_drugs()
            messagebox.showinfo("완료", "약물 수정 완료")
        except ValueError:
            messagebox.showerror("오류", "가격은 숫자여야 합니다.")

    def on_delete_drug(self):
        code = self.ent_drug_code.get().strip()
        if not code:
            messagebox.showwarning("선택", "삭제할 약물을 선택하세요.")
            return
        if messagebox.askyesno("확인", f"{code} 약물을 삭제할까요?"):
            try:
                db_delete_drug(self.conn, code)
                self.refresh_drugs()
                self.clear_drug_form()
                messagebox.showinfo("완료", "삭제 완료")
            except sqlite3.IntegrityError:
                messagebox.showerror("오류", "이미 처방에 사용된 약물은 삭제할 수 없습니다.")

    def on_add_rx_item_temp(self):
        if not self.current_patient_id:
            messagebox.showwarning("선택", "환자를 먼저 선택하세요.")
            return
        if not self.selected_drug_code:
            messagebox.showwarning("선택", "약물을 먼저 선택하세요.")
            return

        qty_s = self.ent_rx_qty.get().strip() or "1"
        try:
            qty = int(qty_s)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("오류", "수량은 1 이상의 정수여야 합니다.")
            return

        drug = db_fetch_drug_one(self.conn, self.selected_drug_code)
        if not drug:
            messagebox.showerror("오류", "약물 정보가 없습니다.")
            return
        unit_price = int(drug[2])

        item = {
            "drug_code": self.selected_drug_code,
            "drug_name": self.selected_drug_name,
            "qty": qty,
            "unit_price": unit_price,
            "directions": self.ent_rx_dir.get().strip(),
            "note": self.ent_rx_note.get().strip(),
        }
        self.temp_rx_items.append(item)
        self.refresh_rx_temp_tree()

        self.ent_rx_qty.delete(0, "end")
        self.ent_rx_qty.insert(0, "1")
        self.ent_rx_dir.delete(0, "end")
        self.ent_rx_note.delete(0, "end")

    def on_remove_rx_item_temp(self):
        sel = self.tree_rx_temp.selection()
        if not sel:
            return
        idx = int(self.tree_rx_temp.item(sel[0])["text"])
        if 0 <= idx < len(self.temp_rx_items):
            self.temp_rx_items.pop(idx)
            self.refresh_rx_temp_tree()

    def refresh_rx_temp_tree(self):
        for x in self.tree_rx_temp.get_children():
            self.tree_rx_temp.delete(x)

        total = 0
        for idx, it in enumerate(self.temp_rx_items):
            line_total = int(it["qty"]) * int(it["unit_price"])
            total += line_total
            self.tree_rx_temp.insert(
                "", "end", text=str(idx),
                values=(it["drug_code"], it["drug_name"], it["qty"], it["unit_price"], line_total)
            )
        self.lbl_rx_total.config(text=f"총액: {total:,}원")

    def on_save_prescription(self):
        if not self.current_patient_id:
            messagebox.showwarning("선택", "환자를 먼저 선택하세요.")
            return
        if not self.temp_rx_items:
            messagebox.showwarning("내용", "처방 항목이 비어있습니다.")
            return
        rx_date = self.ent_rx_date.get().strip() or date.today().strftime("%Y-%m-%d")

        try:
            rx_id = db_create_prescription(self.conn, self.current_patient_id, rx_date, self.temp_rx_items)
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")
            return

        self.temp_rx_items = []
        self.refresh_rx_temp_tree()
        self.refresh_prescriptions()
        messagebox.showinfo("완료", f"처방 저장 완료 (RX ID: {rx_id})")

    def refresh_prescriptions(self):
        if not hasattr(self, "cmb_rx_list"):
            return
        self.cmb_rx_list["values"] = []
        self.cmb_rx_list.set("")
        self.lbl_rx_total.config(text="총액: 0원")

        if not self.current_patient_id:
            return

        rows = db_fetch_prescriptions_by_patient(self.conn, self.current_patient_id)
        values = [f"{rid} | {rx_date} | {total:,}원" for (rid, rx_date, created, total) in rows]
        self.cmb_rx_list["values"] = values
        if values:
            self.cmb_rx_list.current(0)

    def on_load_prescription(self):
        s = self.cmb_rx_list.get().strip()
        if not s:
            return
        rid = int(s.split("|")[0].strip())
        items = db_fetch_prescription_items(self.conn, rid)
        if not items:
            messagebox.showinfo("정보", "처방 항목이 없습니다.")
            return

        self.temp_rx_items = []
        for (_iid, code, name, qty, unit_price, line_total, directions, note) in items:
            self.temp_rx_items.append({
                "drug_code": code,
                "drug_name": name,
                "qty": int(qty),
                "unit_price": int(unit_price),
                "directions": directions or "",
                "note": note or "",
            })
        self.refresh_rx_temp_tree()

    def on_closing(self):
        try:
            self.conn.close()
        except Exception:
            pass
        self.destroy()


# ------------------------------ Main ------------------------------
if __name__ == "__main__":
    # 0) DB 준비 + 기본 계정 생성

    print("START")

    conn = db_connect()
    ensure_default_user(conn)

    # 1) 로그인 먼저 (숨김 root로 모달 처리)
    root = tk.Tk()
    root.withdraw()

    login = LoginWindow(root, conn)
    root.wait_window(login)

    if not login.ok:
        try:
            conn.close()
        except Exception:
            pass
        root.destroy()
    else:
        root.destroy()
        app = MiniEMRv3(conn)
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
