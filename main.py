import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from datetime import datetime
import os

import lexer as ruby_lexer
import parser as ruby_parser

# =============================================================================
# CONSTANTES DE ESTILO
# =============================================================================
BG_MAIN       = "#2b2b2b"
BG_EDITOR     = "#1e1e1e"
BG_ERROR      = "#2d0000"
BG_ROW_A      = "#2b2b2b"
BG_ROW_B      = "#333333"
FG_MAIN       = "#f0f0f0"
FG_ERROR      = "#ff5555"
FG_ACCENT     = "#c8102e"
FONT_MONO     = ("Courier", 11)
FONT_UI       = ("Segoe UI", 10)
FONT_TITLE    = ("Segoe UI", 13, "bold")
FONT_SMALL    = ("Segoe UI", 9)


# =============================================================================
# WIDGET: Editor con numeración de líneas
# =============================================================================
class CodeEditor(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_MAIN)

        self.line_numbers = tk.Text(
            self, width=4, state="disabled",
            bg="#252526", fg="#858585",
            font=FONT_MONO, relief="flat",
            padx=4, pady=4,
            cursor="arrow", selectbackground="#252526",
        )
        self.line_numbers.pack(side="left", fill="y")

        self.text = tk.Text(
            self, bg=BG_EDITOR, fg=FG_MAIN,
            font=FONT_MONO, relief="flat",
            insertbackground=FG_MAIN,
            selectbackground="#264f78",
            undo=True, wrap="none",
            padx=6, pady=4,
        )
        self.text.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(self, orient="vertical",
                                  command=self._scroll_both)
        scroll_y.pack(side="right", fill="y")
        self.text.config(yscrollcommand=scroll_y.set)

        self.text.bind("<KeyRelease>", self._update_lines)
        self.text.bind("<MouseWheel>", self._update_lines)
        self.text.bind("<Button-1>", self._update_lines)
        self._update_lines()

    def _scroll_both(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _update_lines(self, event=None):
        self.after(10, self._redraw_lines)

    def _redraw_lines(self):
        content = self.text.get("1.0", "end-1c")
        n_lines = content.count("\n") + 1
        nums = "\n".join(str(i) for i in range(1, n_lines + 1))
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", nums)
        self.line_numbers.config(state="disabled")
        self.line_numbers.yview_moveto(self.text.yview()[0])

    def get(self):
        return self.text.get("1.0", "end-1c")

    def set(self, content):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self._redraw_lines()

    def clear(self):
        self.text.delete("1.0", "end")
        self._redraw_lines()


# =============================================================================
# PESTAÑA LÉXICO
# =============================================================================
class TabLexico(tk.Frame):
    def __init__(self, parent, status_cb):
        super().__init__(parent, bg=BG_MAIN)
        self.status_cb = status_cb
        self._build()

    def _build(self):
        # ── Layout principal: izquierda / derecha ──────────────────────────
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BG_MAIN, sashwidth=5,
                               sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ── PANEL IZQUIERDO ────────────────────────────────────────────────
        left = tk.Frame(paned, bg=BG_MAIN)
        paned.add(left, minsize=300)

        tk.Label(left, text="Código Ruby", bg=BG_MAIN, fg=FG_MAIN,
                 font=FONT_UI).pack(anchor="w", pady=(0, 4))

        self.editor = CodeEditor(left)
        self.editor.pack(fill="both", expand=True)

        btn_frame = tk.Frame(left, bg=BG_MAIN)
        btn_frame.pack(fill="x", pady=(6, 0))

        self._btn(btn_frame, "📂 Cargar .rb", self._cargar).pack(
            side="left", padx=(0, 6))
        self._btn(btn_frame, "🗑 Limpiar", self._limpiar).pack(
            side="left", padx=(0, 6))
        self._btn(btn_frame, "▶ Analizar", self._analizar,
                  accent=True).pack(side="left")

        # ── PANEL DERECHO ──────────────────────────────────────────────────
        right = tk.Frame(paned, bg=BG_MAIN)
        paned.add(right, minsize=340)

        # Tokens
        tk.Label(right, text="Tokens reconocidos", bg=BG_MAIN, fg=FG_MAIN,
                 font=FONT_UI).pack(anchor="w", pady=(0, 4))

        tree_frame = tk.Frame(right, bg=BG_MAIN)
        tree_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                        background=BG_ROW_A, foreground=FG_MAIN,
                        fieldbackground=BG_ROW_A,
                        rowheight=22, font=FONT_SMALL)
        style.configure("Dark.Treeview.Heading",
                        background="#3c3c3c", foreground=FG_MAIN,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", "#264f78")],
                  foreground=[("selected", FG_MAIN)])

        cols = ("#", "Tipo", "Valor", "Línea")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 style="Dark.Treeview", selectmode="browse")
        self.tree.heading("#",      text="#")
        self.tree.heading("Tipo",   text="Tipo")
        self.tree.heading("Valor",  text="Valor")
        self.tree.heading("Línea",  text="Línea")
        self.tree.column("#",     width=42,  anchor="center", stretch=False)
        self.tree.column("Tipo",  width=160, anchor="w")
        self.tree.column("Valor", width=180, anchor="w")
        self.tree.column("Línea", width=52,  anchor="center", stretch=False)

        self.tree.tag_configure("odd",  background=BG_ROW_A)
        self.tree.tag_configure("even", background=BG_ROW_B)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Errores
        tk.Label(right, text="Errores léxicos", bg=BG_MAIN, fg=FG_MAIN,
                 font=FONT_UI).pack(anchor="w", pady=(10, 4))

        self.error_box = tk.Text(right, height=6, bg=BG_ERROR, fg=FG_ERROR,
                                 font=FONT_SMALL, relief="flat",
                                 state="disabled", padx=6, pady=4)
        self.error_box.pack(fill="x")

    # ── helpers ───────────────────────────────────────────────────────────

    def _btn(self, parent, text, cmd, accent=False):
        bg = FG_ACCENT if accent else "#3c3c3c"
        fg = "#ffffff"
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, activebackground="#a00d24" if accent else "#505050",
                      activeforeground=fg, relief="flat",
                      font=FONT_UI, padx=10, pady=4, cursor="hand2",
                      bd=0, highlightthickness=0)
        return b

    def _cargar(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo Ruby",
            filetypes=[("Ruby files", "*.rb"), ("All files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.set(f.read())
            self.status_cb(f"Archivo cargado: {os.path.basename(path)}")

    def _limpiar(self):
        self.editor.clear()
        self._limpiar_resultados()
        self.status_cb("Listo")

    def _limpiar_resultados(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.error_box.config(state="normal")
        self.error_box.delete("1.0", "end")
        self.error_box.config(state="disabled")

    def _analizar(self):
        codigo = self.editor.get().strip()
        if not codigo:
            messagebox.showwarning("Sin código", "Escribe o carga código Ruby primero.")
            return

        self.status_cb("Analizando...")
        self._limpiar_resultados()
        self.update_idletasks()

        try:
            tok_list = ruby_lexer.analizar(codigo)
            errores  = ruby_lexer.lexer.errores

            for i, tok in enumerate(tok_list):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", values=(
                    i + 1, tok["tipo"], tok["valor"], tok["linea"]
                ), tags=(tag,))

            if errores:
                self.error_box.config(state="normal")
                for err in errores:
                    self.error_box.insert("end", f"  Línea {err['linea']}: {err['mensaje']}\n")
                self.error_box.config(state="disabled")

            self.status_cb(
                f"{len(tok_list)} tokens reconocidos"
                + (f", {len(errores)} error(es)" if errores else ", sin errores")
            )
        except Exception as e:
            messagebox.showerror("Error interno", str(e))
            self.status_cb("Error durante el análisis")

    def get_tokens_text(self):
        """Devuelve el contenido de la tabla como texto para exportar."""
        lines = [f'{"#":<6}{"TIPO":<22}{"VALOR":<30}{"LÍNEA"}']
        lines.append("=" * 65)
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            lines.append(f'{vals[0]:<6}{vals[1]:<22}{vals[2]:<30}{vals[3]}')
        return "\n".join(lines)

    def get_errores(self):
        return ruby_lexer.lexer.errores if hasattr(ruby_lexer.lexer, "errores") else []


# =============================================================================
# PESTAÑA SINTÁCTICO
# =============================================================================
class TabSintactico(tk.Frame):
    def __init__(self, parent, status_cb):
        super().__init__(parent, bg=BG_MAIN)
        self.status_cb = status_cb
        self._build()

    def _build(self):
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BG_MAIN, sashwidth=5,
                               sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ── PANEL IZQUIERDO: editor ────────────────────────────────────────
        left = tk.Frame(paned, bg=BG_MAIN)
        paned.add(left, minsize=300)

        tk.Label(left, text="Código Ruby", bg=BG_MAIN, fg=FG_MAIN,
                 font=FONT_UI).pack(anchor="w", pady=(0, 4))

        self.editor = CodeEditor(left)
        self.editor.pack(fill="both", expand=True)

        btn_frame = tk.Frame(left, bg=BG_MAIN)
        btn_frame.pack(fill="x", pady=(6, 0))
        self._btn(btn_frame, "📂 Cargar .rb", self._cargar).pack(
            side="left", padx=(0, 6))
        self._btn(btn_frame, "🗑 Limpiar", self._limpiar).pack(
            side="left", padx=(0, 6))
        self._btn(btn_frame, "▶ Analizar", self._analizar,
                  accent=True).pack(side="left")

        # ── PANEL DERECHO: estado + errores ────────────────────────────────
        right = tk.Frame(paned, bg=BG_MAIN)
        paned.add(right, minsize=340)

        tk.Label(right, text="Resultado del análisis", bg=BG_MAIN, fg=FG_MAIN,
                 font=FONT_UI).pack(anchor="w", pady=(0, 4))

        self.estado_var = tk.StringVar(value="Sin analizar")
        self.estado_lbl = tk.Label(right, textvariable=self.estado_var,
                                   bg="#1e1e1e", fg="#888888", anchor="w",
                                   font=("Segoe UI", 11, "bold"),
                                   padx=10, pady=8)
        self.estado_lbl.pack(fill="x", pady=(0, 8))

        tk.Label(right, text="Errores sintácticos", bg=BG_MAIN, fg=FG_MAIN,
                 font=FONT_UI).pack(anchor="w", pady=(0, 4))

        tree_frame = tk.Frame(right, bg=BG_MAIN)
        tree_frame.pack(fill="both", expand=True)

        cols = ("#", "Línea", "Columna", "Token", "Mensaje")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 style="Dark.Treeview", selectmode="browse")
        for c, w, anchor in (("#", 40, "center"), ("Línea", 56, "center"),
                             ("Columna", 64, "center"), ("Token", 110, "w"),
                             ("Mensaje", 320, "w")):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor=anchor,
                             stretch=(c == "Mensaje"))
        self.tree.tag_configure("odd", background=BG_ROW_A)
        self.tree.tag_configure("even", background=BG_ROW_B)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    # ── helpers ────────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, accent=False):
        bg = FG_ACCENT if accent else "#3c3c3c"
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg="#ffffff",
                      activebackground="#a00d24" if accent else "#505050",
                      activeforeground="#ffffff", relief="flat",
                      font=FONT_UI, padx=10, pady=4, cursor="hand2",
                      bd=0, highlightthickness=0)
        return b

    def _cargar(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo Ruby",
            filetypes=[("Ruby files", "*.rb"), ("All files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.set(f.read())
            self.status_cb(f"Archivo cargado: {os.path.basename(path)}")

    def _limpiar(self):
        self.editor.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.estado_var.set("Sin analizar")
        self.estado_lbl.config(fg="#888888")
        self.status_cb("Listo")

    def _analizar(self):
        codigo = self.editor.get().strip()
        if not codigo:
            messagebox.showwarning("Sin código",
                                   "Escribe o carga código Ruby primero.")
            return

        self.status_cb("Analizando sintaxis...")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_idletasks()

        try:
            resultado = ruby_parser.analizar(codigo)
            errores = resultado["errores"]

            if resultado["ok"]:
                self.estado_var.set("✔  Código sintácticamente VÁLIDO")
                self.estado_lbl.config(fg="#5fd35f")
            else:
                self.estado_var.set(
                    f"✘  CON ERRORES — {len(errores)} error(es) de sintaxis")
                self.estado_lbl.config(fg=FG_ERROR)

            for i, err in enumerate(errores):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", values=(
                    i + 1, err["linea"], err["columna"],
                    err["token"], err["mensaje"]
                ), tags=(tag,))

            self.status_cb(
                "Análisis sintáctico correcto" if resultado["ok"]
                else f"{len(errores)} error(es) de sintaxis")
        except Exception as e:
            messagebox.showerror("Error interno", str(e))
            self.status_cb("Error durante el análisis")


# =============================================================================
# PESTAÑA PRÓXIMAMENTE
# =============================================================================
class TabProximamente(tk.Frame):
    def __init__(self, parent, nombre):
        super().__init__(parent, bg=BG_MAIN)
        tk.Label(self, text=f"Analizador {nombre}",
                 bg=BG_MAIN, fg=FG_MAIN, font=FONT_TITLE).pack(pady=(60, 12))
        tk.Label(self, text="🚧  Próximamente — Avance 2",
                 bg=BG_MAIN, fg="#888888", font=("Segoe UI", 12)).pack()


# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador de Ruby - ESPOL")
        self.geometry("1100x680")
        self.minsize(800, 540)
        self.configure(bg=BG_MAIN)
        self._nombre_dev = ""
        self._build()

    def _build(self):
        # ── Encabezado ────────────────────────────────────────────────────
        header = tk.Frame(self, bg=FG_ACCENT, height=46)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="  Analizador Léxico de Ruby",
                 bg=FG_ACCENT, fg="#ffffff",
                 font=FONT_TITLE).pack(side="left", padx=12)
        tk.Label(header, text="ESPOL · Lenguajes de Programación",
                 bg=FG_ACCENT, fg="#ffcccc",
                 font=FONT_SMALL).pack(side="right", padx=12)

        # ── Notebook ──────────────────────────────────────────────────────
        style = ttk.Style()
        style.configure("Dark.TNotebook",
                        background=BG_MAIN, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background="#3c3c3c", foreground=FG_MAIN,
                        padding=[14, 6], font=FONT_UI)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", BG_MAIN)],
                  foreground=[("selected", "#ffffff")])

        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True)

        self.tab_lexico = TabLexico(nb, self._set_status)
        nb.add(self.tab_lexico, text="  Léxico  ")

        self.tab_sintactico = TabSintactico(nb, self._set_status)
        nb.add(self.tab_sintactico, text="  Sintáctico  ")

        nb.add(TabProximamente(nb, "Semántico"),  text="  Semántico  ")

        # ── Barra inferior ────────────────────────────────────────────────
        bar = tk.Frame(self, bg="#1e1e1e", height=36)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Button(bar, text="💾 Exportar log",
                  command=self._exportar_log,
                  bg="#3c3c3c", fg=FG_MAIN,
                  activebackground="#505050", activeforeground=FG_MAIN,
                  relief="flat", font=FONT_SMALL, padx=10,
                  cursor="hand2", bd=0, highlightthickness=0
                  ).pack(side="left", padx=8, pady=5)

        self.status_var = tk.StringVar(value="Listo")
        tk.Label(bar, textvariable=self.status_var,
                 bg="#1e1e1e", fg="#888888",
                 font=FONT_SMALL).pack(side="left", padx=4)

        tk.Label(bar, text="ESPOL © 2026",
                 bg="#1e1e1e", fg="#555555",
                 font=FONT_SMALL).pack(side="right", padx=12)

    def _set_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    def _exportar_log(self):
        if not self._nombre_dev:
            nombre = simpledialog.askstring(
                "Nombre del desarrollador",
                "Ingresa tu nombre (ej: AnnabellaSanchez):",
                parent=self)
            if not nombre:
                return
            self._nombre_dev = nombre.strip().replace(" ", "")

        tokens_text = self.tab_lexico.get_tokens_text()
        errores     = self.tab_lexico.get_errores()

        if not tokens_text.strip():
            messagebox.showwarning("Sin datos",
                                   "Primero analiza un archivo antes de exportar.")
            return

        now      = datetime.now().strftime("%d-%m-%Y-%Hh%M")
        filename = f"lexico-{self._nombre_dev}-{now}.txt"
        os.makedirs("logs", exist_ok=True)
        filepath = os.path.join("logs", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Desarrollador  : {self._nombre_dev}\n")
            f.write(f"Fecha/Hora     : {now}\n")
            f.write("=" * 65 + "\n")
            f.write(tokens_text + "\n")
            if errores:
                f.write("\n" + "=" * 65 + "\n")
                f.write("ERRORES LÉXICOS\n")
                f.write("=" * 65 + "\n")
                for err in errores:
                    f.write(f"  Línea {err['linea']}: {err['mensaje']}\n")

        messagebox.showinfo("Log exportado",
                            f"Guardado en:\n{os.path.abspath(filepath)}")
        self._set_status(f"Log exportado: {filename}")


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
