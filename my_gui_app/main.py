import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

class ModernGUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Python GUI Application")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # Create widgets
        self._create_widgets()
        
        # Load saved data
        self.load_data()
    
    def _create_widgets(self):
        # Title
        title_label = ttk.Label(self.main_frame, text="Modern Python GUI Application", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input section
        ttk.Label(self.main_frame, text="Enter Text:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.text_entry = ttk.Entry(self.main_frame, width=50)
        self.text_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_items).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Data", command=self.save_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load File", command=self.load_file).pack(side=tk.LEFT, padx=5)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(self.main_frame)
        list_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.listbox = tk.Listbox(list_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(3, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind double-click to edit
        self.listbox.bind('<Double-1>', self.edit_item)
        
        # Sample data
        self.items = []
    
    def add_item(self):
        text = self.text_entry.get().strip()
        if text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            item = f"[{timestamp}] {text}"
            self.items.append(item)
            self.listbox.insert(tk.END, item)
            self.text_entry.delete(0, tk.END)
            self.status_var.set(f"Added: {text}")
            self.save_data()
        else:
            messagebox.showwarning("Warning", "Please enter some text!")
    
    def clear_items(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all items?"):
            self.items.clear()
            self.listbox.delete(0, tk.END)
            self.status_var.set("All items cleared")
            self.save_data()
    
    def edit_item(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            old_text = self.items[index]
            
            # Create edit dialog
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit Item")
            edit_window.geometry("400x150")
            edit_window.transient(self.root)
            edit_window.grab_set()
            
            ttk.Label(edit_window, text="Edit item:").pack(pady=10)
            edit_entry = ttk.Entry(edit_window, width=50)
            edit_entry.pack(pady=10)
            edit_entry.insert(0, old_text)
            edit_entry.select_range(0, tk.END)
            edit_entry.focus()
            
            def save_edit():
                new_text = edit_entry.get().strip()
                if new_text:
                    self.items[index] = new_text
                    self.listbox.delete(index)
                    self.listbox.insert(index, new_text)
                    self.status_var.set(f"Edited: {new_text}")
                    self.save_data()
                    edit_window.destroy()
                else:
                    messagebox.showwarning("Warning", "Text cannot be empty!")
            
            ttk.Button(edit_window, text="Save", command=save_edit).pack(pady=10)
            edit_entry.bind('<Return>', lambda e: save_edit())
    
    def save_data(self):
        try:
            data = {
                'items': self.items,
                'timestamp': datetime.now().isoformat()
            }
            with open('gui_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            self.status_var.set("Data saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")
    
    def load_data(self):
        try:
            if os.path.exists('gui_data.json'):
                with open('gui_data.json', 'r') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
                    for item in self.items:
                        self.listbox.insert(tk.END, item)
                self.status_var.set("Data loaded successfully")
        except Exception as e:
            self.status_var.set(f"Failed to load data: {e}")
    
    def load_file(self):
        filename = filedialog.askopenfilename(
            title="Select a text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.text_entry.delete(0, tk.END)
                        self.text_entry.insert(0, content)
                        self.status_var.set(f"Loaded file: {os.path.basename(filename)}")
                    else:
                        messagebox.showinfo("Info", "File is empty")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

def main():
    root = tk.Tk()
    app = ModernGUIApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
