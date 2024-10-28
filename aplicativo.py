# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 12:35:16 2024

@author: diego
"""

import tkinter as tk
from tkinter import filedialog
import subprocess
import openpyxl
import customtkinter
from PIL import Image, ImageTk
import pandas as pd
from rev_taxonomia import revisar_taxonomia
from tkinter import messagebox
import threading
import multiprocessing

customtkinter.deactivate_automatic_dpi_awareness()
DF_DATA = None
combo_sheet_name = None
dir_file = None
frame_combo_shee_name = None
df_datos = None
frame_columns = None
combo_clase = None
combo_orden = None
combo_family = None
combo_genero = None
combo_especie = None
root = None
ejecutar_validador = None
label:customtkinter.CTkLabel = None
mensaje_campos = None


def check_if_done(t):
    """AI is creating summary for check_if_done

    Args:
        t ([type]): [description]
    """
    if not t.is_alive():
        label.configure(text='Proceso finalizado 😁')
    else:
        schedule_check(t)

def schedule_check(t):
    """AI is creating summary for schedule_check

    Args:
        t ([type]): [description]
    """
    root.after(1000, check_if_done, t)
    
    
def validador():
    global df_datos, label
    dict_rename = {
        combo_clase.get():'CLASE',
        combo_orden.get():'ORDEN',
        combo_family.get():'FAMILIA',
        combo_genero.get():'GENERO',
        combo_especie.get():'ESPECIE'      
    }
    df_datos = df_datos.rename(columns=dict_rename)
    messagebox.showinfo("Alerta", "¡Asegurar que los archivos excel se encuentran cerrados!")
    t = threading.Thread(
        target=revisar_taxonomia,
        args=(dir_file, df_datos, combo_sheet_name.get())
        )
    
    t.start()
    schedule_check(t)
    if label is not None:
        label.destroy()
    label = customtkinter.CTkLabel(root, text = 'Procesando información, no cierres el programa por favor ... 🤔')
    label.pack()
 #   revisar_taxonomia(dir_file, df_datos)
    
def change_sheet(event):
    global frame_columns, label, mensaje_campos
    if frame_columns is not None:
        frame_columns.destroy()
    if label is not None:
        label.destroy()
        ejecutar_validador.destroy()
        mensaje_campos.destroy()

def read_file():
    global df_datos, frame_columns, combo_clase, combo_orden, combo_family, combo_genero, combo_especie, ejecutar_validador, label, mensaje_campos

    df_datos = pd.read_excel(dir_file, sheet_name = combo_sheet_name.get())
    columns = df_datos.columns.tolist()
    if frame_columns is not None:
        frame_columns.destroy()
        ejecutar_validador.destroy()
    if label is not None:
        label.destroy()
    if mensaje_campos is not None:
        mensaje_campos.destroy()
    frame_columns = customtkinter.CTkFrame(root,fg_color="transparent")
    mensaje_campos=customtkinter.CTkLabel(root, text='Seleccione los campos asociados a cada nivel taxonómico:', anchor='w')
    mensaje_campos.pack(padx=10, pady=(10,0),anchor='w')
    customtkinter.CTkLabel(frame_columns, text='Clase:     ', anchor='w').grid(column=0, row=0, sticky='w')
    combo_clase = customtkinter.CTkComboBox(frame_columns, values=columns)
    combo_clase.grid(column=1, row=0, padx=45, pady=5)
    
    customtkinter.CTkLabel(frame_columns, text='Orden:    ', anchor='w').grid(column=0, row=1, sticky='w')
    combo_orden = customtkinter.CTkComboBox(frame_columns, values=columns)
    combo_orden.grid(column=1, row=1, padx=45, pady=5)
    
    customtkinter.CTkLabel(frame_columns, text='Familia:        ', anchor='w').grid(column=0, row=2, sticky='w')
    combo_family = customtkinter.CTkComboBox(frame_columns, values=columns)
    combo_family.grid(column=1, row=2, padx=45, pady=5)
    
    customtkinter.CTkLabel(frame_columns, text='Genero:', anchor='w').grid(column=0, row=3, sticky='w')
    combo_genero = customtkinter.CTkComboBox(frame_columns, values=columns)
    combo_genero.grid(column=1, row=3, padx=45, pady=5)
    
    customtkinter.CTkLabel(frame_columns, text='Especie:', anchor='w').grid(column=0, row=4, sticky='w')
    combo_especie = customtkinter.CTkComboBox(frame_columns, values=columns)
    combo_especie.grid(column=1, row=4, padx=45, pady=5)
    
    ejecutar_validador = customtkinter.CTkButton(root, text ='Ejecutar Validador', command= validador)
    
    frame_columns.pack(fill='x', padx=10, pady=(2,10))
    ejecutar_validador.pack(pady=10)
    

    
# Función para seleccionar el archivo de Excel
def seleccionar_excel():
    global frame_combo_shee_name, entry_dir_dile, dir_file, combo_sheet_name, frame_columns,ejecutar_validador, label, mensaje_campos
    excel_file = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx"), ("Archivos Macro", "*.xlsm")])
    if excel_file is not None:
        dir_file = excel_file
        entry_dir_dile.insert(tk.END, excel_file)
        libro_excel = openpyxl.load_workbook(excel_file)
        nombres_pestanas = libro_excel.sheetnames
        libro_excel.close()
        if frame_combo_shee_name is not None:
            frame_combo_shee_name.destroy()
        if frame_columns is not None:
            frame_columns.destroy()
            ejecutar_validador.destroy()
        if label is not None:
            label.destroy()
        if mensaje_campos is not None:
            mensaje_campos.destroy()
        frame_combo_shee_name = customtkinter.CTkFrame(root,fg_color="transparent")
        customtkinter.CTkLabel(frame_combo_shee_name, text='Hoja de datos:    ').grid(column=0, row=0, padx=10)
        combo_sheet_name = customtkinter.CTkComboBox(frame_combo_shee_name, values=nombres_pestanas, width=200,command=change_sheet)
        combo_sheet_name.grid(column=1, row=0, padx=10)
        boton_open_file = customtkinter.CTkButton(frame_combo_shee_name, text='Cargar columnas', command=read_file)
        boton_open_file.grid(column=2, row=0, padx=10)
        frame_combo_shee_name.pack(fill='x',pady=(10,0))
    return excel_file

def centrar_ventana(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    root.geometry(f'{width}x{height}+{x}+{y}')
    
def mostrar_mensaje():
    root.update_idletasks()  # Asegura que la ventana esté completamente actualizada
    # Calcular la posición central de la ventana principal
    x = root.winfo_x() + root.winfo_width() // 2
    y = root.winfo_y() + root.winfo_height() // 2
    
    # Mostrar el mensaje en el centro de la ventana principal
    messagebox.showinfo('Info', 'TAXOSCAN es una herramienta desarrollada por el Centro de Monitoreo de Recursos Naturales de la ANLA con el propósito de mejorar el registro taxonómico. Esta herramienta utiliza valores de correlación basados en datos provenientes del GBIF. Sin embargo, es importante destacar que TAXOSCAN no emite conceptos taxonómicos definitivos.', parent=root)
    
   # messagebox.geometry(f"+{x}+{y}")

def main():
    global root, frame_seleccion_archivo, entry_dir_dile
    root = customtkinter.CTk()
    root.title("TAXOSCAN")
    centrar_ventana(root, 500, 600)
#    root.geometry(f"500x550+0+0")
    customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
    customtkinter.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

    image_cargue = Image.open("./logo-anla3.png").resize((300, 70), Image.LANCZOS)
    imagen_gbif = Image.open("./logo-gbif.png").resize((100, 50), Image.LANCZOS)
    tk_image_cargue = ImageTk.PhotoImage(image_cargue)
    tk_image_gbif= ImageTk.PhotoImage(imagen_gbif)
    
    label_image_cargue = tk.Label( root, image=tk_image_cargue)
    label_image_cargue.place(relx=0.4)
    label_image_gbif = tk.Label( root, image=tk_image_gbif)
    label_image_gbif.place(rely=0.84, relx=0.01)
    customtkinter.CTkLabel(root, text='En caso de dudas o inquietudes comunicarse a centromonitoreo@anla.gov.co', font=('arial',10)).place(rely=0.94, relx=0.02)
    frame_seleccion_archivo = customtkinter.CTkFrame(root,fg_color="transparent")
    label_ruta = customtkinter.CTkLabel(frame_seleccion_archivo, text= 'Ruta del archivo:')
    label_ruta.grid(column=0, row=0, padx=10)
    entry_dir_dile = customtkinter.CTkEntry(frame_seleccion_archivo, width=320)
    entry_dir_dile.grid(column=1, row=0, padx=10)
    boton_select_file = customtkinter.CTkButton(frame_seleccion_archivo, text ='↑', command=seleccionar_excel, width=10)
    boton_select_file.grid(column=2, row=0, padx=10)
    frame_seleccion_archivo.pack(fill='x', pady=(100,0))
    root.after(1000, mostrar_mensaje)
    root.mainloop()

if __name__ =='__main__':
    multiprocessing.freeze_support()
    main()
    
    