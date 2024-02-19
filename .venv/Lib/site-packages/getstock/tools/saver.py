import openpyxl

def save_file(data: list, filepath: str) -> None:
    def convIfNum(a: str):
        try:
            a = float(a)
        except:
            pass
        return a

    wb = openpyxl.Workbook()
    ws = wb.active

    for row in data:
        ws.append(list(map(convIfNum, row)))
    wb.save(f"{filepath}.xlsx")