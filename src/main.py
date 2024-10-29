import tkinter as tk
from tkinter import filedialog, messagebox
import openpyxl
import customtkinter
from PIL import Image, ImageTk
import pandas as pd
from lib_taxonomia.rev_taxonomia import revisar_taxonomia
import threading
import multiprocessing

class TaxoScanApp:
    def __init__(self):
        customtkinter.deactivate_automatic_dpi_awareness()
        self.root = customtkinter.CTk()
        self.root.title("TAXOSCAN")
        self._centrar_ventana(500, 600)
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("dark-blue")

        self.dir_file = None
        self.df_datos = None
        self.label = None
        self.combo_sheet_name = None
        self.frame_combo_shee_name = None
        self.frame_columns = None
        self.combo_clase = None
        self.combo_orden = None
        self.combo_family = None
        self.combo_genero = None
        self.combo_especie = None
        self.ejecutar_validador = None
        self.mensaje_campos = None

        self._crear_gui()

    def _centrar_ventana(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _crear_gui(self):
        image_cargue = Image.open("../assets/images/logo-anla3.png").resize((300, 70), Image.LANCZOS)
        imagen_gbif = Image.open("../assets/images/logo-gbif.png").resize((100, 50), Image.LANCZOS)
        tk_image_cargue = ImageTk.PhotoImage(image_cargue)
        tk_image_gbif = ImageTk.PhotoImage(imagen_gbif)
        
        label_image_cargue = tk.Label(self.root, image=tk_image_cargue)
        label_image_cargue.place(relx=0.4)
        
        label_image_gbif = tk.Label(self.root, image=tk_image_gbif)
        label_image_gbif.place(rely=0.84, relx=0.01)
        
        customtkinter.CTkLabel(self.root, text='En caso de dudas o inquietudes comunicarse a centromonitoreo@anla.gov.co', font=('arial',10)).place(rely=0.94, relx=0.02)
        
        self.frame_seleccion_archivo = customtkinter.CTkFrame(self.root, fg_color="transparent")
        customtkinter.CTkLabel(self.frame_seleccion_archivo, text='Ruta del archivo:').grid(column=0, row=0, padx=10)
        
        self.entry_dir_dile = customtkinter.CTkEntry(self.frame_seleccion_archivo, width=320)
        self.entry_dir_dile.grid(column=1, row=0, padx=10)
        
        boton_select_file = customtkinter.CTkButton(self.frame_seleccion_archivo, text='↑', command=self._seleccionar_excel, width=10)
        boton_select_file.grid(column=2, row=0, padx=10)
        
        self.frame_seleccion_archivo.pack(fill='x', pady=(100,0))
        self.root.after(1000, self._mostrar_mensaje)
        self.root.mainloop()

    def _mostrar_mensaje(self):
        self.root.update_idletasks()
        messagebox.showinfo(
            'Info', 
            'TAXOSCAN es una herramienta desarrollada por el Centro de Monitoreo de Recursos Naturales de la ANLA con el propósito de mejorar el registro taxonómico.',
            parent=self.root
        )

    def _seleccionar_excel(self):
        excel_file = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx"), ("Archivos Macro", "*.xlsm")])
        if excel_file:
            self.dir_file = excel_file
            self.entry_dir_dile.insert(tk.END, excel_file)
            libro_excel = openpyxl.load_workbook(excel_file)
            nombres_pestanas = libro_excel.sheetnames
            libro_excel.close()
            self._crear_combobox_hojas(nombres_pestanas)

    def _crear_combobox_hojas(self, nombres_pestanas):
        if self.frame_combo_shee_name:
            self.frame_combo_shee_name.destroy()
        self.frame_combo_shee_name = customtkinter.CTkFrame(self.root, fg_color="transparent")
        
        customtkinter.CTkLabel(self.frame_combo_shee_name, text='Hoja de datos:').grid(column=0, row=0, padx=10)
        
        self.combo_sheet_name = customtkinter.CTkComboBox(
            self.frame_combo_shee_name,
            values=nombres_pestanas,
            width=200,
        )
        self.combo_sheet_name.grid(column=1, row=0, padx=10)
        
        boton_open_file = customtkinter.CTkButton(self.frame_combo_shee_name, text='Cargar columnas', command=self._read_file)
        boton_open_file.grid(column=2, row=0, padx=10)
        
        self.frame_combo_shee_name.pack(fill='x', pady=(10, 0))

    def _read_file(self):
        self.df_datos = pd.read_excel(self.dir_file, sheet_name=self.combo_sheet_name.get())
        columns = self.df_datos.columns.tolist()
        self._crear_combobox_columnas(columns)

    def _crear_combobox_columnas(self, columns):
        if self.frame_columns:
            self.frame_columns.destroy()
        self.frame_columns = customtkinter.CTkFrame(self.root, fg_color="transparent")

        self.mensaje_campos = customtkinter.CTkLabel(
            self.root, text='Seleccione los campos asociados a cada nivel taxonómico:', anchor='w'
        )
        self.mensaje_campos.pack(padx=10, pady=(10, 0), anchor='w')

        columnas_por_defecto = {
            "CLASE": None,
            "ORDEN": None,
            "FAMILIA": None,
            "GENERO": None,
            "ESPECIE": None,
        }

        # Guardar los ComboBoxes como atributos de la clase
        self.combo_clase = None
        self.combo_orden = None
        self.combo_family = None
        self.combo_genero = None
        self.combo_especie = None

        for i, (label_text, _) in enumerate(columnas_por_defecto.items()):
            customtkinter.CTkLabel(self.frame_columns, text=f'{label_text}:', anchor='w').grid(column=0, row=i, sticky='w')

            combo_box = customtkinter.CTkComboBox(self.frame_columns, values=columns)
            if label_text in columns:
                combo_box.set(label_text)  # Establecer valor por defecto si está presente

            combo_box.grid(column=1, row=i, padx=45, pady=5)

            # Asignar el ComboBox a un atributo de la clase
            if label_text == "CLASE":
                self.combo_clase = combo_box
            elif label_text == "ORDEN":
                self.combo_orden = combo_box
            elif label_text == "FAMILIA":
                self.combo_family = combo_box
            elif label_text == "GENERO":
                self.combo_genero = combo_box
            elif label_text == "ESPECIE":
                self.combo_especie = combo_box

        self.ejecutar_validador = customtkinter.CTkButton(self.root, text='Ejecutar Validador', command=self._validador)
        self.frame_columns.pack(fill='x', padx=10, pady=(2, 10))
        self.ejecutar_validador.pack(pady=10)

    def _validador(self):
        dict_rename = {
            self.combo_clase.get(): 'CLASE',
            self.combo_orden.get(): 'ORDEN',
            self.combo_family.get(): 'FAMILIA',
            self.combo_genero.get(): 'GENERO',
            self.combo_especie.get(): 'ESPECIE'
        }
        
        # Asegúrate de que 'dict_rename' tenga valores válidos
        if all(value in self.df_datos.columns for value in dict_rename.keys()):
            self.df_datos = self.df_datos.rename(columns=dict_rename)
            messagebox.showinfo("Alerta", "¡Asegurar que los archivos Excel se encuentran cerrados!")
            t = threading.Thread(target=revisar_taxonomia, args=(self.dir_file, self.df_datos, self.combo_sheet_name.get()))
            t.start()
            self._schedule_check(t)
        else:
            messagebox.showerror("Error", "Una o más columnas seleccionadas no están disponibles en los datos.")

    def _schedule_check(self, t):
        if not t.is_alive():
            if self.label:
                self.label.configure(text='Proceso finalizado 😁')
        else:
            self.root.after(1000, self._schedule_check, t)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = TaxoScanApp()