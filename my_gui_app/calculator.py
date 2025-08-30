import tkinter as tk
from tkinter import ttk

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Calculator")
        self.root.geometry("300x400")
        self.root.resizable(False, False)
        
        # Calculator display
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        
        self.create_widgets()
        self.current_number = ""
        self.operation = ""
        self.first_number = 0
        self.new_number = True
    
    def create_widgets(self):
        # Display
        display_frame = ttk.Frame(self.root, padding="10")
        display_frame.pack(fill=tk.X)
        
        self.display = ttk.Entry(display_frame, textvariable=self.display_var, 
                                font=('Arial', 20), justify='right', state='readonly')
        self.display.pack(fill=tk.X)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.root, padding="10")
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button layout
        buttons = [
            ('C', 0, 0), ('±', 0, 1), ('%', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 2), ('.', 4, 2), ('=', 4, 3)
        ]
        
        for button in buttons:
            if len(button) == 4:  # Special case for zero button
                text, row, col, colspan = button
                btn = ttk.Button(buttons_frame, text=text, command=lambda t=text: self.button_click(t))
                btn.grid(row=row, column=col, columnspan=colspan, sticky='nsew', padx=2, pady=2)
            else:
                text, row, col = button
                btn = ttk.Button(buttons_frame, text=text, command=lambda t=text: self.button_click(t))
                btn.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)
        
        # Configure grid weights
        for i in range(5):
            buttons_frame.rowconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.columnconfigure(i, weight=1)
    
    def button_click(self, value):
        if value.isdigit() or value == '.':
            if self.new_number:
                self.display_var.set(value)
                self.new_number = False
            else:
                if value == '.' and '.' in self.display_var.get():
                    return
                self.display_var.set(self.display_var.get() + value)
        elif value == 'C':
            self.clear()
        elif value == '±':
            self.negate()
        elif value == '%':
            self.percentage()
        elif value in ['+', '-', '×', '÷']:
            self.set_operation(value)
        elif value == '=':
            self.calculate()
    
    def clear(self):
        self.display_var.set("0")
        self.current_number = ""
        self.operation = ""
        self.first_number = 0
        self.new_number = True
    
    def negate(self):
        current = float(self.display_var.get())
        self.display_var.set(str(-current))
    
    def percentage(self):
        current = float(self.display_var.get())
        self.display_var.set(str(current / 100))
    
    def set_operation(self, op):
        self.first_number = float(self.display_var.get())
        self.operation = op
        self.new_number = True
    
    def calculate(self):
        if self.operation:
            second_number = float(self.display_var.get())
            if self.operation == '+':
                result = self.first_number + second_number
            elif self.operation == '-':
                result = self.first_number - second_number
            elif self.operation == '×':
                result = self.first_number * second_number
            elif self.operation == '÷':
                if second_number == 0:
                    self.display_var.set("Error")
                    return
                result = self.first_number / second_number
            
            self.display_var.set(str(result))
            self.operation = ""
            self.new_number = True

def main():
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
