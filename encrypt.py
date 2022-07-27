from datetime import datetime
from pickle import dump, load
from tkinter import Entry, filedialog, Tk, Label, Message


class GUI:
    def __init__(self):
        pass

    @staticmethod
    def askFile(text='', purpose='open', multuple=False):
        root = Tk()
        Label(root, text=text).pack(side='left')
        if purpose == 'save':
            filePath = filedialog.asksaveasfilename()
        elif purpose == 'open':
            if multuple: filePath = filedialog.askopenfilenames()
            else: filePath = filedialog.askopenfilename()
        root.destroy()
        root.mainloop()
        return filePath

    @staticmethod
    def askKeyWord(text):
        global root, keyWord
        def helper(entry):
            global root, keyWord
            keyWord = entry.widget.get()
            root.destroy()
        root = Tk()
        Label(root, text=text).pack(side='left')
        entry = Entry(root, text='')
        entry.pack(side='left')
        entry.bind('<Return>', helper)
        root.mainloop()
        return keyWord

    @staticmethod
    def showMessage(text):
        root = Tk()
        Message(text=text).pack()
        root.mainloop()


class RawTools(GUI):
    def __init__(self):
        self.memoFile = 'memo.log'
        self.terminalBytes = {
            'jpeg': (
                bytes.fromhex('FFD8'),
                bytes.fromhex('FFD9')
            ),
            'jpg': (
                bytes.fromhex('FFD8'),
                bytes.fromhex('FFD9')
            ),
            'png': (
                bytes.fromhex('8950'),
                bytes.fromhex('49454E44AE426082')
            )
        }

    def memo(self, keyWord, size, dataFile, containerFile):
        data = {
            'keyWord': keyWord,
            'time': str(datetime.now()),
            'size': size,
            'dataFile': dataFile,
            'containerFile': containerFile
        }
        with open(self.memoFile, 'ab') as file:
            dump(data, file)

    def getLogs(self):
        try:
            file = open(self.memoFile, 'rb')
            logs = []
            while True:
                try:
                    logs.append(load(file))
                except Exception as error:
                    if type(error) == EOFError:
                        break
        except Exception as err:
            if type(err) == FileNotFoundError:
                self.showMessage('No records exist')
        else:
            return logs

    def searchLogs(self, keyWord):
        logs = self.getLogs()
        if not logs:
            return
        matches = []
        for data in logs:
            if data['keyWord'] == keyWord:
                matches.append(data)
        if not matches:
            self.showMessage('No matches exist')
        else:
            return matches

    def deleteLog(self, keyWord):
        logs = self.getLogs()
        if not logs: return None
        file = open(self.memoFile, 'wb')
        for data in logs:
            if data['keyWord'] == keyWord: continue
            dump(data, file)
        file.close()

    def checkEndBytes(self, path, virginity=False, index=False):
        endBytes = self.terminalBytes[path.split('.')[-1]]
        if not endBytes:
            self.showMessage('Sorry, We do not suppport containers with this file extention')
            return False
        with open(path, 'rb') as file:
            data = file.read()
        if virginity:
            virginity = (data[-len(endBytes):] == endBytes) and (data.count(endBytes) == 1)
        if index:
            index = data.index(endBytes) + len(endBytes)
        return {'virginity': virginity, 'index': index}

    def inject(self, path, data):
        with open(path, 'ab') as file:
            return file.write(data)

    def retrieve(self, path, size=0):
        temp = self.checkEndBytes(path, index=True)
        if temp: offset = temp.get('index')
        else: return False
        del temp
        with open(path, 'rb') as file:
            file.seek(offset)
            if size: data = file.read(size)
            else: data = file.read()
        return data


class Functions(RawTools):
    def __init__(self):
        super().__init__()

    def clean(self, containerPath):
        temp = self.checkEndBytes(containerPath, index=True)
        if temp: offset = temp.get('index')
        else: return False
        del temp
        with open(containerPath, 'rb') as file:
            file.seek(0)
            data = file.read(offset)
        with open(containerPath, 'wb') as file:
            return file.write(data)

    def hideFile(self, dataPath, containerPath, keyWord):
        temp = self.checkEndBytes(virginity=True)
        if not temp: return False
        if not temp.get('virginity'):
            self.showMessage('Sorry, either the file already has some data in it or it has been truncated')
            return False
        del temp
        with open(dataPath, 'rb') as file:
            data = file.read()
        size = self.inject(containerPath, data)
        self.memo(keyWord, size, dataPath, containerPath)

    def revealFile(self, dataPath, containerPath=''):
        temp = self.checkEndBytes(containerPath, virginity=True)
        if not temp: return False
        dataInFile = not temp.get('virginity')
        del temp
        if dataInFile:
            data = self.retrieve(containerPath)
            with open(dataPath, 'ab') as file:
                file.write(data)

    def undoHiding(self, dataPath, keyWord):
        matches = self.searchLogs(keyWord)
        if matches:
            for match in matches:
                containerPath = match['containerFile']
                self.revealFile(dataPath, containerPath)


class FileHider(Functions):
    def __init__(self):
        super().__init__()

    def hide(self):
        keyWord = self.askKeyWord('Please provide a new keyWord for this action:\t')
        dataPath = self.askFile(text='The file you wish to hide')
        containerPath = self.askFile(text='The file you wish to hide in')
        self.hideFile(dataPath, containerPath, keyWord)

    def reveal(self):
        dataPath = self.askFile(text='The file you wish to save data in',purpose='save')
        keyWord = self.askKeyWord('The keyWord for this action was:\t')
        if not keyWord:
            containerPath = self.askFile(text='The file you hid data in', purpose='open')
            self.revealFile(dataPath, containerPath)
        self.undoHiding(dataPath, keyWord)

    def clear(self):
        containerPaths = []
        keyWord = self.askKeyWord('The keyWord for this action was:\t')
        if keyWord:
            logs = self.searchLogs(keyWord)
            if not logs:
                return
            for data in logs: containerPaths.append(data['containerFile'])
            self.deleteLog(keyWord)
        else:
            containerPaths.append(self.askFile(text='The file you wish to clear'), multiple=True)
        for containerPath in containerPaths: self.clean(containerPath=containerPath)

            
if __name__ == "__main__":
    pass
