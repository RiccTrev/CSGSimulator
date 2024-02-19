from tkinter import *
from tkinter import messagebox, filedialog
from dateutil import parser
from getstock.tools.dates import checkDateError, checkValidTime
from getstock.tools.saver import save_file
from getstock.scraper.scraper import run_stock_retriever
from tkinter.ttk import *

class EventLoop():
    def __init__(self):
        self.mainWindow = self.buildMainWindow()
    
    def buildMainWindow(self) -> Tk:
        window = Tk()
        window.title("Stock Data Retrieval")
        window.geometry('1100x300')

        selectedInterval = IntVar()
        selectedTicker = StringVar()
        selectedStartDate = StringVar()
        selectedEndDate = StringVar()

        labelInterval = Label(window, text="Select Interval of Data:")
        labelTicker = Label(window, text="Enter Ticker of Stock You Want Data For:")
        labelStartDate = Label(window, text="Start Date: (Ex. 01/01/2014)")
        labelEndDate = Label(window, text="End Date: (Ex. 01/01/2022)")
        radDay = Radiobutton(window,text='Every Day', value=0, variable=selectedInterval)
        radWk = Radiobutton(window,text='Every Week', value=1, variable=selectedInterval)
        radMon = Radiobutton(window,text='Every Month', value=2, variable=selectedInterval)
        entryTicker = Entry(window, textvariable=selectedTicker)
        buttonSubmit = Button(window, text="Get Stock Data", command=lambda: self.execute(
            selectedTicker.get(), selectedInterval.get(), selectedStartDate.get(), selectedEndDate.get()
            )
        )
        
        startDate = Entry(window, textvariable=selectedStartDate)
        endDate = Entry(window, textvariable=selectedEndDate)

        def entry_limit(entry_text):
            if len(entry_text.get()) == 0:
                return
            if len(entry_text.get()) > 0:
                entry_text.set(entry_text.get()[:4])
            if not entry_text.get()[-1].isalpha():
                entry_text.set(entry_text.get()[0:len(entry_text.get())-1])

        selectedTicker.trace("w", lambda *args: entry_limit(selectedTicker))

        Grid.rowconfigure(window,0,weight=1)
        Grid.rowconfigure(window,1,weight=1)
        Grid.rowconfigure(window,2,weight=1)
        Grid.rowconfigure(window,3,weight=1)
        Grid.columnconfigure(window,0,weight=1)
        Grid.columnconfigure(window,1,weight=1)
        Grid.columnconfigure(window,2,weight=1)
        Grid.columnconfigure(window,3,weight=1)

        radDay.grid(column=1, row=0, sticky=N+W+S+E, pady=2, padx=2)
        radWk.grid(column=2, row=0, sticky=N+W+S+E, pady=2, padx=2)
        radMon.grid(column=3, row=0, sticky=N+W+S+E, pady=2, padx=2)
        labelInterval.grid(column=0, row=0, sticky=N+W+S+E, pady=2, padx=2)
        labelTicker.grid(column=0, row=1, columnspan=2, sticky=N+W+S+E, pady=2, padx=2)
        entryTicker.grid(column=1, row=1, columnspan=3, sticky=N+W+S+E, pady=2, padx=2)
        buttonSubmit.grid(column=1, row=3, columnspan=2, sticky=N+W+S+E, pady=2, padx=2)
        startDate.grid(column=1, row=2, sticky=N+W+S+E, pady=2, padx=2)
        endDate.grid(column=3, row=2, sticky=N+W+S+E, pady=2, padx=2)
        labelStartDate.grid(column=0, row=2, sticky=N+W+S+E, pady=2, padx=2)
        labelEndDate.grid(column=2, row=2, sticky=N+W+S+E, pady=2, padx=2)

        return window

    def execute(self, ticker: str, timeInterval: int, startDate: str, endDate: str):
        if len(ticker) != 4:
            messagebox.showerror("ERROR","Ticker Name Must Be 4 Charecters In Length!")
            return
        if checkDateError(startDate) or checkDateError(endDate):
            messagebox.showerror("ERROR","Date Format Must Be Like:\n dd/mm/yyyy")
            return
        if checkValidTime(startDate) or checkValidTime(endDate):
            messagebox.showerror("ERROR","Date Cannot Be Before: Aug 18, 2004 or After: Jan 06, 2022")
            return

        sd = int(parser.parse(startDate).timestamp())
        ed = int(parser.parse(endDate).timestamp())

        relate = {0:"d", 1:"wk", 2:"mo"}

        try:
            data = run_stock_retriever(sd, ed, ticker, relate[timeInterval])
        except:
            messagebox.showerror("ERROR","An Error Occured Attempting To Retrieve Data From Yahoo")
            return

        filepath = filedialog.asksaveasfilename()

        if not filepath or filepath == "":
            messagebox.showerror("ERROR","An Error Occured Selecting File Location")
            return
            
        try:
            save_file(data, filepath)
        except:
            messagebox.showerror("ERROR","An Error Occured Attempting To Save The Excel Workbook")
            return

        messagebox.showinfo("SUCCESS","Data has been saved!")
        self.mainWindow.destroy()

    def run(self):
        self.mainWindow.mainloop()