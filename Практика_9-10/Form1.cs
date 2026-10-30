using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;
using Excel = Microsoft.Office.Interop.Excel;
using Word = Microsoft.Office.Interop.Word;

namespace Практика_9
{
    public partial class Form1 : Form
    {
        // Вся таблица: список записей. На открытии приложения пуст, данные грузятся из файла.
        List<Record> Table = new List<Record>();

        // Для передачи записи между основной формой и окнами диалога.
        static public Record Rec;

        // Имя открытого файла (null — таблица ещё ни разу не сохранялась).
        string fileName = null;

        // Есть ли несохранённые изменения.
        bool modified = false;

        // Состояния таблицы до каждого изменения — для «Отмены действия».
        Stack<List<Record>> undoStack = new Stack<List<Record>>();

        const string AppTitle = "Табличное представление данных";

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {
            dataGridView1.AutoGenerateColumns = true;
            dataGridView1.DataSource = Table;
            Redraw();
        }

        // Отрисовка обновлённого грида: DataSource нельзя изменить, его снимают и назначают снова.
        // select — номер строки, которую выделить после перерисовки.
        public void Redraw(int select = -1)
        {
            dataGridView1.DataSource = null;
            dataGridView1.AutoGenerateColumns = true;
            dataGridView1.DataSource = Table;

            // Порядок следования колонок и заголовки.
            SetColumn("Name", 0, "Имя", null, 30);
            SetColumn("BirthDate", 1, "Дата рождения", "dd.MM.yyyy", 15);
            SetColumn("Profession", 2, "Должность", null, 22);
            SetColumn("Department", 3, "Отдел", null, 18);
            SetColumn("Money", 4, "Оклад, руб.", "N2", 15);
            dataGridView1.Columns["Money"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            dataGridView1.Columns["BirthDate"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;

            dataGridView1.ClearSelection();
            if (Table.Count > 0)
            {
                if (select < 0) select = 0;
                if (select >= Table.Count) select = Table.Count - 1;
                dataGridView1.CurrentCell = dataGridView1.Rows[select].Cells["Name"];
                dataGridView1.Rows[select].Selected = true;
            }
            ShowCurrent();
            UpdateStatus();
        }

        void SetColumn(string property, int index, string header, string format, float weight)
        {
            DataGridViewColumn column = dataGridView1.Columns[property];
            column.DataPropertyName = property;   // Название поля записи
            column.HeaderText = header;           // Заголовок столбца
            column.DisplayIndex = index;
            column.FillWeight = weight;
            column.SortMode = DataGridViewColumnSortMode.NotSortable;
            if (format != null)
                column.DefaultCellStyle.Format = format;
        }

        // Показать текущую запись в текстовом поле внизу формы.
        void ShowCurrent()
        {
            if (dataGridView1.CurrentRow == null || Table.Count == 0)
            {
                textBox1.Text = "";
                return;
            }
            int current = dataGridView1.CurrentRow.Index;
            // Извлечь данные из таблицы по номеру:
            Record Tmp = new Record(Table[current].Name, Table[current].BirthDate,
                Table[current].Profession, Table[current].Department, Table[current].Money);
            // Показать как строку:
            textBox1.Text = Tmp.ToString();
        }

        private void dataGridView1_CellClick(object sender, DataGridViewCellEventArgs e)
        {
            ShowCurrent();
        }

        // Переход по записям стрелками тоже обновляет текстовое поле.
        private void dataGridView1_SelectionChanged(object sender, EventArgs e)
        {
            ShowCurrent();
        }

        // Двойной щелчок по строке — изменить запись.
        private void dataGridView1_CellDoubleClick(object sender, DataGridViewCellEventArgs e)
        {
            if (e.RowIndex >= 0)
                изменитьToolStripMenuItem_Click(sender, e);
        }

        // Enter — изменить, Delete — удалить.
        private void dataGridView1_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                изменитьToolStripMenuItem_Click(sender, e);
                e.Handled = true;
            }
            else if (e.KeyCode == Keys.Delete)
            {
                удалитьToolStripMenuItem_Click(sender, e);
                e.Handled = true;
            }
        }

        #region Служебные методы

        // Запомнить состояние таблицы перед изменением.
        void SaveUndo()
        {
            undoStack.Push(new List<Record>(Table));
        }

        void SetModified()
        {
            modified = true;
            UpdateStatus();
        }

        void UpdateStatus()
        {
            string name = fileName == null ? "Новая таблица" : Path.GetFileName(fileName);
            Text = AppTitle + " — " + name + (modified ? " *" : "");
            toolStripStatusLabelCount.Text = "Записей: " + Table.Count;
            toolStripStatusLabelFile.Text = fileName == null ? "Файл не выбран" : "Файл: " + fileName;
            отменаToolStripMenuItem.Enabled = toolStripButtonUndo.Enabled = undoStack.Count > 0;
        }

        // Номер текущей строки или -1, если выбирать нечего.
        int CurrentIndex()
        {
            if (Table.Count == 0 || dataGridView1.CurrentRow == null)
            {
                MessageBox.Show("Таблица пуста или запись не выбрана.", AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                return -1;
            }
            return dataGridView1.CurrentRow.Index;
        }

        // Если есть несохранённые изменения, предложить сохранить их.
        // Возвращает false, если пользователь передумал (нажал «Отмена»).
        bool AskSaveChanges()
        {
            if (!modified)
                return true;
            var result = MessageBox.Show("Таблица изменена. Сохранить изменения?", AppTitle,
                MessageBoxButtons.YesNoCancel, MessageBoxIcon.Question);
            if (result == DialogResult.Cancel)
                return false;
            if (result == DialogResult.Yes)
                return Save();
            return true;
        }

        #endregion

        #region Правка: добавить, изменить, удалить, отмена

        private void добавитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            DialogAdd Dialog = new DialogAdd();
            // Показать диалог.
            if (Dialog.ShowDialog(this) == DialogResult.OK)
            {
                SaveUndo();
                Table.Add(Rec);          // Получена запись, добавлена в Table.
                SetModified();
                Redraw(Table.Count - 1);
            }
        }

        private void изменитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            int current = CurrentIndex();
            if (current < 0)
                return;
            // Извлечь в переменную static public Record Rec и передать в диалог.
            Rec = Table[current];
            DialogEdit Dialog = new DialogEdit();
            // Если DialogResult вернул запись, то изменённую запись вставить в таблицу по положению current.
            if (Dialog.ShowDialog(this) == DialogResult.OK)
            {
                SaveUndo();
                Table[current] = Rec;
                SetModified();
                Redraw(current);
            }
        }

        private void удалитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            int current = CurrentIndex();
            if (current < 0)
                return;

            // Если выделено несколько строк (например, «Выделить все») — удаляем их все.
            List<int> rows = dataGridView1.SelectedRows.Cast<DataGridViewRow>()
                .Select(r => r.Index).OrderByDescending(i => i).ToList();
            if (rows.Count <= 1)
                rows = new List<int> { current };

            string question;
            if (rows.Count == 1)
            {
                Rec = Table[current];
                question = "Попытка удалить запись:\n" + Rec.ToString();
            }
            else
                question = "Попытка удалить выделенные записи: " + rows.Count + " шт.";

            var result = MessageBox.Show(question, "Удаление",
                MessageBoxButtons.OKCancel, MessageBoxIcon.Question);
            if (result != DialogResult.OK)
                return;

            SaveUndo();
            foreach (int i in rows)
                Table.RemoveAt(i);
            SetModified();
            Redraw(rows.Last());
        }

        private void отменаToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (undoStack.Count == 0)
                return;
            int current = dataGridView1.CurrentRow == null ? 0 : dataGridView1.CurrentRow.Index;
            Table = undoStack.Pop();
            SetModified();
            Redraw(current);
        }

        private void выделитьВсеToolStripMenuItem_Click(object sender, EventArgs e)
        {
            dataGridView1.SelectAll();
            dataGridView1.Focus();
        }

        #endregion

        #region Файл: создать, открыть, сохранить, сохранить как, выход

        private void создатьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!AskSaveChanges())
                return;
            Table = new List<Record>();
            fileName = null;
            modified = false;
            undoStack.Clear();
            Redraw();
        }

        private void открытьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!AskSaveChanges())
                return;
            if (openFileDialog1.ShowDialog(this) != DialogResult.OK)
                return;
            LoadFromFile(openFileDialog1.FileName);
        }

        void LoadFromFile(string name)
        {
            List<Record> list = new List<Record>();
            int lineNumber = 0;
            List<string> errors = new List<string>();
            try
            {
                using (StreamReader StR = new StreamReader(name, DetectEncoding(name)))
                {
                    // Построчно: строка файла -> запись -> в список.
                    while (!StR.EndOfStream)
                    {
                        string line = StR.ReadLine();
                        lineNumber++;
                        if (String.IsNullOrWhiteSpace(line))
                            continue;
                        try
                        {
                            list.Add(Record.Parse(line));
                        }
                        catch (FormatException ex)
                        {
                            errors.Add("строка " + lineNumber + ": " + ex.Message);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Не удалось открыть файл:\n" + ex.Message, AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            Table = list;
            fileName = name;
            modified = false;
            undoStack.Clear();
            Redraw();

            if (errors.Count > 0)
                MessageBox.Show("Пропущено строк с ошибками: " + errors.Count + "\n\n" +
                    string.Join("\n", errors.Take(10)), AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }

        // Файл, набранный в Блокноте, может быть и в UTF-8, и в ANSI (Windows-1251).
        static Encoding DetectEncoding(string name)
        {
            try
            {
                new UTF8Encoding(false, true).GetString(File.ReadAllBytes(name));
                return Encoding.UTF8;
            }
            catch (DecoderFallbackException)
            {
                return Encoding.GetEncoding(1251);
            }
        }

        private void сохранитьToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Save();
        }

        private void сохранитьКакToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SaveAs();
        }

        // Сохранить в тот же файл, который был открыт. Новую таблицу — через «Сохранить как».
        bool Save()
        {
            if (fileName == null)
                return SaveAs();
            return SaveToFile(fileName);
        }

        bool SaveAs()
        {
            saveFileDialog1.FileName = fileName == null ? "Сотрудники.txt" : Path.GetFileName(fileName);
            if (saveFileDialog1.ShowDialog(this) != DialogResult.OK)
                return false;
            return SaveToFile(saveFileDialog1.FileName);
        }

        bool SaveToFile(string name)
        {
            try
            {
                using (StreamWriter StW = new StreamWriter(name, false, Encoding.UTF8))
                {
                    foreach (Record P in Table)
                        StW.WriteLine(P.ToFileString());
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Не удалось сохранить файл:\n" + ex.Message, AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
            fileName = name;
            modified = false;
            UpdateStatus();
            return true;
        }

        private void выходToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Close();
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (!AskSaveChanges())
                e.Cancel = true;
        }

        #endregion

        #region Импорт: Excel, Word, NotePad

        bool CheckNotEmpty()
        {
            if (Table.Count > 0)
                return true;
            MessageBox.Show("Таблица пуста — нечего передавать.", AppTitle,
                MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }

        // Справка о заработной плате: имя, отдел, оклад.
        string SalaryReport()
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("СПРАВКА О ЗАРАБОТНОЙ ПЛАТЕ СОТРУДНИКОВ");
            sb.AppendLine("на " + DateTime.Today.ToString("dd.MM.yyyy") + " г.");
            sb.AppendLine();
            int n = 1;
            foreach (Record P in Table)
                sb.AppendLine(string.Format("{0}. {1} — {2} — {3:N2} руб.", n++, P.Name, P.Department, P.Money));
            sb.AppendLine();
            sb.AppendLine(string.Format("Всего сотрудников: {0}", Table.Count));
            sb.AppendLine(string.Format("Фонд оплаты труда: {0:N2} руб.", Table.Sum(p => p.Money)));
            return sb.ToString();
        }

        private void excelToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!CheckNotEmpty())
                return;
            saveFileDialog2.Filter = "Книга Excel (*.xlsx)|*.xlsx";
            saveFileDialog2.FileName = "Сотрудники.xlsx";
            if (saveFileDialog2.ShowDialog(this) != DialogResult.OK)
                return;
            string f_Name = saveFileDialog2.FileName;

            Excel.Application ExAplication = null;
            try
            {
                Cursor = Cursors.WaitCursor;
                // Создать приложение, книгу и взять первый лист.
                ExAplication = new Excel.Application();
                Excel.Workbook Book = ExAplication.Workbooks.Add();
                Excel.Worksheet mySheet = (Excel.Worksheet)Book.Sheets[1];
                mySheet.Name = "Сотрудники";

                string[] headers = { "Имя", "Дата рождения", "Должность", "Отдел", "Оклад, руб." };
                for (int j = 0; j < headers.Length; j++)
                    mySheet.Cells[1, j + 1] = headers[j];

                // Построчно переносим записи в клетки Cells[i, j].
                for (int i = 0; i < Table.Count; i++)
                {
                    int row = i + 2;
                    mySheet.Cells[row, 1] = Table[i].Name;
                    mySheet.Cells[row, 2] = Table[i].BirthDate.ToOADate();
                    mySheet.Cells[row, 3] = Table[i].Profession;
                    mySheet.Cells[row, 4] = Table[i].Department;
                    mySheet.Cells[row, 5] = Table[i].Money;
                }
                int last = Table.Count + 1;
                mySheet.Cells[last + 1, 4] = "Итого:";
                mySheet.Cells[last + 1, 5] = "=SUM(E2:E" + last + ")";

                mySheet.get_Range("A1", "E1").Font.Bold = true;
                mySheet.get_Range("D" + (last + 1), "E" + (last + 1)).Font.Bold = true;
                mySheet.get_Range("B2", "B" + last).NumberFormat = "dd.mm.yyyy";
                mySheet.get_Range("E2", "E" + (last + 1)).NumberFormat = "#,##0.00";
                mySheet.Columns.AutoFit();

                Book.SaveAs(f_Name);
                // Показать результат пользователю.
                ExAplication.Visible = true;
                ExAplication.UserControl = true;
            }
            catch (Exception ex)
            {
                if (ExAplication != null)
                    ExAplication.Quit();
                MessageBox.Show("Не удалось выполнить импорт в Excel. Установлен ли Microsoft Excel?\n\n" + ex.Message,
                    AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Cursor = Cursors.Default;
                if (ExAplication != null)
                    Marshal.ReleaseComObject(ExAplication);
            }
        }

        private void wordToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!CheckNotEmpty())
                return;
            saveFileDialog2.Filter = "Документ Word (*.docx)|*.docx";
            saveFileDialog2.FileName = "Справка о зарплате.docx";
            if (saveFileDialog2.ShowDialog(this) != DialogResult.OK)
                return;

            Word.Application WordAplication = null;
            try
            {
                Cursor = Cursors.WaitCursor;
                // Создать приложение и документ.
                WordAplication = new Word.Application();
                Word.Document WordDocument = WordAplication.Documents.Add();
                // Вся справка как строка.
                WordDocument.Content.Text = SalaryReport();
                WordDocument.Content.Font.Name = "Times New Roman";
                WordDocument.Content.Font.Size = 14;
                WordDocument.Paragraphs[1].Range.Font.Bold = 1;
                // Сохранить.
                WordDocument.SaveAs2(saveFileDialog2.FileName);
                WordAplication.Visible = true;
            }
            catch (Exception ex)
            {
                if (WordAplication != null)
                    ((Word._Application)WordAplication).Quit();
                MessageBox.Show("Не удалось выполнить импорт в Word. Установлен ли Microsoft Word?\n\n" + ex.Message,
                    AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Cursor = Cursors.Default;
                if (WordAplication != null)
                    Marshal.ReleaseComObject(WordAplication);
            }
        }

        private void notePadToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!CheckNotEmpty())
                return;
            try
            {
                string name = Path.Combine(Path.GetTempPath(), "Справка о зарплате.txt");
                File.WriteAllText(name, SalaryReport(), Encoding.UTF8);
                Process.Start("notepad.exe", "\"" + name + "\"");
            }
            catch (Exception ex)
            {
                MessageBox.Show("Не удалось открыть Блокнот:\n" + ex.Message, AppTitle,
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        #endregion

        #region Операции с данными: поиск, сортировка, итоги

        private void найтиToolStripMenuItem_Click(object sender, EventArgs e)
        {
            toolStripTextBoxFind.Focus();
            toolStripTextBoxFind.SelectAll();
        }

        private void toolStripButtonFind_Click(object sender, EventArgs e)
        {
            FindNext();
        }

        private void toolStripTextBoxFind_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                FindNext();
                e.Handled = e.SuppressKeyPress = true;
            }
        }

        // Ищет следующую запись, в имени которой есть введённый текст (без учёта регистра).
        void FindNext()
        {
            string text = toolStripTextBoxFind.Text.Trim();
            if (text == "")
            {
                toolStripTextBoxFind.Focus();
                return;
            }
            int start = dataGridView1.CurrentRow == null ? -1 : dataGridView1.CurrentRow.Index;
            for (int k = 1; k <= Table.Count; k++)
            {
                int i = (start + k) % Table.Count;
                if (Table[i].Name.IndexOf(text, StringComparison.CurrentCultureIgnoreCase) >= 0)
                {
                    dataGridView1.ClearSelection();
                    dataGridView1.CurrentCell = dataGridView1.Rows[i].Cells["Name"];
                    dataGridView1.Rows[i].Selected = true;
                    return;
                }
            }
            MessageBox.Show("Записей с именем «" + text + "» не найдено.", "Поиск",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        void SortTable(Comparison<Record> comparison)
        {
            if (Table.Count < 2)
                return;
            SaveUndo();
            Table.Sort(comparison);
            SetModified();
            Redraw();
        }

        private void поИмениToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SortTable((a, b) => string.Compare(a.Name, b.Name, StringComparison.CurrentCulture));
        }

        private void поДатеРожденияToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SortTable((a, b) => a.BirthDate.CompareTo(b.BirthDate));
        }

        private void поОкладуToolStripMenuItem_Click(object sender, EventArgs e)
        {
            SortTable((a, b) => b.Money.CompareTo(a.Money));
        }

        private void итогиToolStripMenuItem_Click(object sender, EventArgs e)
        {
            if (!CheckNotEmpty())
                return;
            StringBuilder sb = new StringBuilder();
            var groups = Table.GroupBy(p => p.Department).OrderBy(g => g.Key);
            foreach (var g in groups)
                sb.AppendLine(string.Format("{0}: {1} чел., сумма {2:N2}, средний оклад {3:N2} руб.",
                    g.Key, g.Count(), g.Sum(p => p.Money), g.Average(p => p.Money)));
            sb.AppendLine();
            sb.AppendLine(string.Format("Всего: {0} чел., фонд оплаты {1:N2} руб.", Table.Count, Table.Sum(p => p.Money)));
            sb.AppendLine(string.Format("Средний оклад: {0:N2} руб.", Table.Average(p => p.Money)));
            Record max = Table.OrderByDescending(p => p.Money).First();
            sb.AppendLine(string.Format("Наибольший оклад: {0} ({1:N2} руб.)", max.Name, max.Money));
            MessageBox.Show(sb.ToString(), "Итоги по отделам", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        #endregion

        private void оПрограммеToolStripMenuItem_Click(object sender, EventArgs e)
        {
            MessageBox.Show(
                "Практическое задание 09-10: прикладная задача на списке.\n" +
                "Таблица сотрудников: имя, дата рождения, должность, отдел, оклад.\n\n" +
                "Данные хранятся в List<Record> и показываются в DataGridView.\n" +
                "Файлы — текстовые (*.txt), поля записи разделены знаком #.\n\n" +
                "Горячие клавиши:\n" +
                "Ctrl+N — создать, Ctrl+O — открыть, Ctrl+S — сохранить\n" +
                "Ctrl+A — добавить, Ctrl+E — изменить, Ctrl+D — удалить, Ctrl+Z — отмена\n" +
                "Ctrl+W — Word, Ctrl+Shift+E — Excel, Ctrl+Shift+N — NotePad\n" +
                "Ctrl+F — поиск, Ctrl+T — итоги по отделам",
                "О программе", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}
