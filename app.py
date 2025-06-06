from tkinter import *
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import os
import sys
from tkinter import simpledialog
from PyPDF2 import PdfReader
from doubt_db import ScreenAnalyzer
from chatbot import TutorChatBot
import requests
import json
from PIL import Image, ImageTk, ImageGrab
import io
import webbrowser
from datetime import datetime
import re
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from huggingface_hub import InferenceClient



# Theme colors
LIGHT_THEME = {
    'bg': '#ffffff',
    'canvas_bg': '#ffffff',
    'sidebar_bg': '#f2f3f5',
    'text': '#2c3e50',
    'button_bg': '#4a90e2',
    'button_hover': '#357abd',
    'frame_bg': '#ffffff',
    'entry_bg': '#f8f9fa',
    'output_bg': '#f8f9fa'
}

DARK_THEME = {
    'bg': '#1a1a1a',
    'canvas_bg': '#2d2d2d',
    'sidebar_bg': '#2d2d2d',
    'text': '#ffffff',
    'button_bg': '#4a90e2',
    'button_hover': '#357abd',
    'frame_bg': '#2d2d2d',
    'entry_bg': '#3d3d3d',
    'output_bg': '#3d3d3d'
}

current_theme = LIGHT_THEME

root = Tk()
root.title("IntelliBoard")
# Make window fullscreen by default
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.config(bg="#ffffff")
root.resizable(False, False)


def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Calculate canvas size based on screen dimensions
canvas_width = int(screen_width * 0.9)  # 80% of screen width
canvas_height = int(screen_height * 0.9)  # 80% of screen height

# Calculate positions for UI elements
sidebar_width = 60
toolbar_height = 50
canvas_x = sidebar_width + 20
canvas_y = 10

current_x = 0
current_y = 0
start_x = None
start_y = None
color = "black"
active_tool = None

# Variables for undo/redo functionality
history = []
redo_stack = []
current_state = 0
max_history = 50

def locate_xy(event):
    global start_x, start_y, current_x, current_y
    start_x, start_y = event.x, event.y
    current_x, current_y = event.x, event.y

def addline(event):
    global current_x, current_y
    if active_tool is None:
        canvas.create_line((current_x, current_y, event.x, event.y), width=int(slider.get()),
                           fill=color, capstyle=ROUND, smooth=True)
        current_x, current_y = event.x, event.y

def insertimage():
    global filename, f_img
    filename = filedialog.askopenfilename(initialdir=os.getcwd(), title="select image file",
                                        filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All file","new.txt")])
    f_img = tk.PhotoImage(file=filename)
    # Center the image on the canvas
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    img_width = f_img.width()
    img_height = f_img.height()
    center_x = (canvas_width - img_width) // 2
    center_y = (canvas_height - img_height) // 2
    my_img = canvas.create_image(center_x, center_y, image=f_img)
    root.bind("<B3-Motion>", my_callback)

def my_callback(event):
    global f_img
    f_img = tk.PhotoImage(file=filename)
    my_img = canvas.create_image(event.x, event.y, image=f_img)

def add_shape(event):
    global start_x, start_y, active_tool
    if active_tool == "rectangle":
        canvas.create_rectangle(start_x, start_y, event.x, event.y,
                                outline=color, width=int(slider.get()))
    elif active_tool == "oval":
        canvas.create_oval(start_x, start_y, event.x, event.y,
                           outline=color, width=int(slider.get()))
    active_tool = None

def show_color(new_color):
    global color
    color = new_color

def new_canvas():
    canvas.delete('all')
    display_pallete()

def set_eraser():
    global color, active_tool
    active_tool = None
    color = "white"

def set_rectangle_tool():
    global active_tool
    active_tool = "rectangle"

def set_oval_tool():
    global active_tool
    active_tool = "oval"

def display_pallete():
    colors_list = ["#2c3e50", "#34495e", "#e74c3c", "#f39c12", "#27ae60", "#2980b9", "#8e44ad"]
    for i, color_name in enumerate(colors_list):
        id = colors.create_rectangle((10, 10 + i * 30, 30, 30 + i * 30), fill=color_name)
        colors.tag_bind(id, '<Button-1>', lambda x, col=color_name: show_color(col))

def toggle_chatbot():#chatbot
    if chatbot_frame.winfo_ismapped():
        chatbot_frame.place_forget()
    else:
        chatbot_frame.place(x=canvas_width + canvas_x-200, y=200, width=300, height=600)

def toggle_chatbotvai():  #ask doubt 
    if chatbotv_frame.winfo_ismapped():
        chatbotv_frame.place_forget()
    else:
        chatbotv_frame.place(x=canvas_width + canvas_x -300, y=200, width=300, height=600)

def minimize_chatbot():
    chatbot_frame.place_forget()

def minimize_chatbotvai():
    chatbotv_frame.place_forget()

def handle_query():
    query = query_entry.get()
    if query:
        # Check if the query is asking for a YouTube video
        youtube_keywords = ["youtube", "video", "watch", "tutorial", "how to", "lesson"]
        is_youtube_query = any(keyword in query.lower() for keyword in youtube_keywords)
        
        if is_youtube_query:
            # Extract the search term from the query
            search_term = query
            for keyword in youtube_keywords:
                if keyword in query.lower():
                    # Try to extract the actual search term after the keyword
                    parts = query.lower().split(keyword)
                    if len(parts) > 1 and parts[1].strip():
                        search_term = parts[1].strip()
                        break
            
            # Set the search term in the YouTube search entry
            youtube_search_entry.delete(0, END)
            youtube_search_entry.insert(0, search_term)
            
            # Show the YouTube search panel
            if not youtube_frame.winfo_ismapped():
                toggle_youtube_search()
            
            # Perform the search
            search_youtube()
            
            # Add a response in the chatbot
            query_output.config(state='normal')
            query_output.delete("1.0", END)
            query_output.insert(END, f"I've searched YouTube for '{search_term}'. Check the YouTube panel for results.")
            query_output.config(state='disabled')
        else:
            # Regular chatbot response
            bot = TutorChatBot()
            output = bot.respond(query)
            query_output.config(state='normal')
            query_output.delete("1.0", END)
            query_output.insert(END, output.content)
            query_output.config(state='disabled')

def handlevai_query():
    user_input = query_entryv.get()
    if user_input:
        analyzer = ScreenAnalyzer()
        outputvai = analyzer.analyze_screen(user_input)
        queryv_output.config(state='normal')
        queryv_output.delete("1.0", END)
        queryv_output.insert(END, outputvai)
        queryv_output.config(state='disabled')


color_box = PhotoImage(file=resource_path("icons/color_section.png"))
Label(root, image=color_box, bg='#f2f3f5').place(x=10, y=20)

eraser = PhotoImage(file=resource_path("icons/eraser1.png"))
Button(root, image=eraser, bg="#f2f3f5", command=set_eraser).place(x=30, y=canvas_height - 150)

import_image = PhotoImage(file=resource_path("icons/add_image.png"))
Button(root, image=import_image, bg="white", command=insertimage).place(x=30, y=canvas_height - 100)

colors = Canvas(root, bg="#fff", width=37, height=300, bd=0)
colors.place(x=30, y=60)
display_pallete()

# main Canvas
canvas = Canvas(root, width=canvas_width, height=canvas_height, background="white", cursor="hand2")
canvas.place(x=canvas_x, y=canvas_y)
canvas.bind('<Button-1>', lambda event: on_canvas_click(event) if active_tool == "text" else locate_xy(event))
canvas.bind('<B1-Motion>', addline)
canvas.bind('<ButtonRelease-1>', add_shape)

# slider setup
current_value = tk.DoubleVar()

def get_current_value():
    return '{: .2f}'.format(current_value.get())

def slider_changed(event):
    value_label.configure(text=get_current_value())

slider = ttk.Scale(root, from_=1, to=10, orient="horizontal", command=slider_changed, variable=current_value)
slider.place(x=30, y=canvas_height - 40)

value_label = ttk.Label(root, text=get_current_value())
value_label.place(x=27, y=canvas_height - 20)

# chatbot setup
chatbot_icon = PhotoImage(file=resource_path("icons/chatbot.png"))
chatbot_button = Button(
    root,
    image=chatbot_icon,
    command=toggle_chatbot,
    bg="#f2f3f5",
    activebackground="#e1e3e6",
    borderwidth=0,
    cursor="hand2"
)
chatbot_button.place(x=canvas_width + canvas_x - 50, y=canvas_height - 50)


chatbot_frame = Frame(
    root,
    bg="white",
    bd=0,
    highlightthickness=1,
    highlightbackground="#e0e0e0"
)


header_frame = Frame(chatbot_frame, bg="#4a90e2", height=40)
header_frame.pack(fill="x", pady=(0, 10))

Label(
    header_frame,
    text="Chat Assistant",
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 12, "bold")
).pack(side="left", padx=10, pady=8)


Label(
    chatbot_frame,
    text="How can I help you?",
    bg="white",
    fg="#2c3e50",
    font=("Helvetica", 10)
).pack(anchor=W, padx=12, pady=(0, 5))


query_entry = Entry(
    chatbot_frame,
    width=30,
    font=("Helvetica", 11),
    bd=1,
    relief="solid",
    bg="#f8f9fa"
)
query_entry.pack(padx=12, pady=(0, 10))


Button(
    chatbot_frame,
    text="Send Message",
    command=handle_query,
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 10, "bold"),
    relief="flat",
    padx=15,
    pady=5,
    cursor="hand2"
).pack(pady=(0, 10))

# chat output area with frame
output_frame = Frame(chatbot_frame, bg="#f8f9fa", padx=2, pady=2)
output_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

query_output = Text(
    output_frame,
    height=25,
    width=35,
    font=("Helvetica", 10),
    state='disabled',
    bg="#f8f9fa",
    relief="flat",
    padx=8,
    pady=8
)
query_output.pack(fill="both", expand=True)

# added scrollbar
scrollbar = Scrollbar(output_frame)
scrollbar.pack(side="right", fill="y")
query_output.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=query_output.yview)

#minimize button
minimize_button = Button(
    header_frame,
    text="−",
    command=minimize_chatbot,
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 16),
    relief="flat",
    bd=0,
    cursor="hand2"
)
minimize_button.pack(side="right", padx=10)

# Hover effects
def on_enter(e):
    e.widget['background'] = '#357abd'

def on_leave(e):
    e.widget['background'] = '#4a90e2'

# add hover effects to buttons
for button in chatbot_frame.winfo_children():
    if isinstance(button, Button) and button['bg'] == '#4a90e2':
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

# document upload setup
document_icon = PhotoImage(file=resource_path("icons/document_icon.png"))
document_button = Button(root, image=document_icon, bg="#f2f3f5", borderwidth=0)
document_button.place(x=canvas_width + canvas_x - 300, y=canvas_height - 50)

# ask doubt part
# Create a modern-looking Ask Doubt button
doubt_button = Button(root, 
    text="Ask doubt ✋", 
    command=toggle_chatbotvai,
    font=("Helvetica", 11, "bold"),
    bg="#4a90e2",  # Modern blue color
    fg="white",
    relief="flat",
    padx=15,
    pady=8,
    cursor="hand2"
).place(x=canvas_width + canvas_x - 500, y=canvas_height - 50)  # Restored original position

chatbotv_frame = Frame(
    root, 
    bg="#ffffff",
    bd=0,
    highlightthickness=1,
    highlightbackground="#e0e0e0"
)


header_frame = Frame(chatbotv_frame, bg="#4a90e2", height=40)
header_frame.pack(fill="x", pady=(0, 10))

Label(
    header_frame, 
    text="Visual Query Assistant",
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 12, "bold")
).pack(side="left", padx=10, pady=8)


Label(
    chatbotv_frame,
    text="ask query about visual",
    bg="white",
    fg="#2c3e50",
    font=("Helvetica", 10)
).pack(anchor=W, padx=12, pady=(0, 5))

query_entryv = Entry(
    chatbotv_frame,
    width=30,
    font=("Helvetica", 11),
    bd=1,
    relief="solid",
    bg="#f8f9fa"
)
query_entryv.pack(padx=12, pady=(0, 10))
Button(
    chatbotv_frame,
    text="Submit Query",
    command=handlevai_query,
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 10, "bold"),
    relief="flat",
    padx=15,
    pady=5,
    cursor="hand2"
).pack(pady=(0, 10))


output_frame = Frame(chatbotv_frame, bg="#f8f9fa", padx=2, pady=2)
output_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

queryv_output = Text(
    output_frame,
    height=25,
    width=30,
    font=("Helvetica", 10),
    state='disabled',
    bg="#f8f9fa",
    relief="flat",
    padx=8,
    pady=8
)
queryv_output.pack(fill="both", expand=True)

#scrollbar for output
scrollbar = Scrollbar(output_frame)
scrollbar.pack(side="right", fill="y")
queryv_output.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=queryv_output.yview)

# modern minimize button
minimize_buttonv = Button(
    header_frame,
    text="−",
    command=minimize_chatbotvai,
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 16),
    relief="flat",
    bd=0,
    cursor="hand2"
)
minimize_buttonv.pack(side="right", padx=10)

# add hover effects for buttons
def on_enter(e):
    e.widget['background'] = '#357abd'

def on_leave(e):
    e.widget['background'] = '#4a90e2'

# Bind hover events to all blue buttons
for button in chatbotv_frame.winfo_children():
    if isinstance(button, Button) and button['bg'] == '#4a90e2':
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

def on_canvas_click(event):
    global active_tool
    if active_tool == "text":
        text = simpledialog.askstring("Input", "Enter text:")
        if text:
            canvas.create_text(event.x, event.y, text=text, fill=color, font=("Arial", int(slider.get()) * 5))
        active_tool = None

def set_text_tool():
    global active_tool
    active_tool = "text"

# slides handling
slides = []
current_slide = 0

def insert_document():
    global slides, current_slide
    file_path = filedialog.askopenfilename(
        initialdir=os.getcwd(),
        title="Select Document",
        filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt"), ("All files", "*.*")]
    )
    
    if not file_path:
        return
    
    slides = []
    current_slide = 0

    if file_path.endswith('.pdf'):
        reader = PdfReader(file_path)
        slides = [page.extract_text() for page in reader.pages]
    elif file_path.endswith('.txt'):
        with open(file_path, 'r') as file:
            slides = file.read().split('\n\n')
    
    if slides:
        display_slide()

def display_slide():
    global slides, current_slide
    if 0 <= current_slide < len(slides):
        canvas.delete('all')
        display_pallete()
        
        slide_text = slides[current_slide]
        canvas.create_text(
            10, 10,
            anchor=NW,
            text=slide_text,
            font=("Arial", 12),
            fill="black",
            width=canvas_width - 20
        )

def next_slide():
    global current_slide
    if current_slide < len(slides) - 1:
        current_slide += 1
        display_slide()

def previous_slide():
    global current_slide
    if current_slide > 0:
        current_slide -= 1
        display_slide()

document_button.config(command=insert_document)

# Bottom toolbar buttons
toolbar_y = canvas_height - 50
# Define common button style parameters
button_style = {
    'font': ('Segoe UI', 10),
    'relief': 'flat',
    'borderwidth': 0,
    'padx': 15,
    'pady': 8,
    'cursor': 'hand2',
    'highlightthickness': 0
}

# Create a horizontal layout with small gaps between buttons
# Tool buttons
Button(root,
    text="Rectangle",
    command=set_rectangle_tool,
    bg="#3498db",  # Modern blue
    fg="white",
    activebackground="#2980b9",
    width=10,
    **button_style
).place(x=canvas_x + 100, y=toolbar_y)

Button(root,
    text="Oval",
    command=set_oval_tool,
    bg="#2ecc71",  # Modern green
    fg="white",
    activebackground="#27ae60",
    width=10,
    **button_style
).place(x=canvas_x + 210, y=toolbar_y)

Button(root,
    text="Text",
    command=set_text_tool,
    bg="#e67e22",  # Modern orange
    fg="white",
    activebackground="#d35400",
    width=10,
    **button_style
).place(x=canvas_x + 320, y=toolbar_y)

Button(root,
    text="Clear Screen",
    command=new_canvas,
    bg="#e74c3c",  # Modern red
    fg="white",
    activebackground="#c0392b",
    width=12,
    **button_style
).place(x=canvas_x + 430, y=toolbar_y)

# Navigation buttons
Button(root, 
    text="Previous",
    command=previous_slide,
    bg="#8e44ad",  # Modern purple
    fg="white",
    activebackground="#732d91",
    width=10,
    **button_style
).place(x=canvas_x + canvas_width - 800, y=toolbar_y)  # Restored original position

Button(root,
    text="Next",
    command=next_slide,
    bg="#3498db",  # Modern blue
    fg="white",
    activebackground="#2980b9",
    width=10,
    **button_style
).place(x=canvas_x + canvas_width - 640, y=toolbar_y)  # Restored original position

# Updated label styles
Label(root, text="IntelliBoard", bg="#ffffff", fg="#2c3e50", font=("Segoe UI", 16, "bold")).place(x=canvas_x + 20, y=20)

# Add context menu for YouTube search
def show_context_menu(event):
    context_menu = Menu(root, tearoff=0)
    context_menu.add_command(label="Search YouTube for this topic", command=lambda: search_from_canvas(event))
    context_menu.post(event.x_root, event.y_root)

def search_from_canvas(event):
    # Get text near the click position
    items = canvas.find_closest(event.x, event.y)
    if items:
        item = items[0]
        tags = canvas.gettags(item)
        
        # Check if the item is text
        if "text" in canvas.type(item):
            text = canvas.itemcget(item, 'text')
            
            # Set the search term in the YouTube search entry
            youtube_search_entry.delete(0, END)
            youtube_search_entry.insert(0, text)
            
            # Show the YouTube search panel
            if not youtube_frame.winfo_ismapped():
                toggle_youtube_search()
            
            # Perform the search
            search_youtube()
        else:
            # If no text found, prompt the user
            search_term = simpledialog.askstring("YouTube Search", "Enter search term:")
            if search_term:
                youtube_search_entry.delete(0, END)
                youtube_search_entry.insert(0, search_term)
                
                if not youtube_frame.winfo_ismapped():
                    toggle_youtube_search()
                
                search_youtube()

# Bind right-click to show context menu
canvas.bind('<Button-3>', show_context_menu)

# YouTube search functionality
def toggle_youtube_search():
    if youtube_frame.winfo_ismapped():
        youtube_frame.place_forget()
    else:
        youtube_frame.place(x=canvas_width + canvas_x - 500, y=200, width=400, height=600)

def minimize_youtube():
    youtube_frame.place_forget()

def search_youtube():
    query = youtube_search_entry.get()
    if query:
        # Clear previous results
        for widget in youtube_results_frame.winfo_children():
            widget.destroy()
        
        # Show loading indicator
        loading_label = Label(youtube_results_frame, text="Searching...", bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 10))
        loading_label.pack(pady=10)
        youtube_results_frame.update()
        
        # Try to use the YouTube API first
        try:
            # Use the Google API key from .env
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                api_key = "AIzaSyDBRUZ-K3GNGESIrXE0Iw6cz3pGYN7YP3I"  # Fallback to the one in .env file
            
            # YouTube Data API v3 search endpoint
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=5&key={api_key}"
            response = requests.get(url)
            
            # Check for API errors
            if response.status_code != 200:
                error_data = response.json()
                error_message = "Unknown error"
                
                if 'error' in error_data:
                    error_message = error_data['error'].get('message', 'Unknown error')
                    
                    # Check for specific API not enabled error
                    if "has not been used" in error_message or "is disabled" in error_message:
                        error_message = "YouTube Data API v3 is not enabled for your API key. Please enable it in the Google Cloud Console."
                    
                    # Check for blocked API error
                    if "blocked" in error_message.lower():
                        error_message = "YouTube Data API v3 is blocked for your API key. This is a restriction from Google."
                
                # Remove loading indicator
                loading_label.destroy()
                
                # Show error message
                error_frame = Frame(youtube_results_frame, bg="#f8f9fa", padx=10, pady=10)
                error_frame.pack(fill="x", pady=10)
                
                error_label = Label(
                    error_frame, 
                    text="API Error", 
                    bg="#f8f9fa", 
                    fg="#e74c3c", 
                    font=("Helvetica", 12, "bold")
                )
                error_label.pack(anchor="w")
                
                message_label = Label(
                    error_frame, 
                    text=error_message, 
                    bg="#f8f9fa", 
                    fg="#2c3e50", 
                    font=("Helvetica", 10),
                    wraplength=350,
                    justify="left"
                )
                message_label.pack(anchor="w", pady=(5, 0))
                
                # Add instructions for enabling the API
                if "not enabled" in error_message:
                    instructions = """
To enable the YouTube Data API v3:
1. Go to the Google Cloud Console
2. Select your project
3. Navigate to APIs & Services > Library
4. Search for "YouTube Data API v3"
5. Click Enable
6. Wait a few minutes for the changes to take effect
                    """
                    instructions_label = Label(
                        error_frame, 
                        text=instructions, 
                        bg="#f8f9fa", 
                        fg="#2c3e50", 
                        font=("Helvetica", 9),
                        wraplength=350,
                        justify="left"
                    )
                    instructions_label.pack(anchor="w", pady=(10, 0))
                    
                    # Add a button to open Google Cloud Console
                    def open_cloud_console():
                        webbrowser.open("https://console.cloud.google.com/apis/library/youtube.googleapis.com")
                    
                    console_button = Button(
                        error_frame,
                        text="Open Google Cloud Console",
                        command=open_cloud_console,
                        bg="#2ecc71",
                        fg="white",
                        font=("Helvetica", 10, "bold"),
                        relief="flat",
                        padx=15,
                        pady=5,
                        cursor="hand2"
                    )
                    console_button.pack(pady=(5, 0))
                    
                    # Custom hover effects for console button
                    def console_on_enter(e):
                        e.widget['background'] = '#27ae60'
                    
                    def console_on_leave(e):
                        e.widget['background'] = '#2ecc71'
                    
                    console_button.bind("<Enter>", console_on_enter)
                    console_button.bind("<Leave>", console_on_leave)
                
                # Add a button to search directly in browser
                def search_in_browser():
                    webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                
                browser_button = Button(
                    error_frame,
                    text="Search in Browser Instead",
                    command=search_in_browser,
                    bg="#4a90e2",
                    fg="white",
                    font=("Helvetica", 10, "bold"),
                    relief="flat",
                    padx=15,
                    pady=5,
                    cursor="hand2"
                )
                browser_button.pack(pady=(10, 0))
                browser_button.bind("<Enter>", on_enter)
                browser_button.bind("<Leave>", on_leave)
                
                # If API is blocked, show alternative search options
                if "blocked" in error_message.lower():
                    alt_label = Label(
                        error_frame,
                        text="Alternative Search Options:",
                        bg="#f8f9fa",
                        fg="#2c3e50",
                        font=("Helvetica", 10, "bold")
                    )
                    alt_label.pack(anchor="w", pady=(15, 5))
                    
                    # Add buttons for alternative search engines
                    def search_google():
                        webbrowser.open(f"https://www.google.com/search?q={query}+youtube")
                    
                    def search_bing():
                        webbrowser.open(f"https://www.bing.com/search?q={query}+youtube")
                    
                    alt_buttons_frame = Frame(error_frame, bg="#f8f9fa")
                    alt_buttons_frame.pack(fill="x", pady=5)
                    
                    google_button = Button(
                        alt_buttons_frame,
                        text="Google Search",
                        command=search_google,
                        bg="#4285F4",
                        fg="white",
                        font=("Helvetica", 9, "bold"),
                        relief="flat",
                        padx=10,
                        pady=3,
                        cursor="hand2"
                    )
                    google_button.pack(side="left", padx=5)
                    
                    bing_button = Button(
                        alt_buttons_frame,
                        text="Bing Search",
                        command=search_bing,
                        bg="#00A4EF",
                        fg="white",
                        font=("Helvetica", 9, "bold"),
                        relief="flat",
                        padx=10,
                        pady=3,
                        cursor="hand2"
                    )
                    bing_button.pack(side="left", padx=5)
                    
                    # Add hover effects
                    def google_on_enter(e):
                        e.widget['background'] = '#3367D6'
                    
                    def google_on_leave(e):
                        e.widget['background'] = '#4285F4'
                    
                    def bing_on_enter(e):
                        e.widget['background'] = '#0091EA'
                    
                    def bing_on_leave(e):
                        e.widget['background'] = '#00A4EF'
                    
                    google_button.bind("<Enter>", google_on_enter)
                    google_button.bind("<Leave>", google_on_leave)
                    bing_button.bind("<Enter>", bing_on_enter)
                    bing_button.bind("<Leave>", bing_on_leave)
                
                # Try to use the alternative search method
                try:
                    search_youtube_alternative(query)
                except Exception as e:
                    print(f"Alternative search error: {str(e)}")
                    # Show fallback search options
                    show_fallback_search(query)
                return
            
            data = response.json()
            
            # Remove loading indicator
            loading_label.destroy()
            
            if 'items' in data and data['items']:
                for item in data['items']:
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    channel = item['snippet']['channelTitle']
                    thumbnail_url = item['snippet']['thumbnails']['medium']['url']
                    
                    # Create a frame for each video result
                    video_frame = Frame(youtube_results_frame, bg="#f8f9fa", padx=5, pady=5)
                    video_frame.pack(fill="x", pady=5)
                    
                    # Try to load thumbnail
                    try:
                        thumbnail_response = requests.get(thumbnail_url)
                        thumbnail_data = io.BytesIO(thumbnail_response.content)
                        thumbnail_img = Image.open(thumbnail_data)
                        thumbnail_img = thumbnail_img.resize((120, 68), Image.LANCZOS)
                        thumbnail_photo = ImageTk.PhotoImage(thumbnail_img)
                        
                        thumbnail_label = Label(video_frame, image=thumbnail_photo, bg="#f8f9fa")
                        thumbnail_label.image = thumbnail_photo  # Keep a reference
                        thumbnail_label.pack(side="left", padx=5)
                    except Exception as e:
                        # If thumbnail loading fails, create a placeholder
                        placeholder = Label(video_frame, text="[Thumbnail]", bg="#f8f9fa", fg="#2c3e50", width=15, height=4)
                        placeholder.pack(side="left", padx=5)
                    
                    # Video info
                    info_frame = Frame(video_frame, bg="#f8f9fa")
                    info_frame.pack(side="left", fill="x", expand=True, padx=5)
                    
                    title_label = Label(info_frame, text=title, bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 10, "bold"), wraplength=250)
                    title_label.pack(anchor="w")
                    
                    channel_label = Label(info_frame, text=channel, bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 9))
                    channel_label.pack(anchor="w")
                    
                    # Buttons frame
                    buttons_frame = Frame(video_frame, bg="#f8f9fa")
                    buttons_frame.pack(side="right", padx=5)
                    
                    # Play button
                    play_button = Button(
                        buttons_frame,
                        text="Play",
                        command=lambda vid=video_id: play_youtube_video(vid),
                        bg="#4a90e2",
                        fg="white",
                        font=("Helvetica", 9, "bold"),
                        relief="flat",
                        padx=10,
                        pady=2,
                        cursor="hand2"
                    )
                    play_button.pack(side="left", padx=2)
                    
                    # Pin button
                    pin_button = Button(
                        buttons_frame,
                        text="Pin",
                        command=lambda vid=video_id, t=title, c=channel: pin_video_to_canvas(vid, t, c),
                        bg="#2ecc71",
                        fg="white",
                        font=("Helvetica", 9, "bold"),
                        relief="flat",
                        padx=10,
                        pady=2,
                        cursor="hand2"
                    )
                    pin_button.pack(side="left", padx=2)
                    
                    # Add hover effects
                    play_button.bind("<Enter>", on_enter)
                    play_button.bind("<Leave>", on_leave)
                    
                    # Custom hover effects for pin button
                    def pin_on_enter(e):
                        e.widget['background'] = '#27ae60'
                    
                    def pin_on_leave(e):
                        e.widget['background'] = '#2ecc71'
                    
                    pin_button.bind("<Enter>", pin_on_enter)
                    pin_button.bind("<Leave>", pin_on_leave)
            else:
                no_results = Label(youtube_results_frame, text="No videos found", bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 10))
                no_results.pack(pady=10)
                
                # Try to use the alternative search method
                try:
                    search_youtube_alternative(query)
                except Exception as e:
                    print(f"Alternative search error: {str(e)}")
                    # Show fallback search options
                    show_fallback_search(query)
        except Exception as e:
            # Remove loading indicator
            loading_label.destroy()
            
            error_msg = Label(youtube_results_frame, text=f"Error: {str(e)}", bg="#f8f9fa", fg="#e74c3c", font=("Helvetica", 10))
            error_msg.pack(pady=10)
            
            # Try to use the alternative search method
            try:
                search_youtube_alternative(query)
            except Exception as e:
                print(f"Alternative search error: {str(e)}")
                # Show fallback search options
                show_fallback_search(query)

def search_youtube_alternative(query):
    """Alternative method to search YouTube videos using web scraping"""
    # Remove loading indicator if it exists
    for widget in youtube_results_frame.winfo_children():
        widget.destroy()
    
    # Show loading indicator
    loading_label = Label(youtube_results_frame, text="Searching YouTube directly...", bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 10))
    loading_label.pack(pady=10)
    youtube_results_frame.update()
    
    try:
        # Use a different approach - search through Google for YouTube videos
        encoded_query = urllib.parse.quote(query + " site:youtube.com")
        
        # Set up headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Make a request to Google search
        url = f"https://www.google.com/search?q={encoded_query}"
        response = requests.get(url, headers=headers)
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find video elements in Google search results
        video_elements = []
        
        # Look for YouTube links in Google search results
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'youtube.com/watch?v=' in href or 'youtu.be/' in href:
                # Extract video ID
                video_id = None
                if 'youtube.com/watch?v=' in href:
                    video_id = href.split('watch?v=')[1].split('&')[0]
                elif 'youtu.be/' in href:
                    video_id = href.split('youtu.be/')[1].split('?')[0]
                
                if video_id and len(video_id) == 11:  # YouTube video IDs are 11 characters
                    # Get title from the link text or parent elements
                    title = link.text.strip()
                    if not title:
                        # Try to find title in parent elements
                        parent = link.parent
                        for _ in range(3):  # Look up to 3 levels up
                            if parent and parent.text.strip():
                                title = parent.text.strip()
                                break
                            if parent:
                                parent = parent.parent
                    
                    # If still no title, use a generic one
                    if not title:
                        title = f"YouTube Video ({video_id})"
                    
                    # Add to video elements
                    video_elements.append({
                        'video_id': video_id,
                        'title': title,
                        'channel': "YouTube Channel",  # We don't have channel info from Google
                        'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                    })
        
        # Remove loading indicator
        loading_label.destroy()
        
        if video_elements:
            # Create a label to show we're using direct search
            direct_label = Label(
                youtube_results_frame, 
                text="YouTube Search Results", 
                bg="#f8f9fa", 
                fg="#2c3e50", 
                font=("Helvetica", 12, "bold")
            )
            direct_label.pack(pady=(0, 10))
            
            # Process up to 5 videos
            for i, video in enumerate(video_elements[:5]):
                try:
                    video_id = video['video_id']
                    title = video['title']
                    channel = video['channel']
                    thumbnail_url = video['thumbnail_url']
                    
                    # Create a frame for each video result
                    video_frame = Frame(youtube_results_frame, bg="#f8f9fa", padx=5, pady=5)
                    video_frame.pack(fill="x", pady=5)
                    
                    # Try to load thumbnail
                    try:
                        thumbnail_response = requests.get(thumbnail_url)
                        thumbnail_data = io.BytesIO(thumbnail_response.content)
                        thumbnail_img = Image.open(thumbnail_data)
                        thumbnail_img = thumbnail_img.resize((120, 68), Image.LANCZOS)
                        thumbnail_photo = ImageTk.PhotoImage(thumbnail_img)
                        
                        thumbnail_label = Label(video_frame, image=thumbnail_photo, bg="#f8f9fa")
                        thumbnail_label.image = thumbnail_photo  # Keep a reference
                        thumbnail_label.pack(side="left", padx=5)
                    except Exception as e:
                        # If thumbnail loading fails, create a placeholder
                        placeholder = Label(video_frame, text="[Thumbnail]", bg="#f8f9fa", fg="#2c3e50", width=15, height=4)
                        placeholder.pack(side="left", padx=5)
                    
                    # Video info
                    info_frame = Frame(video_frame, bg="#f8f9fa")
                    info_frame.pack(side="left", fill="x", expand=True, padx=5)
                    
                    title_label = Label(info_frame, text=title, bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 10, "bold"), wraplength=250)
                    title_label.pack(anchor="w")
                    
                    channel_label = Label(info_frame, text=channel, bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 9))
                    channel_label.pack(anchor="w")
                    
                    # Buttons frame
                    buttons_frame = Frame(video_frame, bg="#f8f9fa")
                    buttons_frame.pack(side="right", padx=5)
                    
                    # Play button
                    play_button = Button(
                        buttons_frame,
                        text="Play",
                        command=lambda vid=video_id: play_youtube_video(vid),
                        bg="#4a90e2",
                        fg="white",
                        font=("Helvetica", 9, "bold"),
                        relief="flat",
                        padx=10,
                        pady=2,
                        cursor="hand2"
                    )
                    play_button.pack(side="left", padx=2)
                    
                    # Pin button
                    pin_button = Button(
                        buttons_frame,
                        text="Pin",
                        command=lambda vid=video_id, t=title, c=channel: pin_video_to_canvas(vid, t, c),
                        bg="#2ecc71",
                        fg="white",
                        font=("Helvetica", 9, "bold"),
                        relief="flat",
                        padx=10,
                        pady=2,
                        cursor="hand2"
                    )
                    pin_button.pack(side="left", padx=2)
                    
                    # Add hover effects
                    play_button.bind("<Enter>", on_enter)
                    play_button.bind("<Leave>", on_leave)
                    
                    # Custom hover effects for pin button
                    def pin_on_enter(e):
                        e.widget['background'] = '#27ae60'
                    
                    def pin_on_leave(e):
                        e.widget['background'] = '#2ecc71'
                    
                    pin_button.bind("<Enter>", pin_on_enter)
                    pin_button.bind("<Leave>", pin_on_leave)
                except Exception as e:
                    print(f"Error processing video element: {str(e)}")
                    continue
        else:
            # No videos found
            no_results = Label(youtube_results_frame, text="No videos found", bg="#f8f9fa", fg="#2c3e50", font=("Helvetica", 10))
            no_results.pack(pady=10)
            
            # Show fallback search options
            show_fallback_search(query)
    except Exception as e:
        # Remove loading indicator
        loading_label.destroy()
        
        error_msg = Label(youtube_results_frame, text=f"Error searching YouTube: {str(e)}", bg="#f8f9fa", fg="#e74c3c", font=("Helvetica", 10))
        error_msg.pack(pady=10)
        
        # Show fallback search options
        show_fallback_search(query)

def show_fallback_search(query):
    """Show fallback search options when the YouTube API is not available"""
    # Create a frame for fallback options
    fallback_frame = Frame(youtube_results_frame, bg="#f8f9fa", padx=10, pady=10)
    fallback_frame.pack(fill="x", pady=10)
    
    fallback_label = Label(
        fallback_frame,
        text="Search YouTube directly:",
        bg="#f8f9fa",
        fg="#2c3e50",
        font=("Helvetica", 10, "bold")
    )
    fallback_label.pack(anchor="w", pady=(5, 10))
    
    # Create buttons for different search options
    def search_youtube():
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
    
    def search_google():
        webbrowser.open(f"https://www.google.com/search?q={query}+youtube")
    
    def search_bing():
        webbrowser.open(f"https://www.bing.com/search?q={query}+youtube")
    
    # YouTube button
    youtube_button = Button(
        fallback_frame,
        text="YouTube Search",
        command=search_youtube,
        bg="#FF0000",
        fg="white",
        font=("Helvetica", 10, "bold"),
        relief="flat",
        padx=15,
        pady=5,
        cursor="hand2"
    )
    youtube_button.pack(fill="x", pady=5)
    
    # Google button
    google_button = Button(
        fallback_frame,
        text="Google Search",
        command=search_google,
        bg="#4285F4",
        fg="white",
        font=("Helvetica", 10, "bold"),
        relief="flat",
        padx=15,
        pady=5,
        cursor="hand2"
    )
    google_button.pack(fill="x", pady=5)
    
    # Bing button
    bing_button = Button(
        fallback_frame,
        text="Bing Search",
        command=search_bing,
        bg="#00A4EF",
        fg="white",
        font=("Helvetica", 10, "bold"),
        relief="flat",
        padx=15,
        pady=5,
        cursor="hand2"
    )
    bing_button.pack(fill="x", pady=5)
    
    # Add hover effects
    def youtube_on_enter(e):
        e.widget['background'] = '#CC0000'
    
    def youtube_on_leave(e):
        e.widget['background'] = '#FF0000'
    
    def google_on_enter(e):
        e.widget['background'] = '#3367D6'
    
    def google_on_leave(e):
        e.widget['background'] = '#4285F4'
    
    def bing_on_enter(e):
        e.widget['background'] = '#0091EA'
    
    def bing_on_leave(e):
        e.widget['background'] = '#00A4EF'
    
    youtube_button.bind("<Enter>", youtube_on_enter)
    youtube_button.bind("<Leave>", youtube_on_leave)
    google_button.bind("<Enter>", google_on_enter)
    google_button.bind("<Leave>", google_on_leave)
    bing_button.bind("<Enter>", bing_on_enter)
    bing_button.bind("<Leave>", bing_on_leave)

def play_youtube_video(video_id):
    # Open the video in the default web browser
    webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")
    
    # Optionally, create a note on the canvas about the video
    canvas.create_text(
        canvas_width // 2, canvas_height // 2,
        text=f"YouTube video opened: {video_id}",
        font=("Arial", 12),
        fill="black"
    )

def pin_video_to_canvas(video_id, title, channel):
    # Create a frame on the canvas to represent the pinned video
    pin_x = canvas_width // 4
    pin_y = canvas_height // 4
    
    # Create a rectangle for the pin
    pin_rect = canvas.create_rectangle(
        pin_x, pin_y, pin_x + 300, pin_y + 100,
        fill="#f8f9fa", outline="#4a90e2", width=2
    )
    
    # Add video title
    canvas.create_text(
        pin_x + 10, pin_y + 10,
        text=f"📺 {title}",
        font=("Arial", 10, "bold"),
        fill="#2c3e50",
        anchor="nw",
        width=280
    )
    
    # Add channel name
    canvas.create_text(
        pin_x + 10, pin_y + 40,
        text=f"Channel: {channel}",
        font=("Arial", 9),
        fill="#2c3e50",
        anchor="nw"
    )
    
    # Add a play button (represented as text for now)
    play_text = canvas.create_text(
        pin_x + 250, pin_y + 70,
        text="▶ Play",
        font=("Arial", 10, "bold"),
        fill="#4a90e2",
        anchor="center"
    )
    
    # Store the video ID as a tag on the play button
    canvas.itemconfig(play_text, tags=(f"play_{video_id}",))
    
    # Bind click event to the play button
    canvas.tag_bind(f"play_{video_id}", '<Button-1>', lambda e, vid=video_id: play_youtube_video(vid))
    
    # Make the pin draggable
    canvas.tag_bind(pin_rect, '<Button-1>', lambda e: canvas.tag_raise(pin_rect))
    canvas.tag_bind(pin_rect, '<B1-Motion>', lambda e: move_pin(e, pin_rect))
    
    # Also bind the text elements
    canvas.tag_bind(play_text, '<Button-1>', lambda e: canvas.tag_raise(pin_rect))
    canvas.tag_bind(play_text, '<B1-Motion>', lambda e: move_pin(e, pin_rect))

def move_pin(event, pin_rect):
    # Get the current position of the pin
    coords = canvas.coords(pin_rect)
    if coords:
        # Calculate the movement
        dx = event.x - coords[0]
        dy = event.y - coords[1]
        
        # Move the pin and all its children
        canvas.move(pin_rect, dx, dy)
        
        # Find all items with the same tag (children of the pin)
        for item in canvas.find_withtag(pin_rect):
            if item != pin_rect:  # Don't move the pin itself again
                canvas.move(item, dx, dy)

# Create YouTube search frame
youtube_frame = Frame(
    root, 
    bg="#ffffff",
    bd=0,
    highlightthickness=1,
    highlightbackground="#e0e0e0"
)

# YouTube header
youtube_header = Frame(youtube_frame, bg="#4a90e2", height=40)
youtube_header.pack(fill="x", pady=(0, 10))

Label(
    youtube_header, 
    text="YouTube Search",
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 12, "bold")
).pack(side="left", padx=10, pady=8)

# YouTube minimize button
youtube_minimize = Button(
    youtube_header,
    text="−",
    command=minimize_youtube,
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 16),
    relief="flat",
    bd=0,
    cursor="hand2"
)
youtube_minimize.pack(side="right", padx=10)

# YouTube search entry
Label(
    youtube_frame,
    text="Search for educational videos:",
    bg="white",
    fg="#2c3e50",
    font=("Helvetica", 10)
).pack(anchor=W, padx=12, pady=(0, 5))

youtube_search_entry = Entry(
    youtube_frame,
    width=40,
    font=("Helvetica", 11),
    bd=1,
    relief="solid",
    bg="#f8f9fa"
)
youtube_search_entry.pack(padx=12, pady=(0, 10))

# Search button
Button(
    youtube_frame,
    text="Search Videos",
    command=search_youtube,
    bg="#4a90e2",
    fg="white",
    font=("Helvetica", 10, "bold"),
    relief="flat",
    padx=15,
    pady=5,
    cursor="hand2"
).pack(pady=(0, 10))

# Results area
youtube_results_frame = Frame(youtube_frame, bg="#f8f9fa", padx=2, pady=2)
youtube_results_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

# Add scrollbar for results
youtube_scrollbar = Scrollbar(youtube_results_frame)
youtube_scrollbar.pack(side="right", fill="y")

# Add hover effects to YouTube buttons
for button in youtube_frame.winfo_children():
    if isinstance(button, Button) and button['bg'] == '#4a90e2':
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

# YouTube button in the toolbar
youtube_button = Button(root, 
    text="▶",  # YouTube play button symbol
    command=toggle_youtube_search,
    font=("Helvetica", 12, "bold"),  # Reduced font size
    bg="#FF0000",  # YouTube red color
    fg="white",
    relief="flat",
    padx=10,    # Reduced padding
    pady=6,    # Reduced padding
    cursor="hand2",
    width=1,   # Reduced width
    height=1   # Maintained height for square shape
).place(x=30, y=canvas_height - 250)  # Same position as before

# Add hover effects for YouTube button
def youtube_on_enter(e):
    e.widget['background'] = '#CC0000'  # Darker YouTube red on hover

def youtube_on_leave(e):
    e.widget['background'] = '#FF0000'  # Back to original YouTube red

# Find the YouTube button and bind hover events
for widget in root.winfo_children():
    if isinstance(widget, Button) and widget.cget('text') == "▶":
        widget.bind("<Enter>", youtube_on_enter)
        widget.bind("<Leave>", youtube_on_leave)

# Add export button to save the whiteboard
def export_whiteboard():
    # Ask user for save location
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
        title="Save Whiteboard As"
    )
    
    if file_path:
        # Get the canvas dimensions
        x = canvas.winfo_rootx()
        y = canvas.winfo_rooty()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Create a PostScript file first (temporary)
        temp_ps = "temp_whiteboard.ps"
        canvas.postscript(file=temp_ps, colormode='color')
        
        # Convert PostScript to image using PIL
        try:
            from PIL import Image
            img = Image.open(temp_ps)
            
            # Save as the selected format
            img.save(file_path, quality=95)
            
            # Remove temporary file
            os.remove(temp_ps)
            
            # Show success message
            messagebox.showinfo("Export Successful", f"Whiteboard saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error saving whiteboard: {str(e)}")
            if os.path.exists(temp_ps):
                os.remove(temp_ps)

# Create export button with icon
export_button = Button(root, 
    text="📥", 
    command=export_whiteboard,
    font=("Helvetica", 10, "bold"),
    bg="#3498db",  # Blue color
    fg="white",
    relief="flat",
    padx=10,
    pady=6,
    cursor="hand2"
).place(x=30, y=canvas_height - 200)  # Moved to left side

# Add hover effects for export button
def export_on_enter(e):
    e.widget['background'] = '#2980b9'

def export_on_leave(e):
    e.widget['background'] = '#3498db'

# Find the export button and bind hover events
for widget in root.winfo_children():
    if isinstance(widget, Button) and widget.cget('text') == "Export 📥":
        widget.bind("<Enter>", export_on_enter)
        widget.bind("<Leave>", export_on_leave)

def generate_image_from_text():
    """Generate image from text using Hugging Face Inference Client"""
    global status_bar  # Add global declaration
    
    # Ensure status bar exists
    if 'status_bar' not in globals():
        status_bar = Label(root, text="Ready", bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)
    
    # Ask user for text input
    text = simpledialog.askstring("Image Generation", "Enter text to generate image:")
    if not text:
        return
        
    try:
        # Show loading message
        status_bar.config(text="Generating image... Please wait.")
        root.update()  # Force update to show status message
        
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Generate image using Inference Client
                pil_img = client.text_to_image(
                    text,
                    model="stabilityai/stable-diffusion-xl-base-1.0",
                    negative_prompt="blurry, bad quality",
                    guidance_scale=7.5,
                    num_inference_steps=30
                )
                
                # If we get here, image generation was successful
                break
                
            except Exception as e:
                if "server unavailable" in str(e).lower() or "temporarily" in str(e).lower():
                    if attempt < max_retries - 1:
                        status_bar.config(text=f"Server busy. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        root.update()
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception("Server is temporarily unavailable. Please try again later.")
                else:
                    raise e
        
        # Resize image if needed
        max_size = (800, 800)
        pil_img.thumbnail(max_size, Image.LANCZOS)
        
        # Convert to PhotoImage
        f_img = ImageTk.PhotoImage(pil_img)
        
        # Center the image on the canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        img_width = f_img.width()
        img_height = f_img.height()
        center_x = (canvas_width - img_width) // 2
        center_y = (canvas_height - img_height) // 2
        
        # Create image on canvas
        canvas.create_image(center_x, center_y, image=f_img, anchor=NW)
        canvas.image = f_img  # Keep reference to prevent garbage collection
        
        # Save state after adding image
        save_canvas_state()
        status_bar.config(text="Image generated successfully!")
        
    except Exception as e:
        error_message = str(e)
        if "server unavailable" in error_message.lower() or "temporarily" in error_message.lower():
            messagebox.showerror("Server Busy", "The image generation server is currently busy. Please try again in a few minutes.")
        else:
            messagebox.showerror("Error", f"Could not generate image: {error_message}")
        status_bar.config(text="Image generation failed")
        print(f"Image generation error: {error_message}")  # For debugging

# Add image generator button before main loop
image_gen_button = Button(
    root,
    text="AI\nImage",
    command=generate_image_from_text,
    bg="#4a90e2",  # Blue color
    fg="white",
    activebackground="#357abd",
    borderwidth=0,
    cursor="hand2",
    font=("Arial", 9, "bold"),
    width=4,
    height=2,
    relief="flat"
)
image_gen_button.place(x=canvas_width + canvas_x - 150, y=canvas_height - 50)

# Add tooltip
tooltip = Label(root, text="Generate Image from Text", bg="#ffffe0", relief="solid", borderwidth=1)
tooltip.place_forget()

def show_tooltip(event):
    tooltip.place(x=event.x_root, y=event.y_root - 30)

def hide_tooltip(event):
    tooltip.place_forget()

image_gen_button.bind("<Enter>", show_tooltip)
image_gen_button.bind("<Leave>", hide_tooltip)

def save_canvas_state():
    """Save current canvas state to history"""
    global history, current_state, redo_stack
    
    if len(history) > 0 and current_state < len(history) - 1:
        # If we're not at the end of history, truncate history
        history = history[:current_state + 1]
        redo_stack = []
    
    try:
        # Get canvas position
        x = root.winfo_rootx() + canvas.winfo_x()
        y = root.winfo_rooty() + canvas.winfo_y()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Capture the canvas area directly
        img = ImageGrab.grab(bbox=(x, y, x+width, y+height))
        
        # Convert to bytes
        with io.BytesIO() as bytes_io:
            img.save(bytes_io, format='PNG')
            bytes_data = bytes_io.getvalue()
        
        history.append(bytes_data)
        current_state = len(history) - 1
        
        # Limit history size
        if len(history) > max_history:
            history.pop(0)
            current_state -= 1
            
    except Exception as e:
        print(f"Could not save canvas state: {e}")

def restore_canvas_state(state_data):
    """Restore canvas state from stored data"""
    try:
        canvas.delete('all')
        
        # Convert bytes to image 
        with io.BytesIO(state_data) as bytes_io:
            img = Image.open(bytes_io)
            photo_img = ImageTk.PhotoImage(img)
            
            # We need to keep a reference to avoid garbage collection
            canvas.photo_img = photo_img
            canvas.create_image(0, 0, image=photo_img, anchor=NW)
    except Exception as e:
        print(f"Could not restore canvas state: {e}")
        # If restore fails, at least clear the canvas
        canvas.delete('all')

def undo():
    """Undo last action"""
    global current_state, redo_stack
    
    if current_state > 0:
        # Save current state to redo stack
        redo_stack.append(history[current_state])
        
        # Go back one state
        current_state -= 1
        restore_canvas_state(history[current_state])

def redo():
    """Redo previously undone action"""
    global current_state, redo_stack
    
    if redo_stack:
        # Get state from redo stack
        state_data = redo_stack.pop()
        
        # Move forward in history
        current_state += 1
        if current_state >= len(history):
            history.append(state_data)
        else:
            history[current_state] = state_data
            
        restore_canvas_state(state_data)

def toggle_dark_mode():
    global current_theme
    if current_theme == LIGHT_THEME:
        current_theme = DARK_THEME
        dark_mode_button.config(text="🌞")  # Sun icon
    else:
        current_theme = LIGHT_THEME
        dark_mode_button.config(text="🌙")  # Moon icon
    
    apply_theme()

def apply_theme():
    # Apply theme to root window
    root.config(bg=current_theme['bg'])
    
    # Apply theme to canvas
    canvas.config(bg=current_theme['canvas_bg'])
    
    # Apply theme to sidebar
    colors.config(bg=current_theme['sidebar_bg'])
    
    # Apply theme to frames
    for frame in [chatbot_frame, chatbotv_frame, youtube_frame]:
        frame.config(bg=current_theme['frame_bg'])
    
    # Apply theme to text widgets
    for text_widget in [query_output, queryv_output]:
        text_widget.config(bg=current_theme['output_bg'], fg=current_theme['text'])
    
    # Apply theme to entries
    for entry in [query_entry, query_entryv, youtube_search_entry]:
        entry.config(bg=current_theme['entry_bg'], fg=current_theme['text'])
    
    # Apply theme to labels
    for label in root.winfo_children():
        if isinstance(label, Label):
            label.config(bg=current_theme['bg'], fg=current_theme['text'])

# Add dark mode toggle button
dark_mode_button = Button(
    root,
    text="🌙",  # Just the moon icon
    command=toggle_dark_mode,
    font=("Helvetica", 12),  # Smaller font size
    bg=current_theme['button_bg'],
    fg="white",
    relief="flat",
    padx=8,  # Smaller padding
    pady=8,  # Smaller padding
    cursor="hand2",
    bd=0,  # No border
    highlightthickness=0,  # No highlight
    activebackground=current_theme['button_hover'],  # Active state color
    width=2,  # Small fixed width
    height=1  # Small fixed height
)

# Make the button circular using a lambda function after placing it
dark_mode_button.place(x=30, y=canvas_height - 300)  # Position above YouTube button
root.after(10, lambda: dark_mode_button.configure(width=2, height=1))  # Ensure circular shape

# Add hover effect for dark mode button
def dark_mode_on_enter(e):
    e.widget['background'] = current_theme['button_hover']

def dark_mode_on_leave(e):
    e.widget['background'] = current_theme['button_bg']

dark_mode_button.bind("<Enter>", dark_mode_on_enter)
dark_mode_button.bind("<Leave>", dark_mode_on_leave)

root.mainloop()